from typing import Literal, Type

import httpx
from pydantic import BaseModel, Field

from .base import EnsoBaseTool, base_url


class EnsoGetApprovalsInput(BaseModel):
    """
    Input model for retrieving wallet approvals.
    """
    fromAddress: str = Field(..., description="Address of the wallet to query approvals for")
    chainId: int = Field(1, description="Chain ID of the blockchain network")
    routingStrategy: Literal["ensowallet", "router", "delegate"] | None = Field(None,
                                                                                description="Routing strategy to use")


class WalletAllowance(BaseModel):
    token: str | None = Field(None, description="The token address")
    allowance: str | None = Field(None, description="The amount of tokens approved")
    spender: str | None = Field(None, description="The spender address")


class EnsoGetApprovalsOutput(BaseModel):
    """
    Output model for retrieving wallet approvals.
    """
    res: list[WalletAllowance] | None = Field(None,
                                              description="Response containing the list of token approvals.")
    error: str | None = Field(None, description="Error message if approvals retrieval fails.")


class EnsoGetApprovals(EnsoBaseTool):
    """
    This tool allows querying for first 50 token spend approvals associated with a specific wallet
    and blockchain network.

    Attributes:
        name (str): Name of the tool, specifically "enso_get_approvals".
        description (str): Comprehensive description of the tool's purpose and functionality.
        args_schema (Type[BaseModel]): Schema for input arguments, specifying expected parameters.
    """

    name: str = "enso_get_approvals"
    description: str = "Retrieve token spend approvals for a wallet on a specified blockchain network."
    args_schema: Type[BaseModel] = EnsoGetApprovalsInput

    def _run(self, fromAddress: str, chainId: int = 1, **kwargs) -> EnsoGetApprovalsOutput:
        """
        Run the tool to get token approvals for a wallet.

        Args:
            fromAddress (str): Address of the wallet to query for approvals.
            chainId (int): Chain ID of the blockchain network.

        Returns:
            EnsoGetApprovalsOutput: The list of approvals or an error message.
        """
        url = f"{base_url}/api/v1/wallet/approvals"

        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        }

        params = EnsoGetApprovalsInput(fromAddress=fromAddress, chainId=chainId)

        if kwargs.get("routingStrategy"):
            params.routingStrategy = kwargs["routingStrategy"]

        with httpx.Client() as client:
            try:
                # Send the GET request
                response = client.get(url, headers=headers, params=params.model_dump(exclude_none=True))
                response.raise_for_status()

                # Map the response JSON into the ApprovalsResponse model
                json_dict = response.json()[:50]
                res = [WalletAllowance(**item) for item in json_dict]

                # Return the parsed response
                return EnsoGetApprovalsOutput(res=res, error=None)
            except httpx.RequestError as req_err:
                return EnsoGetApprovalsOutput(res=None, error=f"Request error: {req_err}")
            except httpx.HTTPStatusError as http_err:
                return EnsoGetApprovalsOutput(res=None, error=f"HTTP error: {http_err}")
            except Exception as e:
                # Return an error response on exceptions
                return EnsoGetApprovalsOutput(res=None, error=str(e))

    async def _arun(self, fromAddress: str, chainId: int = 1, **kwargs) -> EnsoGetApprovalsOutput:
        """Async implementation of the tool.

                This tool doesn't have a native async implementation, so we call the sync version.
                """
        return self._run(fromAddress, chainId, **kwargs)


class EnsoGetBalancesInput(BaseModel):
    """
    Input model for retrieving wallet balances.
    """
    chainId: int = Field(1, description="Chain ID of the blockchain network")
    eoaAddress: str = Field(description="Address of the eoa with which to associate the ensoWallet for balances")
    useEoa: bool = Field(
        description="If true returns balances for the provided eoaAddress, instead of the associated ensoWallet")


class WalletBalance(BaseModel):
    token: str | None = Field(None, description="The address of the token")
    amount: str | None = Field(None, description="The unformatted balance of the token")
    decimals: int | None = Field(None, ge=0, description="The number of decimals")
    price: float | None = Field(None, description="Price of the token in usd")


class EnsoGetBalancesOutput(BaseModel):
    """
    Output model for retrieving wallet balances.
    """
    res: list[WalletBalance] | None = Field(None,
                                            description="The wallet's balances along with token details.")
    error: str | None = Field(None, description="Error message if the balance retrieval fails.")


class EnsoGetBalances(EnsoBaseTool):
    """
    This tool allows querying for first 20 token balances of a specific wallet
    and blockchain network.

    Attributes:
        name (str): Name of the tool, specifically "enso_get_wallet_balances".
        description (str): Comprehensive description of the tool's purpose and functionality.
        args_schema (Type[BaseModel]): Schema for input arguments, specifying expected parameters.
    """

    name: str = "enso_get_wallet_balances"
    description: str = "Retrieve token balances of a wallet on a specified blockchain network."
    args_schema: Type[BaseModel] = EnsoGetBalancesInput

    def _run(self, eoaAddress: str, useEoa: bool, chainId: int = 1) -> EnsoGetBalancesOutput:
        """
        Run the tool to get token balances of a wallet.

        Args:
            eoaAddress (str): Address of the wallet to query for balances.
            chainId (int): Chain ID of the blockchain network.

        Returns:
            EnsoGetBalancesOutput: The list of balances or an error message.
        """
        url = f"{base_url}/api/v1/wallet/balances"

        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        }

        params = EnsoGetBalancesInput(eoaAddress=eoaAddress, useEoa=useEoa, chainId=chainId)

        with httpx.Client() as client:
            try:
                # Send the GET request
                response = client.get(url, headers=headers, params=params.model_dump(exclude_none=True))
                response.raise_for_status()

                # Map the response JSON into the WalletBalance model
                json_dict = response.json()[:20]
                res = [WalletBalance(**item) for item in json_dict]

                # Return the parsed response
                return EnsoGetBalancesOutput(res=res, error=None)
            except httpx.RequestError as req_err:
                return EnsoGetBalancesOutput(res=None, error=f"Request error: {req_err}")
            except httpx.HTTPStatusError as http_err:
                return EnsoGetBalancesOutput(res=None, error=f"HTTP error: {http_err}")
            except Exception as e:
                # Return an error response on exceptions
                return EnsoGetBalancesOutput(res=None, error=str(e))

    async def _arun(self, eoaAddress: str, useEoa: bool, chainId: int = 1) -> EnsoGetBalancesOutput:
        """Async implementation of the tool.

                This tool doesn't have a native async implementation, so we call the sync version.
                """
        return self._run(eoaAddress, useEoa, chainId)
