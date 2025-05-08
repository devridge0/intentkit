import logging
from typing import Any, Dict, Type

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from skills.token.base import TokenBaseTool
from skills.token.constants import DEFAULT_CHAIN

logger = logging.getLogger(__name__)


class TokenAnalyticsInput(BaseModel):
    """Input for token analytics tool."""

    address: str = Field(description="The token address to get analytics for.")
    chain: str = Field(
        description="The chain to query (e.g., 'eth', 'bsc', 'polygon').",
        default=DEFAULT_CHAIN,
    )


class TokenAnalytics(TokenBaseTool):
    """Tool for retrieving token analytics using Moralis.

    This tool uses Moralis' API to fetch analytics for a token by token address,
    including trading volume, buyer/seller data, and liquidity information.
    """

    name: str = "token_analytics"
    description: str = (
        "Get analytics for a token by token address. "
        "Returns trading volumes, number of buyers/sellers, and liquidity information over various time periods."
    )
    args_schema: Type[BaseModel] = TokenAnalyticsInput

    async def _arun(
        self,
        address: str,
        chain: str = DEFAULT_CHAIN,
        config: RunnableConfig = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Fetch token analytics from Moralis.

        Args:
            address: The token address
            chain: The blockchain to query
            config: The configuration for the tool call

        Returns:
            Dict containing token analytics data
        """
        context = self.context_from_config(config)
        logger.debug(
            f"token_analytics.py: Fetching token analytics with context {context}"
        )

        # Get the API key from the agent's configuration
        api_key = context.config.get("api_key")
        if not api_key:
            return {"error": "No Moralis API key provided in the configuration."}

        # Build query parameters
        params = {"chain": chain}

        # Call Moralis API
        try:
            endpoint = f"/tokens/{address}/analytics"
            return await self._make_request(
                method="GET", endpoint=endpoint, api_key=api_key, params=params
            )
        except Exception as e:
            logger.error(
                f"token_analytics.py: Error fetching token analytics: {e}",
                exc_info=True,
            )
            return {
                "error": "An error occurred while fetching token analytics. Please try again later."
            }
