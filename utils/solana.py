from typing import Dict, Optional
import httpx
import json
import logging
from app.config.config import config

logger = logging.getLogger(__name__)

async def create_solana_wallet(api_key: str) -> Optional[Dict]:
    """Create a new Solana wallet using Moralis API.
    
    Args:
        api_key: Moralis API key
        
    Returns:
        Dict with wallet information or None if failed
    """
    api_key = config.moralis_api_key
    
    if not api_key:
        logger.error("Moralis API key not configured")
        return None
    
    url = "https://solana-gateway.moralis.io/account/mainnet/create"
    headers = {"X-API-Key": api_key}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers)
            response.raise_for_status()
            wallet_data = response.json()
            
            # Structure the response in a standard format
            return {
                "address": wallet_data.get("address"),
                "private_key": wallet_data.get("privateKey"),
                "network": "mainnet",
                "created_at": wallet_data.get("createdAt") 
            }
    except Exception as e:
        logger.error(f"Failed to create Solana wallet: {str(e)}")
        return None

async def initialize_agent_solana_wallet(agent_id: str, api_key: str) -> Optional[Dict]:
    """Initialize Solana wallet for an agent.
    
    Args:
        agent_id: Agent ID
        api_key: Moralis API key
        
    Returns:
        Dict with wallet information or None if failed
    """
    from models.agent import AgentData
    
    wallet_data = await create_solana_wallet(api_key)
    if wallet_data:
        # Get agent data
        agent_data = await AgentData.get(agent_id)
        if not agent_data:
            from models.agent import AgentData
            agent_data = AgentData(id=agent_id)
        
        # Update wallet data
        agent_data.solana_wallet_data = wallet_data
        agent_data.solana_wallet_address = wallet_data.get("address")
        await agent_data.save()
        
        return wallet_data
    return None