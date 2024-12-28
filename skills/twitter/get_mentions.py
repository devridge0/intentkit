from typing import Type

from pydantic import BaseModel

from skills.twitter.base import TwitterBaseTool


class TwitterGetMentionsInput(BaseModel):
    """Input for TwitterGetMentions tool."""


class TwitterGetMentions(TwitterBaseTool):
    """Tool for getting mentions from Twitter.

    This tool uses the Twitter API v2 to retrieve mentions (tweets in which the authenticated
    user is mentioned) from Twitter.

    Attributes:
        name: The name of the tool.
        description: A description of what the tool does.
        args_schema: The schema for the tool's input arguments.
    """

    prev_timestamp: str | None = None
    name: str = "twitter_get_mentions"
    description: str = "Get tweets that mention the authenticated user"
    args_schema: Type[BaseModel] = TwitterGetMentionsInput

    def _run(self) -> str:
        """Run the tool to get mentions.

        Returns:
            str: A formatted string containing the mentions data.

        Raises:
            Exception: If there's an error accessing the Twitter API.
        """
        try:
            # Get mentions using tweepy client
            max_results = 10
            start_time = self.prev_timestamp
            if self.prev_timestamp:
                max_results = 100
            mentions = self.client.get_users_mentions(
                id=self.client.get_me()[0].id,
                max_results=max_results,
                start_time=start_time,
                tweet_fields=["created_at", "author_id", "text"],
            )

            if not mentions.data:
                return "No mentions found."

            # Update the previous timestamp, so we can use it for the next request
            self.prev_timestamp = (
                max(tweet.created_at for tweet in mentions.data)
                if mentions.data
                else None
            )

            # Format the mentions into a readable string
            result = []
            for tweet in mentions.data:
                result.append(
                    f"Tweet ID: {tweet.id}\n"
                    f"Created at: {tweet.created_at}\n"
                    f"Author ID: {tweet.author_id}\n"
                    f"Text: {tweet.text}\n"
                )

            return "\n".join(result)

        except Exception as e:
            return f"Error retrieving mentions: {str(e)}"

    async def _arun(self) -> str:
        """Async implementation of the tool.

        This tool doesn't have a native async implementation, so we call the sync version.
        """
        return self._run()
