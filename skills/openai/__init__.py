"""OpenAI skills."""

import logging
from typing import TypedDict

from langchain_community.tools.openai_dalle_image_generation import (
    OpenAIDALLEImageGenerationTool,
)
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper

from abstracts.skill import SkillStoreABC
from skills.base import SkillConfig, SkillState
from skills.openai.base import OpenAIBaseTool
from skills.openai.image_to_text import ImageToText

# Cache skills at the system level, because they are stateless
_cache: dict[str, OpenAIBaseTool] = {}

logger = logging.getLogger(__name__)


class SkillStates(TypedDict):
    image_to_text: SkillState
    dalle_image_generation: SkillState


class Config(SkillConfig):
    """Configuration for OpenAI skills."""

    states: SkillStates


async def get_skills(
    config: "Config",
    is_private: bool,
    store: SkillStoreABC,
    **_,
) -> list[OpenAIBaseTool]:
    """Get all OpenAI skills.

    Args:
        config: The configuration for OpenAI skills.
        is_private: Whether to include private skills.
        store: The skill store for persisting data.

    Returns:
        A list of OpenAI skills.
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
        skill = get_openai_skill(name, store)
        if skill:
            result.append(skill)
    return result


def get_openai_skill(
    name: str,
    store: SkillStoreABC,
) -> OpenAIBaseTool:
    """Get an OpenAI skill by name.

    Args:
        name: The name of the skill to get
        store: The skill store for persisting data

    Returns:
        The requested OpenAI skill
    """
    if name == "image_to_text":
        if name not in _cache:
            _cache[name] = ImageToText(
                skill_store=store,
            )
        return _cache[name]
    elif name == "dalle_image_generation":
        if name not in _cache:
            _cache[name] = OpenAIDALLEImageGenerationTool(
                api_wrapper=DallEAPIWrapper(
                    model="dall-e-3",
                    quality="hd",
                    api_key=store.get_system_config("openai_api_key"),
                ),
                handle_tool_error=lambda e: f"tool error: {e}",
                handle_validation_error=lambda e: f"validation error: {e}",
            )
        return _cache[name]
    else:
        logger.warning(f"Unknown OpenAI skill: {name}")
        return None
