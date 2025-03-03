from typing import Dict, Optional

from abstracts.agent import AgentStoreABC
from models.agent import Agent, AgentData, AgentQuota


class AgentStore(AgentStoreABC):
    """Implementation of agent data storage operations.

    This class provides concrete implementations for storing and retrieving
    agent-related data.

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
        return await Agent.get(self.agent_id)

    async def get_data(self) -> Optional[AgentData]:
        """Get additional agent data.

        Returns:
            Agent data if found, None otherwise
        """
        return await AgentData.get(self.agent_id)

    async def set_data(self, data: Dict) -> None:
        """Update agent data.

        Args:
            data: Dictionary containing fields to update
        """
        await AgentData.patch(self.agent_id, data)

    async def get_quota(self) -> Optional[AgentQuota]:
        """Get agent quota information.

        Returns:
            Agent quota if found, None otherwise
        """
        return await AgentQuota.get(self.agent_id)
