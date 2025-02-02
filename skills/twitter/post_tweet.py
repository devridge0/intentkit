from typing import Type

from pydantic import BaseModel, Field

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

    async def _arun(self, text: str) -> str:
        """Async implementation of the tool to post a tweet.

        Args:
            text (str): The text content of the tweet to post.

        Returns:
            str: A message indicating success or failure of the tweet posting.

        Raises:
            Exception: If there's an error posting to the Twitter API.
        """
        try:
            # Check rate limit only when not using OAuth
            if not self.twitter.use_key:
                is_rate_limited, error = await self.check_rate_limit(
                    max_requests=24, interval=1440
                )
                if is_rate_limited:
                    return f"Error posting tweet: {error}"

            client = self.twitter.get_client()
            if not client:
                return self._get_error_with_username(
                    "Failed to get Twitter client. Please check your authentication."
                )

            # Post tweet using tweepy client
            response = await client.create_tweet(
                text=text, user_auth=self.twitter.use_key
            )

            if "data" in response and "id" in response["data"]:
                tweet_id = response["data"]["id"]
                return f"Tweet posted successfully! Tweet ID: {tweet_id}"
            return self._get_error_with_username("Failed to post tweet.")

        except Exception as e:
            return self._get_error_with_username(str(e))

    def _run(self, text: str) -> str:
        """Sync implementation of the tool.

        This method is deprecated since we now have native async implementation in _arun.
        """
        raise NotImplementedError(
            "Use _arun instead, which is the async implementation"
        )
