from typing import Any, Dict, Optional, Type, Union

import httpx
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from skills.cookiefun.base import CookieFunBaseTool
from skills.cookiefun.constants import DEFAULT_HEADERS, ENDPOINTS


class GetAccountDetailsInput(BaseModel):
    """Input for GetAccountDetails tool."""

    username: Optional[str] = Field(
        default=None,
        description="Twitter username (either username or userId is required)",
    )

    userId: Optional[str] = Field(
        default=None,
        description="Twitter user ID (either username or userId is required)",
    )


class GetAccountDetails(CookieFunBaseTool):
    """Tool to get detailed information about a Twitter account."""

    name: str = "cookiefun_get_account_details"
    description: str = "Retrieves detailed information about a Twitter account including followers, following, posts, metrics, and engagement data."
    args_schema: Type[BaseModel] = GetAccountDetailsInput

    async def _arun(
        self,
        config: RunnableConfig,
        username: Optional[str] = None,
        userId: Optional[str] = None,
        **kwargs,
    ) -> Union[Dict[str, Any], str]:
        """
        Get detailed information about a Twitter account.

        Args:
            username: Twitter username (either username or userId is required)
            userId: Twitter user ID (either username or userId is required)

        Returns:
            Account details including followers, following, posts, metrics, and engagement data.
        """
        # Validate input parameters
        if not username and not userId:
            return "Error: Either username or userId must be provided."

        try:
            # Get context to retrieve API key
            context = self.context_from_config(config)
            api_key = context.config.get("api_key", "")

            if not api_key:
                return "Error: No API key provided for CookieFun API. Please configure the API key in the agent settings."

            # Prepare request payload
            payload = {}
            if username:
                payload["username"] = username
            if userId:
                payload["userId"] = userId

            # Make API request
            headers = {**DEFAULT_HEADERS, "x-api-key": api_key}

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    ENDPOINTS["account_details"], headers=headers, json=payload
                )

                response.raise_for_status()
                data = response.json()

                if data.get("success") and "ok" in data:
                    return data["ok"]
                else:
                    return f"Error fetching account details: {data.get('error', 'Unknown error')}"

        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            return f"Request error occurred: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"
