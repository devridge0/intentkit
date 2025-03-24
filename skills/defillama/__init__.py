"""DeFi Llama skills."""

from typing import TypedDict

from abstracts.skill import SkillStoreABC
from skills.base import SkillConfig, SkillState
from skills.defillama.base import DefiLlamaBaseTool
from skills.defillama.coins.fetch_batch_historical_prices import (
    DefiLlamaFetchBatchHistoricalPrices,
)
from skills.defillama.coins.fetch_block import DefiLlamaFetchBlock

# Coins Tools
from skills.defillama.coins.fetch_current_prices import DefiLlamaFetchCurrentPrices
from skills.defillama.coins.fetch_first_price import DefiLlamaFetchFirstPrice
from skills.defillama.coins.fetch_historical_prices import (
    DefiLlamaFetchHistoricalPrices,
)
from skills.defillama.coins.fetch_price_chart import DefiLlamaFetchPriceChart
from skills.defillama.coins.fetch_price_percentage import DefiLlamaFetchPricePercentage

# Fees Tools
from skills.defillama.fees.fetch_fees_overview import DefiLlamaFetchFeesOverview
from skills.defillama.stablecoins.fetch_stablecoin_chains import (
    DefiLlamaFetchStablecoinChains,
)
from skills.defillama.stablecoins.fetch_stablecoin_charts import (
    DefiLlamaFetchStablecoinCharts,
)
from skills.defillama.stablecoins.fetch_stablecoin_prices import (
    DefiLlamaFetchStablecoinPrices,
)

# Stablecoins Tools
from skills.defillama.stablecoins.fetch_stablecoins import DefiLlamaFetchStablecoins
from skills.defillama.tvl.fetch_chain_historical_tvl import (
    DefiLlamaFetchChainHistoricalTvl,
)
from skills.defillama.tvl.fetch_chains import DefiLlamaFetchChains
from skills.defillama.tvl.fetch_historical_tvl import DefiLlamaFetchHistoricalTvl
from skills.defillama.tvl.fetch_protocol import DefiLlamaFetchProtocol
from skills.defillama.tvl.fetch_protocol_current_tvl import (
    DefiLlamaFetchProtocolCurrentTvl,
)

# TVL Tools
from skills.defillama.tvl.fetch_protocols import DefiLlamaFetchProtocols

# Volumes Tools
from skills.defillama.volumes.fetch_dex_overview import DefiLlamaFetchDexOverview
from skills.defillama.volumes.fetch_dex_summary import DefiLlamaFetchDexSummary
from skills.defillama.volumes.fetch_options_overview import (
    DefiLlamaFetchOptionsOverview,
)
from skills.defillama.yields.fetch_pool_chart import DefiLlamaFetchPoolChart

# Yields Tools
from skills.defillama.yields.fetch_pools import DefiLlamaFetchPools

# we cache skills in system level, because they are stateless
_cache: dict[str, DefiLlamaBaseTool] = {}


class SkillStates(TypedDict):
    # TVL Skills
    fetch_protocols: SkillState
    fetch_protocol: SkillState
    fetch_historical_tvl: SkillState
    fetch_chain_historical_tvl: SkillState
    fetch_protocol_current_tvl: SkillState
    fetch_chains: SkillState

    # Coins Skills
    fetch_current_prices: SkillState
    fetch_historical_prices: SkillState
    fetch_batch_historical_prices: SkillState
    fetch_price_chart: SkillState
    fetch_price_percentage: SkillState
    fetch_first_price: SkillState
    fetch_block: SkillState

    # Stablecoins Skills
    fetch_stablecoins: SkillState
    fetch_stablecoin_charts: SkillState
    fetch_stablecoin_chains: SkillState
    fetch_stablecoin_prices: SkillState

    # Yields Skills
    fetch_pools: SkillState
    fetch_pool_chart: SkillState

    # Volumes Skills
    fetch_dex_overview: SkillState
    fetch_dex_summary: SkillState
    fetch_options_overview: SkillState

    # Fees Skills
    fetch_fees_overview: SkillState


class Config(SkillConfig):
    """Configuration for DeFi Llama skills."""

    states: SkillStates


async def get_skills(
    config: "Config",
    is_private: bool,
    store: SkillStoreABC,
    **_,
) -> list[DefiLlamaBaseTool]:
    """Get all DeFi Llama skills."""
    available_skills = []

    # Include skills based on their state
    for skill_name, state in config["states"].items():
        if state == "disabled":
            continue
        elif state == "public" or (state == "private" and is_private):
            available_skills.append(skill_name)

    # Get each skill using the cached getter
    return [get_defillama_skill(name, store) for name in available_skills]


