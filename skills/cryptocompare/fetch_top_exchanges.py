"""Tool for fetching top exchanges for a trading pair via CryptoCompare API."""

from typing import Any, Dict, Type
from pydantic import BaseModel
from skills.cryptocompare.base import CryptoCompareBaseTool
from skills.cryptocompare.api import fetch_top_exchanges, FetchTopExchangesInput

class CryptoCompareFetchTopExchangesOutput(BaseModel):
    result: Dict[str, Any]
    error: str | None = None

class CryptoCompareFetchTopExchanges(CryptoCompareBaseTool):
    name: str = "cryptocompare_fetch_top_exchanges"
    description: str = FETCH_TOP_EXCHANGES_PROMPT
    args_schema: Type[BaseModel] = FetchTopExchangesInput

    def _run(self, from_symbol: str, to_symbol: str) -> CryptoCompareFetchTopExchangesOutput:
        raise NotImplementedError("Use _arun instead")

    async def _arun(self, from_symbol: str, to_symbol: str) -> CryptoCompareFetchTopExchangesOutput:
        is_rate_limited, error_msg = await self.check_rate_limit()
        if is_rate_limited:
            return CryptoCompareFetchTopExchangesOutput(result={}, error=error_msg)
        try:
            result = await fetch_top_exchanges(self.api_key, from_symbol, to_symbol)
            return CryptoCompareFetchTopExchangesOutput(result=result)
        except Exception as e:
            return CryptoCompareFetchTopExchangesOutput(result={}, error=str(e))


FETCH_TOP_EXCHANGES_PROMPT = """
This tool fetches the top cryptocurrency exchanges for a specific trading pair.
Specify base and quote currencies (e.g., 'BTC'/'USD') to get exchange rankings.
Returns key information such as 24h trading volume and market share.
"""
