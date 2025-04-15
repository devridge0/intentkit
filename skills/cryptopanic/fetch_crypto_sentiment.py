from typing import ClassVar, List, Type

import httpx
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from .base import CryptopanicBaseTool, base_url


class CryptopanicSentimentInput(BaseModel):
    currency: str = Field(default="BTC")


class FetchCryptoSentiment(CryptopanicBaseTool):
    name: str = "fetch_crypto_sentiment"
    description: str = "Fetches recent CryptoPanic posts and defines market sentiment via LLM analysis."
    args_schema: Type[BaseModel] = CryptopanicSentimentInput

    DEFAULT_PROMPT: ClassVar[str] = """
    Hey, you’re a seasoned crypto analyst with a knack for reading the market, and I’ve got {total_posts} fresh CryptoPanic headlines about {currency} for you to break down. Votes are flat (all 0/0 or none), so it’s all about these headlines:

    - Headlines: {headlines}

    Give me your expert take on the sentiment—Bullish, Bearish, Neutral, or something like Cautiously Bullish. Picture us chatting this out: kick off with what the vibe feels like across these {total_posts} posts, then roll through each headline, tossing in a quick note on what it’s hinting at. Dig into what’s steering the mood—market buzz, economic signals, whatever’s in play. Point out any big wins or red flags, and wrap it up with where you see {currency} heading short-term. Keep it pro, detailed, and natural—no headings or stiff formatting, just your straight-up analysis.
    """

    def _run(self, question: str):
        raise NotImplementedError("Use _arun")

    async def fetch_all_posts(self, currency: str, api_key: str) -> List[dict]:
        url = base_url
        params = {
            "auth_token": api_key,
            "public": "true",
            "currencies": currency.upper(),
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()["results"]

    async def _arun(self, currency: str, config: RunnableConfig, **kwargs):
        context = self.context_from_config(config)
        api_key = self.get_api_key(context)

        # Fetch all recent posts
        posts = await self.fetch_all_posts(currency, api_key)
        total_posts = len(posts)

        if total_posts == 0:
            data = {
                "total_posts": 0,
                "headlines": ["No recent posts available"],
                "votes": "None",
            }
        else:
            headlines = [p["title"] for p in posts[:5]]  # Limit to 5
            votes = (
                [
                    f"{p['votes']['positive']}/{p['votes']['negative']}"
                    for p in posts[:5]
                ]
                if posts and "votes" in posts[0]
                else "None"
            )

            data = {"total_posts": total_posts, "headlines": headlines, "votes": votes}

        # Bundle data with prompt for LLM
        formatted_headlines = "\n- ".join([""] + data["headlines"])
        formatted_votes = (
            "\n- ".join([""] + data["votes"]) if data["votes"] != "None" else "None"
        )
        output = {
            "prompt": self.DEFAULT_PROMPT,
            "currency": currency,
            "total_posts": data["total_posts"],
            "headlines": formatted_headlines,
            "votes": formatted_votes,
        }

        return output
