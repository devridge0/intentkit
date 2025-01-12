from typing import List, Optional, Type

import httpx
from pydantic import BaseModel, Field

from .base import EnsoBaseTool, base_url


class EnsoGetWalletInput(BaseModel):
    """
    Input model for retrieving wallet information.
    """
    address: str = Field(..., description="Address of the wallet to retrieve information for")
    chainId: str = Field(..., description="Chain ID of the blockchain network")


class TokenBalance(BaseModel):
    """
    Represents a single token's balance within a wallet.
    """
    tokenAddress: str = Field(..., description="Address of the token contract.")
    tokenSymbol: str = Field(..., description="Symbol of the token (e.g., 'ETH', 'USDC').")
    balance: str = Field(..., description="The balance of the token in the wallet.")
    priceUSD: Optional[float] = Field(None, description="The current price of the token in USD.")
    valueUSD: Optional[float] = Field(None,
                                      description="The total value of the token balance in USD (balance * priceUSD).")


class WalletResponse(BaseModel):
    """
    Response model for wallet details.
    """
    address: str = Field(..., description="Address of the queried wallet")
    chainId: str = Field(..., description="Chain ID of the queried blockchain network")
    tokens: List[TokenBalance] = Field(..., description="List of tokens and their balances in the wallet")


class EnsoGetWalletOutput(BaseModel):
    """
    Output model for wallet data retrieval.
    """
    wallet_res: Optional[WalletResponse] = Field(..., description="Details of the wallet, including token balances")
    error: Optional[str] = Field(None, description="Error message if wallet retrieval fails")


class EnsoGetWallet(EnsoBaseTool):
    """
    Tool for retrieving wallet details via the `/api/v1/wallet` endpoint.

    This tool retrieves a list of token balances along with token values in a specific wallet address
    on a given blockchain network.
    """

    name: str = "enso_get_wallet"
    description: str = "Retrieve wallet balances and token values"
    args_schema: Type[BaseModel] = EnsoGetWalletInput

    def _run(self) -> EnsoGetWalletOutput:
        """Sync implementation of the tool.

        This tool doesn't have a native sync implementation.
        """

    async def _arun(self, api_token: str, address: str, chain_id: str) -> EnsoGetWalletOutput:
        """
        Asynchronous function to request wallet details.

        Args:
            api_token (str): API authorization token.
            address (str): Address of the wallet to query.
            chain_id (str): Chain ID of the blockchain network.

        Returns:
            EnsoGetWalletOutput: The wallet details or an error message.
        """
        url = f"{base_url}/api/v1/wallet"

        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {api_token}",
        }

        params = {
            "address": address,
            "chainId": chain_id,
        }

        async with httpx.AsyncClient() as client:
            try:
                # Send the GET request
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()

                # Parse the response JSON into the WalletResponse model
                json_dict = response.json()
                wallet_response = WalletResponse(**json_dict)

                # Return the parsed response
                return EnsoGetWalletOutput(wallet_res=wallet_response, error=None)
            except Exception as e:
                # Handle any errors
                return EnsoGetWalletOutput(wallet_res=None, error=str(e))


class EnsoApproveWalletInput(BaseModel):
    """
    Input model for approving token spend allowance in a wallet.
    """
    walletAddress: str = Field(..., description="Address of the wallet initiating the approval")
    tokenAddress: str = Field(..., description="Address of the token to approve")
    spenderAddress: str = Field(..., description="Address of the spender who will be allowed to spend tokens")
    amount: str = Field(..., description="Amount of the token to approve for spending")
    chainId: str = Field(..., description="Chain ID of the blockchain network where the approval is executed")


class ApproveResponse(BaseModel):
    """
    Response model for wallet approval.
    """
    status: str = Field(..., description="Status of the approval (e.g., 'success', 'pending', 'failed')")
    transactionHash: Optional[str] = Field(None,
                                           description="Transaction hash of the approval transaction (if available)")


class EnsoApproveWalletOutput(BaseModel):
    """
    Output model for wallet approval action.
    """
    approve_res: Optional[ApproveResponse] = Field(...,
                                                   description="Response containing the status of the approval transaction")
    error: Optional[str] = Field(None, description="Error message if the approval fails")


## Approve

class EnsoApproveWallet(EnsoBaseTool):
    """
    Tool for approving token spending in a wallet using the `/api/v1/wallet/approve` endpoint.

    This tool allows the user to approve a specified spender to spend an amount of tokens
    on their behalf within a particular blockchain network.
    """

    name: str = "enso_approve_wallet"
    description: str = "Approve token spending for a wallet on a specified blockchain network."
    args_schema: Type[BaseModel] = EnsoApproveWalletInput

    def _run(self) -> EnsoApproveWalletOutput:
        """Sync implementation of the tool.

        This tool doesn't have a native sync implementation.
        """

    async def _arun(self, api_token: str, wallet_address: str, token_address: str, spender_address: str, amount: str,
                    chain_id: str) -> EnsoApproveWalletOutput:
        """
        Asynchronous function to execute token spend approval.

        Args:
            api_token (str): API authorization token.
            wallet_address (str): Address of the wallet initiating the approval.
            token_address (str): Address of the token to approve.
            spender_address (str): Address of the spender to approve.
            amount (str): Amount of the token to approve.
            chain_id (str): Chain ID of the blockchain network.

        Returns:
            EnsoApproveWalletOutput: Status or error message related to the approval transaction.
        """
        url = f"{base_url}/api/v1/wallet/approve"

        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

        data = {
            "walletAddress": wallet_address,
            "tokenAddress": token_address,
            "spenderAddress": spender_address,
            "amount": amount,
            "chainId": chain_id,
        }

        async with httpx.AsyncClient() as client:
            try:
                # Send the POST request
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()

                # Parse the response JSON into the ApproveResponse model
                json_dict = response.json()
                approve_response = ApproveResponse(**json_dict)

                # Return the parsed response
                return EnsoApproveWalletOutput(approve_res=approve_response, error=None)
            except Exception as e:
                # Handle errors and return a response with the error message
                return EnsoApproveWalletOutput(approve_res=None, error=str(e))


