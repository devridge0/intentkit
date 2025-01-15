from datetime import datetime, timedelta, timezone
from typing import Type

from pydantic import BaseModel

from .base import Tweet, TwitterBaseTool


class TwitterGetTimelineInput(BaseModel):
    """Input for TwitterGetTimeline tool."""


class TwitterGetTimelineOutput(BaseModel):
    tweets: list[Tweet]
    error: str | None = None


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

    def _run(self) -> TwitterGetTimelineOutput:
        """Run the tool to get timeline tweets.

        Returns:
            TwitterGetTimelineOutput: A structured output containing the timeline tweets data.

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

            client = self.twitter.get_client()
            if not client:
                return TwitterGetTimelineOutput(
                    tweets=[],
                    error="Failed to get Twitter client. Please check your authentication.",
                )

            timeline = client.get_home_timeline(
                max_results=max_results,
                since_id=since_id,
                start_time=start_time,
                expansions=[
                    "referenced_tweets.id",
                    "attachments.media_keys",
                ],
                tweet_fields=[
                    "created_at",
                    "author_id",
                    "text",
                    "referenced_tweets",
                    "attachments",
                ],
            )

            result = []
            if timeline.data:
                for tweet in timeline.data:
                    tweet_obj = Tweet(
                        id=str(tweet.id),
                        text=tweet.text,
                        author_id=str(tweet.author_id),
                        created_at=tweet.created_at,
                        referenced_tweets=tweet.referenced_tweets
                        if hasattr(tweet, "referenced_tweets")
                        else None,
                        attachments=tweet.attachments
                        if hasattr(tweet, "attachments")
                        else None,
                    )
                    result.append(tweet_obj)

            # Update the since_id in store for the next request
            if timeline.meta:
                last["since_id"] = timeline.meta.get("newest_id")
                self.store.save_agent_skill_data(self.agent_id, self.name, "last", last)

            return TwitterGetTimelineOutput(tweets=result)

        except Exception as e:
            return TwitterGetTimelineOutput(tweets=[], error=str(e))

    async def _arun(self) -> TwitterGetTimelineOutput:
        """Async implementation of the tool.

        This tool doesn't have a native async implementation, so we call the sync version.
        """
        return self._run()
