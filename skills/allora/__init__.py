"""Allora skills."""

from abstracts.skill import SkillStoreABC
from skills.allora.base import AlloraBaseTool
from skills.allora.price import AlloraGetPrice


def get_allora_skill(
    name: str,
    api_key: str,
    skill_store: SkillStoreABC,
    agent_store: SkillStoreABC,
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
