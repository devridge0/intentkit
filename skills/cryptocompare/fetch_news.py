"""Tool for fetching news via CryptoCompare API."""

import time
from typing import List, Type

from pydantic import BaseModel, Field

from skills.cryptocompare.api import FetchNewsInput, fetch_news
from skills.cryptocompare.base import CryptoCompareBaseTool

FETCH_NEWS_PROMPT = """
This tool fetches the latest cryptocurrency news articles for a specific token.
You can optionally specify a timestamp to get historical news, otherwise it uses the current time.
Returns articles in English with details like title, body, source, and publish time.
"""


class NewsArticle(BaseModel):
    """Model representing a news article."""

    id: str
    title: str
    body: str
    published_at: int
    url: str
    source: str
    categories: List[str]


class CryptoCompareFetchNewsOutput(BaseModel):
    """Output model for the news fetching tool."""

    articles: List[NewsArticle] = Field(
        default_factory=list, description="List of fetched news articles"
    )
    error: str | None = Field(default=None, description="Error message if any")


class CryptoCompareFetchNews(CryptoCompareBaseTool):
    """Tool for fetching cryptocurrency news from CryptoCompare.

    This tool fetches the latest news articles for a specific cryptocurrency token.
    It uses the CryptoCompare News API and includes rate limiting to avoid API abuse.

    Example:
        news_tool = CryptoCompareFetchNews(
            api_key="your_api_key",
            skill_store=store,
            agent_id="agent_123",
            agent_store=agent_store
        )
        result = await news_tool._arun(token="BTC")
    """

    name: str = "cryptocompare_fetch_news"
    description: str = FETCH_NEWS_PROMPT
    args_schema: Type[BaseModel] = FetchNewsInput

    def _run(self, token: str) -> CryptoCompareFetchNewsOutput:
        """Synchronous implementation - not supported."""
        raise NotImplementedError("Use _arun instead")

    async def _arun(self, token: str) -> CryptoCompareFetchNewsOutput:
        """Fetch news articles for the given token.

        Args:
            token: Cryptocurrency token symbol (e.g., "BTC", "ETH")
            timestamp: Optional Unix timestamp to search for news from

        Returns:
            CryptoCompareFetchNewsOutput containing list of articles or error
        """
        try:
            # Check rate limiting
            is_rate_limited, error_msg = await self.check_rate_limit()
            if is_rate_limited:
                return CryptoCompareFetchNewsOutput(error=error_msg)

            timestamp = int(time.time())

            # Fetch news from API
            result = await fetch_news(self.api_key, token, timestamp)

            if "Data" not in result:
                return CryptoCompareFetchNewsOutput(
                    error="Invalid response format from CryptoCompare API"
                )

            # Convert raw data to NewsArticle models
            articles = [
                NewsArticle(
                    id=str(article["id"]),
                    title=article["title"],
                    body=article["body"],
                    published_at=article["published_on"],
                    url=article["url"],
                    source=article["source"],
                    categories=article["categories"].split("|"),
                )
                for article in result["Data"]
            ]

            return CryptoCompareFetchNewsOutput(articles=articles)

        except Exception as e:
            return CryptoCompareFetchNewsOutput(error=str(e))
