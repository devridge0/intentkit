from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from langchain_core.tools import BaseTool


class IntentKitSkill(BaseTool):
    """Abstract base class for IntentKit skills.
    Will have predefined abilities.
    """

    agent_id: str
    skill_store: "SkillStoreABC"
    # overwrite the value of BaseTool
    handle_tool_error: True
    # overwrite the value of BaseTool
    handle_validation_error: True


class SkillStoreABC(ABC):
    """Abstract base class for skill data storage operations.

    This class defines the interface for interacting with skill-related data
    for both agents and threads.
    """

    @abstractmethod
    async def get_agent_skill_data(
        self, agent_id: str, skill: str, key: str
    ) -> Optional[Dict[str, Any]]:
        """Get skill data for an agent.

        Args:
            agent_id: ID of the agent
            skill: Name of the skill
            key: Data key

        Returns:
            Dictionary containing the skill data if found, None otherwise
        """
        pass

    @abstractmethod
    async def save_agent_skill_data(
        self, agent_id: str, skill: str, key: str, data: Dict[str, Any]
    ) -> None:
        """Save or update skill data for an agent.

        Args:
            agent_id: ID of the agent
            skill: Name of the skill
            key: Data key
            data: JSON data to store
        """
        pass

    @abstractmethod
    async def get_thread_skill_data(
        self, thread_id: str, skill: str, key: str
    ) -> Optional[Dict[str, Any]]:
        """Get skill data for a thread.

        Args:
            thread_id: ID of the thread
            skill: Name of the skill
            key: Data key

        Returns:
            Dictionary containing the skill data if found, None otherwise
        """
        pass

    @abstractmethod
    async def save_thread_skill_data(
        self,
        thread_id: str,
        agent_id: str,
        skill: str,
        key: str,
        data: Dict[str, Any],
    ) -> None:
        """Save or update skill data for a thread.

        Args:
            thread_id: ID of the thread
            agent_id: ID of the agent that owns this thread
            skill: Name of the skill
            key: Data key
            data: JSON data to store
        """
        pass
