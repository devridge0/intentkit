"""Tool for fetching top cryptocurrencies by trading volume via CryptoCompare API."""

from typing import Any, Dict, Type
from pydantic import BaseModel
from skills.cryptocompare.base import CryptoCompareBaseTool
from skills.cryptocompare.api import fetch_top_volume, FetchTopVolumeInput

class CryptoCompareFetchTopVolumeOutput(BaseModel):
    result: Dict[str, Any]
    error: str | None = None

class CryptoCompareFetchTopVolume(CryptoCompareBaseTool):
    name: str = "cryptocompare_fetch_top_volume"
    description: str = FETCH_TOP_VOLUME_PROMPT
    args_schema: Type[BaseModel] = FetchTopVolumeInput

    def _run(self, limit: int, to_symbol: str) -> CryptoCompareFetchTopVolumeOutput:
        raise NotImplementedError("Use _arun instead")

    async def _arun(self, limit: int, to_symbol: str) -> CryptoCompareFetchTopVolumeOutput:
        is_rate_limited, error_msg = await self.check_rate_limit()
        if is_rate_limited:
            return CryptoCompareFetchTopVolumeOutput(result={}, error=error_msg)
        try:
            result = await fetch_top_volume(self.api_key, limit, to_symbol)
            return CryptoCompareFetchTopVolumeOutput(result=result)
        except Exception as e:
            return CryptoCompareFetchTopVolumeOutput(result={}, error=str(e))

FETCH_TOP_VOLUME_PROMPT = """
This tool retrieves cryptocurrencies ranked by their total trading volume.
Customize the view with limit and quote currency parameters.
Returns comprehensive volume data including 24h trading volume and volume distribution.
"""

