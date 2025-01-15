"""Twitter OAuth2 authentication module."""

from datetime import datetime, timezone

import tweepy
from fastapi import APIRouter, Depends, HTTPException
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session
from sqlmodel import Session, select
from starlette.responses import JSONResponse

from app.config.config import config
from models.agent import AgentData
from models.db import get_db


# this class is forked from:
# https://github.com/tweepy/tweepy/blob/main/tweepy/auth.py
# it is not maintained by the original author, bug need to be fixed
class OAuth2UserHandler(OAuth2Session):
    """OAuth 2.0 Authorization Code Flow with PKCE (User Context)
    authentication handler
    """

    def __init__(self, *, client_id, redirect_uri, scope, client_secret=None):
        super().__init__(client_id, redirect_uri=redirect_uri, scope=scope)
        if client_secret is not None:
            self.auth = HTTPBasicAuth(client_id, client_secret)
        else:
            self.auth = None

    def get_authorization_url(self, agent_id: str):
        """Get the authorization URL to redirect the user to"""
        authorization_url, _ = self.authorization_url(
            "https://twitter.com/i/oauth2/authorize",
            state=agent_id,
            code_challenge=self._client.create_code_challenge(
                self._client.create_code_verifier(128), "S256"
            ),
            code_challenge_method="S256",
        )
        return authorization_url

    def get_token(self, authorization_response):
        """After user has authorized the app, fetch access token with
        authorization response URL
        """
        return super().fetch_token(
            "https://api.twitter.com/2/oauth2/token",
            authorization_response=authorization_response,
            auth=self.auth,
            include_client_id=True,
            code_verifier=self._client.code_verifier,
        )

    def refresh(self, refresh_token: str):
        """Refresh token"""
        return super().refresh_token(
            "https://api.twitter.com/2/oauth2/token",
            refresh_token=refresh_token,
            include_client_id=True,
        )


router = APIRouter(prefix="/callback/auth", tags=["twitter"])

# Initialize Twitter OAuth2 client
oauth2_user_handler = OAuth2UserHandler(
    client_id=config.twitter_oauth2_client_id,
    client_secret=config.twitter_oauth2_client_secret,
    redirect_uri=config.twitter_oauth2_redirect_uri,
    scope=[
        "tweet.read",
        "tweet.write",
        "users.read",
        "offline.access",
        "follows.read",
        "follows.write",
        "like.read",
        "like.write",
        "media.write",
    ],
)


def get_authorization_url(agent_id: str) -> str:
    """Get Twitter OAuth2 authorization URL.

    Args:
        agent_id: ID of the agent to authenticate

    Returns:
        Authorization URL with agent_id as state parameter
    """
    return oauth2_user_handler.get_authorization_url(agent_id)


@router.get("/twitter")
async def twitter_oauth_callback(state: str, code: str, db: Session = Depends(get_db)):
    """Handle Twitter OAuth2 callback.

    This endpoint is called by Twitter after the user authorizes the application.
    It exchanges the authorization code for access and refresh tokens, then stores
    them in the database.

    Args:
        state: Agent ID from authorization request
        code: Authorization code from Twitter
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

        # State is the agent ID
        agent_id = state

        # Get access token
        url = f"{config.twitter_oauth2_redirect_uri}?state={agent_id}&code={code}"
        token = oauth2_user_handler.get_token(url)

        # Get agent data from database
        agent_data = db.exec(select(AgentData).where(AgentData.id == agent_id)).first()

        # Create agent data if it doesn't exist
        if not agent_data:
            agent_data = AgentData(id=agent_id)
            db.add(agent_data)

        # Update token information
        agent_data.twitter_access_token = token["access_token"]
        agent_data.twitter_refresh_token = token["refresh_token"]
        agent_data.twitter_access_token_expires_at = datetime.fromtimestamp(
            token["expires_at"], tz=timezone.utc
        )

        # Get user info from Twitter
        client = tweepy.Client(bearer_token=token["access_token"])
        me = client.get_me(user_auth=False)
        if me and me.data:
            agent_data.twitter_id = str(me.data.id)
            agent_data.twitter_username = me.data.username
            agent_data.twitter_name = me.data.name

        # Commit changes
        db.commit()
        db.refresh(agent_data)

        return JSONResponse(
            content={"message": "Authentication successful, you can close this window"},
            status_code=200,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
