"""Twitter OAuth2 token refresh functionality."""

import logging
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app.services.twitter.oauth2 import oauth2_user_handler
from models.agent import AgentData
from models.db import get_session

logger = logging.getLogger(__name__)


def get_expiring_tokens(db: Session, minutes_threshold: int = 10) -> list[AgentData]:
    """Get all agents with tokens expiring within the specified threshold.

    Args:
        db: Database session
        minutes_threshold: Number of minutes before expiration to consider tokens as expiring

    Returns:
        List of AgentData records with expiring tokens
    """
    expiration_threshold = datetime.now(timezone.utc) + timedelta(
        minutes=minutes_threshold
    )

    return db.exec(
        select(AgentData).where(
            AgentData.twitter_access_token.is_not(None),
            AgentData.twitter_refresh_token.is_not(None),
            AgentData.twitter_access_token_expires_at <= expiration_threshold,
        )
    ).all()


def refresh_token(db: Session, agent: AgentData) -> bool:
    """Refresh Twitter OAuth2 token for an agent.

    Args:
        db: Database session
        agent: Agent data record containing refresh token

    Returns:
        bool: True if refresh successful, False otherwise
    """
    try:
        # Get new token using refresh token
        token = oauth2_user_handler.refresh(agent.twitter_refresh_token)

        # Update token information
        agent.twitter_access_token = token["access_token"]
        if "refresh_token" in token:  # Some providers return new refresh tokens
            agent.twitter_refresh_token = token["refresh_token"]
        agent.twitter_access_token_expires_at = datetime.fromtimestamp(
            token["expires_at"], tz=timezone.utc
        )

        # Save changes
        db.add(agent)
        db.commit()
        db.refresh(agent)

        logger.info(f"Refreshed token for agent {agent.id}")
        return True
    except Exception as e:
        logger.error(f"Failed to refresh token for agent {agent.id}: {str(e)}")
        return False


def refresh_expiring_tokens():
    """Refresh all tokens that are about to expire.

    This function is designed to be called by the scheduler every minute.
    It will check for tokens expiring in the next 5 minutes and refresh them.
    """
    with get_session() as session:
        expiring_tokens = get_expiring_tokens(session)
        for agent in expiring_tokens:
            refresh_token(session, agent)
