from datetime import datetime, timedelta, timezone
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
            # get since id from store
            last = self.store.get_agent_skill_data(self.agent_id, self.name, "last")
            last = last or {}
            max_results = 10
            since_id = last.get("since_id")
            if since_id:
                max_results = 100

            # Always get timeline for the last day
            start_time = datetime.now(timezone.utc) - timedelta(days=1)

            timeline = self.client.get_home_timeline(
                max_results=max_results,
                since_id=since_id,
                start_time=start_time,
                tweet_fields=["created_at", "author_id", "text"],
            )

            if not timeline.data:
                return "No tweets found."

            # Format the timeline tweets into a readable string
            result = []
            for tweet in timeline.data:
                result.append(
                    f"Tweet ID: {tweet.id}\n"
                    f"Author ID: {tweet.author_id}\n"
                    f"Created at: {tweet.created_at}\n"
                    f"Text: {tweet.text}\n"
                )

            # Update the since_id in store for the next request
            if timeline.meta:
                last["since_id"] = timeline.meta.get("newest_id")
                self.store.save_agent_skill_data(self.agent_id, self.name, "last", last)

            return "\n".join(result)

        except Exception as e:
            return f"Error getting timeline: {str(e)}"

    async def _arun(self) -> str:
        """Async implementation of the tool.

        This tool doesn't have a native async implementation, so we call the sync version.
        """
        return self._run()
