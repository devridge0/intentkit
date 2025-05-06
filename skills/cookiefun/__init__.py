"""Cookie.fun analytics skills."""

from typing import TypedDict

from abstracts.skill import SkillStoreABC
from skills.base import SkillConfig, SkillState
from skills.cookiefun.base import CookieFunBaseTool
from skills.cookiefun.generate_image import GenerateImage
from skills.cookiefun.get_ai_response import GetAIResponse
from skills.cookiefun.get_country_time import GetCountryTime
from skills.cookiefun.get_crypto import GetCrypto
from skills.cookiefun.translate_text import TranslateText

# Cache skills at the system level, because they are stateless
_cache: dict[str, CookieFunBaseTool] = {}


class SkillStates(TypedDict):
    get_country_time: SkillState
    get_ai_response: SkillState
    generate_image: SkillState
    translate_text: SkillState
    get_crypto: SkillState


class Config(SkillConfig):
    """Configuration for Cookie.fun skills."""

    states: SkillStates
    cookiefun_api_key: str  # Cookie.fun API key


async def get_skills(
    config: "Config",
    is_private: bool,
    store: SkillStoreABC,
    **_,
) -> list[CookieFunBaseTool]:
    """Get all Cookie.fun skills."""
    available_skills = []

    # Include skills based on their state
    for skill_name, state in config["states"].items():
        if state == "disabled":
            continue
        elif state == "public" or (state == "private" and is_private):
            available_skills.append(skill_name)

    # Get each skill using the cached getter
    return [get_cookiefun_skill(name, store) for name in available_skills]


def get_cookiefun_skill(
    name: str,
    store: SkillStoreABC,
) -> CookieFunBaseTool:
    """Get a Cookie.fun skill by name."""
    if name not in _cache:
        if name == "get_country_time":
            _cache[name] = GetCountryTime(skill_store=store)
        elif name == "get_ai_response":
            _cache[name] = GetAIResponse(skill_store=store)
        elif name == "generate_image":
            _cache[name] = GenerateImage(skill_store=store)
        elif name == "translate_text":
            _cache[name] = TranslateText(skill_store=store)
        elif name == "get_crypto":
            _cache[name] = GetCrypto(skill_store=store)
        else:
            raise ValueError(f"Unknown Cookie.fun skill: {name}")
    return _cache[name]
