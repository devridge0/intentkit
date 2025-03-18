"""Base class for Wallet Portfolio tools."""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
from pydantic import BaseModel

from abstracts.agent import AgentStoreABC
from abstracts.skill import SkillStoreABC
from skills.wallet_portfolio.api import CHAIN_MAPPING
from utils.chain import ChainProvider

class WalletPortfolioBaseTool(ABC):
    """Base class for all wallet portfolio tools."""
    
    def __init__(
        self,
        api_key: str,
        skill_store: SkillStoreABC,
        agent_id: str,
        agent_store: AgentStoreABC,
        chain_provider: ChainProvider = None
    ):
        self.api_key = api_key
        self.skill_store = skill_store
        self.agent_id = agent_id
        self.agent_store = agent_store
        self.chain_provider = chain_provider

    async def check_rate_limit(self) -> Tuple[bool, str]:
        """Check rate limiting status."""
        # Implementation remains similar
        return False, ""

    @abstractmethod
    async def _arun(self, *args, **kwargs) -> BaseModel:
        """Async execution method."""
        pass

    def _get_chain_name(self, chain_id: int) -> str:
        """Convert chain ID to Moralis chain name."""
        return CHAIN_MAPPING.get(chain_id, "eth")