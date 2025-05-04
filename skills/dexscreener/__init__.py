import logging
from typing import Optional, TypedDict

from abstracts.skill import SkillStoreABC
from skills.base import SkillConfig, SkillState
from skills.dexscreener.base import DexScreenerBaseTool
from skills.dexscreener.search_token import SearchToken

# Cache skills at the system level, because they are stateless
_cache: dict[str, DexScreenerBaseTool] = {}

logger = logging.getLogger(__name__)


class SkillStates(TypedDict):
    search_token: SkillState


_SKILL_NAME_TO_CLASS_MAP: dict[str, type[DexScreenerBaseTool]] = {
    "search_token": SearchToken,
}


class Config(SkillConfig):
    """Configuration for DexScreener skills."""

    enabled: bool
    states: SkillStates


async def get_skills(
    config: "Config",
    is_private: bool,
    store: SkillStoreABC,
    **_,
) -> list[DexScreenerBaseTool]:
    """Get all DexScreener skills.

    Args:
        config: The configuration for DexScreener skills.
        is_private: Whether to include private skills.
        store: The skill store for persisting data.

    Returns:
        A list of DexScreener skills.
    """

    logger.error("DEX get_skills 1")
    available_skills = []

    logger.error("DEX get_skills 2")

    # Include skills based on their state
    for skill_name, state in config["states"].items():
        if state == "disabled":
            continue
        elif state == "public" or (state == "private" and is_private):
            available_skills.append(skill_name)

    logger.error("DEX get_skills 3")
    # Get each skill using the cached getter

    result = []
    for name in available_skills:
        skill = get_dexscreener_skills(name, store)
        if skill:
            result.append(skill)
    logger.error("DEX get_skills 4")
    return result


def get_dexscreener_skills(
    name: str,
    store: SkillStoreABC,
) -> Optional[DexScreenerBaseTool]:
    """Get a DexScreener skill by name.

    Args:
        name: The name of the skill to get
        store: The skill store for persisting data

    Returns:
        The requested DexScreener skill
    """
    logger.error("DEX get_dexscreener_skills 1")

    # Return from cache immediately if already exists
    if name in _cache:
        return _cache[name]

    logger.error("DEX get_dexscreener_skills 2")
    skill_class = _SKILL_NAME_TO_CLASS_MAP.get(name)
    logger.error("DEX get_dexscreener_skills 3")
    if not skill_class:
        logger.error("DEX get_dexscreener_skills 4")
        logger.warning(f"Unknown Venice skill: {name}")
        return None

    logger.error("DEX get_dexscreener_skills 5")
    logger.error("DEX get_dexscreener_skills 6")
    _cache[name] = skill_class(skill_store=store)
    logger.error("DEX get_dexscreener_skills 7")
    return _cache[name]
