"""Tool for fetching top exchanges for a trading pair via CryptoCompare API."""

from typing import Any, Dict, Type

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel

from skills.cryptocompare.api import FetchTopExchangesInput, fetch_top_exchanges
from skills.cryptocompare.base import CryptoCompareBaseTool

FETCH_TOP_EXCHANGES_PROMPT = """
This tool fetches the top cryptocurrency exchanges for a specific trading pair.
Specify base and quote currencies (e.g., 'BTC'/'USD') to get exchange rankings.
Returns key information such as 24h trading volume and market share.
"""


class CryptoCompareFetchTopExchangesOutput(BaseModel):
    result: Dict[str, Any]
    error: str | None = None


class CryptoCompareFetchTopExchanges(CryptoCompareBaseTool):
    name: str = "cryptocompare_fetch_top_exchanges"
    description: str = FETCH_TOP_EXCHANGES_PROMPT
    args_schema: Type[BaseModel] = FetchTopExchangesInput

    async def _arun(
        self, from_symbol: str, to_symbol: str, config: RunnableConfig, **kwargs
    ) -> CryptoCompareFetchTopExchangesOutput:
        try:
            # Get agent context if available
            context = self.context_from_config(config)
            agent_id = context.agent.id if context else None
            # Check rate limiting with agent_id
            is_rate_limited, error_msg = await self.check_rate_limit(agent_id=agent_id)
            if is_rate_limited:
                return CryptoCompareFetchTopExchangesOutput(result={}, error=error_msg)

            # Fetch top exchanges from API using API key from context
            result = await fetch_top_exchanges(
                context.config.get("api_key"), from_symbol, to_symbol
            )
            return CryptoCompareFetchTopExchangesOutput(result=result)
        except Exception as e:
            return CryptoCompareFetchTopExchangesOutput(result={}, error=str(e))
