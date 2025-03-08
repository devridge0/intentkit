from typing import Type

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from clients.twitter import get_twitter_client
from skills.twitter.base import TwitterBaseTool


class TwitterRetweetInput(BaseModel):
    """Input for TwitterRetweet tool."""

    tweet_id: str = Field(description="The ID of the tweet to retweet")


class TwitterRetweet(TwitterBaseTool):
    """Tool for retweeting tweets on Twitter.

    This tool uses the Twitter API v2 to retweet tweets on Twitter.

    Attributes:
        name: The name of the tool.
        description: A description of what the tool does.
        args_schema: The schema for the tool's input arguments.
    """

    name: str = "twitter_retweet"
    description: str = "Retweet a tweet on Twitter"
    args_schema: Type[BaseModel] = TwitterRetweetInput

    async def _arun(self, tweet_id: str, config: RunnableConfig, **kwargs) -> bool:
        """Async implementation of the tool to retweet a tweet.

        Args:
            tweet_id (str): The ID of the tweet to retweet.
            config (RunnableConfig): The configuration for the runnable, containing agent context.

        Returns:
            bool: True if the tweet was successfully retweeted.

        Raises:
            Exception: If there's an error accessing the Twitter API.
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

            # Get authenticated user's ID
            user_id = twitter.self_id
            if not user_id:
                raise ValueError("Failed to get authenticated user ID.")

            # Retweet the tweet using tweepy client
            response = await client.retweet(
                tweet_id=tweet_id, user_auth=twitter.use_key
            )

            if (
                "data" in response
                and "retweeted" in response["data"]
                and response["data"]["retweeted"]
            ):
                return True
            else:
                raise ValueError("Failed to retweet.")

        except Exception as e:
            raise type(e)(f"[agent:{context.agent.id}]: {e}") from e
