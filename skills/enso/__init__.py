"""Enso skills."""
from abstracts.skill import SkillStoreABC
from skills.enso.actions import EnsoGetActions
from skills.enso.base import EnsoBaseTool
from skills.enso.bundle import EnsoShortcutBundle
from skills.enso.ipor import EnsoIporShortcut
from skills.enso.networks import EnsoGetNetworks
from skills.enso.prices import EnsoGetPrices
from skills.enso.quote import EnsoGetQuote, EnsoPostQuoteShortcut
from skills.enso.route import EnsoGetRouteShortcut, EnsoPostRouteShortcut
from skills.enso.standards import EnsoGetStandards
from skills.enso.tokens import EnsoGetTokens
from skills.enso.wallet import (
    EnsoApproveWallet,
    EnsoGetApprovals,
    EnsoGetBalances,
    EnsoGetWallet,
)


def get_enso_skill(
        name: str, api_token: str, main_tokens: list[str], store: SkillStoreABC, agent_id: str
) -> EnsoBaseTool:
    if not api_token:
        raise ValueError("Enso API token is empty")

    if name == "get_actions":
        return EnsoGetActions(api_token=api_token, store=store, agent_id=agent_id)
    if name == "get_networks":
        return EnsoGetNetworks(api_token=api_token, store=store, agent_id=agent_id)
    if name == "get_price":
        return EnsoGetPrices(api_token=api_token, store=store, agent_id=agent_id)
    if name == "get_quote":
        return EnsoGetQuote(api_token=api_token, store=store, agent_id=agent_id)
    if name == "get_route":
        return EnsoGetRouteShortcut(api_token=api_token, store=store, agent_id=agent_id)
    if name == "get_standards":
        return EnsoGetStandards(api_token=api_token, store=store, agent_id=agent_id)
    if name == "get_tokens":
        return EnsoGetTokens(api_token=api_token, main_tokens=main_tokens, store=store, agent_id=agent_id)
    if name == "get_wallet":
        return EnsoGetWallet(api_token=api_token, store=store, agent_id=agent_id)
    if name == "get_approve_wallet":
        return EnsoApproveWallet(api_token=api_token, store=store, agent_id=agent_id)
    if name == "get_wallet_approvals":
        return EnsoGetApprovals(api_token=api_token, store=store, agent_id=agent_id)
    if name == "get_wallet_balances":
        return EnsoGetBalances(api_token=api_token, store=store, agent_id=agent_id)

    if name == "post_bundle":
        return EnsoShortcutBundle(api_token=api_token, store=store, agent_id=agent_id)
    if name == "post_route":
        return EnsoPostRouteShortcut(api_token=api_token, store=store, agent_id=agent_id)
    if name == "post_quote":
        return EnsoPostQuoteShortcut(api_token=api_token, store=store, agent_id=agent_id)
    if name == "post_ipor":
        return EnsoIporShortcut(api_token=api_token, store=store, agent_id=agent_id)

    else:
        raise ValueError(f"Unknown Enso skill: {name}")
