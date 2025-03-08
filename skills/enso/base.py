from typing import Type

from cdp import Wallet
from pydantic import BaseModel, Field

from abstracts.skill import SkillStoreABC
from skills.base import IntentKitSkill
from utils.chain import ChainProvider, NetworkId

base_url = "https://api.enso.finance"
default_chain_id = int(NetworkId.BaseMainnet)


class EnsoBaseTool(IntentKitSkill):
    """Base class for Enso tools."""

    api_token: str = Field(description="API token")
    main_tokens: list[str] = Field(description="Main supported tokens")
    wallet: Wallet | None = Field(None, description="The wallet of the agent")
    chain_provider: ChainProvider | None = Field(
        None, description="Chain Provider object"
    )
    name: str = Field(description="The name of the tool")
    description: str = Field(description="A description of what the tool does")
    args_schema: Type[BaseModel]
    skill_store: SkillStoreABC = Field(
        description="The skill store for persisting data"
    )
