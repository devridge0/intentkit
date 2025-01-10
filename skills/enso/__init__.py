"""Enso skills."""

from abstracts.skill import SkillStoreABC
from skills.enso.base import EnsoBaseTool
from skills.enso.tokens import EnsoGetTokens


def get_enso_skill(
        name: str, api_token: str, store: SkillStoreABC, agent_id: str
) -> EnsoBaseTool:
    if name == "get_tokens":
        return EnsoGetTokens(api_token=api_token, store=store, agent_id=agent_id)
    else:
        raise ValueError(f"Unknown Enso skill: {name}")
