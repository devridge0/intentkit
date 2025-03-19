"""Enso skills."""

from typing import List, TypedDict

from abstracts.skill import SkillStoreABC
from skills.base import SkillConfig, SkillState
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


class SkillStates(TypedDict):
    get_networks: SkillState
    get_tokens: SkillState
    get_prices: SkillState
    get_wallet_approvals: SkillState
    get_wallet_balances: SkillState
    wallet_approve: SkillState
    route_shortcut: SkillState


class Config(SkillConfig):
    """Configuration for Enso skills."""

    states: SkillStates
    api_token: str
    main_tokens: List[str]


def get_skills(
    config: Config,
    is_private: bool,
    store: SkillStoreABC,
    **_,
) -> list[EnsoBaseTool]:
    """Get all Enso skills."""
    available_skills = []

    # Include skills based on their state
    for skill_name, state in config["states"].items():
        if state == "disabled":
            continue
        elif state == "public" or (state == "private" and is_private):
            available_skills.append(skill_name)

    # Get each skill using the cached getter
    return [get_enso_skill(name, store) for name in available_skills]


def get_enso_skill(
    name: str,
    skill_store: SkillStoreABC,
) -> EnsoBaseTool:
    if name == "get_networks":
        return EnsoGetNetworks(
            skill_store=skill_store,
        )
    if name == "get_tokens":
        return EnsoGetTokens(
            skill_store=skill_store,
        )
    if name == "get_prices":
        return EnsoGetPrices(
            skill_store=skill_store,
        )
    if name == "get_wallet_approvals":
        return EnsoGetWalletApprovals(
            skill_store=skill_store,
        )
    if name == "get_wallet_balances":
        return EnsoGetWalletBalances(
            skill_store=skill_store,
        )
    if name == "wallet_approve":
        return EnsoWalletApprove(
            skill_store=skill_store,
        )
    if name == "route_shortcut":
        return EnsoRouteShortcut(
            skill_store=skill_store,
        )
    else:
        raise ValueError(f"Unknown Enso skill: {name}")
