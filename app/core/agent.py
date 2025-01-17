from typing import Any, Callable, Dict, Optional

from sqlmodel import select

from abstracts.agent import AgentStoreABC
from models.agent import Agent, AgentData, AgentQuota


class AgentStore(AgentStoreABC):
    """Implementation of agent data storage operations.

    This class provides concrete implementations for storing and retrieving
    agent-related data using SQLModel-based storage.

    Args:
        agent_id: ID of the agent
        get_session: A callable that returns a database session
    """

    def __init__(self, agent_id: str, get_session: Callable[[], Any]) -> None:
        """Initialize the agent store.

        Args:
            agent_id: ID of the agent
            get_session: A callable that returns a database session
        """
        super().__init__(agent_id)
        self._get_session = get_session

    def get_config(self) -> Optional[Agent]:
        """Get agent configuration.

        Returns:
            Agent configuration if found, None otherwise
        """
        with self._get_session() as session:
            return session.exec(select(Agent).where(Agent.id == self.agent_id)).first()

    def get_data(self) -> Optional[AgentData]:
        """Get additional agent data.

        Returns:
            Agent data if found, None otherwise
        """
        with self._get_session() as session:
            return session.exec(
                select(AgentData).where(AgentData.id == self.agent_id)
            ).first()

    def set_data(self, data: Dict) -> None:
        """Update agent data.

        Args:
            data: Dictionary containing fields to update
        """
        with self._get_session() as session:
            agent_data = session.exec(
                select(AgentData).where(AgentData.id == self.agent_id)
            ).first()

            if agent_data:
                # Update existing record
                for field, value in data.items():
                    if hasattr(agent_data, field):
                        setattr(agent_data, field, value)
                session.add(agent_data)
            else:
                # Create new record
                agent_data = AgentData(id=self.agent_id, **data)
                session.add(agent_data)

            session.commit()

    def get_quota(self) -> Optional[AgentQuota]:
        """Get agent quota information.

        Returns:
            Agent quota if found, None otherwise
        """
        with self._get_session() as session:
            return AgentQuota.get(self.agent_id, session)
