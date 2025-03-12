"""Base class for all CryptoCompare tools."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Type

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from abstracts.skill import SkillStoreABC
from skills.base import IntentKitSkill


class AgentContext:
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        self.agent = AgentInfo(agent_id)
        self.config = config


class AgentInfo:
    def __init__(self, agent_id: str):
        self.id = agent_id


class CryptoCompareBaseTool(IntentKitSkill):
    """Base class for CryptoCompare tools.

    This class provides common functionality for all CryptoCompare API tools:
    - Rate limiting
    - State management through skill_store
    """

    name: str = Field(description="The name of the tool")
    description: str = Field(description="A description of what the tool does")
    args_schema: Type[BaseModel]
    skill_store: SkillStoreABC = Field(
        description="The skill store for persisting data"
    )

    @property
    def category(self) -> str:
        return "cryptocompare"

    def context_from_config(self, config: RunnableConfig) -> AgentContext:
        """Extract agent context from RunnableConfig.

        Args:
            config: The RunnableConfig containing agent information

        Returns:
            AgentContext: Containing agent information
        """
        agent_id = config.get(
            "agent_id", config.get("configurable", {}).get("agent_id", "default_agent")
        )
        agent_config = config.get("configurable", {}).get("config", {})
        return AgentContext(agent_id, agent_config)

    async def check_rate_limit(
        self, max_requests: int = 1, interval: int = 15, agent_id: str = None
    ) -> tuple[bool, str | None]:
        """Check if the rate limit has been exceeded.

        Args:
            max_requests: Maximum number of requests allowed in the interval
            interval: Time interval in minutes
            agent_id: Optional agent ID for agent-specific rate limiting

        Returns:
            Tuple of (is_rate_limited, error_message)
        """
        # Use the skill name and optional agent_id as a unique identifier for rate limiting
        rate_limit_key = f"rate_limit_{self.name}"
        if agent_id:
            rate_limit_key = f"{rate_limit_key}_{agent_id}"

        rate_limit = await self.skill_store.get_skill_data(rate_limit_key)
        current_time = datetime.now(tz=timezone.utc)

        if (
            rate_limit
            and rate_limit.get("reset_time")
            and rate_limit.get("count") is not None
            and datetime.fromisoformat(rate_limit["reset_time"]) > current_time
        ):
            if rate_limit["count"] >= max_requests:
                return True, "Rate limit exceeded"
            else:
                rate_limit["count"] += 1
                await self.skill_store.save_skill_data(rate_limit_key, rate_limit)
                return False, None

        new_rate_limit = {
            "count": 1,
            "reset_time": (current_time + timedelta(minutes=interval)).isoformat(),
        }
        await self.skill_store.save_skill_data(rate_limit_key, new_rate_limit)
        return False, None
