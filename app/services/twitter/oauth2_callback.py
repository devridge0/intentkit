"""Twitter OAuth2 callback handler."""

from datetime import datetime, timezone

import tweepy
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlmodel import Session, select
from starlette.responses import JSONResponse

from app.config.config import config
from app.core.engine import initialize_agent
from app.services.twitter.oauth2 import oauth2_user_handler
from models.agent import AgentData
from models.db import get_db

router = APIRouter(prefix="/callback/auth", tags=["twitter"])


async def _background_task(agent_id: str):
    """Background task to perform after OAuth callback.

    Args:
        agent_id: ID of the agent to initialize
    """
    # Add any post-processing work here
    initialize_agent(agent_id)


@router.get("/twitter")
async def twitter_oauth_callback(
    state: str,
    code: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Handle Twitter OAuth2 callback.

    This endpoint is called by Twitter after the user authorizes the application.
    It exchanges the authorization code for access and refresh tokens, then stores
    them in the database.

    Args:
        state: Agent ID from authorization request
        code: Authorization code from Twitter
        background_tasks: FastAPI background tasks
        db: Database session from FastAPI dependency injection

    Returns:
        JSONResponse with success message

    Raises:
        HTTPException: If state/code is missing or token exchange fails
    """
    try:
        if not state or not code:
            raise HTTPException(
                status_code=400, detail="Missing state or code parameter"
            )

        agent_id = state
        agent_data = db.exec(select(AgentData).where(AgentData.id == agent_id)).first()

        if not agent_data:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        # Exchange code for tokens
        authorization_response = (
            f"{config.twitter_oauth2_redirect_uri}?state={state}&code={code}"
        )
        token = oauth2_user_handler.get_token(authorization_response)

        # Store tokens in database
        agent_data.twitter_access_token = token["access_token"]
        agent_data.twitter_refresh_token = token["refresh_token"]
        agent_data.twitter_token_expires_at = datetime.fromtimestamp(
            token["expires_at"], tz=timezone.utc
        )

        # Get user info
        client = tweepy.Client(bearer_token=token["access_token"])
        me = client.get_me()

        if me and me.data:
            agent_data.twitter_id = me.data.id
            agent_data.twitter_username = me.data.username
            agent_data.twitter_name = me.data.name

        # Commit changes
        db.commit()
        db.refresh(agent_data)

        # Schedule agent initialization as a background task
        background_tasks.add_task(_background_task, agent_id)

        return JSONResponse(
            content={"message": "Authentication successful, you can close this window"},
            status_code=200,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
