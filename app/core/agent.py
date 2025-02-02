from typing import Dict, Optional

from abstracts.agent import AgentStoreABC
from models.agent import Agent, AgentData, AgentQuota
from models.db import get_session


class AgentStore(AgentStoreABC):
    """Implementation of agent data storage operations.

    This class provides concrete implementations for storing and retrieving
    agent-related data using SQLModel-based storage.

    Args:
        agent_id: ID of the agent
    """

    def __init__(self, agent_id: str) -> None:
        """Initialize the agent store.

        Args:
            agent_id: ID of the agent
        """
        super().__init__(agent_id)

    async def get_config(self) -> Optional[Agent]:
        """Get agent configuration.

        Returns:
            Agent configuration if found, None otherwise
        """
        async with get_session() as session:
            return await session.get(Agent, self.agent_id)

    async def get_data(self) -> Optional[AgentData]:
        """Get additional agent data.

        Returns:
            Agent data if found, None otherwise
        """
        async with get_session() as session:
            return await session.get(AgentData, self.agent_id)

    async def set_data(self, data: Dict) -> None:
        """Update agent data.

        Args:
            data: Dictionary containing fields to update
        """
        async with get_session() as session:
            agent_data = await session.get(AgentData, self.agent_id)

            if agent_data:
                for key, value in data.items():
                    setattr(agent_data, key, value)
            else:
                agent_data = AgentData(id=self.agent_id, **data)
                session.add(agent_data)

            await session.commit()

    async def get_quota(self) -> Optional[AgentQuota]:
        """Get agent quota information.

        Returns:
            Agent quota if found, None otherwise
        """
        async with get_session() as session:
            return await session.get(AgentQuota, self.agent_id)
