"""CryptoCompare skills."""

from typing import TypedDict

from abstracts.skill import SkillStoreABC
from skills.base import SkillConfig, SkillState
from skills.cryptocompare.base import CryptoCompareBaseTool
from skills.cryptocompare.fetch_news import CryptoCompareFetchNews
from skills.cryptocompare.fetch_price import CryptoCompareFetchPrice
from skills.cryptocompare.fetch_top_exchanges import CryptoCompareFetchTopExchanges
from skills.cryptocompare.fetch_top_market_cap import CryptoCompareFetchTopMarketCap
from skills.cryptocompare.fetch_top_volume import CryptoCompareFetchTopVolume
from skills.cryptocompare.fetch_trading_signals import CryptoCompareFetchTradingSignals

# Cache skills at the system level, because they are stateless
_cache: dict[str, CryptoCompareBaseTool] = {}


class SkillStates(TypedDict):
    fetch_news: SkillState
    fetch_price: SkillState
    fetch_trading_signals: SkillState
    fetch_top_market_cap: SkillState
    fetch_top_exchanges: SkillState
    fetch_top_volume: SkillState


class CryptoCompareConfig(TypedDict):
    """Configuration for CryptoCompare API client."""

    api_key: str


class Config(SkillConfig, CryptoCompareConfig):
    """Configuration for CryptoCompare skills."""

    states: SkillStates


def get_skills(
    config: "Config",
    is_private: bool,
    store: SkillStoreABC,
    **_,
) -> list[CryptoCompareBaseTool]:
    """Get all CryptoCompare skills.

    Args:
        config: The configuration for CryptoCompare skills.
        is_private: Whether to include private skills.
        store: The skill store for persisting data.

    Returns:
        A list of CryptoCompare skills.
    """
    available_skills = []

    # Include skills based on their state
    for skill_name, state in config["states"].items():
        if state == "disabled":
            continue
        elif state == "public" or (state == "private" and is_private):
            available_skills.append(skill_name)

    # Get each skill using the cached getter
    return [get_cryptocompare_skill(name, store) for name in available_skills]


def get_cryptocompare_skill(
    name: str,
    store: SkillStoreABC,
) -> CryptoCompareBaseTool:
    """Get a CryptoCompare skill by name.

    Args:
        name: The name of the skill to get
        api_key: The CryptoCompare API key
        store: The skill store for persisting data

    Returns:
        The requested CryptoCompare skill

    Raises:
        ValueError: If the requested skill name is unknown
    """

    if name == "fetch_news":
        if name not in _cache:
            _cache[name] = CryptoCompareFetchNews(
                skill_store=store,
            )
        return _cache[name]
    elif name == "fetch_price":
        if name not in _cache:
            _cache[name] = CryptoCompareFetchPrice(
                skill_store=store,
            )
        return _cache[name]
    elif name == "fetch_trading_signals":
        if name not in _cache:
            _cache[name] = CryptoCompareFetchTradingSignals(
                skill_store=store,
            )
        return _cache[name]
    elif name == "fetch_top_market_cap":
        if name not in _cache:
            _cache[name] = CryptoCompareFetchTopMarketCap(
                skill_store=store,
            )
        return _cache[name]
    elif name == "fetch_top_exchanges":
        if name not in _cache:
            _cache[name] = CryptoCompareFetchTopExchanges(
                skill_store=store,
            )
        return _cache[name]
    elif name == "fetch_top_volume":
        if name not in _cache:
            _cache[name] = CryptoCompareFetchTopVolume(
                skill_store=store,
            )
        return _cache[name]
    else:
        raise ValueError(f"Unknown CryptoCompare skill: {name}")
