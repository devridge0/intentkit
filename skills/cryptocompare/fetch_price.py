"""Tool for fetching cryptocurrency prices via CryptoCompare API."""

from typing import Any, Dict, List, Type

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel

from skills.cryptocompare.api import FetchPriceInput, fetch_price
from skills.cryptocompare.base import CryptoCompareBaseTool

FETCH_PRICE_PROMPT = """
This tool fetches real-time cryptocurrency price data with multi-currency support.
Provide a base currency (e.g., 'BTC', 'ETH') and a list of target currencies (e.g., ['USD', 'EUR', 'JPY']).
Returns current exchange rates for all requested currency pairs.
"""


class CryptoCompareFetchPriceOutput(BaseModel):
    result: Dict[str, Any]
    error: str | None = None


class CryptoCompareFetchPrice(CryptoCompareBaseTool):
    name: str = "cryptocompare_fetch_price"
    description: str = FETCH_PRICE_PROMPT
    args_schema: Type[BaseModel] = FetchPriceInput

    async def _arun(
        self,
        from_symbol: str,
        to_symbols: List[str],
        config: RunnableConfig,
        **kwargs,
    ) -> CryptoCompareFetchPriceOutput:
        try:
            # Get agent context if available
            context = self.context_from_config(config)
            agent_id = context.agent.id if context else None
            # Check rate limiting with agent_id
            is_rate_limited, error_msg = await self.check_rate_limit(agent_id=agent_id)
            if is_rate_limited:
                return CryptoCompareFetchPriceOutput(result={}, error=error_msg)

            # Fetch price from API using API key from context
            result = await fetch_price(
                context.config.get("api_key"), from_symbol, to_symbols
            )
            return CryptoCompareFetchPriceOutput(result=result)
        except Exception as e:
            return CryptoCompareFetchPriceOutput(result={}, error=str(e))
