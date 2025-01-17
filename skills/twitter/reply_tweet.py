from typing import Type

from pydantic import BaseModel, Field

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

    def _run(self, tweet_id: str, text: str) -> str:
        """Run the tool to post a reply tweet.

        Args:
            tweet_id (str): The ID of the tweet to reply to.
            text (str): The text content of the reply tweet.

        Returns:
            str: A message indicating success or failure of the reply posting.

        Raises:
            Exception: If there's an error posting to the Twitter API.
        """
        try:
            client = self.twitter.get_client()
            if not client:
                return "Failed to get Twitter client. Please check your authentication."

            # Post reply tweet using tweepy client
            response = client.create_tweet(
                text=text, user_auth=self.twitter.use_key, in_reply_to_tweet_id=tweet_id
            )

            if response.data:
                reply_id = response.data["id"]
                return f"Reply posted successfully! Reply Tweet ID: {reply_id}"
            return "Failed to post reply tweet."

        except Exception as e:
            return f"Error posting reply tweet: {str(e)}"

    async def _arun(self, tweet_id: str, text: str) -> str:
        """Async implementation of the tool.

        This tool doesn't have a native async implementation, so we call the sync version.
        """
        return self._run(tweet_id=tweet_id, text=text)
