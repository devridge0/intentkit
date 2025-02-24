import logging
from datetime import datetime, timezone
from typing import Dict, NotRequired, Optional, TypedDict

from tweepy.asynchronous import AsyncClient

from abstracts.agent import AgentStoreABC
from abstracts.twitter import TwitterABC
from models.agent import AgentData

logger = logging.getLogger(__name__)


class TwitterClientConfig(TypedDict):
    consumer_key: NotRequired[str]
    consumer_secret: NotRequired[str]
    access_token: NotRequired[str]
    access_token_secret: NotRequired[str]


class TwitterClient(TwitterABC):
    """Implementation of Twitter operations using Tweepy client.

    This class provides concrete implementations for interacting with Twitter's API
    through a Tweepy client, supporting both API key and OAuth2 authentication.

    Args:
        agent_store: The agent store for persisting data
        config: Configuration dictionary that may contain API keys
    """

    def __init__(self, agent_id, agent_store: AgentStoreABC, config: Dict) -> None:
        """Initialize the Twitter client.

        Args:
            agent_store: The agent store for persisting data
            config: Configuration dictionary that may contain API keys
        """
        self.agent_id = agent_id
        self._client: Optional[AsyncClient] = None
        self._agent_store = agent_store
        self._agent_data: Optional[AgentData] = None
        self.use_key = False
        self._config = config

    async def get_client(self) -> Optional[AsyncClient]:
        """Get the initialized Twitter client.

        Returns:
            Optional[AsyncClient]: The Twitter client if initialized, None otherwise
        """
        if not self._agent_data:
            self._agent_data = await self._agent_store.get_data()
            if not self._agent_data:
                raise Exception(f"[{self.agent_id}] Agent data not found")
        if not self._client:
            # Check if we have API keys in config
            if self._config and all(
                key in self._config and self._config[key]
                for key in [
                    "consumer_key",
                    "consumer_secret",
                    "access_token",
                    "access_token_secret",
                ]
            ):
                self._client = AsyncClient(
                    consumer_key=self._config["consumer_key"],
                    consumer_secret=self._config["consumer_secret"],
                    access_token=self._config["access_token"],
                    access_token_secret=self._config["access_token_secret"],
                    return_type=dict,
                )
                self.use_key = True
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
                return self._client
            # Otherwise try to get OAuth2 tokens from agent data
            if not self._agent_data.twitter_access_token:
                raise Exception(f"[{self.agent_id}] Twitter access token not found")
            if not self._agent_data.twitter_access_token_expires_at:
                raise Exception(
                    f"[{self.agent_id}] Twitter access token expiration not found"
                )
            if self._agent_data.twitter_access_token_expires_at <= datetime.now(
                tz=timezone.utc
            ):
                raise Exception(f"[{self.agent_id}] Twitter access token has expired")
            self._client = AsyncClient(
                bearer_token=self._agent_data.twitter_access_token,
                return_type=dict,
            )
            return self._client
        if not self.use_key:
            # check if access token has expired
            if self._agent_data.twitter_access_token_expires_at <= datetime.now(
                tz=timezone.utc
            ):
                self._agent_data = await self._agent_store.get_data()
                # check again
                if self._agent_data.twitter_access_token_expires_at <= datetime.now(
                    tz=timezone.utc
                ):
                    raise Exception(
                        f"[{self.agent_id}] Twitter access token has expired"
                    )
                self._client = AsyncClient(
                    bearer_token=self._agent_data.twitter_access_token,
                    return_type=dict,
                )
                return self._client
        return self._client

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
