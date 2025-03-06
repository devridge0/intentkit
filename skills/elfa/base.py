from typing import Type

from pydantic import BaseModel, Field

from abstracts.skill import IntentKitSkill, SkillStoreABC

base_url = "https://api.elfa.ai"


class ElfaBaseTool(IntentKitSkill):
    """Base class for Elfa tools."""

    api_key: str = Field(description="API Key")

    name: str = Field(description="The name of the tool")
    description: str = Field(description="A description of what the tool does")
    args_schema: Type[BaseModel]
    skill_store: SkillStoreABC = Field(
        description="The skill store for persisting data"
    )

    @property
    def category(self) -> str:
        return "elfa"
