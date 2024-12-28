from typing import Type

from pydantic import BaseModel

from skills.twitter.base import TwitterBaseTool


class TwitterGetTimelineInput(BaseModel):
    """Input for TwitterGetTimeline tool."""


class TwitterGetTimeline(TwitterBaseTool):
    """Tool for getting the user's timeline from Twitter.

    This tool uses the Twitter API v2 to retrieve tweets from the authenticated user's
    timeline.

    Attributes:
        name: The name of the tool.
        description: A description of what the tool does.
        args_schema: The schema for the tool's input arguments.
    """

    prev_timestamp: str | None = None
    name: str = "twitter_get_timeline"
    description: str = "Get tweets from the authenticated user's timeline"
    args_schema: Type[BaseModel] = TwitterGetTimelineInput

    def _run(self) -> str:
        """Run the tool to get timeline tweets.

        Returns:
            str: A formatted string containing the timeline tweets data.

        Raises:
            Exception: If there's an error accessing the Twitter API.
        """
        try:
            # Get timeline tweets using tweepy client
            max_results = 100
            timeline = self.client.get_home_timeline(
                max_results=max_results,
                start_time=self.prev_timestamp,
                tweet_fields=["created_at", "author_id", "text"],
            )

            if not timeline.data:
                return "No tweets found."

            # Update the previous timestamp for the next request
            self.prev_timestamp = (
                max(tweet.created_at for tweet in timeline.data)
                if timeline.data
                else None
            )

            # Format the tweets into a readable string
            result = []
            for tweet in timeline.data:
                result.append(
                    f"Tweet ID: {tweet.id}\n"
                    f"Created at: {tweet.created_at}\n"
                    f"Text: {tweet.text}\n"
                )

            return "\n".join(result)

        except Exception as e:
            return f"Error retrieving timeline: {str(e)}"

    async def _arun(self) -> str:
        """Async implementation of the tool.

        This tool doesn't have a native async implementation, so we call the sync version.
        """
        return self._run()
