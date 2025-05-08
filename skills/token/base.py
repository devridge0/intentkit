"""Base class for token-related skills."""

import logging
from typing import Any, Dict, Optional

import aiohttp
from langchain_core.runnables import RunnableConfig

from abstracts.skill import SkillStoreABC
from skills.base import IntentKitSkill
from skills.token.constants import MORALIS_API_BASE_URL

logger = logging.getLogger(__name__)


class TokenBaseTool(IntentKitSkill):
    """Base class for all token-related skills.

    This base class provides common functionality for token API interactions,
    including making HTTP requests to the Moralis API.
    """

    def __init__(self, skill_store: SkillStoreABC = None):
        """Initialize the token tool with a skill store."""
        super().__init__(skill_store=skill_store)

    @property
    def category(self) -> str:
        return "token"

    def context_from_config(self, config: Optional[RunnableConfig] = None) -> Any:
        """Extract context from the runnable config."""
        if not config:
            return None
        return config.get("context")

    def _prepare_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Convert boolean values to lowercase strings for API compatibility.

        Args:
            params: Dictionary with query parameters that may contain boolean values

        Returns:
            Dictionary with boolean values converted to lowercase strings
        """
        if not params:
            return params

        result = {}
        for key, value in params.items():
            if isinstance(value, bool):
                result[key] = str(value).lower()
            else:
                result[key] = value
        return result

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        api_key: str,
        params: Dict[str, Any] = None,
        data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Make a request to the Moralis API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            api_key: Moralis API key
            params: Query parameters
            data: Request body data for POST requests

        Returns:
            Response data as dictionary
        """
        url = f"{MORALIS_API_BASE_URL}{endpoint}"

        headers = {"accept": "application/json", "X-API-Key": api_key}

        # Convert boolean params to strings
        processed_params = self._prepare_params(params) if params else None

        logger.debug(f"token/base.py: Making request to {url}")

        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                headers=headers,
                params=processed_params,
                json=data,
            ) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(f"token/base.py: API error: {error_text}")
                    return {
                        "error": f"API error: {response.status}",
                        "details": error_text,
                    }

                return await response.json()
