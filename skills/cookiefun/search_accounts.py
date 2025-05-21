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
    """Sort options for account search results."""
    SmartEngagementPoints = 0
    Impressions = 1
    MatchingTweetsCount = 2


class SortOrder(IntEnum):
    """Sort order options."""
    Ascending = 0
    Descending = 1


class SearchAccountsInput(BaseModel):
    """Input for SearchAccounts tool."""
    
    searchQuery: str = Field(
        description="Search term to find in tweets",
    )
    
    type: Optional[TweetType] = Field(
        default=None,
        description="Tweet type: Original (0), Reply (1), Quote (2)",
    )
    
    startDate: Optional[str] = Field(
        default=None,
        description="Start date for filtering in format dd/mm/yyyy (default: 30 days ago)",
    )
    
    endDate: Optional[str] = Field(
        default=None,
        description="End date for filtering in format dd/mm/yyyy (default: now)",
    )
    
    sortBy: Optional[SortBy] = Field(
        default=None,
        description="Sort by: SmartEngagementPoints (0), Impressions (1), MatchingTweetsCount (2)",
    )
    
    sortOrder: Optional[SortOrder] = Field(
        default=None,
        description="Sort order: Ascending (0), Descending (1)",
    )


class SearchAccounts(CookieFunBaseTool):
    """Tool to search for Twitter accounts that authored tweets matching specified criteria."""

    name: str = "cookiefun_search_accounts"
    description: str = "Searches for Twitter accounts that authored tweets matching specified search criteria."
    args_schema: Type[BaseModel] = SearchAccountsInput

    async def _arun(
        self, 
        config: RunnableConfig, 
        searchQuery: str,
        type: Optional[int] = None,
        startDate: Optional[str] = None,
        endDate: Optional[str] = None,
        sortBy: Optional[int] = None,
        sortOrder: Optional[int] = None,
        **kwargs
    ) -> Union[Dict[str, Any], str]:
        """
        Search for Twitter accounts that authored tweets matching the specified criteria.
        
        Args:
            searchQuery: Search term to find in tweets
            type: Tweet type: Original (0), Reply (1), Quote (2)
            startDate: Start date for filtering in format dd/mm/yyyy (default: 30 days ago)
            endDate: End date for filtering in format dd/mm/yyyy (default: now)
            sortBy: Sort by: SmartEngagementPoints (0), Impressions (1), MatchingTweetsCount (2)
            sortOrder: Sort order: Ascending (0), Descending (1)
            
        Returns:
            List of Twitter accounts matching the search criteria, with detailed account metrics.
        """
        try:
            # Get context to retrieve API key
            context = self.context_from_config(config)
            api_key = context.config.get("api_key", "")
            
            if not api_key:
                return "Error: No API key provided for CookieFun API. Please configure the API key in the agent settings."
                
            # Prepare request payload
            payload = {"searchQuery": searchQuery}
            
            if type is not None:
                payload["type"] = type
            if startDate is not None:
                payload["startDate"] = startDate
            if endDate is not None:
                payload["endDate"] = endDate
            if sortBy is not None:
                payload["sortBy"] = sortBy
            if sortOrder is not None:
                payload["sortOrder"] = sortOrder
                
            # Make API request
            headers = {**DEFAULT_HEADERS, "x-api-key": api_key}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    ENDPOINTS["search_accounts"],
                    headers=headers,
                    json=payload
                )
                
                response.raise_for_status()
                data = response.json()
                
                if data.get("success") and "ok" in data:
                    return data["ok"]
                else:
                    return f"Error searching accounts: {data.get('error', 'Unknown error')}"
                    
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            return f"Request error occurred: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}" 