"""Acolyt skills."""

from cdp import Wallet

from abstracts.skill import SkillStoreABC
from skills.acolyt.ask import AcolytAskGpt
from skills.acolyt.base import AcolytBaseTool


def get_Acolyt_skill(
    name: str,
    api_key: str,
    skill_store: SkillStoreABC,
    agent_store: SkillStoreABC,
    agent_id: str,
) -> AcolytBaseTool:
    if not api_key:
        raise ValueError("Acolyt API token is empty")

    if name == "ask_gpt":
        return AcolytAskGpt(
            api_key=api_key,
            agent_id=agent_id,
            skill_store=skill_store,
            agent_store=agent_store,
        )

    else:
        raise ValueError(f"Unknown Acolyt skill: {name}")
