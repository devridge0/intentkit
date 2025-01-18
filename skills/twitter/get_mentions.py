from datetime import datetime, timedelta, timezone
from typing import Type

from pydantic import BaseModel

from .base import Tweet, TwitterBaseTool


class TwitterGetMentionsInput(BaseModel):
    """Input for TwitterGetMentions tool."""


class TwitterGetMentionsOutput(BaseModel):
    mentions: list[Tweet]
    error: str | None = None


class TwitterGetMentions(TwitterBaseTool):
    """Tool for getting mentions from Twitter.

    This tool uses the Twitter API v2 to retrieve mentions (tweets in which the authenticated
    user is mentioned) from Twitter.

    Attributes:
        name: The name of the tool.
        description: A description of what the tool does.
        args_schema: The schema for the tool's input arguments.
    """

    name: str = "twitter_get_mentions"
    description: str = "Get tweets that mention the authenticated user"
    args_schema: Type[BaseModel] = TwitterGetMentionsInput

    def _run(self) -> TwitterGetMentionsOutput:
        """Run the tool to get mentions.

        Returns:
            TwitterGetMentionsOutput: A structured output containing the mentions data.

        Raises:
            Exception: If there's an error accessing the Twitter API.
        """
        try:
            # Check rate limit only when not using OAuth
            if not self.twitter.use_key:
                is_rate_limited, error = self.check_rate_limit(max_requests=1)
                if is_rate_limited:
                    return TwitterGetMentionsOutput(
                        mentions=[],
                        error=error,
                    )

            # get since id from store
            last = self.store.get_agent_skill_data(self.agent_id, self.name, "last")
            last = last or {}
            max_results = 10
            since_id = last.get("since_id")
            if since_id:
                max_results = 100

            # Always get mentions for the last day
            start_time = (datetime.now(tz=timezone.utc) - timedelta(days=1)).isoformat(
                timespec="milliseconds"
            )

            client = self.twitter.get_client()
            if not client:
                return TwitterGetMentionsOutput(
                    mentions=[],
                    error="Failed to get Twitter client. Please check your authentication.",
                )

            user_id = self.twitter.get_id()
            if not user_id:
                return TwitterGetMentionsOutput(
                    mentions=[], error="Failed to get Twitter user ID."
                )

            mentions = client.get_users_mentions(
                user_auth=self.twitter.use_key,
                id=user_id,
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
            if mentions.data:
                # Process and return results
                for tweet in mentions.data:
                    mention = Tweet(
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
                    result.append(mention)

            # Update the previous since_id for the next request
            if mentions.meta:
                last["since_id"] = mentions.meta.get("newest_id")
                self.store.save_agent_skill_data(self.agent_id, self.name, "last", last)

            return TwitterGetMentionsOutput(mentions=result)

        except Exception as e:
            return TwitterGetMentionsOutput(mentions=[], error=str(e))

    async def _arun(self) -> TwitterGetMentionsOutput:
        """Async implementation of the tool.

        This tool doesn't have a native async implementation, so we call the sync version.
        """
        return self._run()
