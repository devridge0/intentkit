"""Twitter OAuth2 token refresh functionality."""

import logging
from datetime import datetime, timedelta, timezone

from sqlmodel import select

from app.services.twitter.oauth2 import oauth2_user_handler
from models.agent import AgentData
from models.db import get_session

logger = logging.getLogger(__name__)


async def get_expiring_tokens(minutes_threshold: int = 10) -> list[AgentData]:
    """Get all agents with tokens expiring within the specified threshold.

    Args:
        minutes_threshold: Number of minutes before expiration to consider tokens as expiring

    Returns:
        List of AgentData records with expiring tokens
    """
    expiration_threshold = datetime.now(timezone.utc) + timedelta(
        minutes=minutes_threshold
    )

    async with get_session() as db:
        result = await db.exec(
            select(AgentData).where(
                AgentData.twitter_access_token.is_not(None),
                AgentData.twitter_refresh_token.is_not(None),
                AgentData.twitter_access_token_expires_at <= expiration_threshold,
            )
        )
    return result.all()


async def refresh_token(agent_data: AgentData):
    """Refresh Twitter OAuth2 token for an agent.

    Args:
        agent_data: Agent data record containing refresh token
    """
    try:
        # Get new token using refresh token
        token = oauth2_user_handler.refresh(agent_data.twitter_refresh_token)

        token = {} if token is None else token

        # Update token information
        agent_data.twitter_access_token = token.get("access_token")
        agent_data.twitter_refresh_token = token.get("refresh_token")
        if "expires_at" in token:
            agent_data.twitter_access_token_expires_at = datetime.fromtimestamp(
                token["expires_at"], timezone.utc
            )

        await agent_data.save()

        logger.info(
            f"Successfully refreshed Twitter token for agent {agent_data.id}, "
            f"expires at {agent_data.twitter_access_token_expires_at}"
        )
    except Exception as e:
        logger.error(
            f"Failed to refresh Twitter token for agent {agent_data.id}: {str(e)}"
        )


async def refresh_expiring_tokens():
    """Refresh all tokens that are about to expire.

    This function is designed to be called by the scheduler every minute.
    It will check for tokens expiring in the next 5 minutes and refresh them.
    """
    agents = await get_expiring_tokens()
    for agent in agents:
        await refresh_token(agent)
