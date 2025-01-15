from abc import ABC, abstractmethod
from typing import Optional

from tweepy import Client


class TwitterABC(ABC):
    """Abstract base class for Twitter operations.

    This class defines the interface for interacting with Twitter's API
    through a Tweepy client.
    """

    @abstractmethod
    def get_client(self) -> Optional[Client]:
        """Get a configured Tweepy client.

        Returns:
            A configured Tweepy client if credentials are valid, None otherwise
        """
        pass

    @abstractmethod
    def get_id(self) -> Optional[str]:
        """Get the Twitter user ID.

        Returns:
            The Twitter user ID if available, None otherwise
        """
        pass

    @abstractmethod
    def get_username(self) -> Optional[str]:
        """Get the Twitter username.

        Returns:
            The Twitter username (without @ symbol) if available, None otherwise
        """
        pass

    @abstractmethod
    def get_name(self) -> Optional[str]:
        """Get the Twitter display name.

        Returns:
            The Twitter display name if available, None otherwise
        """
        pass
