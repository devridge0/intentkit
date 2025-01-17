from abc import ABC, abstractmethod
from typing import Dict, Optional

from models.agent import Agent, AgentData, AgentQuota


class AgentStoreABC(ABC):
    """Abstract base class for agent data storage operations.

    This class defines the interface for interacting with agent-related data,
    including configuration, additional data, and quotas.

    Attributes:
        agent_id: ID of the agent to store/retrieve data for
    """

    def __init__(self, agent_id: str) -> None:
        """Initialize the agent store.

        Args:
            agent_id: ID of the agent
        """
        self.agent_id = agent_id

    @abstractmethod
    def get_config(self) -> Optional[Agent]:
        """Get agent configuration.

        Returns:
            Agent configuration if found, None otherwise
        """
        pass

    @abstractmethod
    def get_data(self) -> Optional[AgentData]:
        """Get additional agent data.

        Returns:
            Agent data if found, None otherwise
        """
        pass

    @abstractmethod
    def set_data(self, data: Dict) -> None:
        """Update agent data.

        Args:
            data: Dictionary containing fields to update
        """
        pass

    @abstractmethod
    def get_quota(self) -> Optional[AgentQuota]:
        """Get agent quota information.

        Returns:
            Agent quota if found, None otherwise
        """
        pass
