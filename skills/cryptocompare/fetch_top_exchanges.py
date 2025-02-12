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

    def _run(self) -> CryptoCompareFetchTopExchangesOutput:
        raise NotImplementedError("Use _arun instead")

    async def _arun(self) -> CryptoCompareFetchTopExchangesOutput:
        input_data: FetchTopExchangesInput = self.args
        is_rate_limited, error_msg = await self.check_rate_limit()
        if is_rate_limited:
            return CryptoCompareFetchTopExchangesOutput(result={}, error=error_msg)
        try:
            result = await fetch_top_exchanges(input_data.from_symbol, input_data.to_symbol)
            return CryptoCompareFetchTopExchangesOutput(result=result)
        except Exception as e:
            return CryptoCompareFetchTopExchangesOutput(result={}, error=str(e))


FETCH_TOP_EXCHANGES_PROMPT = """
This tool fetches the top cryptocurrency exchanges for a specific trading pair.
Specify base and quote currencies (e.g., 'BTC'/'USD') to get exchange rankings.
Returns key information such as 24h trading volume and market share.
"""
