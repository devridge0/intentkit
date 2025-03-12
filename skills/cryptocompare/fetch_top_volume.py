"""Tool for fetching top cryptocurrencies by trading volume via CryptoCompare API."""

from typing import Any, Dict, Type

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel

from skills.cryptocompare.api import FetchTopVolumeInput, fetch_top_volume
from skills.cryptocompare.base import CryptoCompareBaseTool

FETCH_TOP_VOLUME_PROMPT = """
This tool retrieves cryptocurrencies ranked by their total trading volume.
Customize the view with limit and quote currency parameters.
Returns comprehensive volume data including 24h trading volume and volume distribution.
"""


class CryptoCompareFetchTopVolumeOutput(BaseModel):
    result: Dict[str, Any]
    error: str | None = None


class CryptoCompareFetchTopVolume(CryptoCompareBaseTool):
    name: str = "cryptocompare_fetch_top_volume"
    description: str = FETCH_TOP_VOLUME_PROMPT
    args_schema: Type[BaseModel] = FetchTopVolumeInput

    async def _arun(
        self, to_symbol: str, config: RunnableConfig, **kwargs
    ) -> CryptoCompareFetchTopVolumeOutput:
        try:
            # Get agent context if available
            context = self.context_from_config(config)
            agent_id = context.agent.id if context else None
            # Check rate limiting with agent_id
            is_rate_limited, error_msg = await self.check_rate_limit(agent_id=agent_id)
            if is_rate_limited:
                return CryptoCompareFetchTopVolumeOutput(result={}, error=error_msg)

            limit = 10
            # Fetch top volume data from API using API key from context
            result = await fetch_top_volume(
                context.config.get("api_key"), limit, to_symbol
            )
            return CryptoCompareFetchTopVolumeOutput(result=result)
        except Exception as e:
            return CryptoCompareFetchTopVolumeOutput(result={}, error=str(e))
