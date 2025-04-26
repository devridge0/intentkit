import logging
from typing import Optional, TypedDict

from abstracts.skill import SkillStoreABC
from skills.base import SkillState
from skills.venice_audio.venice_audio import VeniceAudioTool

logger = logging.getLogger(__name__)


_cache: dict[str, VeniceAudioTool] = {}


class SkillStates(TypedDict):
    af_heart: SkillState
    bm_daniel: SkillState


class Config(TypedDict):
    enabled: bool
    api_key: str  # API Key may be optional if provided system-wide
    states: SkillStates


async def get_skills(
    config: "Config",
    is_private: bool,
    store: SkillStoreABC,
    **_,  # Allow for extra arguments if the loader passes them
) -> list[VeniceAudioTool]:
    """
    Factory function to create and return Venice Audio skill tools.

    Args:
        config: The configuration dictionary for the Venice Audio skill.
        skill_store: The skill store instance.
        agent_id: The ID of the agent requesting the skills.

    Returns:
        A list of VeniceAudioTool instances for the Venice Audio skill.
    """
    # Check if the entire category is disabled first
    if not config.get("enabled", False):
        return []

    available_skills: list[VeniceAudioTool] = []

    # Include skills based on their state
    for skill_name, state in config["states"].items():
        if state == "disabled":
            continue
        elif state == "public" or (state == "private" and is_private):
            available_skills.append(skill_name)

    # Get each skill using the cached getter
    result = []
    for name in available_skills:
        skill = get_venice_audio_skill(name, store)
        if skill:
            result.append(skill)
    return result


def get_venice_audio_skill(
    name: str,
    store: SkillStoreABC,
) -> Optional[VeniceAudioTool]:
    """
    Factory function to get a cached Venice Image skill instance by name.

    Args:
        name: The name of the skill to get (must match keys in _SKILL_NAME_TO_CLASS_MAP).
        store: The skill store, passed to the skill constructor.

    Returns:
        The requested Venice Image skill instance, or None if the name is unknown.
    """

    # Return from cache immediately if already exists
    if name in _cache:
        return _cache[name]

    # Cache and return the newly created instance
    _cache[name] = VeniceAudioTool(
        skill_store=store,
        voice_model=name,
    )
    return _cache[name]
