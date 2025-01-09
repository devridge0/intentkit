from datetime import datetime, timedelta, timezone
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

            mentions = self.client.get_users_mentions(
                id=self.client.get_me()[0].id,
                max_results=max_results,
                since_id=since_id,
                start_time=start_time,
                tweet_fields=["created_at", "author_id", "text"],
            )

            if not mentions.data:
                return "No mentions found."

            # Format the mentions into a readable string
            result = []
            for tweet in mentions.data:
                result.append(
                    f"Tweet ID: {tweet.id}\n"
                    f"Created at: {tweet.created_at}\n"
                    f"Author ID: {tweet.author_id}\n"
                    f"Text: {tweet.text}\n"
                )

            # Update the previous since_id for the next request
            if mentions.meta:
                last["since_id"] = mentions.meta.get("newest_id")
                self.store.save_agent_skill_data(self.agent_id, self.name, "last", last)

            return "\n".join(result)

        except Exception as e:
            return f"Error retrieving mentions: {str(e)}"

    async def _arun(self) -> str:
        """Async implementation of the tool.

        This tool doesn't have a native async implementation, so we call the sync version.
        """
        return self._run()
