from typing import Type

from pydantic import BaseModel, Field

from skills.twitter.base import TwitterBaseTool


class TwitterRetweetInput(BaseModel):
    """Input for TwitterRetweet tool."""

    tweet_id: str = Field(description="The ID of the tweet to retweet")


class TwitterRetweetOutput(BaseModel):
    """Output for TwitterRetweet tool."""

    success: bool
    message: str


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

    async def _arun(self, tweet_id: str) -> TwitterRetweetOutput:
        """Async implementation of the tool to retweet a tweet.

        Args:
            tweet_id (str): The ID of the tweet to retweet.

        Returns:
            TwitterRetweetOutput: A structured output containing the result of the retweet action.

        Raises:
            Exception: If there's an error accessing the Twitter API.
        """
        try:
            # Check rate limit only when not using OAuth
            if not self.twitter.use_key:
                is_rate_limited, error = await self.check_rate_limit(
                    max_requests=5, interval=15
                )
                if is_rate_limited:
                    return TwitterRetweetOutput(
                        success=False, message=f"Error retweeting: {error}"
                    )

            client = self.twitter.get_client()
            if not client:
                return TwitterRetweetOutput(
                    success=False,
                    message=self._get_error_with_username(
                        "Failed to get Twitter client. Please check your authentication."
                    ),
                )

            # Get authenticated user's ID
            user_id = self.twitter.self_id
            if not user_id:
                return TwitterRetweetOutput(
                    success=False, message="Failed to get authenticated user ID."
                )

            # Retweet the tweet using tweepy client
            response = await client.retweet(
                tweet_id=tweet_id, user_auth=self.twitter.use_key
            )

            if (
                "data" in response
                and "retweeted" in response["data"]
                and response["data"]["retweeted"]
            ):
                return TwitterRetweetOutput(
                    success=True, message=f"Successfully retweeted tweet {tweet_id}"
                )
            return TwitterRetweetOutput(
                success=False,
                message=self._get_error_with_username("Failed to retweet."),
            )

        except Exception as e:
            return TwitterRetweetOutput(
                success=False, message=self._get_error_with_username(str(e))
            )

    def _run(self, tweet_id: str) -> TwitterRetweetOutput:
        """Sync implementation of the tool.

        This method is deprecated since we now have native async implementation in _arun.
        """
        raise NotImplementedError(
            "Use _arun instead, which is the async implementation"
        )
