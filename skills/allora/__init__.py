"""Allora skill module."""

from abstracts.agent import AgentStoreABC
from abstracts.skill import SkillStoreABC
from models.skill import SkillConfig
from skills.allora.base import AlloraBaseTool
from skills.allora.price import AlloraGetPrice


class Config(SkillConfig):
    """Configuration for Allora skills."""

    api_key: str


def get_skills(
    config: Config,
    agent_id: str,
    is_private: bool,
    store: SkillStoreABC,
    agent_store: AgentStoreABC,
    **_,
) -> list[AlloraBaseTool]:
    """Get all Allora skills."""
    # always return public skills
    resp = [
        get_allora_skill(
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
            get_allora_skill(
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


def get_allora_skill(
    name: str,
    api_key: str,
    skill_store: SkillStoreABC,
    agent_store: AgentStoreABC,
    agent_id: str,
) -> AlloraBaseTool:
    if not api_key:
        raise ValueError("Allora API token is empty")

    if name == "get_price_prediction":
        return AlloraGetPrice(
            api_key=api_key,
            agent_id=agent_id,
            skill_store=skill_store,
            agent_store=agent_store,
        )

    else:
        raise ValueError(f"Unknown Allora skill: {name}")
