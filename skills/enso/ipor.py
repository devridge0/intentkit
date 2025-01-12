from typing import Any, Dict, Optional, Type

import httpx
from pydantic import BaseModel, Field

from .base import EnsoBaseTool, base_url


class EnsoIporShortcutInput(BaseModel):
    """
    Input schema for the `/api/v1/static/ipor` endpoint based on IporShortcutInput.
    """
    isRouter: Optional[bool] = Field(
        None,
        description="Flag that indicates whether to use the shared router.",
    )
    amountIn: str = Field(
        ...,
        description="Amount of tokenIn in wei.",
    )
    tokenIn: str = Field(
        ...,
        description="Address of tokenIn. Use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee for ETH.",
    )
    tokenBToBuy: str = Field(
        ...,
        description="Address of the tokenBToBuy.",
    )
    percentageForTokenB: str = Field(
        ...,
        description="Percentage of tokenB to buy in basis points (1/10000).",
    )
    slippage: Optional[str] = Field(
        default="300",
        description="Slippage in basis points (1/10000). Default is 300.",
    )
    simulate: Optional[bool] = Field(
        default=False,
        description="Flag to simulate the transaction, verify assertions, and return simulationURL and events.",
    )


class IporShortcutTransaction(BaseModel):
    """
    Output schema for the `/api/v1/static/ipor` endpoint response (IporShortcutTransaction).
    """
    success: bool = Field(..., description="Indicates whether the IPOR transaction request was successful.")
    transactionId: Optional[str] = Field(
        None,
        description="The ID of the transaction, if applicable.",
    )
    simulationUrl: Optional[str] = Field(
        None,
        description="The URL of the simulation, if simulation is enabled.",
    )
    events: Optional[Dict[str, Any]] = Field(
        None, description="Details of the simulation events or results."
    )
    error: Optional[str] = Field(None, description="Error message, if any.")


class EnsoIporShortcutOutput(BaseModel):
    success: bool = Field(..., description="Indicates whether the Quote data request was successful.")
    data: Optional[IporShortcutTransaction] = Field(
        None, description="Detailed Quote data, including rates and other information."
    )
    error: Optional[str] = Field(None, description="Error message, if any.")


class EnsoIporShortcut(EnsoBaseTool):
    """
    Handles the POST request to the `/api/v1/static/ipor` endpoint.
    """

    name: str = "enso_post_ipor_shortcut"
    description: str = "Execute a transaction shortcut via the `/api/v1/static/ipor` endpoint."
    args_schema: Type[BaseModel] = EnsoIporShortcutInput

    def _run(self) -> EnsoIporShortcutOutput:
        """Sync implementation of the tool.

        This tool doesn't have a native sync implementation.
        """

    async def _arun(
            self,
            api_token: str,
            is_router: Optional[bool] = None,
            amount_in: str = "1000000000000000",
            token_in: str = "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
            token_b_to_buy: str = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            percentage_for_token_b: str = "5000",
            slippage: Optional[str] = "300",
            simulate: Optional[bool] = False,
    ) -> EnsoIporShortcutOutput:
        """
        Executes the IPOR transaction shortcut asynchronously.

        Args:
            api_token (str): Authorization token for accessing the API.
            is_router (Optional[bool]): Indicates whether to use the shared router.
            amount_in (str): Amount of tokenIn in wei.
            token_in (str): Address of tokenIn.
            token_b_to_buy (str): Address of tokenBToBuy.
            percentage_for_token_b (str): Percentage of tokenB to buy in basis points.
            slippage (Optional[str]): Slippage in basis points.
            simulate (Optional[bool]): Whether to simulate the transaction.

        Returns:
            EnsoIporShortcutOutput: Contains the transaction details or any errors encountered.
        """

        api_url = f"{base_url}/api/v1/static/ipor"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_token}",
        }

        payload = {
            "isRouter": is_router,
            "amountIn": amount_in,
            "tokenIn": token_in,
            "tokenBToBuy": token_b_to_buy,
            "percentageForTokenB": percentage_for_token_b,
            "slippage": slippage,
            "simulate": simulate,
        }

        # Remove null values from the payload
        payload = {key: value for key, value in payload.items() if value is not None}

        async with httpx.AsyncClient() as client:
            try:
                # Send POST request to the API
                response = await client.post(api_url, headers=headers, json=payload)
                response.raise_for_status()  # Raise an exception for HTTP errors

                # Parse and return the resulting JSON response
                return EnsoIporShortcutOutput(success=True,
                                              data=IporShortcutTransaction(success=True, **response.json()),
                                              error=None)

            except httpx.RequestError as request_error:
                # Handle request errors
                return EnsoIporShortcutOutput(success=False, data=None, error=f"request error: {str(request_error)}")
            except httpx.HTTPStatusError as http_error:
                # Handle HTTP response errors
                return EnsoIporShortcutOutput(success=False, data=None, error=f"HTTP status error: {str(http_error)}")
            except Exception as e:
                # Handle unexpected exceptions
                return EnsoIporShortcutOutput(success=False, data=None, error=str(e))
