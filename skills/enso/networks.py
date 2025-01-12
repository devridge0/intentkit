from typing import List, Optional, Type

import httpx
from pydantic import BaseModel, Field

from .base import EnsoBaseTool, base_url


class EnsoGetNetworksInput(BaseModel):
    """
    Input model for retrieving networks.
    """
    name: Optional[str] = Field(None, description="Optional name of the network to filter")
    chainId: Optional[str] = Field(None, description="Optional chain ID of the network to filter")


class ConnectedNetwork(BaseModel):
    """
    Represents a single network connection.
    """
    id: str = Field(..., description="Unique identifier of the network")
    name: str = Field(..., description="Name of the network")
    isConnected: bool = Field(..., description="Indicates if the network is connected")


class Metadata(BaseModel):
    """
    Metadata about the network response.
    """
    totalCount: int = Field(..., description="Total number of networks returned")


class NetworkResponse(BaseModel):
    """
    Response model containing network list and metadata.
    """
    data: List[ConnectedNetwork] = Field(..., description="List of networks in the response")
    meta: Metadata = Field(..., description="Metadata information about the response")


class EnsoGetNetworksOutput(BaseModel):
    """
    Output model for retrieving networks.
    """
    network_res: Optional[NetworkResponse] = Field(..., description="Response containing networks and metadata")
    error: Optional[str] = Field(None, description="Error message if network retrieval failed")


class EnsoGetNetworks(EnsoBaseTool):
    """
    Tool for retrieving networks supported by the API.

    Endpoint: `/api/v1/networks`

    This class allows fetching a filtered list of networks using optional query parameters `name` and `chainId`.
    """

    name: str = "enso_get_networks"
    description: str = "Retrieve networks supported by the API"
    args_schema: Type[BaseModel] = EnsoGetNetworksInput

    def _run(self) -> EnsoGetNetworksOutput:
        """Sync implementation of the tool.

        This tool doesn't have a native sync implementation.
        """

    async def _arun(self, api_token: str, name: Optional[str] = None,
                    chain_id: Optional[str] = None) -> EnsoGetNetworksOutput:
        """
        Asynchronous function to request the list of supported networks.

        Args:
            api_token (str): API authorization token.
            name (Optional[str]): Optional name of the network to filter.
            chain_id (Optional[str]): Optional chain ID to filter.

        Returns:
            EnsoGetNetworksOutput: A structured output containing the network list or an error message.
        """
        url = f"{base_url}/api/v1/networks"

        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {api_token}",
        }

        # Add optional query parameters
        params = {}
        if name:
            params["name"] = name
        if chain_id:
            params["chainId"] = chain_id

        async with httpx.AsyncClient() as client:
            try:
                # Send the GET request
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()

                # Parse the response JSON into the NetworkResponse model
                json_dict = response.json()
                network_response = NetworkResponse(**json_dict)
                return EnsoGetNetworksOutput(network_res=network_response)
            except Exception as e:
                # Handle any errors that occur
                return EnsoGetNetworksOutput(network_res=None, error=str(e))
