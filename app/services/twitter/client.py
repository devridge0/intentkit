import logging
from datetime import datetime, timezone
from typing import Dict, Optional

from tweepy.asynchronous import AsyncClient

from abstracts.agent import AgentStoreABC
from abstracts.twitter import TwitterABC
from models.agent import AgentData

logger = logging.getLogger(__name__)


class TwitterClient(TwitterABC):
    """Implementation of Twitter operations using Tweepy client.

    This class provides concrete implementations for interacting with Twitter's API
    through a Tweepy client, supporting both API key and OAuth2 authentication.

    Args:
        agent_store: The agent store for persisting data
        config: Configuration dictionary that may contain API keys
    """

    def __init__(self, agent_store: AgentStoreABC, config: Dict) -> None:
        """Initialize the Twitter client.

        Args:
            agent_store: The agent store for persisting data
            config: Configuration dictionary that may contain API keys
        """
        self._client: Optional[AsyncClient] = None
        self._agent_store = agent_store
        self._agent_data: Optional[AgentData] = None
        self.use_key = False
        self.need_auth = False

        # Check if we have API keys in config
        if all(
            key in config and config[key]
            for key in [
                "consumer_key",
                "consumer_secret",
                "access_token",
                "access_token_secret",
            ]
        ):
            self._client = AsyncClient(
                consumer_key=config["consumer_key"],
                consumer_secret=config["consumer_secret"],
                access_token=config["access_token"],
                access_token_secret=config["access_token_secret"],
                return_type=dict,
            )
            self.use_key = True
            return

        # Otherwise try to get OAuth2 tokens from agent data
        self._agent_data = None
        self.need_auth = True

    async def initialize(self) -> None:
        """Initialize the Twitter client with OAuth2 tokens if available."""
        if self.use_key:
            me = await self._client.get_me(user_auth=self.use_key)
            if me and "data" in me and "id" in me["data"]:
                await self._agent_store.set_data(
                    {
                        "twitter_id": me["data"]["id"],
                        "twitter_username": me["data"]["username"],
                        "twitter_name": me["data"]["name"],
                    }
                )
            self._agent_data = await self._agent_store.get_data()
            logger.info(
                f"Twitter client initialized. "
                f"Use API key: {self.use_key}, "
                f"User ID: {self.self_id}, "
                f"Username: {self.self_username}, "
                f"Name: {self.self_name}"
            )
            return

        self._agent_data = await self._agent_store.get_data()
        if not self._agent_data:
            return

        if (
            self._agent_data.twitter_access_token
            and self._agent_data.twitter_access_token_expires_at
        ):
            # Check if token is expired
            if self._agent_data.twitter_access_token_expires_at <= datetime.now(
                tz=timezone.utc
            ):
                self.need_auth = True
                return

            # Initialize client with access token
            self._client = AsyncClient(
                bearer_token=self._agent_data.twitter_access_token,
                return_type=dict,
            )
            self.need_auth = False

    async def update_tokens(
        self, access_token: str, refresh_token: str, expires_at: datetime
    ) -> None:
        """Update OAuth2 tokens in agent data.

        Args:
            access_token: New access token
            refresh_token: New refresh token
            expires_at: Token expiration timestamp
        """
        if not self._agent_data:
            self._agent_data = await self._agent_store.get_data()
            if not self._agent_data:
                return

        self._agent_data.twitter_access_token = access_token
        self._agent_data.twitter_refresh_token = refresh_token
        self._agent_data.twitter_access_token_expires_at = expires_at
        await self._agent_store.set_data(self._agent_data)

        # Update client with new access token
        self._client = AsyncClient(bearer_token=access_token, return_type=dict)
        self.need_auth = False

    def get_client(self) -> Optional[AsyncClient]:
        """Get the initialized Twitter client.

        Returns:
            Optional[AsyncClient]: The Twitter client if initialized, None otherwise
        """
        return self._client

    def get_agent_data(self) -> Optional[AgentData]:
        """Get the agent data.

        Returns:
            Optional[AgentData]: The agent data if available, None otherwise
        """
        return self._agent_data

    @property
    def self_id(self) -> Optional[str]:
        """Get the Twitter user ID.

        Returns:
            The Twitter user ID if available, None otherwise
        """
        if not self._client:
            return None
        if not self._agent_data:
            return None
        return self._agent_data.twitter_id

    @property
    def self_username(self) -> Optional[str]:
        """Get the Twitter username.

        Returns:
            The Twitter username (without @ symbol) if available, None otherwise
        """
        if not self._client:
            return None
        if not self._agent_data:
            return None
        return self._agent_data.twitter_username

    @property
    def self_name(self) -> Optional[str]:
        """Get the Twitter display name.

        Returns:
            The Twitter display name if available, None otherwise
        """
        if not self._client:
            return None
        if not self._agent_data:
            return None
        return self._agent_data.twitter_name
