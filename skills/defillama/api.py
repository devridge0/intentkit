"""DeFi Llama API implementation and shared schemas."""

from typing import List, Optional, Union
from datetime import datetime

import httpx
from pydantic import BaseModel, Field

DEFILLAMA_BASE_URL = "https://api.llama.fi"

# TVL API Functions
async def fetch_protocols() -> dict:
    """List all protocols on defillama along with their TVL."""
    url = f"{DEFILLAMA_BASE_URL}/protocols"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    if response.status_code != 200:
        return {"error": f"API returned status code {response.status_code}"}
    return response.json()

async def fetch_protocol(protocol: str) -> dict:
    """Get historical TVL of a protocol and breakdowns by token and chain."""
    url = f"{DEFILLAMA_BASE_URL}/protocol/{protocol}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    if response.status_code != 200:
        return {"error": f"API returned status code {response.status_code}"}
    return response.json()

async def fetch_historical_tvl() -> dict:
    """Get historical TVL of DeFi on all chains."""
    url = f"{DEFILLAMA_BASE_URL}/v2/historicalChainTvl"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    if response.status_code != 200:
        return {"error": f"API returned status code {response.status_code}"}
    return response.json()

async def fetch_chain_historical_tvl(chain: str) -> dict:
    """Get historical TVL of a specific chain."""
    url = f"{DEFILLAMA_BASE_URL}/v2/historicalChainTvl/{chain}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    if response.status_code != 200:
        return {"error": f"API returned status code {response.status_code}"}
    return response.json()

async def fetch_protocol_current_tvl(protocol: str) -> dict:
    """Get current TVL of a protocol."""
    url = f"{DEFILLAMA_BASE_URL}/tvl/{protocol}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    if response.status_code != 200:
        return {"error": f"API returned status code {response.status_code}"}
    return response.json()

async def fetch_chains() -> dict:
    """Get current TVL of all chains."""
    url = f"{DEFILLAMA_BASE_URL}/v2/chains"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    if response.status_code != 200:
        return {"error": f"API returned status code {response.status_code}"}
    return response.json()

