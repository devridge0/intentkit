from typing import Type, List, Optional, Dict, Any

import httpx
from pydantic import BaseModel, Field, HttpUrl

from .base import EnsoBaseTool, base_url


class ActionToBundleArgs(BaseModel):
    """
    Schema for the `args` property inside ActionToBundle.
    """
    tokenIn: str = Field(..., description="Token input address.")
    tokenOut: str = Field(..., description="Token output address.")
    amountIn: str = Field(..., description="Amount of input token in wei.")
    slippage: str = Field(..., description="Slippage in basis points (1/10000).")
    fee: List[str] = Field(
        None,
        description="An array of fee percentages in basis points.",
    )
    feeReceiver: str = Field(
        default=None,
        description="Ethereum address to receive fees.",
    )


class ActionToBundle(BaseModel):
    """
    Input schema for individual actions within the bundle.
    """
    protocol: List[str] = Field(..., description="Protocols to interact with.")
    action: str = Field(
        ...,
        description="Action to perform.",
    )
    args: ActionToBundleArgs = Field(..., description="Arguments for the action.")


class EnsoShortcutBundleInput(BaseModel):
    actions_to_bundle: List[ActionToBundle]


class Transaction(BaseModel):
    """
    Schema for the `tx` object in BundleShortcutTransaction.
    """
    # Add properties of the Transaction schema here based on your actual transaction structure
    data: Dict[str, Any] = Field(..., description="Transaction data properties.")


class BundleShortcutTransaction(BaseModel):
    """
    Output schema for the `/api/v1/shortcuts/bundle` endpoint.
    """
    bundle: List[ActionToBundle] = Field(..., description="The actions in the resulting bundle.")
    gas: str = Field(..., description="Gas amount for the transaction.")
    createdAt: int = Field(..., description="Block number when the transaction was created.")
    tx: Transaction = Field(..., description="The transaction object to use in `ethers`.")


class EnsoShortcutBundleOutput(BaseModel):
    """
    Output model for the `/api/v1/shortcuts/route` endpoint response.
    """
    success: bool = Field(..., description="Indicates whether the request was successful.")
    data: Optional[BundleShortcutTransaction] = Field(None, description="Details about the route, if successful.")
    error: Optional[str] = Field(None, description="Error message, if the request failed.")


class EnsoShortcutBundle(EnsoBaseTool):
    """
    Handles the POST request to the `/api/v1/shortcuts/bundle` endpoint.
    """

    name: str = "enso_post_bundle_shortcut"
    description: str = "Create a transaction bundle using the `/api/v1/shortcuts/bundle` endpoint."
    args_schema: BaseModel = ActionToBundle

    def _run(self) -> EnsoShortcutBundleOutput:
        """Sync implementation of the tool.

        This tool doesn't have a native sync implementation.
        """

    async def _arun(self, api_token: str, bundle: EnsoShortcutBundleInput) -> EnsoShortcutBundleOutput:
        """
        Executes the bundle creation process asynchronously.

        Args:
            api_token (str): Authorization token for accessing the API.
            bundle (EnsoShortcutBundleInput): List of actions to include in the bundle.

        Returns:
            EnsoShortcutBundleOutput: The response containing bundling results or error details.
        """

        api_url = f"{base_url}/api/v1/shortcuts/bundle"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_token}",
        }

        payload = {
            "bundle": [action.dict() for action in bundle],
        }

        async with httpx.AsyncClient() as client:
            try:
                # Send POST request to the API
                response = await client.post(api_url, headers=headers, json=payload)
                response.raise_for_status()  # Raise an exception for non-success HTTP codes

                # Parse and return the resulting JSON response
                return EnsoShortcutBundleOutput(success=True, data=BundleShortcutTransaction(**response.json()),
                                                error=None)

            except httpx.RequestError as request_error:
                # Handle request errors
                return EnsoShortcutBundleOutput(success=True, data=None,
                                                error=f"Request error occurred: {str(request_error)}")
            except httpx.HTTPStatusError as http_error:
                # Handle HTTP response errors
                return EnsoShortcutBundleOutput(success=True, data=None,
                                                error=f"HTTP status error occurred: {str(http_error)}")
            except Exception as e:
                # Handle unexpected exceptions
                return EnsoShortcutBundleOutput(success=True, data=None,
                                                error=f"An unexpected error occurred: {str(e)}")
