from typing import List, Optional, Type

import httpx
from pydantic import BaseModel, Field

from .base import EnsoBaseTool, base_url


class EnsoGetStandardsInput(BaseModel):
    """
    Input model for retrieving available standards.
    """
    chainId: str = Field(..., description="The ID of the blockchain network to fetch standards for.")


class StandardInfo(BaseModel):
    """
    Represents a single standard supported by the API.
    """
    standardId: str = Field(..., description="The unique identifier of the standard.")
    name: str = Field(..., description="The name of the standard.")
    description: Optional[str] = Field(None, description="A brief description of the standard.")
    version: str = Field(..., description="The version of the standard supported.")


class StandardsResponse(BaseModel):
    """
    Response model for available standards.
    """
    chainId: str = Field(..., description="The blockchain network ID for which the standards apply.")
    standards: List[StandardInfo] = Field(..., description="List of supported standards on the specified chain.")


class EnsoGetStandardsOutput(BaseModel):
    """
    Output model for retrieving standards.
    """
    standards_res: Optional[StandardsResponse] = Field(..., description="Response containing the list of standards.")
    error: Optional[str] = Field(None, description="Error message if the standards retrieval fails.")


class EnsoGetStandards(EnsoBaseTool):
    """
    Tool for retrieving supported blockchain standards via the `/api/v1/standards` endpoint.

    This tool fetches a list of all supported standards on a specific blockchain identified by the `chainId`.
    """

    name: str = "enso_get_standards"
    description: str = "Retrieve a list of supported blockchain standards for a specific chain ID."
    args_schema: Type[BaseModel] = EnsoGetStandardsInput

    def _run(self) -> EnsoGetStandardsOutput:
        """Sync implementation of the tool.

        This tool doesn't have a native sync implementation.
        """

    async def _arun(self, api_token: str, chain_id: str) -> EnsoGetStandardsOutput:
        """
        Asynchronous function to fetch blockchain standards.

        Args:
            api_token (str): Authorization token for the API.
            chain_id (str): The chain ID of the blockchain network.

        Returns:
            EnsoGetStandardsOutput: A response containing the blockchain standards or error details.
        """
        url = f"{base_url}/api/v1/standards"

        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {api_token}",
        }

        params = {
            "chainId": chain_id,
        }

        async with httpx.AsyncClient() as client:
            try:
                # Send the GET request
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()

                # Parse the response JSON into the StandardsResponse model
                json_dict = response.json()
                standards_response = StandardsResponse(**json_dict)

                # Return the parsed response
                return EnsoGetStandardsOutput(standards_res=standards_response, error=None)
            except Exception as e:
                # Handle errors and return response with error message
                return EnsoGetStandardsOutput(standards_res=None, error=str(e))
