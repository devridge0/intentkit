"""Tool for fetching cryptocurrency prices via CryptoCompare API."""

from typing import Any, Dict, List, Type

from pydantic import BaseModel

from skills.cryptocompare.api import FetchPriceInput, fetch_price
from skills.cryptocompare.base import CryptoCompareBaseTool


class CryptoCompareFetchPriceOutput(BaseModel):
    result: Dict[str, Any]
    error: str | None = None


class CryptoCompareFetchPrice(CryptoCompareBaseTool):
    name: str = "cryptocompare_fetch_price"
    description: str = FETCH_PRICE_PROMPT
    args_schema: Type[BaseModel] = FetchPriceInput

    def _run(
        self, from_symbol: str, to_symbols: List[str]
    ) -> CryptoCompareFetchPriceOutput:
        raise NotImplementedError("Use _arun instead")

    async def _arun(
        self, from_symbol: str, to_symbols: List[str]
    ) -> CryptoCompareFetchPriceOutput:
        is_rate_limited, error_msg = await self.check_rate_limit()
        if is_rate_limited:
            return CryptoCompareFetchPriceOutput(result={}, error=error_msg)
        try:
            result = await fetch_price(self.api_key, from_symbol, to_symbols)
            return CryptoCompareFetchPriceOutput(result=result)
        except Exception as e:
            return CryptoCompareFetchPriceOutput(result={}, error=str(e))


FETCH_PRICE_PROMPT = """
This tool fetches real-time cryptocurrency price data with multi-currency support.
Provide a base currency (e.g., 'BTC', 'ETH') and a list of target currencies (e.g., ['USD', 'EUR', 'JPY']).
Returns current exchange rates for all requested currency pairs.
"""
