from typing import Type

from pydantic import BaseModel, Field

from abstracts.skill import SkillStoreABC
from skills.base import IntentKitSkill

base_url = "http://backend-api/v1"

class NationBaseTool(IntentKitSkill):
    """Base class for GitHub tools."""

    name: str = Field(description="The name of the tool")
    description: str = Field(description="A description of what the tool does")
    args_schema: Type[BaseModel]
    skill_store: SkillStoreABC = Field(
        description="The skill store for persisting data"
    )

    @property
    def category(self) -> str:
        return "nation"
