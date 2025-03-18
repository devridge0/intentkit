"""Tool for fetching complete wallet portfolio."""

from typing import List, Optional, Type

from pydantic import BaseModel, Field

from .api import fetch_multi_chain_balances
from .base import WalletPortfolioBaseTool

FETCH_WALLET_PORTFOLIO_PROMPT = """
This tool fetches a complete portfolio overview for a wallet address across multiple blockchains.
Provide a wallet address to get detailed information about all tokens and their values.
Returns:
- Token balances for each chain
- USD value of each token
- Total portfolio value
- Token metadata (symbol, name, decimals)
"""


class FetchWalletPortfolioInput(BaseModel):
    """Input schema for fetching wallet portfolio."""

    address: str = Field(
        ..., description="Wallet address to fetch portfolio for"
    )
    include_nfts: bool = Field(
        False, description="Whether to include NFTs in the response"
    )


class TokenInfo(BaseModel):
    """Model representing token information."""

    symbol: str = Field(..., description="Token symbol")
    name: str = Field(..., description="Token name")
    decimals: int = Field(..., description="Token decimals")
    logo_url: Optional[str] = Field(None, description="Token logo URL")


class TokenBalance(BaseModel):
    """Model representing a token balance."""

    contract_address: str = Field(..., description="Token contract address")
    balance: float = Field(..., description="Token balance")
    balance_usd: float = Field(..., description="USD value of token balance")
    token_info: TokenInfo = Field(..., description="Token information")


class ChainPortfolio(BaseModel):
    """Model representing portfolio data for a specific chain."""

    chain_id: str = Field(..., description="Chain ID")
    chain_name: str = Field(..., description="Chain name")
    total_usd_value: float = Field(..., description="Total USD value on this chain")
    tokens: List[TokenBalance] = Field(..., description="List of token balances")


class FetchWalletPortfolioOutput(BaseModel):
    """Response schema for fetching wallet portfolio."""

    address: str = Field(..., description="Wallet address")
    total_usd_value: float = Field(..., description="Total USD value of the portfolio")
    portfolios_by_chain: List[ChainPortfolio] = Field(
        ..., description="Portfolio data by chain"
    )
    error: Optional[str] = Field(None, description="Error message if any")


class FetchWalletPortfolio(WalletPortfolioBaseTool):
    """Tool for fetching complete wallet portfolio across multiple chains.

    This tool retrieves a detailed portfolio overview for a wallet address,
    including token balances and their USD values across multiple blockchains.

    Example:
        portfolio_tool = FetchWalletPortfolio(
            api_key="your_api_key",
            skill_store=store,
            agent_id="agent_123",
            agent_store=agent_store,
            chain_provider=chain_provider
        )
        result = await portfolio_tool._arun(
            address="0x..."
        )
    """

    name: str = "fetch_wallet_portfolio"
    description: str = FETCH_WALLET_PORTFOLIO_PROMPT
    args_schema: Type[BaseModel] = FetchWalletPortfolioInput

    def _run(
        self, address: str, include_nfts: bool = False
    ) -> FetchWalletPortfolioOutput:
        """Synchronous implementation - not supported."""
        raise NotImplementedError("Use _arun instead")

    async def _arun(
        self, address: str, include_nfts: bool = False
    ) -> FetchWalletPortfolioOutput:
        """Fetch complete wallet portfolio.

        Args:
            address: Wallet address to fetch portfolio for
            include_nfts: Whether to include NFTs in the response

        Returns:
            FetchWalletPortfolioOutput containing portfolio data or error
        """
        try:
            # Check rate limiting
            is_rate_limited, error_msg = await self.check_rate_limit()
            if is_rate_limited:
                return FetchWalletPortfolioOutput(
                    address=address,
                    total_usd_value=0,
                    portfolios_by_chain=[],
                    error=error_msg
                )

            # Get chain IDs from chain provider or use default list
            chain_ids = []
            if self.chain_provider:
                for network, config in self.chain_provider.chain_configs.items():
                    chain_ids.append(config.chain_id)
            else:
                # Fallback to common chains if no chain provider
                chain_ids = [1, 56, 137, 42161, 10]  # ETH, BSC, Polygon, Arbitrum, Optimism

            # Fetch multi-chain balances
            result = await fetch_multi_chain_balances(
                self.api_key, address, chain_ids, include_nfts
            )
            
            if "error" in result:
                return FetchWalletPortfolioOutput(
                    address=address,
                    total_usd_value=0,
                    portfolios_by_chain=[],
                    error=result["error"]
                )

            # Process the data
            portfolios_by_chain = []
            total_usd_value = 0

            for chain_id, chain_data in result["chains"].items():
                if "data" in chain_data and "items" in chain_data["data"]:
                    tokens = []
                    chain_total_usd = 0
                    
                    chain_name = self._get_chain_name(chain_id) or f"Chain {chain_id}"
                    
                    for item in chain_data["data"]["items"]:
                        token_balance = TokenBalance(
                            contract_address=item["contract_address"],
                            balance=float(item["balance"]) / (10 ** item["contract_decimals"]),
                            balance_usd=item["quote"],
                            token_info=TokenInfo(
                                symbol=item["contract_ticker_symbol"],
                                name=item["contract_name"],
                                decimals=item["contract_decimals"],
                                logo_url=item.get("logo_url")
                            )
                        )
                        tokens.append(token_balance)
                        chain_total_usd += item["quote"]
                    
                    chain_portfolio = ChainPortfolio(
                        chain_id=chain_id,
                        chain_name=chain_name,
                        total_usd_value=chain_total_usd,
                        tokens=tokens
                    )
                    
                    portfolios_by_chain.append(chain_portfolio)
                    total_usd_value += chain_total_usd

            return FetchWalletPortfolioOutput(
                address=address,
                total_usd_value=total_usd_value,
                portfolios_by_chain=portfolios_by_chain
            )

        except Exception as e:
            return FetchWalletPortfolioOutput(
                address=address,
                total_usd_value=0,
                portfolios_by_chain=[],
                error=str(e)
            )
    
    def _get_chain_name(self, chain_id: str) -> Optional[str]:
        """Get chain name from chain ID using chain provider."""
        if not self.chain_provider:
            return None
            
        for network, config in self.chain_provider.chain_configs.items():
            if str(config.chain_id) == chain_id:
                return network.value
                
        return None