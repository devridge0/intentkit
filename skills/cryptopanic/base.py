from typing import Type

from pydantic import BaseModel, Field

from abstracts.skill import SkillStoreABC
from skills.base import IntentKitSkill, SkillContext

base_url = "https://cryptopanic.com/api/v1/posts/"


class CryptopanicBaseTool(IntentKitSkill):
    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")
    args_schema: Type[BaseModel]
    skill_store: SkillStoreABC = Field(description="Skill store for data persistence")

    def get_api_key(self, context: SkillContext) -> str:
        api_key = context.config.get("api_key")
        if not api_key:
            raise ValueError("CryptoPanic API key not found in context.config['api_key']")
        return api_key

    @property
    def category(self) -> str:
        return "cryptopanic"
