"""Acolyt skill module."""

from typing import TypedDict

from abstracts.skill import SkillStoreABC
from skills.acolyt.ask import AcolytAskGpt
from skills.acolyt.base import AcolytBaseTool
from skills.base import SkillConfig, SkillState

# Cache skills at the system level, because they are stateless
_cache: dict[str, AcolytBaseTool] = {}


class SkillStates(TypedDict):
    ask_gpt: SkillState


class AcolytClientConfig(TypedDict):
    """Configuration for Acolyt API client."""

    api_key: str


class Config(SkillConfig, AcolytClientConfig):
    """Configuration for Acolyt skills."""

    skill_states: SkillStates


def get_skills(
    config: "Config",
    is_private: bool,
    store: SkillStoreABC,
    **_,
) -> list[AcolytBaseTool]:
    """Get all Acolyt skills.

    Args:
        config: The configuration for Acolyt skills.
        is_private: Whether to include private skills.
        store: The skill store for persisting data.

    Returns:
        A list of Acolyt skills.
    """
    available_skills = []

    # Include skills based on their state
    for skill_name, state in config["skill_states"].items():
        if state == "disabled":
            continue
        elif state == "public" or (state == "private" and is_private):
            available_skills.append(skill_name)

    # Get each skill using the cached getter
    return [get_acolyt_skill(name, store) for name in available_skills]


def get_acolyt_skill(
    name: str,
    store: SkillStoreABC,
) -> AcolytBaseTool:
    """Get an Acolyt skill by name.

    Args:
        name: The name of the skill to get
        store: The skill store for persisting data

    Returns:
        The requested Acolyt skill

    Raises:
        ValueError: If the requested skill name is unknown
    """
    if name == "ask_gpt":
        if name not in _cache:
            _cache[name] = AcolytAskGpt(
                skill_store=store,
            )
        return _cache[name]
    else:
        raise ValueError(f"Unknown Acolyt skill: {name}")
