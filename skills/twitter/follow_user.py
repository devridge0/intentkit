from typing import Type

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from clients.twitter import get_twitter_client
from skills.twitter.base import TwitterBaseTool


class TwitterFollowUserInput(BaseModel):
    """Input for TwitterFollowUser tool."""

    user_id: str = Field(description="The ID of the user to follow")


class TwitterFollowUser(TwitterBaseTool):
    """Tool for following a Twitter user.

    This tool uses the Twitter API v2 to follow a user on Twitter.

    Attributes:
        name: The name of the tool.
        description: A description of what the tool does.
        args_schema: The schema for the tool's input arguments.
    """

    name: str = "twitter_follow_user"
    description: str = "Follow a Twitter user"
    args_schema: Type[BaseModel] = TwitterFollowUserInput

    async def _arun(self, user_id: str, config: RunnableConfig, **kwargs) -> bool:
        """Async implementation of the tool to follow a user.

        Args:
            user_id (str): The ID of the user to follow.
            config (RunnableConfig): The configuration for the runnable, containing agent context.

        Returns:
            bool: True if the user was successfully followed, otherwise raises an exception.

        Raises:
            Exception: If there's an error accessing the Twitter API or following the user.
        """
        try:
            context = self.context_from_config(config)
            twitter = get_twitter_client(
                agent_id=context.agent.id,
                skill_store=self.skill_store,
                config=context.config,
            )

            # Check rate limit only when not using OAuth
            if not twitter.use_key:
                await self.check_rate_limit(
                    context.agent.id, max_requests=5, interval=15
                )

            client = await twitter.get_client()

            # Follow the user using tweepy client
            response = await client.follow_user(
                target_user_id=user_id, user_auth=twitter.use_key
            )

            if response.data and response.data.get("following"):
                return True
            else:
                raise ValueError("Failed to follow user")

        except Exception as e:
            raise type(e)(f"[agent:{context.agent.id}]: {e}") from e
