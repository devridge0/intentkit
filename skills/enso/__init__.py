"""Enso skills."""
from abstracts.skill import SkillStoreABC
from skills.enso.base import EnsoBaseTool
from skills.enso.tokens import EnsoGetTokens
from skills.enso.wallet import EnsoGetApprovals, EnsoGetApprove, EnsoGetBalances


def get_enso_skill(
        name: str, api_token: str, main_tokens: list[str], store: SkillStoreABC, agent_id: str
) -> EnsoBaseTool:
    if not api_token:
        raise ValueError("Enso API token is empty")

    if name == "get_tokens":
        return EnsoGetTokens(api_token=api_token, main_tokens=main_tokens, store=store, agent_id=agent_id)
    if name == "get_wallet_approve":
        return EnsoGetApprove(api_token=api_token, main_tokens=main_tokens, store=store, agent_id=agent_id)
    if name == "get_wallet_approvals":
        return EnsoGetApprovals(api_token=api_token, main_tokens=main_tokens, store=store, agent_id=agent_id)
    if name == "get_wallet_balances":
        return EnsoGetBalances(api_token=api_token, main_tokens=main_tokens, store=store, agent_id=agent_id)

    else:
        raise ValueError(f"Unknown Enso skill: {name}")
