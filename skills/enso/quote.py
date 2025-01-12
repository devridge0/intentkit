from typing import Any, Dict, List, Optional, Type

import httpx
from pydantic import BaseModel, Field

from .base import EnsoBaseTool, base_url


class EnsoGetQuoteInput(BaseModel):
    """
    Input model for retrieving a quote using the shortcuts endpoint.
    """
    fromToken: str = Field(..., description="The token address being exchanged from.")
    toToken: str = Field(..., description="The token address being exchanged to.")
    amount: str = Field(..., description="The amount of the `fromToken` to exchange.")
    walletAddress: Optional[str] = Field(None, description="The wallet address requesting the quote (optional).")
    chainId: str = Field(..., description="The chain ID of the blockchain network where the exchange will take place.")


class QuoteResponse(BaseModel):
    """
    Response model for quote details from the shortcuts endpoint.
    """
    fromToken: str = Field(..., description="The token address being exchanged from.")
    toToken: str = Field(..., description="The token address being exchanged to.")
    amount: str = Field(..., description="The amount of the `fromToken` being exchanged.")
    toAmount: str = Field(..., description="The resulting amount of the `toToken` after the exchange.")
    priceImpact: Optional[float] = Field(None, description="The price impact percentage of the exchange.")
    estimatedGas: Optional[int] = Field(None, description="The estimated gas fee (in units) for the transaction.")


class EnsoGetQuoteOutput(BaseModel):
    """
    Output model for retrieving a quote.
    """
    quote_res: Optional[QuoteResponse] = Field(..., description="Response containing the quote details.")
    error: Optional[str] = Field(None, description="Error message if the quote retrieval fails.")


class EnsoGetQuote(EnsoBaseTool):
    """
    Tool for retrieving a trade quote via the `/api/v1/shortcuts/quote` endpoint.

    This tool calculates the exchange details between two tokens (`fromToken` and `toToken`)
    by providing their respective token addresses, the transfer amount, and the blockchain network
    where the trade will take place.
    """

    name: str = "enso_get_quote"
    description: str = "Retrieve a trade quote for token exchange using `/api/v1/shortcuts/quote`."
    args_schema: Type[BaseModel] = EnsoGetQuoteInput

    def _run(self) -> EnsoGetQuoteOutput:
        """Sync implementation of the tool.

        This tool doesn't have a native sync implementation.
        """

    async def _arun(self, api_token: str, from_token: str, to_token: str, amount: str, wallet_address: Optional[str],
                    chain_id: str) -> EnsoGetQuoteOutput:
        """
        Asynchronous function to retrieve a trade quote.

        Args:
            api_token (str): Authorization token for the API.
            from_token (str): The token address being exchanged from.
            to_token (str): The token address being exchanged to.
            amount (str): The amount of the `fromToken` to be exchanged.
            wallet_address (Optional[str]): Address of the wallet requesting the quote (optional).
            chain_id (str): The chain ID of the blockchain where the trade is happening.

        Returns:
            EnsoGetQuoteOutput: A response containing the trade quote or error message.
        """
        url = f"{base_url}/api/v1/shortcuts/quote"

        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {api_token}",
        }

        params = {
            "fromToken": from_token,
            "toToken": to_token,
            "amount": amount,
            "chainId": chain_id,
        }

        # Add walletAddress if provided
        if wallet_address:
            params["walletAddress"] = wallet_address

        async with httpx.AsyncClient() as client:
            try:
                # Send the GET request
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()

                # Parse the JSON response into the QuoteResponse model
                json_dict = response.json()
                quote_response = QuoteResponse(**json_dict)

                # Return the parsed response
                return EnsoGetQuoteOutput(quote_res=quote_response, error=None)
            except Exception as e:
                # Handle errors and return response with error message
                return EnsoGetQuoteOutput(quote_res=None, error=str(e))


class SimplePath(BaseModel):
    """
    Placeholder schema for the SimplePath object referenced in the route definition.
    Define its properties based on the schema if needed.
    """
    # Add fields here based on the SimplePath schema
    name: str = Field(..., description="An example field for SimplePath.")


