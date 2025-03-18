"""Wallet Portfolio API implementation."""

import logging
from typing import Dict, List, Optional

import httpx
from app.config.config import config

logger = logging.getLogger(__name__)

# Chain ID to Moralis chain name mapping
CHAIN_MAPPING = {
    1: "eth",
    56: "bsc",
    137: "polygon",
    42161: "arbitrum",
    10: "optimism",
    43114: "avalanche",
    250: "fantom",
    8453: "base",
}

async def fetch_moralis_data(
    api_key: str,
    endpoint: str,
    address: str,
    chain_id: int = None,
    params: dict = None
) -> dict:
    """Base function for Moralis API calls."""
    
    api_key = config.moralis_api_key
    
    if not api_key:
        logger.error("Moralis API key not configured")
        return None
    
    base_url = "https://deep-index.moralis.io/api/v2.2"
    headers = {"X-API-Key": api_key}
    
    url = f"{base_url}/{endpoint.format(address=address)}"
    
    if chain_id:
        params = params or {}
        params["chain"] = CHAIN_MAPPING.get(chain_id, "eth")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Moralis API request error: {e}")
            return {"error": str(e)}
        except httpx.HTTPStatusError as e:
            logger.error(f"Moralis API error: {e.response.status_code} {e.response.text}")
            return {"error": f"HTTP error {e.response.status_code}"}

# Wallet Balances
async def fetch_wallet_balances(
    api_key: str, 
    address: str,
    chain_id: int = None
) -> dict:
    """Get token balances with prices (Method 8)"""
    endpoint = "wallets/{address}/tokens"
    return await fetch_moralis_data(api_key, endpoint, address, chain_id)

# NFT Balances
async def fetch_nft_data(
    api_key: str,
    address: str,
    chain_id: int = None
) -> dict:
    """Get NFT balances (Method 13)"""
    endpoint = "{address}/nft"
    params = {"normalizeMetadata": True}
    return await fetch_moralis_data(api_key, endpoint, address, chain_id, params)

# Transaction History
async def fetch_transaction_history(
    api_key: str,
    address: str,
    chain_id: int = None,
    cursor: str = None,
    limit: int = 100
) -> dict:
    """Get wallet history (Method 1)"""
    endpoint = "wallets/{address}/history"
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor
    return await fetch_moralis_data(api_key, endpoint, address, chain_id, params)

# Token Approvals
async def fetch_token_approvals(
    api_key: str,
    address: str,
    chain_id: int = None
) -> dict:
    """Get token approvals (Method 11)"""
    endpoint = "wallets/{address}/approvals"
    return await fetch_moralis_data(api_key, endpoint, address, chain_id)

# DeFi Positions
async def fetch_defi_positions(
    api_key: str,
    address: str
) -> dict:
    """Get DeFi positions summary (Method 16)"""
    endpoint = "wallets/{address}/defi/positions"
    return await fetch_moralis_data(api_key, endpoint, address)

# Net Worth
async def fetch_net_worth(
    api_key: str,
    address: str
) -> dict:
    """Get wallet net worth (Method 18)"""
    endpoint = "wallets/{address}/net-worth"
    return await fetch_moralis_data(api_key, endpoint, address)

# ENS Resolution
async def resolve_ens_address(
    api_key: str,
    address: str
) -> dict:
    """Resolve ENS domain (Method 23)"""
    endpoint = "resolve/{address}/reverse"
    return await fetch_moralis_data(api_key, endpoint, address)