"""Common utility skills."""

from abstracts.agent import AgentStoreABC
from abstracts.skill import SkillStoreABC
from models.skill import SkillConfig
from skills.common.base import CommonBaseTool
from skills.common.current_time import CurrentTime


class Config(SkillConfig):
    """Configuration for common utility skills."""


def get_skills(
    config: "Config",
    agent_id: str,
    is_private: bool,
    store: SkillStoreABC,
    agent_store: AgentStoreABC,
    **_,
) -> list[CommonBaseTool]:
    """Get all common utility skills."""
    # always return public skills
    resp = [
        get_common_skill(name, store, agent_id, agent_store)
        for name in config["public_skills"]
    ]
    # return private skills only if is_private
    if is_private and "private_skills" in config:
        resp.extend(
            [
                get_common_skill(name, store, agent_id, agent_store)
                for name in config["private_skills"]
                # remove duplicates
                if name not in config["public_skills"]
            ]
        )
    return resp


def get_common_skill(
    name: str,
    store: SkillStoreABC,
    agent_id: str,
    agent_store: AgentStoreABC,
) -> CommonBaseTool:
    """Get a common utility skill by name.

    Args:
        name: The name of the skill to get
        store: The skill store for persisting data
        agent_id: The ID of the agent
        agent_store: The agent store for persisting data

    Returns:
        The requested common utility skill

    Raises:
        ValueError: If the requested skill name is unknown
    """
    if name == "current_time":
        return CurrentTime(
            skill_store=store,
            agent_id=agent_id,
            agent_store=agent_store,
        )
    else:
        raise ValueError(f"Unknown skill: {name}")
