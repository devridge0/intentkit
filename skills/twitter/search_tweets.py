import logging
from typing import Type

from pydantic import BaseModel, Field

from skills.twitter.base import Tweet, TwitterBaseTool

logger = logging.getLogger(__name__)


class TwitterSearchTweetsInput(BaseModel):
    """Input for TwitterSearchTweets tool."""

    query: str = Field(description="The search query to find tweets")


class TwitterSearchTweetsOutput(BaseModel):
    """Output for TwitterSearchTweets tool."""

    tweets: list[Tweet]
    error: str | None = None


class TwitterSearchTweets(TwitterBaseTool):
    """Tool for searching recent tweets on Twitter.

    This tool uses the Twitter API v2 to search for recent tweets based on a query.

    Attributes:
        name: The name of the tool.
        description: A description of what the tool does.
        args_schema: The schema for the tool's input arguments.
    """

    name: str = "twitter_search_tweets"
    description: str = "Search for recent tweets on Twitter using a query"
    args_schema: Type[BaseModel] = TwitterSearchTweetsInput

    def _run(
        self, query: str, max_results: int = 10, recent_only: bool = True
    ) -> TwitterSearchTweetsOutput:
        """Run the tool to search tweets.

        Args:
            query (str): The search query to use.
            max_results (int, optional): Maximum number of results to return. Defaults to 10.
            recent_only (bool, optional): Whether to only search recent tweets. Defaults to True.

        Returns:
            TwitterSearchTweetsOutput: A structured output containing the search results.

        Raises:
            Exception: If there's an error searching via the Twitter API.
        """
        try:
            # Check rate limit only when not using OAuth
            if not self.twitter.use_key:
                is_rate_limited, error = self.check_rate_limit(max_requests=1, interval=15)
                if is_rate_limited:
                    return TwitterSearchTweetsOutput(tweets=[], error=error)

            client = self.twitter.get_client()
            if not client:
                return TwitterSearchTweetsOutput(
                    tweets=[],
                    error="Failed to get Twitter client. Please check your authentication.",
                )

            # Get since_id from store to avoid duplicate results
            last = self.store.get_agent_skill_data(self.agent_id, self.name, query)
            last = last or {}
            since_id = last.get("since_id")

            tweet_fields = [
                "created_at",
                "author_id",
                "text",
                "referenced_tweets",
                "attachments",
            ]
            tweets = client.search_recent_tweets(
                query=query,
                user_auth=self.twitter.use_key,
                since_id=since_id,
                expansions=[
                    "referenced_tweets.id",
                    "attachments.media_keys",
                ],
                tweet_fields=tweet_fields,
            )

            result = []
            if tweets.data:
                logger.debug(tweets.data)
                for tweet in tweets.data:
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
                if tweets.meta:
                    last["since_id"] = tweets.meta.get("newest_id")
                    self.store.save_agent_skill_data(
                        self.agent_id, self.name, query, last
                    )

            return TwitterSearchTweetsOutput(tweets=result)

        except Exception as e:
            return TwitterSearchTweetsOutput(
                tweets=[], error=f"Error searching tweets: {str(e)}"
            )

    async def _arun(self, query: str) -> TwitterSearchTweetsOutput:
        """Async implementation of the tool.

        This tool doesn't have a native async implementation, so we call the sync version.
        """
        return self._run(query=query)
