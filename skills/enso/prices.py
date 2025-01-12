from typing import Optional, Type

import httpx
from pydantic import BaseModel, Field

from .base import EnsoBaseTool, base_url


class EnsoGetPricesInput(BaseModel):
    """
    Input model for retrieving the price of a specific token.
    """
    chainId: str = Field(..., description="Blockchain chain ID of the token")
    address: str = Field(..., description="Contract address of the token")


class PriceInfo(BaseModel):
    """
    Represents the price information of a token.
    """
    chainId: str = Field(..., description="Blockchain chain ID of the token")
    address: str = Field(..., description="Contract address of the token")
    priceUSD: float = Field(..., description="The price of the token in USD")
    updatedAt: str = Field(..., description="The timestamp when the price was last updated in ISO 8601 format")


class EnsoGetPricesOutput(BaseModel):
    """
    Output model for retrieving token prices.
    """
    price_info: Optional[PriceInfo] = Field(..., description="Price information of the requested token")
    error: Optional[str] = Field(None, description="Error message if price retrieval fails")


class EnsoGetPrices(EnsoBaseTool):
    """
    Tool for retrieving the price of a token using its chain ID and contract address.

    Endpoint: `/api/v1/prices/{chainId}/{address}`

    This class allows fetching the price in USD for a given blockchain's token using its `chainId` and `address`.
    """

    name: str = "enso_get_prices"
    description: str = "Retrieve the price of a token by chain ID and contract address"
    args_schema: Type[BaseModel] = EnsoGetPricesInput

    def _run(self) -> EnsoGetPricesOutput:
        """Sync implementation of the tool.

        This tool doesn't have a native sync implementation.
        """

    async def _arun(self, api_token: str, chain_id: str, address: str) -> EnsoGetPricesOutput:
        """
        Asynchronous function to request the token price from the API.

        Args:
            api_token (str): API authorization token.
            chain_id (str): The blockchain's chain ID.
            address (str): Contract address of the token.

        Returns:
            EnsoGetPricesOutput: Token price response or error message.
        """
        url = f"{base_url}/api/v1/prices/{chain_id}/{address}"

        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {api_token}",
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                json_dict = response.json()

                # Parse the response into a `PriceInfo` object
                price_info = PriceInfo(**json_dict)

                # Return the parsed response
                return EnsoGetPricesOutput(price_info=price_info, error=None)
            except Exception as e:
                # Return an error message in case of exceptions
                return EnsoGetPricesOutput(price_info=None, error=str(e))
