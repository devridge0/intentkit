from typing import Any, Callable, Dict, Optional

from abstracts.skill import SkillStoreABC
from models.skill import AgentSkillData, ThreadSkillData


class SkillStore(SkillStoreABC):
    """Implementation of skill data storage operations.

    This class provides concrete implementations for storing and retrieving
    skill-related data for both agents and threads using SQLModel-based storage.

    Args:
        get_session: A callable that returns a database session
    """

    def __init__(self, get_session: Callable[[], Any]) -> None:
        self._get_session = get_session

    def get_agent_skill_data(
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
        with self._get_session() as session:
            return AgentSkillData.get(agent_id, skill, key, session)

    def save_agent_skill_data(
        self, agent_id: str, skill: str, key: str, data: Dict[str, Any]
    ) -> None:
        """Save or update skill data for an agent.

        Args:
            agent_id: ID of the agent
            skill: Name of the skill
            key: Data key
            data: JSON data to store
        """
        with self._get_session() as session:
            skill_data = AgentSkillData(
                agent_id=agent_id,
                skill=skill,
                key=key,
                data=data,
            )
            skill_data.save(session)
            session.commit()

    def get_thread_skill_data(
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
        with self._get_session() as session:
            return ThreadSkillData.get(thread_id, skill, key, session)

    def save_thread_skill_data(
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
        with self._get_session() as session:
            skill_data = ThreadSkillData(
                thread_id=thread_id,
                agent_id=agent_id,
                skill=skill,
                key=key,
                data=data,
            )
            skill_data.save(session)
            session.commit()
