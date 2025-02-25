"""Enso skills."""

from typing import List, NotRequired

from cdp import Wallet

from abstracts.agent import AgentStoreABC
from abstracts.skill import SkillStoreABC
from models.skill import SkillConfig
from skills.enso.base import EnsoBaseTool
from skills.enso.networks import EnsoGetNetworks
from skills.enso.prices import EnsoGetPrices
from skills.enso.route import EnsoRouteShortcut
from skills.enso.tokens import EnsoGetTokens
from skills.enso.wallet import (
    EnsoGetWalletApprovals,
    EnsoGetWalletBalances,
    EnsoWalletApprove,
)
from utils.chain import ChainProvider


class Config(SkillConfig):
    """Configuration for Enso skills."""

    api_token: str
    main_tokens: List[str]
    public_skills: List[str]
    private_skills: NotRequired[List[str]]


def get_skills(
    config: Config,
    agent_id: str,
    is_private: bool,
    store: SkillStoreABC,
    agent_store: AgentStoreABC,
    wallet: Wallet = None,
    chain_provider: ChainProvider = None,
    **_,
) -> list[EnsoBaseTool]:
    """Get all Enso skills."""
    # always return public skills
    resp = [
        get_enso_skill(
            name,
            config["api_token"],
            config["main_tokens"],
            wallet,
            chain_provider,
            store,
            agent_store,
            agent_id,
        )
        for name in config["public_skills"]
    ]
    # return private skills only if is_private
    if is_private and "private_skills" in config:
        resp.extend(
            get_enso_skill(
                name,
                config["api_token"],
                config["main_tokens"],
                wallet,
                chain_provider,
                store,
                agent_store,
                agent_id,
            )
            for name in config["private_skills"]
            # remove duplicates
            if name not in config["public_skills"]
        )
    return resp


def get_enso_skill(
    name: str,
    api_token: str,
    main_tokens: list[str],
    wallet: Wallet,
    chain_provider: ChainProvider,
    skill_store: SkillStoreABC,
    agent_store: AgentStoreABC,
    agent_id: str,
) -> EnsoBaseTool:
    if not api_token:
        raise ValueError("Enso API token is empty")

    if name == "get_networks":
        return EnsoGetNetworks(
            api_token=api_token,
            main_tokens=main_tokens,
            skill_store=skill_store,
            agent_store=agent_store,
            agent_id=agent_id,
        )

    if name == "get_tokens":
        return EnsoGetTokens(
            api_token=api_token,
            main_tokens=main_tokens,
            skill_store=skill_store,
            agent_store=agent_store,
            agent_id=agent_id,
        )

    if name == "get_prices":
        return EnsoGetPrices(
            api_token=api_token,
            main_tokens=main_tokens,
            skill_store=skill_store,
            agent_store=agent_store,
            agent_id=agent_id,
        )

    if name == "get_wallet_approvals":
        if not wallet:
            raise ValueError("Wallet is empty")
        return EnsoGetWalletApprovals(
            api_token=api_token,
            main_tokens=main_tokens,
            wallet=wallet,
            skill_store=skill_store,
            agent_store=agent_store,
            agent_id=agent_id,
        )

    if name == "get_wallet_balances":
        if not wallet:
            raise ValueError("Wallet is empty")
        return EnsoGetWalletBalances(
            api_token=api_token,
            main_tokens=main_tokens,
            wallet=wallet,
            skill_store=skill_store,
            agent_store=agent_store,
            agent_id=agent_id,
        )

    if name == "wallet_approve":
        if not chain_provider:
            raise ValueError("chain provider is empty")
        if not wallet:
            raise ValueError("Wallet is empty")
        return EnsoWalletApprove(
            api_token=api_token,
            main_tokens=main_tokens,
            wallet=wallet,
            chain_provider=chain_provider,
            skill_store=skill_store,
            agent_store=agent_store,
            agent_id=agent_id,
        )

    if name == "route_shortcut":
        if not chain_provider:
            raise ValueError("chain provider is empty")
        if not wallet:
            raise ValueError("Wallet is empty")
        return EnsoRouteShortcut(
            api_token=api_token,
            main_tokens=main_tokens,
            wallet=wallet,
            chain_provider=chain_provider,
            skill_store=skill_store,
            agent_store=agent_store,
            agent_id=agent_id,
        )

    else:
        raise ValueError(f"Unknown Enso skill: {name}")
