"""Tool for fetching stablecoin prices via DeFi Llama API."""

from typing import Dict, List, Optional, Type
from pydantic import BaseModel, Field

from skills.defillama.base import DefiLlamaBaseTool
from skills.defillama.api import fetch_stablecoin_prices

FETCH_STABLECOIN_PRICES_PROMPT = """
This tool fetches current price data for stablecoins from DeFi Llama.
Returns:
- Historical price points with timestamps
- Current prices for each stablecoin
- Prices indexed by stablecoin identifier
"""


class PriceDataPoint(BaseModel):
    """Model representing a price data point."""

    date: str = Field(
        ...,
        description="Unix timestamp for the price data"
    )
    prices: Dict[str, float] = Field(
        ...,
        description="Dictionary of stablecoin prices indexed by identifier"
    )


class FetchStablecoinPricesResponse(BaseModel):
    """Response schema for stablecoin prices data."""

    data: List[PriceDataPoint] = Field(
        default_factory=list,
        description="List of price data points"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if any"
    )


class DefiLlamaFetchStablecoinPrices(DefiLlamaBaseTool):
    """Tool for fetching stablecoin prices from DeFi Llama.
    
    This tool retrieves current price data for stablecoins, including historical
    price points and their timestamps.

    Example:
        prices_tool = DefiLlamaFetchStablecoinPrices(
            skill_store=store,
            agent_id="agent_123",
            agent_store=agent_store
        )
        result = await prices_tool._arun()
    """

    name: str = "defillama_fetch_stablecoin_prices"
    description: str = FETCH_STABLECOIN_PRICES_PROMPT
    args_schema: None = None  # No input parameters needed

    def _run(self) -> FetchStablecoinPricesResponse:
        """Synchronous implementation - not supported."""
        raise NotImplementedError("Use _arun instead")

    async def _arun(self) -> FetchStablecoinPricesResponse:
        """Fetch stablecoin price data.

        Returns:
            FetchStablecoinPricesResponse containing price data or error
        """
        try:
            # Check rate limiting
            is_rate_limited, error_msg = await self.check_rate_limit()
            if is_rate_limited:
                return FetchStablecoinPricesResponse(error=error_msg)

            # Fetch price data from API
            result = await fetch_stablecoin_prices()
            
            # Check for API errors
            if isinstance(result, dict) and "error" in result:
                return FetchStablecoinPricesResponse(error=result["error"])

            # Parse results into models
            data_points = [
                PriceDataPoint(**point) 
                for point in result
            ]

            return FetchStablecoinPricesResponse(data=data_points)

        except Exception as e:
            return FetchStablecoinPricesResponse(error=str(e))