# Coins API Functions ----- check if they need additional query params bellow
# async def fetch_current_prices(coins: List[str]) -> dict:
#     """Get current prices of tokens by contract address."""
#     coins_str = ','.join(coins)
#     url = f"{DEFILLAMA_BASE_URL}/prices/current/{coins_str}"
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#     if response.status_code != 200:
#         return {"error": f"API returned status code {response.status_code}"}
#     return response.json()
#
# async def fetch_historical_prices(timestamp: int, coins: List[str]) -> dict:
#     """Get historical prices of tokens by contract address."""
#     coins_str = ','.join(coins)
#     url = f"{DEFILLAMA_BASE_URL}/prices/historical/{timestamp}/{coins_str}"
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#     if response.status_code != 200:
#         return {"error": f"API returned status code {response.status_code}"}
#     return response.json()
#
# async def fetch_batch_historical_prices(coins: List[str], timestamps: List[int]) -> dict:
#     """Get historical prices for multiple tokens at multiple timestamps."""
#     url = f"{DEFILLAMA_BASE_URL}/batchHistorical"
#     data = {"coins": coins, "timestamps": timestamps}
#     async with httpx.AsyncClient() as client:
#         response = await client.post(url, json=data)
#     if response.status_code != 200:
#         return {"error": f"API returned status code {response.status_code}"}
#     return response.json()
#
# async def fetch_price_chart(coins: List[str]) -> dict:
#     """Get token prices at regular time intervals."""
#     coins_str = ','.join(coins)
#     url = f"{DEFILLAMA_BASE_URL}/chart/{coins_str}"
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#     if response.status_code != 200:
#         return {"error": f"API returned status code {response.status_code}"}
#     return response.json()
#
# async def fetch_price_percentage(coins: List[str]) -> dict:
#     """Get percentage change in price over time."""
#     coins_str = ','.join(coins)
#     url = f"{DEFILLAMA_BASE_URL}/percentage/{coins_str}"
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#     if response.status_code != 200:
#         return {"error": f"API returned status code {response.status_code}"}
#     return response.json()
#
# async def fetch_first_price(coins: List[str]) -> dict:
#     """Get earliest timestamp price record for coins."""
#     coins_str = ','.join(coins)
#     url = f"{DEFILLAMA_BASE_URL}/prices/first/{coins_str}"
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#     if response.status_code != 200:
#         return {"error": f"API returned status code {response.status_code}"}
#     return response.json()
#
# async def fetch_block(chain: str, timestamp: int) -> dict:
#     """Get the closest block to a timestamp."""
#     url = f"{DEFILLAMA_BASE_URL}/block/{chain}/{timestamp}"
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#     if response.status_code != 200:
#         return {"error": f"API returned status code {response.status_code}"}
#     return response.json()
#
# # Stablecoins API Functions
# async def fetch_stablecoins() -> dict:
#     """List all stablecoins along with their circulating amounts."""
#     url = f"{DEFILLAMA_BASE_URL}/stablecoins"
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#     if response.status_code != 200:
#         return {"error": f"API returned status code {response.status_code}"}
#     return response.json()
#
# async def fetch_stablecoin_charts(chain: Optional[str] = None) -> dict:
#     """Get historical mcap sum of all stablecoins (optionally by chain)."""
#     base_url = f"{DEFILLAMA_BASE_URL}/stablecoincharts"
#     url = f"{base_url}/all" if chain is None else f"{base_url}/{chain}"
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#     if response.status_code != 200:
#         return {"error": f"API returned status code {response.status_code}"}
#     return response.json()
#
# async def fetch_stablecoin_asset(asset: str) -> dict:
#     """Get historical mcap and chain distribution of a stablecoin."""
#     url = f"{DEFILLAMA_BASE_URL}/stablecoin/{asset}"
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#     if response.status_code != 200:
#         return {"error": f"API returned status code {response.status_code}"}
#     return response.json()
#
# async def fetch_stablecoin_chains() -> dict:
#     """Get current mcap sum of all stablecoins on each chain."""
#     url = f"{DEFILLAMA_BASE_URL}/stablecoinchains"
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#     if response.status_code != 200:
#         return {"error": f"API returned status code {response.status_code}"}
#     return response.json()
#
# async def fetch_stablecoin_prices() -> dict:
#     """Get historical prices of all stablecoins."""
#     url = f"{DEFILLAMA_BASE_URL}/stablecoinprices"
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#     if response.status_code != 200:
#         return {"error": f"API returned status code {response.status_code}"}
#     return response.json()
#
# # Yields API Functions
# async def fetch_pools() -> dict:
#     """Retrieve the latest data for all pools."""
#     url = f"{DEFILLAMA_BASE_URL}/pools"
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#     if response.status_code != 200:
#         return {"error": f"API returned status code {response.status_code}"}
#     return response.json()
#
# async def fetch_pool_chart(pool: str) -> dict:
#     """Get historical APY and TVL of a pool."""
#     url = f"{DEFILLAMA_BASE_URL}/chart/{pool}"
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#     if response.status_code != 200:
#         return {"error": f"API returned status code {response.status_code}"}
#     return response.json()
#
# # Volumes API Functions
# async def fetch_dex_overview(chain: Optional[str] = None) -> dict:
#     """List all dexs with volume summaries, optionally filtered by chain."""
#     base_url = f"{DEFILLAMA_BASE_URL}/overview/dexs"
#     url = base_url if chain is None else f"{base_url}/{chain}"
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#     if response.status_code != 200:
#         return {"error": f"API returned status code {response.status_code}"}
#     return response.json()
#
# async def fetch_dex_summary(protocol: str) -> dict:
#     """Get summary of dex volume with historical data."""
#     url = f"{DEFILLAMA_BASE_URL}/summary/dexs/{protocol}"
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#     if response.status_code != 200:
#         return {"error": f"API returned status code {response.status_code}"}
#     return response.json()
#
# async def fetch_options_overview(chain: Optional[str] = None) -> dict:
#     """List all options dexs with volume summaries, optionally filtered by chain."""
#     base_url = f"{DEFILLAMA_BASE_URL}/overview/options"
#     url = base_url if chain is None else f"{base_url}/{chain}"
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#     if response.status_code != 200:
#         return {"error": f"API returned status code {response.status_code}"}
#     return response.json()
#
# async def fetch_options_summary(protocol: str) -> dict:
#     """Get summary of options protocol volume with historical data."""
#     url = f"{DEFILLAMA_BASE_URL}/summary/options/{protocol}"
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#     if response.status_code != 200:
#         return {"error": f"API returned status code {response.status_code}"}
#     return response.json()
#
# # Fees and Revenue API Functions
# async def fetch_fees_overview(chain: Optional[str] = None) -> dict:
#     """List all protocols with fees and revenue summaries, optionally filtered by chain."""
#     base_url = f"{DEFILLAMA_BASE_URL}/overview/fees"
#     url = base_url if chain is None else f"{base_url}/{chain}"
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#     if response.status_code != 200:
#         return {"error": f"API returned status code {response.status_code}"}
#     return response.json()
#
# async def fetch_fees_summary(protocol: str) -> dict:
#     """Get summary of protocol fees and revenue with historical data."""
#     url = f"{DEFILLAMA_BASE_URL}/summary/fees/{protocol}"
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#     if response.status_code != 200:
#         return {"error": f"API returned status code {response.status_code}"}
#     return response.json()
