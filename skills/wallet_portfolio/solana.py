"""Solana integration for Wallet Portfolio skills."""

from typing import Dict, List, Optional, Union

import httpx
import logging
from pydantic import BaseModel, Field

from .base import WalletPortfolioBaseTool

logger = logging.getLogger(__name__)

# Solana API endpoints from the documentation
SOLANA_API_BASE = "https://solana-gateway.moralis.io"

class SolanaTokenInfo(BaseModel):
    """Model representing Solana token information."""
    
    symbol: str = Field(..., description="Token symbol")
    name: str = Field(..., description="Token name")
    decimals: int = Field(..., description="Token decimals")
    mint: str = Field(..., description="Token mint address")
    associated_token_address: str = Field(..., description="Associated token address")


class SolanaNftInfo(BaseModel):
    """Model representing Solana NFT information."""
    
    mint: str = Field(..., description="NFT mint address")
    name: Optional[str] = Field(None, description="NFT name")
    symbol: Optional[str] = Field(None, description="NFT symbol")
    associated_token_address: str = Field(..., description="Associated token address")
    metadata: Optional[Dict] = Field(None, description="NFT metadata")


class SolanaTokenBalance(BaseModel):
    """Model representing a Solana token balance."""
    
    token_info: SolanaTokenInfo = Field(..., description="Token information")
    amount: float = Field(..., description="Token amount")
    amount_raw: str = Field(..., description="Raw token amount")
    usd_value: Optional[float] = Field(0.0, description="USD value if available")


class SolanaPortfolio(BaseModel):
    """Model representing Solana portfolio data."""
    
    address: str = Field(..., description="Wallet address")
    sol_balance: float = Field(..., description="Native SOL balance")
    sol_balance_lamports: int = Field(..., description="Native SOL balance in lamports")
    sol_price_usd: Optional[float] = Field(None, description="SOL price in USD")
    sol_value_usd: Optional[float] = Field(None, description="USD value of SOL balance")
    tokens: List[SolanaTokenBalance] = Field(default_factory=list, description="List of token balances")
    nfts: List[SolanaNftInfo] = Field(default_factory=list, description="List of NFTs")
    total_value_usd: float = Field(0.0, description="Total USD value of the portfolio")


class SolanaPortfolioInput(BaseModel):
    """Input schema for fetching Solana wallet portfolio."""
    
    address: str = Field(..., description="Solana wallet address")
    network: str = Field("mainnet", description="Solana network (mainnet or devnet)")
    include_nfts: bool = Field(False, description="Whether to include NFTs in the response")
    include_price: bool = Field(True, description="Whether to include price data")


async def fetch_solana_api(
    api_key: str,
    endpoint: str,
    params: Dict = None
) -> Dict:
    """Base function for Solana API calls using Moralis."""
    headers = {"X-API-Key": api_key}
    url = f"{SOLANA_API_BASE}{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Solana API request error: {e}")
            return {"error": str(e)}
        except httpx.HTTPStatusError as e:
            logger.error(f"Solana API error: {e.response.status_code} {e.response.text}")
            return {"error": f"HTTP error {e.response.status_code}: {e.response.text}"}


async def get_solana_portfolio(
    api_key: str,
    address: str,
    network: str = "mainnet"
) -> Dict:
    """Get portfolio by wallet as shown in the Moralis Solana API docs."""
    endpoint = f"/account/{network}/{address}/portfolio"
    return await fetch_solana_api(api_key, endpoint)


async def get_solana_balance(
    api_key: str,
    address: str,
    network: str = "mainnet"
) -> Dict:
    """Get native SOL balance by wallet."""
    endpoint = f"/account/{network}/{address}/balance"
    return await fetch_solana_api(api_key, endpoint)


async def get_solana_spl_tokens(
    api_key: str,
    address: str,
    network: str = "mainnet"
) -> Dict:
    """Get SPL token balances by wallet."""
    endpoint = f"/account/{network}/{address}/tokens"
    return await fetch_solana_api(api_key, endpoint)


async def get_solana_nfts(
    api_key: str,
    address: str,
    network: str = "mainnet"
) -> Dict:
    """Get NFTs owned by wallet."""
    endpoint = f"/account/{network}/{address}/nft"
    return await fetch_solana_api(api_key, endpoint)


async def get_token_price(
    api_key: str,
    token_address: str,
    network: str = "mainnet"
) -> Dict:
    """Get token price by address."""
    endpoint = f"/token/{network}/{token_address}/price"
    return await fetch_solana_api(api_key, endpoint)


