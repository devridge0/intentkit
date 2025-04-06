"""Web search skills."""

import logging
from typing import TypedDict

from abstracts.skill import SkillStoreABC
from skills.base import SkillConfig, SkillState
from skills.web_search.base import WebSearchBaseTool
from skills.web_search.web_search import WebSearch

# Cache skills at the system level, because they are stateless
_cache: dict[str, WebSearchBaseTool] = {}

logger = logging.getLogger(__name__)


class SkillStates(TypedDict):
    web_search: SkillState


class Config(SkillConfig):
    """Configuration for web search skills."""

    states: SkillStates
    api_key: str


async def get_skills(
    config: "Config",
    is_private: bool,
    store: SkillStoreABC,
    **_,
) -> list[WebSearchBaseTool]:
    """Get all web search skills.

    Args:
        config: The configuration for web search skills.
        is_private: Whether to include private skills.
        store: The skill store for persisting data.

    Returns:
        A list of web search skills.
    """
    available_skills = []

    # Include skills based on their state
    for skill_name, state in config["states"].items():
        if state == "disabled":
            continue
        elif state == "public" or (state == "private" and is_private):
            available_skills.append(skill_name)

    # Get each skill using the cached getter
    result = []
    for name in available_skills:
        skill = get_web_search_skill(name, store)
        if skill:
            result.append(skill)
    return result


def get_web_search_skill(
    name: str,
    store: SkillStoreABC,
) -> WebSearchBaseTool:
    """Get a web search skill by name.

    Args:
        name: The name of the skill to get
        store: The skill store for persisting data

    Returns:
        The requested web search skill
    """
    if name == "web_search":
        if name not in _cache:
            _cache[name] = WebSearch(
                skill_store=store,
            )
        return _cache[name]
    else:
        logger.warning(f"Unknown web search skill: {name}")
        return None 