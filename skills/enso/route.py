from typing import Any, Dict, List, Optional, Type

import httpx
from pydantic import BaseModel, Field

from .base import EnsoBaseTool


class EnsoGetRouteShortcutInput(BaseModel):
    """
    Input schema for the `/api/v1/shortcuts/route` GET endpoint.
    """
    chainId: Optional[int] = Field(
        default=1,
        description="Chain ID of the network to execute the transaction on.",
    )
    fromAddress: Optional[str] = Field(
        None,
        description="Ethereum address of the wallet to send the transaction from.",
    )
    routingStrategy: Optional[str] = Field(
        None,
        description="Routing strategy to use. Options: 'ensowallet', 'router', 'delegate'.",
    )
    toEoa: Optional[bool] = Field(
        None,
        deprecated=True,
        description="Flag that indicates if gained tokenOut should be sent to EOA."
    )
    receiver: Optional[str] = Field(
        None,
        description="Ethereum address of the receiver of the tokenOut.",
    )
    spender: Optional[str] = Field(
        None,
        description="Ethereum address of the spender of the tokenIn.",
    )
    amountIn: Optional[List[str]] = Field(
        None,
        description="Amount of tokenIn to swap in wei.",
    )
    amountOut: Optional[List[str]] = Field(
        None,
        description="Amount of tokenOut to receive.",
    )
    minAmountOut: Optional[List[str]] = Field(
        None,
        description="Minimum amount out in wei. If specified, slippage should not be specified.",
    )
    slippage: Optional[str] = Field(
        default="300",
        description="Slippage in basis points (1/10000). If specified, minAmountOut should not be specified.",
    )
    fee: Optional[List[str]] = Field(
        None,
        description="Fee in basis points (1/10000) for each amountIn value.",
    )
    feeReceiver: Optional[str] = Field(
        None,
        description="Ethereum address that will receive the collected fee.",
    )
    disableRFQs: Optional[bool] = Field(
        None,
        description="Exclude RFQ sources from routes.",
    )
    ignoreAggregators: Optional[List[str]] = Field(
        None,
        description="List of swap aggregators to ignore.",
    )
    ignoreStandards: Optional[List[str]] = Field(
        None,
        description="List of standards to ignore.",
    )
    tokenIn: Optional[List[str]] = Field(
        None,
        description="Token addresses to swap from (For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee).",
    )
    tokenOut: Optional[List[str]] = Field(
        None,
        description="Token addresses to swap to (For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee).",
    )
    variableEstimates: Optional[dict] = Field(
        None,
        description="Variable estimates for the route."
    )


class RouteShortcutGetTransaction(BaseModel):
    """
    Output schema for the `/api/v1/shortcuts/route` GET endpoint.
    """
    gas: str = Field(..., description="Gas amount for the transaction.")
    amountOut: dict = Field(
        ..., description="The calculated amountOut as an object."
    )
    priceImpact: Optional[float] = Field(
        None, description="Price impact in basis points, null if USD price is not found."
    )
    feeAmount: List[str] = Field(
        ..., description="An array of the fee amounts collected for each tokenIn."
    )
    createdAt: int = Field(..., description="Block number when the transaction was created.")
    route: List[dict] = Field(
        ..., description="The route that the shortcut will use."
    )


class EnsoGetRouteShortcutOutput(BaseModel):
    res: Optional[RouteShortcutGetTransaction]
    error: Optional[str] | None = None


class EnsoGetRouteShortcut(EnsoBaseTool):
    """
    Handles the GET request to the `/api/v1/shortcuts/route` endpoint.
    """

    name: str = "enso_get_route_shortcut"
    description: str = "Retrieve route information for a specified transaction via the `/api/v1/shortcuts/route` endpoint."
    args_schema: Type[BaseModel] = EnsoGetRouteShortcutInput

    def _run(self) -> EnsoGetRouteShortcutOutput:
        """Sync implementation of the tool.

        This tool doesn't have a native sync implementation.
        """

    async def _arun(self, api_token: str, **query_params) -> EnsoGetRouteShortcutOutput:
        """
        Retrieves route information asynchronously.

        Args:
            api_token (str): Authorization token for API access.
            **query_params: Parameters for querying the route, matching EnsoGetRouteShortcutInput.

        Returns:
            EnsoGetRouteShortcutOutput: The response containing route shortcut information.
        """
        api_url = "https://api.yourapi.com/api/v1/shortcuts/route"  # Replace with actual API URL.

        headers = {
            "Authorization": f"Bearer {api_token}",
        }

        # Prepare query parameters
        query = EnsoGetRouteShortcutInput(**query_params).dict(exclude_none=True)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(api_url, headers=headers, params=query)
                response.raise_for_status()  # Raise HTTPError for non-2xx responses

                # Parse and return the response as a RouteShortcutGetTransaction object
                return EnsoGetRouteShortcutOutput(res=RouteShortcutGetTransaction(**response.json()), error=None)

            except httpx.RequestError as req_err:
                return EnsoGetRouteShortcutOutput(res=None, error=f"Request error: {req_err}")
            except httpx.HTTPStatusError as http_err:
                return EnsoGetRouteShortcutOutput(res=None, error=f"HTTP error: {http_err}")
            except Exception as e:
                return EnsoGetRouteShortcutOutput(res=None, error=str(e))


class VariableEstimates(BaseModel):
    """
    Placeholder schema for VariableEstimates.
    Define its properties based on your actual schema or leave as a generic object.
    """
    # Placeholder example: Add appropriate fields as needed
    data: Optional[Dict[str, Any]] = Field(None, description="An example field for variable estimates.")


