"""Portfolio skills for blockchain wallet analysis."""

import logging
from typing import TypedDict

from abstracts.skill import SkillStoreABC
from skills.base import SkillConfig, SkillState
from skills.portfolio.base import PortfolioBaseTool
from skills.portfolio.token_balances import TokenBalances
from skills.portfolio.wallet_approvals import WalletApprovals
from skills.portfolio.wallet_history import WalletHistory
from skills.portfolio.wallet_net_worth import WalletNetWorth
from skills.portfolio.wallet_profitability import WalletProfitability
from skills.portfolio.wallet_profitability_summary import WalletProfitabilitySummary
from skills.portfolio.wallet_stats import WalletStats
from skills.portfolio.wallet_swaps import WalletSwaps

# Cache skills at the system level, because they are stateless
_cache: dict[str, PortfolioBaseTool] = {}

logger = logging.getLogger(__name__)


class SkillStates(TypedDict):
    """State configurations for Portfolio skills."""

    wallet_history: SkillState
    token_balances: SkillState
    wallet_approvals: SkillState
    wallet_swaps: SkillState
    wallet_net_worth: SkillState
    wallet_profitability_summary: SkillState
    wallet_profitability: SkillState
    wallet_stats: SkillState


class Config(SkillConfig):
    """Configuration for Portfolio blockchain analysis skills."""

    states: SkillStates
    api_key: str


async def get_skills(
    config: "Config",
    is_private: bool,
    store: SkillStoreABC,
    **_,
) -> list[PortfolioBaseTool]:
    """Get all Portfolio blockchain analysis skills.

    Args:
        config: The configuration for Portfolio skills.
        is_private: Whether to include private skills.
        store: The skill store for persisting data.

    Returns:
        A list of Portfolio blockchain analysis skills.
    """
    available_skills = []

    # Include skills based on their state
    for skill_name, state in config["states"].items():
        if state == "disabled":
            continue
        elif state == "public" or (state == "private" and is_private):
            available_skills.append(skill_name)

    # Get each skill using the cached getter
    result = []
    for name in available_skills:
        skill = get_portfolio_skill(name, store)
        if skill:
            result.append(skill)
    return result


def get_portfolio_skill(
    name: str,
    store: SkillStoreABC,
) -> PortfolioBaseTool:
    """Get a Portfolio blockchain analysis skill by name.

    Args:
        name: The name of the skill to get
        store: The skill store for persisting data

    Returns:
        The requested Portfolio blockchain analysis skill
    """
    if name in _cache:
        return _cache[name]

    skill = None
    if name == "wallet_history":
        skill = WalletHistory(skill_store=store)
    elif name == "token_balances":
        skill = TokenBalances(skill_store=store)
    elif name == "wallet_approvals":
        skill = WalletApprovals(skill_store=store)
    elif name == "wallet_swaps":
        skill = WalletSwaps(skill_store=store)
    elif name == "wallet_net_worth":
        skill = WalletNetWorth(skill_store=store)
    elif name == "wallet_profitability_summary":
        skill = WalletProfitabilitySummary(skill_store=store)
    elif name == "wallet_profitability":
        skill = WalletProfitability(skill_store=store)
    elif name == "wallet_stats":
        skill = WalletStats(skill_store=store)
    else:
        logger.warning(f"Unknown Portfolio skill: {name}")
        return None

    if skill:
        _cache[name] = skill
    return skill
