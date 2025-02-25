"""Acolyt skill module."""

from abstracts.agent import AgentStoreABC
from abstracts.skill import SkillStoreABC
from models.skill import SkillConfig
from skills.acolyt.ask import AcolytAskGpt
from skills.acolyt.base import AcolytBaseTool


class Config(SkillConfig):
    """Configuration for Acolyt skills."""

    api_key: str


def get_skills(
    config: Config,
    agent_id: str,
    is_private: bool,
    store: SkillStoreABC,
    agent_store: AgentStoreABC,
    **_,
) -> list[AcolytBaseTool]:
    """Get all Acolyt skills."""
    # always return public skills
    resp = [
        get_Acolyt_skill(
            name,
            config["api_key"],
            store,
            agent_store,
            agent_id,
        )
        for name in config["public_skills"]
    ]
    # return private skills only if is_private
    if is_private and "private_skills" in config:
        resp.extend(
            get_Acolyt_skill(
                name,
                config["api_key"],
                store,
                agent_store,
                agent_id,
            )
            for name in config["private_skills"]
            # remove duplicates
            if name not in config["public_skills"]
        )
    return resp


def get_Acolyt_skill(
    name: str,
    api_key: str,
    skill_store: SkillStoreABC,
    agent_store: AgentStoreABC,
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
