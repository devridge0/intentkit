async def get_skills(
    config: "Config",
    is_private: bool,
    store: SkillStoreABC,
    chain_provider: Any = None,
    **_,
) -> List[WalletBaseTool]:
    """Get all Wallet Portfolio skills.
    
    Args:
        config: Skill configuration
        is_private: Whether the request is from an authenticated user
        store: Skill store for persistence
        chain_provider: Optional chain provider for blockchain interactions
        **_: Additional arguments
        
    Returns:
        List of enabled wallet skills
    """
    available_skills = []

    # Include skills based on their state
    for skill_name, state in config["states"].items():
        if state == "disabled":
            continue
        elif state == "public" or (state == "private" and is_private):
            # Check chain support for Solana-specific skills
            if skill_name == "fetch_solana_portfolio" and not config.get("supported_chains", {}).get("solana", True):
                continue
                
            available_skills.append(skill_name)

    # Get each skill using the getter
    result = []
    for name in available_skills:
        skill = await get_wallet_skill(
            name, 
            config["api_key"], 
            store,                         
            chain_provider
        )
        result.append(skill)
    
    return result


async def get_wallet_skill(
    name: str,
    api_key: str,    
    store: SkillStoreABC,
    chain_provider: Any = None,            
) -> WalletBaseTool:
    """Get a specific Wallet Portfolio skill by name.
    
    Args:
        name: Name of the skill to get
        api_key: API key for service authentication
        store: Skill store for persistence
        chain_provider: Optional chain provider for blockchain interactions
        
    Returns:
        The requested skill
        
    Raises:
        ValueError: If the skill name is unknown
    """
    skill_classes = {
        "fetch_wallet_portfolio": FetchWalletPortfolio,
        "fetch_chain_portfolio": FetchChainPortfolio,
        "fetch_nft_portfolio": FetchNftPortfolio,
        "fetch_transaction_history": FetchTransactionHistory,
        "fetch_solana_portfolio": FetchSolanaPortfolio,
    }
    
    if name not in skill_classes:
        raise ValueError(f"Unknown Wallet Portfolio skill: {name}")
    
    skill = skill_classes[name](
        api_key=api_key,
        skill_store=store,
        chain_provider=chain_provider,
    )
    
    # If the skill has an async initialization method, call it
    if hasattr(skill, "async_init") and callable(skill.async_init):
        await skill.async_init()
    
    return skill