class EnsoPostQuoteShortcutInput(BaseModel):
    """
    Input schema for the `/api/v1/static/shortcuts/quote` endpoint.
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
    route: List[SimplePath] = Field(
        ...,
        description="Ordered array of paths that you want to simulate (required)."
    )
    fee: Optional[List[str]] = Field(
        None,
        description="Fee in basis points (1/10000) for each route. If specified, this percentage of each amountIn value will be sent to feeReceiver.",
    )
    feeReceiver: Optional[str] = Field(
        None,
        description="The Ethereum address that will receive the collected fee. Required if fee is provided.",
    )
    disableRFQs: Optional[bool] = Field(
        None,
        description="A flag indicating whether to exclude RFQ sources from routes.",
    )
    ignoreAggregators: Optional[List[str]] = Field(
        None,
        description="A list of swap aggregators to be ignored from consideration.",
    )
    blockNumber: Optional[str] = Field(
        None,
        description="Hex string of block number.",
    )


class Quote(BaseModel):
    """
    Output schema for the `/api/v1/static/shortcuts/quote` endpoint response.
    """
    gas: str = Field(..., description="Gas used for the transaction.")
    amountOut: Dict[str, Any] = Field(
        ..., description="The output amount as an object (details depend on usage)."
    )
    priceImpact: Optional[float] = Field(
        None, description="Price impact in basis points, null if USD price not found."
    )
    feeAmount: List[str] = Field(
        ..., description="An array of the fee amount collected for each tokenIn."
    )


class QuotePostRouteOutput(BaseModel):
    success: bool = Field(..., description="Indicates whether the Quote data request was successful.")
    data: Optional[Quote] = Field(
        None, description="Detailed Quote data, including rates and other information."
    )
    error: Optional[str] = Field(None, description="Error message, if any.")


class EnsoPostQuoteShortcut(EnsoBaseTool):
    """
    Handles the POST request to the `/api/v1/static/shortcuts/quote` endpoint.
    """

    name: str = "enso_post_quote_shortcut"
    description: str = "Retrieve a transaction quote using the `/api/v1/static/shortcuts/quote` endpoint."
    args_schema: Type[BaseModel] = EnsoPostQuoteShortcutInput

    def _run(self) -> QuotePostRouteOutput:
        """Sync implementation of the tool.

        This tool doesn't have a native sync implementation.
        """

    async def _arun(
            self,
            api_token: str,
            chain_id: Optional[int] = 1,
            from_address: Optional[str] = None,
            routing_strategy: Optional[str] = None,
            route: List[SimplePath] = None,
            fee: Optional[List[str]] = None,
            fee_receiver: Optional[str] = None,
            disable_rf_qs: Optional[bool] = None,
            ignore_aggregators: Optional[List[str]] = None,
            block_number: Optional[str] = None,
    ) -> QuotePostRouteOutput:
        """
        Asynchronously executes the quote request.

        Args:
            api_token (str): Token for API authentication.
            chain_id (Optional[int]): Chain ID of the network for transaction execution. Default is 1.
            from_address (Optional[str]): Ethereum address of the wallet to send the transaction from.
            routing_strategy (Optional[str]): Routing strategy: 'ensowallet', 'router', or 'delegate'.
            route (List[SimplePath]): Ordered array of paths for simulation (required).
            fee (Optional[List[str]]): Fee in basis points for the route.
            fee_receiver (Optional[str]): Address to receive the fees.
            disable_rf_qs (Optional[bool]): Whether to exclude RFQ sources from routes.
            ignore_aggregators (Optional[List[str]]): List of swap aggregators to ignore.
            block_number (Optional[str]): Hex string of the block number.

        Returns:
            QuotePostRouteOutput: Output data for the `/api/v1/static/shortcuts/quote` endpoint.
        """
        api_url = "https://api.yourapplication.com/api/v1/static/shortcuts/quote"  # Replace with the actual API URL.

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_token}",
        }

        payload = {
            "chainId": chain_id,
            "fromAddress": from_address,
            "routingStrategy": routing_strategy,
            "route": [route_item.dict() for route_item in route] if route else None,
            "fee": fee,
            "feeReceiver": fee_receiver,
            "disableRFQs": disable_rf_qs,
            "ignoreAggregators": ignore_aggregators,
            "blockNumber": block_number,
        }

        # Remove null values from the payload
        payload = {key: value for key, value in payload.items() if value is not None}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(api_url, headers=headers, json=payload)
                response.raise_for_status()  # Raise HTTPError for non-success codes

                return QuotePostRouteOutput(success=True, data=Quote(**response.json()), error=None)

            except httpx.RequestError as request_error:
                return QuotePostRouteOutput(success=False, data=None, error=f"Request error: {str(request_error)}")
            except httpx.HTTPStatusError as http_error:
                return QuotePostRouteOutput(success=False, data=None, error=f"HTTP status error: {str(http_error)}")
            except Exception as e:
                return QuotePostRouteOutput(success=False, error=str(e))
