from typing import Type

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from clients.twitter import get_twitter_client
from skills.twitter.base import TwitterBaseTool


class TwitterReplyTweetInput(BaseModel):
    """Input for TwitterReplyTweet tool."""

    tweet_id: str = Field(description="The ID of the tweet to reply to")
    text: str = Field(description="The text content of the reply tweet", max_length=280)


class TwitterReplyTweet(TwitterBaseTool):
    """Tool for replying to tweets on Twitter.

    This tool uses the Twitter API v2 to post reply tweets to existing tweets.

    Attributes:
        name: The name of the tool.
        description: A description of what the tool does.
        args_schema: The schema for the tool's input arguments.
    """

    name: str = "twitter_reply_tweet"
    description: str = "Reply to an existing tweet on Twitter"
    args_schema: Type[BaseModel] = TwitterReplyTweetInput

    async def _arun(
        self, tweet_id: str, text: str, config: RunnableConfig, **kwargs
    ) -> str:
        """Async implementation of the tool to reply to a tweet.

        Args:
            tweet_id (str): The ID of the tweet to reply to.
            text (str): The text content of the reply.
            config (RunnableConfig): The configuration for the runnable, containing agent context.

        Returns:
            str: The ID of the posted reply tweet.

        Raises:
            Exception: If there's an error replying via the Twitter API.
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
                    context.agent.id, max_requests=48, interval=1440
                )

            client = await twitter.get_client()

            # Post reply tweet using tweepy client
            response = await client.create_tweet(
                text=text, user_auth=twitter.use_key, in_reply_to_tweet_id=tweet_id
            )

            if "data" in response and "id" in response["data"]:
                reply_id = response["data"]["id"]
                return reply_id
            else:
                raise ValueError("Failed to post reply tweet.")

        except Exception as e:
            raise type(e)(f"[agent:{context.agent.id}]: {e}") from e

    def _run(self, tweet_id: str, text: str) -> str:
        """Sync implementation of the tool.

        This method is deprecated since we now have native async implementation in _arun.
        """
        raise NotImplementedError(
            "Use _arun instead, which is the async implementation"
        )
