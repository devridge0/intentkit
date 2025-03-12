from typing import Any, Callable, Dict, Literal, NotRequired, Optional, TypedDict, Union

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langchain_core.tools.base import ToolException
from pydantic import (
    BaseModel,
    ValidationError,
)
from pydantic.v1 import ValidationError as ValidationErrorV1

from abstracts.skill import SkillStoreABC
from models.agent import Agent

SkillState = Literal["disabled", "public", "private"]


class SkillConfig(TypedDict):
    """Abstract base class for skill configuration."""

    states: Dict[str, SkillState]
    __extra__: NotRequired[Dict[str, Any]]


class SkillContext(BaseModel):
    agent: Agent
    config: SkillConfig
    user_id: Optional[str]
    entrypoint: Literal["web", "twitter", "telegram", "trigger"]


class IntentKitSkill(BaseTool):
    """Abstract base class for IntentKit skills.
    Will have predefined abilities.
    """

    skill_store: SkillStoreABC
    # overwrite the value of BaseTool
    handle_tool_error: Optional[Union[bool, str, Callable[[ToolException], str]]] = (
        lambda e: f"tool error: {e}"
    )
    """Handle the content of the ToolException thrown."""

    # overwrite the value of BaseTool
    handle_validation_error: Optional[
        Union[bool, str, Callable[[Union[ValidationError, ValidationErrorV1]], str]]
    ] = lambda e: f"validation error: {e}"
    """Handle the content of the ValidationError thrown."""

    @property
    def category(self) -> str:
        """Get the category of the skill."""
        raise NotImplementedError

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError(
            "Use _arun instead, IntentKit only supports synchronous skill calls"
        )

    def context_from_config(self, runner_config: RunnableConfig) -> SkillContext:
        if "configurable" not in runner_config:
            raise ValueError("configurable not in runner_config")
        if "agent" not in runner_config["configurable"]:
            raise ValueError("agent not in runner_config['configurable']")
        agent: Agent = runner_config["configurable"].get("agent")
        return SkillContext(
            agent=agent,
            config=agent.skills.get(self.category),
            user_id=runner_config["configurable"].get("user_id"),
            entrypoint=runner_config["configurable"].get("entrypoint"),
        )
