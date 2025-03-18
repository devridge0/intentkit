"""Tool for fetching complete wallet portfolio."""

from pydantic import BaseModel, Field
from .base import WalletPortfolioBaseTool
from .api import fetch_wallet_balances, fetch_net_worth

FETCH_WALLET_PORTFOLIO_PROMPT = """
Get comprehensive portfolio data for a wallet including:
- Token balances and prices
- NFT holdings
- Net worth
- Chain distribution
"""

class FetchWalletPortfolioInput(BaseModel):
    address: str = Field(..., description="Ethereum wallet address")
    chains: Optional[List[int]] = Field(
        default=None,
        description="List of chain IDs to check (default: all supported)"
    )

class TokenBalance(BaseModel):
    symbol: str
    name: str
    balance: float
    usd_value: float
    chain: str

class PortfolioOutput(BaseModel):
    address: str
    total_net_worth: float
    chains: Dict[str, float]
    tokens: List[TokenBalance]
    error: Optional[str]

class FetchWalletPortfolio(WalletPortfolioBaseTool):
    
    async def _arun(self, address: str, chains: List[int] = None) -> PortfolioOutput:
        try:
            # Get chain IDs to query
            chain_ids = chains or list(CHAIN_MAPPING.keys())
            
            # Fetch data from Moralis
            portfolio = {"tokens": [], "chains": {}, "total_net_worth": 0}
            
            # Get balances for each chain
            for chain_id in chain_ids:
                balance_data = await fetch_wallet_balances(
                    self.api_key, address, chain_id
                )
                
                if "error" in balance_data:
                    continue
                
                chain_name = self._get_chain_name(chain_id)
                chain_total = 0
                
                for token in balance_data.get("result", []):
                    if token["usd_value"]:
                        portfolio["tokens"].append(TokenBalance(
                            symbol=token.get("symbol", "UNKNOWN"),
                            name=token.get("name", "Unknown Token"),
                            balance=float(token.get("balance_formatted", 0)),
                            usd_value=token["usd_value"],
                            chain=chain_name
                        ))
                        chain_total += token["usd_value"]
                
                portfolio["chains"][chain_name] = chain_total
                portfolio["total_net_worth"] += chain_total
            
            # Add net worth data
            net_worth = await fetch_net_worth(self.api_key, address)
            if "result" in net_worth:
                portfolio["total_net_worth"] = net_worth["result"].get("total_networth_usd", 0)
            
            return PortfolioOutput(**portfolio)
        
        except Exception as e:
            return PortfolioOutput(
                address=address,
                total_net_worth=0,
                chains={},
                tokens=[],
                error=str(e)
            )