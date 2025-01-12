from typing import List, Optional, Type

import httpx
from pydantic import BaseModel, Field

from .base import EnsoBaseTool, base_url


class EnsoGetActionsInput(BaseModel):
    """
    Input model for retrieving available actions.
    """
    walletAddress: str = Field(..., description="The wallet address to execute the action.")
    chainId: str = Field(..., description="The ID of the blockchain network where the action applies.")


class ActionInfo(BaseModel):
    """
    Represents metadata about a specific available action.
    """
    actionId: str = Field(..., description="The unique identifier for the action.")
    name: str = Field(..., description="The name of the action.")
    description: Optional[str] = Field(None, description="A detailed description of what the action does.")
    parameters: List[str] = Field(..., description="The list of parameters required by the action.")


class ActionsResponse(BaseModel):
    """
    Response model for available actions.
    """
    walletAddress: str = Field(..., description="The wallet for which actions are retrieved.")
    chainId: str = Field(..., description="The blockchain network where the actions are applicable.")
    actions: List[ActionInfo] = Field(..., description="The list of available actions.")


class EnsoGetActionsOutput(BaseModel):
    """
    Output model for retrieving actions.
    """
    actions_res: Optional[ActionsResponse] = Field(..., description="A response containing the list of actions.")
    error: Optional[str] = Field(None, description="Error message if the retrieval of actions fails.")


class EnsoGetActions(EnsoBaseTool):
    """
    Tool for retrieving available actions via the `/api/v1/actions` endpoint.

    This tool fetches metadata about all available actions for a specific wallet address
    and blockchain network.
    """

    name: str = "enso_get_actions"
    description: str = "Retrieve a list of available actions for a wallet and blockchain network."
    args_schema: Type[BaseModel] = EnsoGetActionsInput

    def _run(self) -> EnsoGetActionsOutput:
        """Sync implementation of the tool.

        This tool doesn't have a native sync implementation.
        """

    async def _arun(self, api_token: str, wallet_address: str, chain_id: str) -> EnsoGetActionsOutput:
        """
        Asynchronous function to fetch available actions.

        Args:
            api_token (str): Authorization token for the API.
            wallet_address (str): The wallet address whose actions are being fetched.
            chain_id (str): The chain ID of the blockchain network.

        Returns:
            EnsoGetActionsOutput: A response containing metadata about available actions or error details.
        """
        url = f"{base_url}/api/v1/actions"

        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {api_token}",
        }

        params = {
            "walletAddress": wallet_address,
            "chainId": chain_id,
        }

        async with httpx.AsyncClient() as client:
            try:
                # Send the GET request
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()

                # Parse the response into the ActionsResponse model
                json_dict = response.json()
                actions_response = ActionsResponse(**json_dict)

                # Return the parsed response
                return EnsoGetActionsOutput(actions_res=actions_response, error=None)
            except Exception as e:
                # Handle errors and return response with error message
                return EnsoGetActionsOutput(actions_res=None, error=str(e))
