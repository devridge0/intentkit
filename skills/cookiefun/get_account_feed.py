from typing import Any, Dict, List, Optional, Type, Union
from enum import IntEnum

import httpx
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from skills.cookiefun.base import CookieFunBaseTool
from skills.cookiefun.constants import ENDPOINTS, DEFAULT_HEADERS


class TweetType(IntEnum):
    """Tweet type for filtering."""
    Original = 0
    Reply = 1
    Quote = 2


class SortBy(IntEnum):
    """Sort options for tweets."""
    CreatedDate = 0
    Impressions = 1


class SortOrder(IntEnum):
    """Sort order options."""
    Ascending = 0
    Descending = 1


class GetAccountFeedInput(BaseModel):
    """Input for GetAccountFeed tool."""
    
    username: Optional[str] = Field(
        default=None,
        description="Twitter username (either username or userId is required)",
    )
    
    userId: Optional[str] = Field(
        default=None,
        description="Twitter user ID (either username or userId is required)",
    )
    
    startDate: Optional[str] = Field(
        default=None,
        description="Start date for filtering in format dd/mm/yyyy (default: 30 days ago)",
    )
    
    endDate: Optional[str] = Field(
        default=None,
        description="End date for filtering in format dd/mm/yyyy (default: now)",
    )
    
    type: Optional[TweetType] = Field(
        default=None,
        description="Tweet type: Original (0), Reply (1), Quote (2)",
    )
    
    hasMedia: Optional[bool] = Field(
        default=None,
        description="Filter to only tweets with media",
    )
    
    sortBy: Optional[SortBy] = Field(
        default=None,
        description="Sort by: CreatedDate (0), Impressions (1)",
    )
    
    sortOrder: Optional[SortOrder] = Field(
        default=None,
        description="Sort order: Ascending (0), Descending (1)",
    )


class GetAccountFeed(CookieFunBaseTool):
    """Tool to retrieve a list of tweets for a specific Twitter account with various filtering options."""

    name: str = "cookiefun_get_account_feed"
    description: str = "Retrieves a list of tweets for a specific Twitter account with various filtering options including date range, tweet type, and media presence."
    args_schema: Type[BaseModel] = GetAccountFeedInput

    async def _arun(
        self, 
        config: RunnableConfig, 
        username: Optional[str] = None,
        userId: Optional[str] = None,
        startDate: Optional[str] = None,
        endDate: Optional[str] = None,
        type: Optional[int] = None,
        hasMedia: Optional[bool] = None,
        sortBy: Optional[int] = None,
        sortOrder: Optional[int] = None,
        **kwargs
    ) -> Union[List[Dict[str, Any]], str]:
        """
        Get a list of tweets for a specific Twitter account with various filtering options.
        
        Args:
            username: Twitter username (either username or userId is required)
            userId: Twitter user ID (either username or userId is required)
            startDate: Start date for filtering in format dd/mm/yyyy (default: 30 days ago)
            endDate: End date for filtering in format dd/mm/yyyy (default: now)
            type: Tweet type: Original (0), Reply (1), Quote (2)
            hasMedia: Filter to only tweets with media
            sortBy: Sort by: CreatedDate (0), Impressions (1)
            sortOrder: Sort order: Ascending (0), Descending (1)
            
        Returns:
            List of tweets from the specified account matching the filter criteria.
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
            if startDate is not None:
                payload["startDate"] = startDate
            if endDate is not None:
                payload["endDate"] = endDate
            if type is not None:
                payload["type"] = type
            if hasMedia is not None:
                payload["hasMedia"] = hasMedia
            if sortBy is not None:
                payload["sortBy"] = sortBy
            if sortOrder is not None:
                payload["sortOrder"] = sortOrder
                
            # Make API request
            headers = {**DEFAULT_HEADERS, "x-api-key": api_key}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    ENDPOINTS["account_feed"],
                    headers=headers,
                    json=payload
                )
                
                response.raise_for_status()
                data = response.json()
                
                if data.get("success") and "ok" in data and "entries" in data["ok"]:
                    return data["ok"]["entries"]
                else:
                    return f"Error fetching account feed: {data.get('error', 'Unknown error')}"
                    
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            return f"Request error occurred: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}" 