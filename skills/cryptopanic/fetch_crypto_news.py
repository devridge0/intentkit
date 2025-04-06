from typing import Literal, Type, List
import httpx
import asyncio
from langchain.tools.base import ToolException
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from .base import CryptopanicBaseTool, base_url

FILTERS = ["rising", "hot", "bullish", "bearish", "important", "saved", "lol"]

class CryptopanicNewsInput(BaseModel):
    currency: str = Field(default="all")
    filter: Literal["rising", "hot", "bullish", "bearish", "important", "saved", "lol"] = Field(default="hot")

class NewsItem(BaseModel):
    title: str = Field()
    published_at: str = Field()
    source: str = Field()
    filter: str = Field()

class CryptopanicNewsOutput(BaseModel):
    currency: str = Field()
    news_items: List[NewsItem] = Field()
    summary: str = Field()

class FetchCryptoNews(CryptopanicBaseTool):
    name: str = "fetch_crypto_news"
    description: str = "Fetches latest crypto market news from CryptoPanic across all filters."
    args_schema: Type[BaseModel] = CryptopanicNewsInput

    def _run(self, question: str):
        raise NotImplementedError("Use _arun")

    async def fetch_filter_news(self, currency: str, filter: str, api_key: str) -> List[NewsItem]:
        url = base_url
        params = {"auth_token": api_key, "public": "true", "filter": filter}
        if currency.lower() != "all":
            params["currencies"] = currency.upper()

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()["results"]

            return [
                NewsItem(
                    title=post["title"],
                    published_at=post.get("published_at", "Unknown"),
                    source=post.get("source", {}).get("domain", "CryptoPanic"),
                    filter=filter
                )
                for post in data
            ]

    async def _arun(self, currency: str, config: RunnableConfig, **kwargs):
        context = self.context_from_config(config)
        api_key = self.get_api_key(context)

        tasks = [self.fetch_filter_news(currency, f, api_key) for f in FILTERS]
        filter_results = await asyncio.gather(*tasks)

        all_news_items = [item for sublist in filter_results for item in sublist]
        total_items = len(all_news_items)
        active_filters = sum(1 for r in filter_results if r)

        summary = f"Found {total_items} news items across {active_filters} filters."
        return CryptopanicNewsOutput(currency=currency, news_items=all_news_items, summary=summary)
