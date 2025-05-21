from typing import Any, Dict, List, Optional, Type, Union

import httpx
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from skills.cookiefun.base import CookieFunBaseTool
from skills.cookiefun.constants import ENDPOINTS, DEFAULT_HEADERS


class GetAccountSmartFollowersInput(BaseModel):
    """Input for GetAccountSmartFollowers tool."""
    
    username: Optional[str] = Field(
        default=None,
        description="Twitter username (either username or userId is required)",
    )
    
    userId: Optional[str] = Field(
        default=None,
        description="Twitter user ID (either username or userId is required)",
    )


class GetAccountSmartFollowers(CookieFunBaseTool):
    """Tool to get a list of top smart followers for a specific Twitter account."""

    name: str = "cookiefun_get_account_smart_followers"
    description: str = "Returns a list of top smart followers for a specific Twitter account, with detailed metrics about these followers."
    args_schema: Type[BaseModel] = GetAccountSmartFollowersInput

    async def _arun(
        self, 
        config: RunnableConfig, 
        username: Optional[str] = None,
        userId: Optional[str] = None,
        **kwargs
    ) -> Union[List[Dict[str, Any]], str]:
        """
        Get a list of top smart followers for a specified Twitter account.
        
        Args:
            username: Twitter username (either username or userId is required)
            userId: Twitter user ID (either username or userId is required)
            
        Returns:
            List of top smart followers with detailed metrics for each follower.
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
                    ENDPOINTS["smart_followers"],
                    headers=headers,
                    json=payload
                )
                
                response.raise_for_status()
                data = response.json()
                
                if data.get("success") and "ok" in data and "entries" in data["ok"]:
                    return data["ok"]["entries"]
                else:
                    return f"Error fetching smart followers: {data.get('error', 'Unknown error')}"
                    
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            return f"Request error occurred: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}" 