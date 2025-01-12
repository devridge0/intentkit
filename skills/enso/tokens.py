from datetime import datetime, timedelta, timezone
from typing import Type, List, Optional

import httpx
from pydantic import BaseModel, Field, HttpUrl

from .base import EnsoBaseTool, base_url


class UnderlyingToken(BaseModel):
    address: str = Field(..., description="The address of the token")
    chainId: int = Field(..., description="The blockchain chain ID")
    type: str = Field(..., description="The type of the token (e.g., base token)")
    decimals: int = Field(..., description="The number of decimals for the token")
    name: str = Field(..., description="The name of the token")
    symbol: str = Field(..., description="The symbol of the token")
    logosUri: List[HttpUrl] = Field(..., description="List of URLs to token's logos")


class TokenData(BaseModel):
    chainId: int = Field(..., description="The blockchain chain ID")
    address: str = Field(..., description="The address of the token")
    decimals: int = Field(..., description="The number of decimals for the token")
    name: str = Field(..., description="The name of the token")
    symbol: str = Field(..., description="The symbol of the token")
    logosUri: List[HttpUrl] = Field(..., description="List of URLs to token's logos")
    type: str = Field(..., description="The type of the token (e.g., defi, nft, etc.)")
    protocolSlug: str = Field(..., description="The protocol slug associated with the token")
    underlyingTokens: List[UnderlyingToken] = Field(..., description="List of underlying tokens")
    primaryAddress: str = Field(..., description="The primary address associated with the token")
    apy: float = Field(..., description="The annual percentage yield (APY) for the token")


class MetaData(BaseModel):
    total: int = Field(..., description="Total number of records")
    lastPage: int = Field(..., description="Last page of the data")
    currentPage: int = Field(..., description="Current page of the data")
    perPage: int = Field(..., description="Number of records per page")
    prev: Optional[int] = Field(None, description="Previous page number, if applicable")
    next: Optional[int] = Field(None, description="Next page number, if applicable")


class TokenResponse(BaseModel):
    data: List[TokenData] = Field(..., description="List of token data")
    meta: MetaData = Field(..., description="Metadata regarding pagination")


class EnsoGetTokensInput(BaseModel):
    api_token: str = Field(description="Enso API token")
    chain_id: int = Field(description="The blockchain chain ID", default=None)
    protocol_slug: str = Field(description="The protocol slug (e.g., 'aave-v2', 'compound')", default=None)
    token_type: str = Field(description="The type of the token (e.g., 'defi', 'nft')", default=None)
    underlying_tokens: str | list[str] = Field(
        description="Underlying tokens (e.g. 0xdAC17F958D2ee523a2206206994597C13D831ec7)", default=None)
    page: int = Field(description="Page number (e.g., 1)", default=1)


class EnsoGetTokensOutput(BaseModel):
    token_res: TokenResponse
    error: str | None = None


class EnsoGetTokens(EnsoBaseTool):
    """Tool for getting APY from Enso.

    This tool uses the Enso API v1 to retrieve tokens APY from Enso.

    Attributes:
        name: The name of the tool.
        description: A description of what the tool does.
        args_schema: The schema for the tool's input arguments.
    """

    name: str = "enso_get_apy"
    description: str = "Get APY from Enso"
    args_schema: Type[BaseModel] = EnsoGetTokensInput

    def _run(self) -> EnsoGetTokensOutput:
        """Sync implementation of the tool.

        This tool doesn't have a native sync implementation.
        """

    async def _arun(self, api_token, protocol_slug: Optional[str] = None, token_type: Optional[str] = None,
                    underlying_tokens: Optional[str | list[str]] = None,
                    chain_id: Optional[int] = None,
                    page: Optional[int] = 1) -> EnsoGetTokensOutput:
        """Run the tool to get Tokens and APY.
        Args:
            api_token (str): API authorization token.
            protocol_slug (Optional[str]): Protocol Slug to filter (e.g., 'aave-v2', 'compound').
            token_type (Optional[str]): Type of token to filter (e.g., 'defi', 'nft').
            underlying_tokens (str | list[str]): Underlying tokens to filter (e.g. 0xdAC17F958D2ee523a2206206994597C13D831ec7).
            chain_id (Optional[str]): Chain ID to filter.
            page (Optional[int]): Page number (e.g., 1)
        Returns:
            EnsoGetTokensOutput: A structured output containing the tokens APY data.

        Raises:
            Exception: If there's an error accessing the Enso API.
        """
        url = f"{base_url}/api/v1/tokens"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {api_token}",
        }

        params = {
            "page": page,
            "perPage": 20,
            "includeMetadata": "true"
        }

        if chain_id:
            params["chainId"] = chain_id

        if protocol_slug:
            params["protocolSlug"] = protocol_slug

        if token_type:
            params["type"] = token_type

        if isinstance(underlying_tokens, str):
            params["underlyingTokens"] = underlying_tokens
        elif isinstance(underlying_tokens, list):
            params["underlyingTokens"] = ",".join(underlying_tokens)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                json_dict = response.json()
                token_response = TokenResponse(**json_dict)
                return EnsoGetTokensOutput(token_res=token_response)
            except Exception as e:
                return EnsoGetTokensOutput(token_res=TokenResponse(data=[], meta=MetaData()), error=str(e))
