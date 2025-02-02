from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from tweepy.asynchronous import AsyncClient

from models.agent import AgentData


class TwitterABC(ABC):
    """Abstract base class for Twitter operations.

    This class defines the interface for interacting with Twitter's API
    through a Tweepy client.
    """

    use_key = False
    need_auth = True

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the Twitter client with OAuth2 tokens if available."""
        pass

    @abstractmethod
    async def update_tokens(
        self, access_token: str, refresh_token: str, expires_at: datetime
    ) -> None:
        """Update OAuth2 tokens in agent data.

        Args:
            access_token: New access token
            refresh_token: New refresh token
            expires_at: Token expiration timestamp
        """
        pass

    @abstractmethod
    def get_client(self) -> Optional[AsyncClient]:
        """Get a configured Tweepy client.

        Returns:
            A configured Tweepy client if credentials are valid, None otherwise
        """
        pass

    @abstractmethod
    def get_agent_data(self) -> Optional[AgentData]:
        """Get the agent data.

        Returns:
            Optional[AgentData]: The agent data if available, None otherwise
        """
        pass

    @property
    @abstractmethod
    def self_id(self) -> Optional[str]:
        """Get the Twitter user ID.

        Returns:
            The Twitter user ID if available, None otherwise
        """
        pass

    @property
    @abstractmethod
    def self_username(self) -> Optional[str]:
        """Get the Twitter username.

        Returns:
            The Twitter username (without @ symbol) if available, None otherwise
        """
        pass

    @property
    @abstractmethod
    def self_name(self) -> Optional[str]:
        """Get the Twitter display name.

        Returns:
            The Twitter display name if available, None otherwise
        """
        pass
