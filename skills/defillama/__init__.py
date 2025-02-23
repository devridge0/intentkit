"""DeFi Llama skills."""

from abstracts.agent import AgentStoreABC
from abstracts.skill import SkillStoreABC
from skills.defillama.base import DefiLlamaBaseTool

# TVL Tools
from skills.defillama.tvl.fetch_protocols import DefiLlamaFetchProtocols
from skills.defillama.tvl.fetch_protocol import DefiLlamaFetchProtocol
from skills.defillama.tvl.fetch_historical_tvl import DefiLlamaFetchHistoricalTvl
from skills.defillama.tvl.fetch_chain_historical_tvl import DefiLlamaFetchChainHistoricalTvl
from skills.defillama.tvl.fetch_protocol_current_tvl import DefiLlamaFetchProtocolCurrentTvl
from skills.defillama.tvl.fetch_chains import DefiLlamaFetchChains

# Coins Tools
from skills.defillama.coins.fetch_current_prices import DefiLlamaFetchCurrentPrices
from skills.defillama.coins.fetch_historical_prices import DefiLlamaFetchHistoricalPrices
from skills.defillama.coins.fetch_batch_historical_prices import DefiLlamaFetchBatchHistoricalPrices
from skills.defillama.coins.fetch_price_chart import DefiLlamaFetchPriceChart
from skills.defillama.coins.fetch_price_percentage import DefiLlamaFetchPricePercentage
from skills.defillama.coins.fetch_first_price import DefiLlamaFetchFirstPrice
from skills.defillama.coins.fetch_block import DefiLlamaFetchBlock

# Stablecoins Tools
from skills.defillama.stablecoins.fetch_stablecoins import DefiLlamaFetchStablecoins
from skills.defillama.stablecoins.fetch_stablecoin_charts import DefiLlamaFetchStablecoinCharts
from skills.defillama.stablecoins.fetch_stablecoin_chains import DefiLlamaFetchStablecoinChains
from skills.defillama.stablecoins.fetch_stablecoin_prices import DefiLlamaFetchStablecoinPrices

# Yields Tools
from skills.defillama.yields.fetch_pools import DefiLlamaFetchPools
from skills.defillama.yields.fetch_pool_chart import DefiLlamaFetchPoolChart

# Volumes Tools
from skills.defillama.volumes.fetch_dex_overview import DefiLlamaFetchDexOverview
from skills.defillama.volumes.fetch_dex_summary import DefiLlamaFetchDexSummary
from skills.defillama.volumes.fetch_options_overview import DefiLlamaFetchOptionsOverview

# Fees Tools
from skills.defillama.fees.fetch_fees_overview import DefiLlamaFetchFeesOverview

def get_defillama_skill(
    name: str,
    store: SkillStoreABC,
    agent_id: str,
    agent_store: AgentStoreABC,
) -> DefiLlamaBaseTool:
    """Get a DeFi Llama skill by name.

    Args:
        name: The name of the skill to get
        store: The skill store for persisting data
        agent_id: The ID of the agent
        agent_store: The agent store for persisting data

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
        return DefiLlamaFetchProtocols(
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "fetch_protocol":
        return DefiLlamaFetchProtocol(
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "fetch_historical_tvl":  
        return DefiLlamaFetchHistoricalTvl(
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "fetch_chain_historical_tvl":  
        return DefiLlamaFetchChainHistoricalTvl(
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "fetch_protocol_current_tvl": 
        return DefiLlamaFetchProtocolCurrentTvl(
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "fetch_chains":
        return DefiLlamaFetchChains(
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    
    # Coins Skills
    elif name == "fetch_current_prices":
        return DefiLlamaFetchCurrentPrices(
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "fetch_historical_prices":
        return DefiLlamaFetchHistoricalPrices(
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "fetch_batch_historical_prices":
        return DefiLlamaFetchBatchHistoricalPrices(
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "fetch_price_chart":
        return DefiLlamaFetchPriceChart(
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "fetch_price_percentage":
        return DefiLlamaFetchPricePercentage(
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "fetch_first_price":
        return DefiLlamaFetchFirstPrice(
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "fetch_block":
        return DefiLlamaFetchBlock(
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    
    # Stablecoins Skills
    elif name == "fetch_stablecoins":
        return DefiLlamaFetchStablecoins(
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "fetch_stablecoin_charts":  # Handles both all and chain-specific charts
        return DefiLlamaFetchStablecoinCharts(
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "fetch_stablecoin_chains":
        return DefiLlamaFetchStablecoinChains(
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "fetch_stablecoin_prices":
        return DefiLlamaFetchStablecoinPrices(
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    
    # Yields Skills
    elif name == "fetch_pools":
        return DefiLlamaFetchPools(
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "fetch_pool_chart":
        return DefiLlamaFetchPoolChart(
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    
    # Volumes Skills
    elif name == "fetch_dex_overview":  # Handles both base and chain-specific overviews
        return DefiLlamaFetchDexOverview(
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "fetch_dex_summary":
        return DefiLlamaFetchDexSummary(
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    elif name == "fetch_options_overview":  # Handles both base and chain-specific overviews
        return DefiLlamaFetchOptionsOverview(
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    
    # Fees Skills
    elif name == "fetch_fees_overview":  # Handles both base and chain-specific overviews
        return DefiLlamaFetchFeesOverview(
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )

    else:
        raise ValueError(f"Unknown DeFi Llama skill: {name}")
