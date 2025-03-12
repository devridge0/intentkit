"""Tool for fetching trading signals via CryptoCompare API."""

from typing import Any, Dict, Type

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel

from skills.cryptocompare.api import FetchTradingSignalsInput, fetch_trading_signals
from skills.cryptocompare.base import CryptoCompareBaseTool

FETCH_TRADING_SIGNALS_PROMPT = """
This tool retrieves advanced trading signals from IntoTheBlock analytics for a specific cryptocurrency.
Provide a cryptocurrency symbol (e.g., 'BTC') to get detailed market indicators.
Returns key metrics like network growth, large transaction patterns, holder composition, and market momentum.
"""


class CryptoCompareFetchTradingSignalsOutput(BaseModel):
    result: Dict[str, Any]
    error: str | None = None


class CryptoCompareFetchTradingSignals(CryptoCompareBaseTool):
    name: str = "cryptocompare_fetch_trading_signals"
    description: str = FETCH_TRADING_SIGNALS_PROMPT
    args_schema: Type[BaseModel] = FetchTradingSignalsInput

    async def _arun(
        self, from_symbol: str, config: RunnableConfig, **kwargs
    ) -> CryptoCompareFetchTradingSignalsOutput:
        try:
            # Get agent context if available
            context = self.context_from_config(config)
            agent_id = context.agent.id if context else None
            # Check rate limiting with agent_id
            is_rate_limited, error_msg = await self.check_rate_limit(agent_id=agent_id)
            if is_rate_limited:
                return CryptoCompareFetchTradingSignalsOutput(
                    result={}, error=error_msg
                )

            # Fetch trading signals from API using API key from context
            result = await fetch_trading_signals(
                context.config.get("api_key"), from_symbol
            )
            return CryptoCompareFetchTradingSignalsOutput(result=result)
        except Exception as e:
            return CryptoCompareFetchTradingSignalsOutput(result={}, error=str(e))
