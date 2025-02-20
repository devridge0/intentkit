"""Enso skills."""

from cdp import Wallet

from abstracts.skill import SkillStoreABC
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


def get_enso_skill(
    name: str,
    api_token: str,
    main_tokens: list[str],
    wallet: Wallet,
    chain_provider: ChainProvider,
    skill_store: SkillStoreABC,
    agent_store: SkillStoreABC,
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
