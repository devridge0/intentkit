"""Base class for CryptoPanic skills."""

from typing import Optional, Type

from pydantic import BaseModel, Field

from abstracts.skill import SkillStoreABC
from app.config.config import config
from skills.base import IntentKitSkill, SkillContext

base_url = "https://cryptopanic.com/api/v1/posts/"

class CryptopanicBaseTool(IntentKitSkill):
    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")
    args_schema: Type[BaseModel]
    skill_store: SkillStoreABC = Field(description="Skill store for data persistence")

    def get_api_key(self, context: SkillContext) -> Optional[str]:
        if hasattr(config, "cryptopanic_api_key") and config.cryptopanic_api_key:
            return config.cryptopanic_api_key
        if "api_key" in context.config and context.config["api_key"]:
            return context.config["api_key"]
        return self.skill_store.get_system_config("cryptopanic_api_key")

    @property
    def category(self) -> str:
        return "cryptopanic"