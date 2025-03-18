"""Multi-Chain Wallet Portfolio skills."""

from typing import NotRequired, List, Dict, Optional, Union

from abstracts.agent import AgentStoreABC
from abstracts.skill import SkillStoreABC
from models.skill import SkillConfig
from skills.wallet_portfolio.base import WalletPortfolioBaseTool
from skills.wallet_portfolio.fetch_asset_portfolio import FetchAssetPortfolio
from skills.wallet_portfolio.fetch_chain_portfolio import FetchChainPortfolio
from skills.wallet_portfolio.fetch_nft_portfolio import FetchNftPortfolio
from skills.wallet_portfolio.fetch_transaction_history import FetchTransactionHistory
from skills.wallet_portfolio.fetch_wallet_portfolio import FetchWalletPortfolio
from skills.wallet_portfolio.solana import FetchSolanaPortfolio
from utils.chain import ChainProvider


class Config(SkillConfig):
    """Configuration for Wallet Portfolio skills."""

    api_key: str
    public_skills: NotRequired[list[str]] = []
    private_skills: NotRequired[list[str]] = []
    supported_chains: NotRequired[Dict[str, bool]] = {"evm": True, "solana": True}


def get_skills(
    config: Config,
    agent_id: str,
    is_private: bool,
    store: SkillStoreABC,
    agent_store: AgentStoreABC,
    chain_provider: ChainProvider = None,
    **_,
) -> List[WalletPortfolioBaseTool]:
    """Get all Wallet Portfolio skills."""
    skills = [
        get_wallet_portfolio_skill(
            name,
            config["api_key"],
            store,
            agent_id,
            agent_store,
            chain_provider,
            config.get("supported_chains", {"evm": True, "solana": True})
        )
        for name in config.get("public_skills", [])
    ]
    
    if is_private and "private_skills" in config:
        skills.extend(
            get_wallet_portfolio_skill(
                name,
                config["api_key"],
                store,
                agent_id,
                agent_store,
                chain_provider,
                config.get("supported_chains", {"evm": True, "solana": True})
            )
            for name in config["private_skills"]
            if name not in config.get("public_skills", [])
        )
    return skills


def get_wallet_portfolio_skill(
    name: str,
    api_key: str,
    skill_store: SkillStoreABC,
    agent_id: str,
    agent_store: AgentStoreABC,
    chain_provider: ChainProvider = None,
    supported_chains: Dict[str, bool] = {"evm": True, "solana": True}
) -> WalletPortfolioBaseTool:
    """Get a Wallet Portfolio skill by name."""
    skill_classes = {
        "fetch_wallet_portfolio": FetchWalletPortfolio,
        "fetch_chain_portfolio": FetchChainPortfolio,
        "fetch_asset_portfolio": FetchAssetPortfolio,
        "fetch_nft_portfolio": FetchNftPortfolio,
        "fetch_transaction_history": FetchTransactionHistory,
        "fetch_solana_portfolio": FetchSolanaPortfolio
    }
    
    if name not in skill_classes:
        raise ValueError(f"Unknown Wallet Portfolio skill: {name}")
    
    return skill_classes[name](
        api_key=api_key,
        skill_store=skill_store,
        agent_id=agent_id,
        agent_store=agent_store,
        chain_provider=chain_provider
    )