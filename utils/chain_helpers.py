"""Utilities for blockchain chain providers and configuration."""

import logging
from typing import Optional

from models.agent import Agent
from app.config.config import config
from utils.chain import ChainProvider, Network

logger = logging.getLogger(__name__)

def setup_chain_provider(agent: Agent) -> Optional[ChainProvider]:
    """
    Set up and configure the chain provider for an agent.
    
    This function:
    1. Checks if a chain provider is available in the global config
    2. Configures Solana support when needed
    3. Returns an appropriately configured ChainProvider
    
    Args:
        agent: The Agent object containing configuration
        
    Returns:
        ChainProvider or None if not available or needed
    """
    # Start with the global chain provider if available
    chain_provider = None
    if hasattr(config, "chain_provider") and config.chain_provider:
        chain_provider = config.chain_provider
        logger.debug(f"Using existing chain provider: {type(chain_provider).__name__}")
    
    # Check if Solana support is required
    solana_enabled = False
    if (agent.wallet_portfolio_config and 
        agent.wallet_portfolio_config.get("supported_chains", {}).get("solana", False)):
        solana_enabled = True
        logger.info(f"Solana support enabled for agent {agent.id}")
        
        # Create chain provider if not available
        if not chain_provider:
            from utils.chain import ChainProvider
            chain_provider = ChainProvider()
            logger.debug("Created new chain provider for Solana support")
            
        # Configure Solana networks if not already present
        if not hasattr(chain_provider, "solana_networks"):
            chain_provider.solana_networks = ["mainnet", "devnet"]
            logger.debug("Added Solana networks to chain provider")
    
    # For debugging purposes, log the configured chains
    if chain_provider and logger.isEnabledFor(logging.DEBUG):
        supported_chains = []
        for network in chain_provider.chain_configs:
            supported_chains.append(str(network))
        if hasattr(chain_provider, "solana_networks"):
            for network in chain_provider.solana_networks:
                supported_chains.append(f"solana-{network}")
        logger.debug(f"Chain provider supporting: {', '.join(supported_chains)}")
    
    return chain_provider