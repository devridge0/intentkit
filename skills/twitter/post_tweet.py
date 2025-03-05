from typing import Type

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from clients.twitter import get_twitter_client
from skills.twitter.base import TwitterBaseTool


class TwitterPostTweetInput(BaseModel):
    """Input for TwitterPostTweet tool."""

    text: str = Field(
        description="The text content of the tweet to post", max_length=280
    )


class TwitterPostTweet(TwitterBaseTool):
    """Tool for posting tweets to Twitter.

    This tool uses the Twitter API v2 to post new tweets to Twitter.

    Attributes:
        name: The name of the tool.
        description: A description of what the tool does.
        args_schema: The schema for the tool's input arguments.
    """

    name: str = "twitter_post_tweet"
    description: str = "Post a new tweet to Twitter"
    args_schema: Type[BaseModel] = TwitterPostTweetInput

    async def _arun(self, text: str, config: RunnableConfig, **kwargs) -> str:
        """Async implementation of the tool to post a tweet.

        Args:
            text (str): The text content of the tweet to post.
            config (RunnableConfig): The configuration for the runnable, containing agent context.

        Returns:
            str: The ID of the posted tweet.

        Raises:
            Exception: If there's an error posting to the Twitter API.
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
                    context.agent.id, max_requests=24, interval=1440
                )

            client = await twitter.get_client()

            # Post tweet using tweepy client
            response = await client.create_tweet(text=text, user_auth=twitter.use_key)

            if "data" in response and "id" in response["data"]:
                tweet_id = response["data"]["id"]
                return tweet_id
            else:
                raise ValueError("Failed to post tweet.")

        except Exception as e:
            raise type(e)(f"[agent:{context.agent.id}]: {e}") from e
