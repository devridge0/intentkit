"""Tool for fetching wallet portfolio for a specific chain."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from .base import WalletPortfolioBaseTool
from .api import fetch_wallet_balances, fetch_token_approvals

FETCH_CHAIN_PORTFOLIO_PROMPT = """
This tool fetches wallet portfolio data for a specific blockchain.
Provide a wallet address and chain ID to get detailed information about tokens and their values.
Returns:
- Token balances for the specified chain
- USD value of each token
- Total chain value
- Token metadata (symbol, name, decimals)
"""

class FetchChainPortfolioInput(BaseModel):
    """Input schema for fetching chain portfolio."""
    
    address: str = Field(..., description="Wallet address")
    chain_id: int = Field(..., description="Chain ID to fetch portfolio for")


class ChainTokenBalance(BaseModel):
    """Model representing a token balance on a specific chain."""
    
    contract_address: str = Field(..., description="Token contract address")
    symbol: str = Field(..., description="Token symbol")
    name: str = Field(..., description="Token name")
    logo: Optional[str] = Field(None, description="Token logo URL")
    decimals: int = Field(..., description="Token decimals")
    balance: float = Field(..., description="Token balance")
    balance_raw: str = Field(..., description="Raw token balance")
    balance_usd: float = Field(0.0, description="USD value of token balance")


class ChainPortfolioOutput(BaseModel):
    """Response schema for chain portfolio."""
    
    address: str = Field(..., description="Wallet address")
    chain_id: int = Field(..., description="Chain ID")
    chain_name: str = Field(..., description="Chain name")
    native_token: Optional[ChainTokenBalance] = Field(None, description="Native token balance")
    tokens: List[ChainTokenBalance] = Field(default_factory=list, description="List of token balances")
    total_usd_value: float = Field(0.0, description="Total USD value on this chain")
    token_approvals: Optional[List[Dict]] = Field(None, description="Token approvals if requested")
    error: Optional[str] = Field(None, description="Error message if any")


class FetchChainPortfolio(WalletPortfolioBaseTool):
    """Tool for fetching wallet portfolio for a specific blockchain.
    
    This tool retrieves detailed portfolio data for a wallet address on a specific blockchain,
    including token balances and their USD values.
    """
    
    name: str = "fetch_chain_portfolio"
    description: str = FETCH_CHAIN_PORTFOLIO_PROMPT
    args_schema = FetchChainPortfolioInput
    
    def _run(
        self, address: str, chain_id: int
    ) -> ChainPortfolioOutput:
        """Synchronous implementation - not supported."""
        raise NotImplementedError("Use _arun instead")
    
    async def _arun(
        self, address: str, chain_id: int
    ) -> ChainPortfolioOutput:
        """Fetch wallet portfolio for a specific chain.
        
        Args:
            address: Wallet address to fetch portfolio for
            chain_id: Chain ID to fetch portfolio for
            
        Returns:
            ChainPortfolioOutput containing portfolio data for the specified chain
        """
        try:
            # Check rate limiting
            is_rate_limited, error_msg = await self.check_rate_limit()
            if is_rate_limited:
                return ChainPortfolioOutput(
                    address=address,
                    chain_id=chain_id,
                    chain_name=self._get_chain_name(chain_id),
                    error=error_msg
                )
            
            # Fetch wallet balances for the specified chain
            balances = await fetch_wallet_balances(self.api_key, address, chain_id)
            
            if "error" in balances:
                return ChainPortfolioOutput(
                    address=address,
                    chain_id=chain_id,
                    chain_name=self._get_chain_name(chain_id),
                    error=balances["error"]
                )
            
            # Process the data
            portfolio = {
                "address": address,
                "chain_id": chain_id,
                "chain_name": self._get_chain_name(chain_id),
                "tokens": [],
                "total_usd_value": 0.0
            }
            
            for token in balances.get("result", []):
                token_balance = ChainTokenBalance(
                    contract_address=token["token_address"],
                    symbol=token.get("symbol", "UNKNOWN"),
                    name=token.get("name", "Unknown Token"),
                    logo=token.get("logo", None),
                    decimals=token.get("decimals", 18),
                    balance=float(token.get("balance_formatted", 0)),
                    balance_raw=token.get("balance", "0"),
                    balance_usd=float(token.get("usd_value", 0))
                )
                
                # Identify native token
                if token.get("native_token", False):
                    portfolio["native_token"] = token_balance
                else:
                    portfolio["tokens"].append(token_balance)
                
                # Add to total USD value
                portfolio["total_usd_value"] += token_balance.balance_usd
            
            # Fetch token approvals if available through the API
            try:
                approvals = await fetch_token_approvals(self.api_key, address, chain_id)
                if "error" not in approvals:
                    portfolio["token_approvals"] = approvals.get("result", [])
            except:
                # Approvals are optional, continue even if this fails
                pass
            
            return ChainPortfolioOutput(**portfolio)
            
        except Exception as e:
            return ChainPortfolioOutput(
                address=address,
                chain_id=chain_id,
                chain_name=self._get_chain_name(chain_id),
                error=str(e)
            )