class RouteShortcutVariableInput(BaseModel):
    """
    Input schema for the `/api/v1/shortcuts/route` endpoint.
    """
    chainId: Optional[int] = Field(
        default=1,
        description="Chain ID of the network to execute the transaction on.")
    fromAddress: str = Field(
        ...,
        description="Ethereum address of the wallet to send the transaction from.",
    )
    routingStrategy: Optional[str] = Field(
        None,
        description="Routing strategy to use. Options: 'ensowallet', 'router', 'delegate'.",
    )
    toEoa: Optional[bool] = Field(
        None,
        deprecated=True,
        description="Flag that indicates if gained tokenOut should be sent to EOA."
    )
    receiver: Optional[str] = Field(
        None,
        description="Ethereum address of the receiver of the tokenOut.",
    )
    spender: Optional[str] = Field(
        None,
        description="Ethereum address of the spender of the tokenIn.",
    )
    amountIn: List[str] = Field(
        ...,
        description="Amount of tokenIn to swap in wei.",
    )
    amountOut: Optional[List[str]] = Field(
        None,
        description="Amount of tokenOut to receive.",
    )
    minAmountOut: Optional[List[str]] = Field(
        None,
        description="Minimum amount out in wei. If specified, slippage should not be specified.",
    )
    slippage: Optional[str] = Field(
        default="300",
        description="Slippage in basis points (1/10000). If specified, minAmountOut should not be specified.",
    )
    fee: Optional[List[str]] = Field(
        None,
        description="Fee in basis points (1/10000) for each amountIn value.",
    )
    feeReceiver: Optional[str] = Field(
        None,
        description="Ethereum address that will receive the collected fee.",
    )
    disableRFQs: Optional[bool] = Field(
        None,
        description="Exclude RFQ sources from routes.",
    )
    ignoreAggregators: Optional[List[str]] = Field(
        None,
        description="List of swap aggregators to ignore.",
    )
    ignoreStandards: Optional[List[str]] = Field(
        None,
        description="List of standards to ignore.",
    )
    tokenIn: List[str] = Field(
        ...,
        description="Token addresses to swap from (For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee).",
    )
    tokenOut: List[str] = Field(
        ...,
        description="Token addresses to swap to (For ETH, use 0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee).",
    )
    variableEstimates: Optional[VariableEstimates] = Field(
        default=None,
        description="Variable estimates for the route."
    )


class Transaction(BaseModel):
    """
    Schema for the `tx` object in RouteShortcutTransaction.
    """
    # Add properties of the Transaction schema here based on your actual transaction structure
    data: Dict[str, Any] = Field(..., description="Transaction data properties.")


class Hop(BaseModel):
    """
    Schema for individual hop in the route if applicable.
    """
    # Placeholder example: Add appropriate fields based on the actual schema
    hopData: str = Field(..., description="Details about the hop.")


class RouteShortcutTransaction(BaseModel):
    """
    Output schema for the `/api/v1/shortcuts/route` endpoint.
    """
    gas: str = Field(..., description="Gas amount for the transaction.")
    amountOut: Dict[str, Any] = Field(
        ..., description="The calculated amountOut as an object."
    )
    priceImpact: Optional[float] = Field(
        None, description="Price impact in basis points, null if USD price is not found."
    )
    feeAmount: List[str] = Field(
        ..., description="An array of the fee amounts collected for each tokenIn."
    )
    createdAt: int = Field(..., description="Block number when the transaction was created.")
    tx: Transaction = Field(..., description="The transaction object to use in `ethers`.")
    route: List[Hop] = Field(
        ..., description="The route that the shortcut will use."
    )


class EnsoPostRouteShortcutOutput(BaseModel):
    success: bool = Field(..., description="Indicates whether the Quote data request was successful.")
    data: Optional[RouteShortcutTransaction] = Field(
        None, description="Detailed Quote data, including rates and other information."
    )
    error: Optional[str] = Field(None, description="Error message, if any.")


class EnsoPostRouteShortcut(EnsoBaseTool):
    """
    Handles the POST request to the `/api/v1/shortcuts/route` endpoint.
    """

    name: str = "enso_post_route_shortcut"
    description: str = "Execute a transaction route using the `/api/v1/shortcuts/route` endpoint."
    args_schema: Type[BaseModel] = RouteShortcutVariableInput

    def _run(self) -> EnsoPostRouteShortcutOutput:
        """Sync implementation of the tool.

        This tool doesn't have a native sync implementation.
        """

    async def _arun(self, api_token: str, **inputs) -> EnsoPostRouteShortcutOutput:
        """
        Asynchronously execute the route shortcut.

        Args:
            api_token (str): Authorization token for the API.
            **inputs: Parameters matching the RouteShortcutVariableInputs schema.

        Returns:
            EnsoPostRouteShortcutOutput: The response representing the executed route shortcut or error details.
        """
        api_url = "https://api.yourapi.com/api/v1/shortcuts/route"  # Replace with actual API URL.

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_token}",
        }

        payload = RouteShortcutVariableInput(**inputs).dict()

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(api_url, headers=headers, json=payload)
                response.raise_for_status()  # Raise HTTPError for non-2xx responses

                return EnsoPostRouteShortcutOutput(success=True, data=RouteShortcutTransaction(**response.json()),
                                                   error=None)

            except httpx.RequestError as request_error:
                return EnsoPostRouteShortcutOutput(success=False, data=None,
                                                   error=f"Request error: {str(request_error)}")
            except httpx.HTTPStatusError as http_err:
                return EnsoPostRouteShortcutOutput(success=False, data=None, error=f"HTTP error: {str(http_err)}")
            except Exception as e:
                return EnsoPostRouteShortcutOutput(success=False, data=None, error=str(e))