class FetchSolanaPortfolio(WalletPortfolioBaseTool):
    """Tool for fetching Solana wallet portfolio.
    
    This tool retrieves a detailed portfolio overview for a Solana wallet address,
    including SOL balance, SPL tokens, and NFTs if requested.
    """
    
    name: str = "fetch_solana_portfolio"
    description: str = """
    This tool fetches a complete portfolio overview for a Solana wallet address.
    Provide a wallet address to get detailed information about SOL balance, SPL tokens, and NFTs.
    Returns:
    - Native SOL balance
    - SPL token balances
    - NFT holdings (optional)
    - USD value of assets (optional)
    """
    args_schema = SolanaPortfolioInput
    
    def _run(
        self, 
        address: str, 
        network: str = "mainnet",
        include_nfts: bool = False,
        include_price: bool = True
    ) -> SolanaPortfolio:
        """Synchronous implementation - not supported."""
        raise NotImplementedError("Use _arun instead")
    
    async def _arun(
        self, 
        address: str, 
        network: str = "mainnet",
        include_nfts: bool = False,
        include_price: bool = True
    ) -> SolanaPortfolio:
        """Fetch complete Solana wallet portfolio.
        
        Args:
            address: Solana wallet address
            network: Solana network (mainnet or devnet)
            include_nfts: Whether to include NFTs in the response
            include_price: Whether to include price data
            
        Returns:
            SolanaPortfolio containing portfolio data
        """
        try:
            # Check rate limiting
            is_rate_limited, error_msg = await self.check_rate_limit()
            if is_rate_limited:
                return SolanaPortfolio(
                    address=address,
                    sol_balance=0,
                    sol_balance_lamports=0,
                    error=error_msg
                )
            
            # Fetch portfolio data
            portfolio_result = await get_solana_portfolio(self.api_key, address, network)
            
            if "error" in portfolio_result:
                # If portfolio endpoint fails, try to fetch balance and tokens separately
                balance_result = await get_solana_balance(self.api_key, address, network)
                tokens_result = await get_solana_spl_tokens(self.api_key, address, network)
                
                if "error" in balance_result:
                    return SolanaPortfolio(
                        address=address,
                        sol_balance=0,
                        sol_balance_lamports=0,
                        error=balance_result["error"]
                    )
                
                # Initialize the portfolio with balance data
                portfolio = SolanaPortfolio(
                    address=address,
                    sol_balance=float(balance_result.get("solana", 0)),
                    sol_balance_lamports=int(balance_result.get("lamports", 0))
                )
                
                # Add token data if available
                if "error" not in tokens_result:
                    tokens = []
                    for token in tokens_result:
                        token_info = SolanaTokenInfo(
                            symbol=token.get("symbol", ""),
                            name=token.get("name", ""),
                            decimals=int(token.get("decimals", 0)),
                            mint=token.get("mint", ""),
                            associated_token_address=token.get("associatedTokenAddress", "")
                        )
                        
                        token_balance = SolanaTokenBalance(
                            token_info=token_info,
                            amount=float(token.get("amount", 0)),
                            amount_raw=token.get("amountRaw", "0")
                        )
                        
                        tokens.append(token_balance)
                    
                    portfolio.tokens = tokens
            else:
                # Process the portfolio data
                portfolio = SolanaPortfolio(
                    address=address,
                    sol_balance=float(portfolio_result.get("nativeBalance", {}).get("solana", 0)),
                    sol_balance_lamports=int(portfolio_result.get("nativeBalance", {}).get("lamports", 0))
                )
                
                # Process tokens
                tokens = []
                for token in portfolio_result.get("tokens", []):
                    token_info = SolanaTokenInfo(
                        symbol=token.get("symbol", ""),
                        name=token.get("name", ""),
                        decimals=int(token.get("decimals", 0)),
                        mint=token.get("mint", ""),
                        associated_token_address=token.get("associatedTokenAddress", "")
                    )
                    
                    token_balance = SolanaTokenBalance(
                        token_info=token_info,
                        amount=float(token.get("amount", 0)),
                        amount_raw=token.get("amountRaw", "0")
                    )
                    
                    tokens.append(token_balance)
                
                portfolio.tokens = tokens
            
            # Fetch NFTs if requested
            if include_nfts:
                nfts_result = await get_solana_nfts(self.api_key, address, network)
                
                if "error" not in nfts_result:
                    nfts = []
                    for nft in nfts_result:
                        nft_info = SolanaNftInfo(
                            mint=nft.get("mint", ""),
                            name=nft.get("name", ""),
                            symbol=nft.get("symbol", ""),
                            associated_token_address=nft.get("associatedTokenAddress", ""),
                            metadata=nft.get("metadata", None)
                        )
                        
                        nfts.append(nft_info)
                    
                    portfolio.nfts = nfts
            
            # Fetch price data if requested
            if include_price:
                # Fetch SOL price
                sol_price_result = await get_token_price(
                    self.api_key, 
                    "So11111111111111111111111111111111111111112",  # SOL mint address
                    network
                )
                
                if "error" not in sol_price_result:
                    sol_price_usd = float(sol_price_result.get("usdPrice", 0))
                    portfolio.sol_price_usd = sol_price_usd
                    portfolio.sol_value_usd = sol_price_usd * portfolio.sol_balance
                
                # Add this value to the total
                portfolio.total_value_usd += portfolio.sol_value_usd or 0
                
                # Fetch token prices
                for token in portfolio.tokens:
                    if token.token_info.mint:
                        price_result = await get_token_price(
                            self.api_key, 
                            token.token_info.mint,
                            network
                        )
                        
                        if "error" not in price_result:
                            token_price_usd = float(price_result.get("usdPrice", 0))
                            token.usd_value = token_price_usd * token.amount
                            portfolio.total_value_usd += token.usd_value
            
            return portfolio
            
        except Exception as e:
            logger.error(f"Error fetching Solana portfolio: {str(e)}")
            return SolanaPortfolio(
                address=address,
                sol_balance=0,
                sol_balance_lamports=0,
                error=str(e)
            )