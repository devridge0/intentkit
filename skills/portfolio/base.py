"""Base classes for portfolio skills."""

import asyncio
import logging
from abc import ABC
from typing import Any, Dict, Optional, Type

import aiohttp
from pydantic import BaseModel, Field

from abstracts.skill import SkillStoreABC
from skills.base import IntentKitSkill
from skills.portfolio.constants import MORALIS_API_BASE_URL

logger = logging.getLogger(__name__)


class PortfolioBaseTool(IntentKitSkill, ABC):
    """Base class for portfolio analysis skills."""

    name: str = Field(description="The name of the tool")
    description: str = Field(description="A description of what the tool does")
    args_schema: Type[BaseModel]
    skill_store: SkillStoreABC = Field(
        description="The skill store for persisting data"
    )
    base_url: str = MORALIS_API_BASE_URL

    @property
    def category(self) -> str:
        return "portfolio"

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
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a request to the Moralis API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            api_key: The Moralis API key
            params: Query parameters
            json_data: JSON data for request body

        Returns:
            API response as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        headers = {"accept": "application/json", "X-API-Key": api_key}

        # Convert boolean params to strings
        processed_params = self._prepare_params(params) if params else None

        logger.debug(f"Portfolio skill {self.name} making {method} request to {url}")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=processed_params,
                    json=json_data,
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Moralis API error: {response.status} - {error_text}"
                        )
                        raise ValueError(
                            f"Moralis API error: {response.status} - {error_text}"
                        )
            except aiohttp.ClientError as e:
                logger.error(f"Request error in {self.name}: {str(e)}")
                raise ValueError(f"Request error: {str(e)}")

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the tool synchronously by running the async version in a loop."""
        return asyncio.run(self._arun(*args, **kwargs))
