"""Heurist AI skills."""

from typing import TypedDict

from abstracts.skill import SkillStoreABC
from skills.base import SkillConfig, SkillState
from skills.heurist.base import HeuristBaseTool
from skills.heurist.heurist_image_generation import HeuristImageGeneration

# Cache skills at the system level, because they are stateless
_cache: dict[str, HeuristBaseTool] = {}


class SkillStates(TypedDict):
    heurist_image_generation: SkillState


class Config(SkillConfig):
    """Configuration for Heurist AI skills."""

    states: SkillStates


async def get_skills(
    config: "Config",
    is_private: bool,
    store: SkillStoreABC,
    **_,
) -> list[HeuristBaseTool]:
    """Get all Heurist AI skills.

    Args:
        config: The configuration for Heurist AI skills.
        is_private: Whether to include private skills.
        store: The skill store for persisting data.

    Returns:
        A list of Heurist AI skills.
    """
    available_skills = []

    # Include skills based on their state
    for skill_name, state in config["states"].items():
        if state == "disabled":
            continue
        elif state == "public" or (state == "private" and is_private):
            available_skills.append(skill_name)

    # Get each skill using the cached getter
    return [get_heurist_skill(name, store) for name in available_skills]


def get_heurist_skill(
    name: str,
    store: SkillStoreABC,
) -> HeuristBaseTool:
    """Get a Heurist AI skill by name.

    Args:
        name: The name of the skill to get
        store: The skill store for persisting data

    Returns:
        The requested Heurist AI skill

    Raises:
        ValueError: If the requested skill name is unknown
    """
    if name == "heurist_image_generation":
        if name not in _cache:
            _cache[name] = HeuristImageGeneration(
                skill_store=store,
            )
        return _cache[name]
    else:
        raise ValueError(f"Unknown Heurist skill: {name}")
