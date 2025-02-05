from typing import Type

from pydantic import BaseModel, Field

from skills.twitter.base import TwitterBaseTool


class TwitterLikeTweetInput(BaseModel):
    """Input for TwitterLikeTweet tool."""

    tweet_id: str = Field(description="The ID of the tweet to like")


class TwitterLikeTweetOutput(BaseModel):
    """Output for TwitterLikeTweet tool."""

    success: bool
    message: str


class TwitterLikeTweet(TwitterBaseTool):
    """Tool for liking tweets on Twitter.

    This tool uses the Twitter API v2 to like tweets on Twitter.

    Attributes:
        name: The name of the tool.
        description: A description of what the tool does.
        args_schema: The schema for the tool's input arguments.
    """

    name: str = "twitter_like_tweet"
    description: str = "Like a tweet on Twitter"
    args_schema: Type[BaseModel] = TwitterLikeTweetInput

    async def _arun(self, tweet_id: str) -> TwitterLikeTweetOutput:
        """Async implementation of the tool to like a tweet.

        Args:
            tweet_id (str): The ID of the tweet to like.

        Returns:
            TwitterLikeTweetOutput: A structured output containing the result of the like action.

        Raises:
            Exception: If there's an error accessing the Twitter API.
        """
        try:
            # Check rate limit only when not using OAuth
            if not self.twitter.use_key:
                is_rate_limited, error = await self.check_rate_limit(
                    max_requests=100, interval=1440
                )
                if is_rate_limited:
                    return TwitterLikeTweetOutput(
                        success=False, message=f"Error liking tweet: {error}"
                    )

            client = await self.twitter.get_client()
            if not client:
                return TwitterLikeTweetOutput(
                    success=False,
                    message=self._get_error_with_username(
                        "Failed to get Twitter client. Please check your authentication."
                    ),
                )

            # Like the tweet using tweepy client
            response = await client.like(
                tweet_id=tweet_id, user_auth=self.twitter.use_key
            )

            if "data" in response and "liked" in response["data"]:
                return TwitterLikeTweetOutput(
                    success=True, message=f"Successfully liked tweet {tweet_id}"
                )
            return TwitterLikeTweetOutput(
                success=False,
                message=self._get_error_with_username("Failed to like tweet."),
            )

        except Exception as e:
            return TwitterLikeTweetOutput(
                success=False, message=self._get_error_with_username(str(e))
            )

    def _run(self, tweet_id: str) -> TwitterLikeTweetOutput:
        """Sync implementation of the tool.

        This method is deprecated since we now have native async implementation in _arun.
        """
        raise NotImplementedError(
            "Use _arun instead, which is the async implementation"
        )