## Get Approvals

class EnsoGetApprovalsInput(BaseModel):
    """
    Input model for retrieving wallet approvals.
    """
    walletAddress: str = Field(..., description="Address of the wallet to query approvals for")
    chainId: str = Field(..., description="Chain ID of the blockchain network")


class ApprovalInfo(BaseModel):
    """
    Represents details about a specific token approval in a wallet.
    """
    tokenAddress: str = Field(..., description="Address of the token approved")
    tokenSymbol: str = Field(..., description="Symbol of the approved token")
    spenderAddress: str = Field(..., description="Address of the spender who has the approval")
    approvedAmount: str = Field(..., description="Amount of tokens the spender is approved to spend")


class ApprovalsResponse(BaseModel):
    """
    Response model for wallet approvals.
    """
    walletAddress: str = Field(..., description="Address of the queried wallet")
    chainId: str = Field(..., description="Chain ID of the queried network")
    approvals: List[ApprovalInfo] = Field(..., description="List of token approvals in the wallet")


class EnsoGetApprovalsOutput(BaseModel):
    """
    Output model for retrieving wallet approvals.
    """
    approvals_res: Optional[ApprovalsResponse] = Field(...,
                                                       description="Response containing the list of token approvals.")
    error: Optional[str] = Field(None, description="Error message if approvals retrieval fails.")


class EnsoGetApprovals(EnsoBaseTool):
    """
    Tool for retrieving token approvals within a wallet via the `/api/v1/wallet/approvals` endpoint.

    This tool allows querying for all token spend approvals associated with a specific wallet
    and blockchain network.
    """

    name: str = "enso_get_approvals"
    description: str = "Retrieve token spend approvals for a wallet on a specified blockchain network."
    args_schema: Type[BaseModel] = EnsoGetApprovalsInput

    def _run(self) -> EnsoGetApprovalsOutput:
        """Sync implementation of the tool.

        This tool doesn't have a native sync implementation.
        """

    async def _arun(self, api_token: str, wallet_address: str, chain_id: str) -> EnsoGetApprovalsOutput:
        """
        Asynchronous function to retrieve token approvals for a wallet.

        Args:
            api_token (str): API authorization token.
            wallet_address (str): Address of the wallet to query for approvals.
            chain_id (str): Chain ID of the blockchain network.

        Returns:
            EnsoGetApprovalsOutput: The list of approvals or an error message.
        """
        url = f"{base_url}/api/v1/wallet/approvals"

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

                # Map the response JSON into the ApprovalsResponse model
                json_dict = response.json()
                approvals_response = ApprovalsResponse(**json_dict)

                # Return the parsed response
                return EnsoGetApprovalsOutput(approvals_res=approvals_response, error=None)
            except Exception as e:
                # Return an error response on exceptions
                return EnsoGetApprovalsOutput(approvals_res=None, error=str(e))


# Balances


class EnsoGetBalancesInput(BaseModel):
    """
    Input model for retrieving wallet balances.
    """
    walletAddress: str = Field(..., description="The address of the wallet to fetch balances for.")
    chainId: str = Field(..., description="The chain ID of the blockchain network where the wallet is located.")


class WalletBalancesResponse(BaseModel):
    """
    Response model for wallet balances.
    """
    walletAddress: str = Field(..., description="The address of the queried wallet.")
    chainId: str = Field(..., description="The chain ID of the blockchain network.")
    tokenBalances: List[TokenBalance] = Field(..., description="List of all token balances available in the wallet.")


class EnsoGetBalancesOutput(BaseModel):
    """
    Output model for retrieving wallet balances.
    """
    balances_res: Optional[WalletBalancesResponse] = Field(...,
                                                           description="The wallet's balances along with token details.")
    error: Optional[str] = Field(None, description="Error message if the balance retrieval fails.")


class EnsoGetBalances(EnsoBaseTool):
    """
    Tool for retrieving token balances from a wallet via the `/api/v1/wallet/balances` endpoint.

    This tool fetches the token balances within a specific wallet address on a specified blockchain network.
    """

    name: str = "enso_get_balances"
    description: str = "Retrieve all token balances in a wallet for a specific blockchain network."
    args_schema: Type[BaseModel] = EnsoGetBalancesInput

    def _run(self) -> EnsoGetBalancesOutput:
        """Sync implementation of the tool.

        This tool doesn't have a native sync implementation.
        """

    async def _arun(self, api_token: str, wallet_address: str, chain_id: str) -> EnsoGetBalancesOutput:
        """
        Asynchronous function to retrieve wallet balances.

        Args:
            api_token (str): The API authorization token.
            wallet_address (str): Address of the wallet whose balances are being queried.
            chain_id (str): The chain ID of the blockchain network.

        Returns:
            EnsoGetBalancesOutput: A response containing wallet balances or an error message.
        """
        url = f"{base_url}/api/v1/wallet/balances"

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

                # Parse the JSON response into the WalletBalancesResponse model
                json_dict = response.json()
                balances_response = WalletBalancesResponse(**json_dict)

                # Return the parsed response
                return EnsoGetBalancesOutput(balances_res=balances_response, error=None)
            except Exception as e:
                # Handle errors and return a response with the error message
                return EnsoGetBalancesOutput(balances_res=None, error=str(e))
