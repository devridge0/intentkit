"""CryptoCompare skills."""

from abstracts.agent import AgentStoreABC
from abstracts.skill import SkillStoreABC
from skills.cryptocompare.base import CryptoCompareBaseTool
from skills.cryptocompare.fetch_news import CryptoCompareFetchNews
from skills.cryptocompare.fetch_price import CryptoCompareFetchPrice
from skills.cryptocompare.fetch_top_exchanges import CryptoCompareFetchTopExchanges
from skills.cryptocompare.fetch_top_market_cap import CryptoCompareFetchTopMarketCap
from skills.cryptocompare.fetch_top_volume import CryptoCompareFetchTopVolume
from skills.cryptocompare.fetch_trading_signals import CryptoCompareFetchTradingSignals


def get_cryptocompare_skill(
    name: str,
    api_key: str,
    store: SkillStoreABC,
    agent_id: str,
    agent_store: AgentStoreABC,
) -> CryptoCompareBaseTool:
    """Get a CryptoCompare skill by name.

    Args:
        name: The name of the skill to get
        api_key: The CryptoCompare API key
        store: The skill store for persisting data
        agent_id: The ID of the agent
        agent_store: The agent store for persisting data

    Returns:
        The requested CryptoCompare skill

    Raises:
        ValueError: If the requested skill name is unknown
    """
    if name == "fetch_news":
        return CryptoCompareFetchNews(
            api_key=api_key,
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "fetch_price":
        return CryptoCompareFetchPrice(
            api_key=api_key,
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "fetch_trading_signals":
        return CryptoCompareFetchTradingSignals(
            api_key=api_key,
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "fetch_top_market_cap":
        return CryptoCompareFetchTopMarketCap(
            api_key=api_key,
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "fetch_top_exchanges":
        return CryptoCompareFetchTopExchanges(
            api_key=api_key,
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "fetch_top_volume":
        return CryptoCompareFetchTopVolume(
            api_key=api_key,
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    else:
        raise ValueError(f"Unknown CryptoCompare skill: {name}")
