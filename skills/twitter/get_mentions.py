import logging
from datetime import datetime, timedelta, timezone
from typing import Type

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel

from clients.twitter import Tweet, get_twitter_client

from .base import TwitterBaseTool

logger = logging.getLogger(__name__)


class TwitterGetMentionsInput(BaseModel):
    """Input for TwitterGetMentions tool."""

    pass


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
    description: str = "Get tweets that mention you, the result is a list of json-formatted tweets. If the result is empty list, means no new mentions, don't retry."
    args_schema: Type[BaseModel] = TwitterGetMentionsInput

    async def _arun(self, config: RunnableConfig, **kwargs) -> list[Tweet]:
        """Async implementation of the tool to get mentions.

        Args:
            config (RunnableConfig): The configuration for the runnable, containing agent context.

        Returns:
            list[Tweet]: A list of tweets that mention the authenticated user.

        Raises:
            Exception: If there's an error accessing the Twitter API.
        """
        try:
            context = self.context_from_config(config)
            twitter = get_twitter_client(
                agent_id=context.agent.id,
                skill_store=self.skill_store,
                config=context.config,
            )

            # Check rate limit only when not using OAuth
            if not twitter.use_key:
                await self.check_rate_limit(
                    context.agent.id,
                    max_requests=1,
                    interval=15,  # TODO: tmp to 15, back to 240 later
                )

            # get since id from store
            last = await self.skill_store.get_agent_skill_data(
                context.agent.id, self.name, "last"
            )
            last = last or {}
            max_results = 10
            since_id = last.get("since_id")
            if since_id:
                max_results = 30

            # Always get mentions for the last day
            start_time = datetime.now(tz=timezone.utc) - timedelta(days=1)

            client = await twitter.get_client()
            user_id = twitter.self_id
            if not user_id:
                raise ValueError("Failed to get Twitter user ID.")

            mentions = await client.get_users_mentions(
                user_auth=twitter.use_key,
                id=user_id,
                max_results=max_results,
                since_id=since_id,
                start_time=start_time,
                expansions=[
                    "referenced_tweets.id",
                    "referenced_tweets.id.attachments.media_keys",
                    "referenced_tweets.id.author_id",
                    "attachments.media_keys",
                    "author_id",
                ],
                tweet_fields=[
                    "created_at",
                    "author_id",
                    "text",
                    "referenced_tweets",
                    "attachments",
                ],
                user_fields=[
                    "username",
                    "name",
                    "description",
                    "public_metrics",
                    "location",
                    "connection_status",
                ],
                media_fields=["url", "type", "width", "height"],
            )

            # Update since_id in store
            if mentions.get("meta") and mentions["meta"].get("newest_id"):
                last["since_id"] = mentions["meta"].get("newest_id")
                await self.skill_store.save_agent_skill_data(
                    context.agent.id, self.name, "last", last
                )

            return mentions

        except Exception as e:
            raise type(e)(f"[agent:{context.agent.id}]: {e}") from e