def get_defillama_skill(
    name: str,
    store: SkillStoreABC,
) -> DefiLlamaBaseTool:
    """Get a DeFi Llama skill by name.

    Args:
        name: The name of the skill to get
        store: The skill store for persisting data

    Returns:
        The requested DeFi Llama skill

    Raises:
        ValueError: If the requested skill name is unknown

    Notes:
        Each skill maps to a specific DeFi Llama API endpoint. Some skills handle both
        base and chain-specific endpoints through optional parameters rather than
        separate implementations.
    """
    # TVL Skills
    if name == "fetch_protocols":
        if name not in _cache:
            _cache[name] = DefiLlamaFetchProtocols(
                skill_store=store,
            )
        return _cache[name]
    elif name == "fetch_protocol":
        if name not in _cache:
            _cache[name] = DefiLlamaFetchProtocol(
                skill_store=store,
            )
        return _cache[name]
    elif name == "fetch_historical_tvl":
        if name not in _cache:
            _cache[name] = DefiLlamaFetchHistoricalTvl(
                skill_store=store,
            )
        return _cache[name]
    elif name == "fetch_chain_historical_tvl":
        if name not in _cache:
            _cache[name] = DefiLlamaFetchChainHistoricalTvl(
                skill_store=store,
            )
        return _cache[name]
    elif name == "fetch_protocol_current_tvl":
        if name not in _cache:
            _cache[name] = DefiLlamaFetchProtocolCurrentTvl(
                skill_store=store,
            )
        return _cache[name]
    elif name == "fetch_chains":
        if name not in _cache:
            _cache[name] = DefiLlamaFetchChains(
                skill_store=store,
            )
        return _cache[name]

    # Coins Skills
    elif name == "fetch_current_prices":
        if name not in _cache:
            _cache[name] = DefiLlamaFetchCurrentPrices(
                skill_store=store,
            )
        return _cache[name]
    elif name == "fetch_historical_prices":
        if name not in _cache:
            _cache[name] = DefiLlamaFetchHistoricalPrices(
                skill_store=store,
            )
        return _cache[name]
    elif name == "fetch_batch_historical_prices":
        if name not in _cache:
            _cache[name] = DefiLlamaFetchBatchHistoricalPrices(
                skill_store=store,
            )
        return _cache[name]
    elif name == "fetch_price_chart":
        if name not in _cache:
            _cache[name] = DefiLlamaFetchPriceChart(
                skill_store=store,
            )
        return _cache[name]
    elif name == "fetch_price_percentage":
        if name not in _cache:
            _cache[name] = DefiLlamaFetchPricePercentage(
                skill_store=store,
            )
        return _cache[name]
    elif name == "fetch_first_price":
        if name not in _cache:
            _cache[name] = DefiLlamaFetchFirstPrice(
                skill_store=store,
            )
        return _cache[name]
    elif name == "fetch_block":
        if name not in _cache:
            _cache[name] = DefiLlamaFetchBlock(
                skill_store=store,
            )
        return _cache[name]

    # Stablecoins Skills
    elif name == "fetch_stablecoins":
        if name not in _cache:
            _cache[name] = DefiLlamaFetchStablecoins(
                skill_store=store,
            )
        return _cache[name]
    elif name == "fetch_stablecoin_charts":
        if name not in _cache:
            _cache[name] = DefiLlamaFetchStablecoinCharts(
                skill_store=store,
            )
        return _cache[name]
    elif name == "fetch_stablecoin_chains":
        if name not in _cache:
            _cache[name] = DefiLlamaFetchStablecoinChains(
                skill_store=store,
            )
        return _cache[name]
    elif name == "fetch_stablecoin_prices":
        if name not in _cache:
            _cache[name] = DefiLlamaFetchStablecoinPrices(
                skill_store=store,
            )
        return _cache[name]

    # Yields Skills
    elif name == "fetch_pools":
        if name not in _cache:
            _cache[name] = DefiLlamaFetchPools(
                skill_store=store,
            )
        return _cache[name]
    elif name == "fetch_pool_chart":
        if name not in _cache:
            _cache[name] = DefiLlamaFetchPoolChart(
                skill_store=store,
            )
        return _cache[name]

    # Volumes Skills
    elif name == "fetch_dex_overview":  # Handles both base and chain-specific overviews
        if name not in _cache:
            _cache[name] = DefiLlamaFetchDexOverview(
                skill_store=store,
            )
        return _cache[name]
    elif name == "fetch_dex_summary":
        if name not in _cache:
            _cache[name] = DefiLlamaFetchDexSummary(
                skill_store=store,
            )
        return _cache[name]
    elif (
        name == "fetch_options_overview"
    ):  # Handles both base and chain-specific overviews
        if name not in _cache:
            _cache[name] = DefiLlamaFetchOptionsOverview(
                skill_store=store,
            )
        return _cache[name]

    # Fees Skills
    elif (
        name == "fetch_fees_overview"
    ):  # Handles both base and chain-specific overviews
        if name not in _cache:
            _cache[name] = DefiLlamaFetchFeesOverview(
                skill_store=store,
            )
        return _cache[name]

    else:
        raise ValueError(f"Unknown DeFi Llama skill: {name}")
