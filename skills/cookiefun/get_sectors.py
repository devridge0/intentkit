from typing import Any, Dict, List, Type

import httpx
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel

from skills.cookiefun.base import CookieFunBaseTool
from skills.cookiefun.constants import DEFAULT_HEADERS, ENDPOINTS


class GetSectorsInput(BaseModel):
    """Input for GetSectors tool."""

    pass


class GetSectors(CookieFunBaseTool):
    """Tool to get all available sectors from the CookieFun API."""

    name: str = "cookiefun_get_sectors"
    description: str = (
        "Returns a list of all available sectors in the CookieFun system."
    )
    args_schema: Type[BaseModel] = GetSectorsInput

    async def _arun(self, config: RunnableConfig, **kwargs) -> List[Dict[str, Any]]:
        """
        Get all available sectors from the CookieFun API.

        Returns:
            List of sector objects, each containing id, name, and other metadata.
        """
        try:
            # Get context to retrieve API key
            context = self.context_from_config(config)
            api_key = context.config.get("api_key", "")

            if not api_key:
                return "Error: No API key provided for CookieFun API. Please configure the API key in the agent settings."

            # Make API request
            headers = {**DEFAULT_HEADERS, "x-api-key": api_key}

            async with httpx.AsyncClient() as client:
                response = await client.get(ENDPOINTS["sectors"], headers=headers)

                response.raise_for_status()
                data = response.json()

                if data.get("success") and "ok" in data and "sectors" in data["ok"]:
                    return data["ok"]["sectors"]
                else:
                    return (
                        f"Error fetching sectors: {data.get('error', 'Unknown error')}"
                    )

        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            return f"Request error occurred: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"
