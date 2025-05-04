import json
import logging
from typing import (
    Any,
    Literal,
    Optional,
    Type,
)

from pydantic import BaseModel, Field, ValidationError

from skills.dexscreener.base import DexScreenerBaseTool
from skills.dexscreener.model.search_token_response import SearchTokenResponseModel

logger = logging.getLogger(__name__)

MAX_RESULTS_LIMIT = 10  # limit to 10 pair entries

# Define the allowed sort options, including multiple volume types
SortByOption = Literal["liquidity", "volume24h", "volume6h", "volume1h", "volume5m"]


class SearchTokenInput(BaseModel):
    """Input schema for the DexScreener search_token tool."""

    query: str = Field(
        description="The search query string (e.g., token symbol 'WIF', pair address, token address '0x...', token name 'Dogwifhat', or ticker '$WIF'). Prefixing with '$' filters results to match the base token symbol exactly (case-insensitive)."
    )
    sort_by: Optional[SortByOption] = Field(
        default="liquidity",
        description="Sort preference for the results. Options: 'liquidity' (default), 'volume24h', 'volume6h', 'volume1h', 'volume5m'.",
    )


class SearchToken(DexScreenerBaseTool):
    """
    Tool to search for token pairs on DexScreener based on a query string.
    """

    name: str = "dexscreener_search_token"
    description: str = (
        f"Searches DexScreener for token pairs matching the provided query string "
        f"(e.g., token symbol like 'WIF', pair address, token name like 'Dogwifhat', or ticker like '$WIF'). "
        f"If the query starts with '$', it filters results to only include pairs where the base token symbol exactly matches the ticker (case-insensitive). "
        f"Returns a list of matching pairs with details like price, volume, liquidity, etc., "
        f"sorted by the specified criteria (via 'sort_by': 'liquidity', 'volume24h', 'volume6h', 'volume1h', 'volume5m'; defaults to 'liquidity'), "
        f"limited to the top {MAX_RESULTS_LIMIT}. "
        f"Use this tool to find token information based on user queries."
    )
    args_schema: Type[BaseModel] = SearchTokenInput

    async def _arun(
        self,
        query: str,
        sort_by: Optional[SortByOption] = "liquidity",
        **kwargs: Any,
    ) -> str:
        """Implementation to search token, with added ticker filtering."""

        # dexscreener 300 request per minute (across all user) based on dexscreener docs
        # https://docs.dexscreener.com/api/reference#get-latest-dex-search
        await self.user_rate_limit_by_category(
            # using hardcoded user_id to make sure it limit across all users
            user_id=f"{self.category}{self.name}",
            limit=300,
            minutes=1,
        )

        # Ensure default if None is passed explicitly
        if sort_by is None:
            sort_by = "liquidity"

        is_ticker_query = query.startswith("$") and len(query) > 1
        search_query = query[1:] if is_ticker_query else query
        target_ticker = (
            search_query.upper() if is_ticker_query else None
        )  # Store uppercase for comparison

        logger.info(
            f"Executing DexScreener search_token tool with query: '{query}' "
            f"(interpreted as {'ticker' if is_ticker_query else 'general'} search for '{search_query}'), "
            f"sort_by: {sort_by}"
        )

        # --- Sorting Key Functions ---
        def get_liquidity_usd(pair_dict: dict):
            """Gets the USD liquidity value from a pair dict."""
            return pair_dict.get("liquidity", {}).get("usd", 0) or 0

        def get_volume_h24(pair_dict: dict):
            """Gets the 24-hour volume value from a pair dict."""
            return pair_dict.get("volume", {}).get("h24", 0) or 0

        def get_volume_h6(pair_dict: dict):
            """Gets the 6-hour volume value from a pair dict."""
            return pair_dict.get("volume", {}).get("h6", 0) or 0

        def get_volume_h1(pair_dict: dict):
            """Gets the 1-hour volume value from a pair dict."""
            return pair_dict.get("volume", {}).get("h1", 0) or 0

        def get_volume_m5(pair_dict: dict):
            """Gets the 5-minute volume value from a pair dict."""
            return pair_dict.get("volume", {}).get("m5", 0) or 0

        # --- End Sorting Key Functions ---

        # Use the potentially modified search_query for the API call
        params = {"q": search_query}

        try:
            data, error_details = await self._get(
                path="/latest/dex/search", params=params
            )

            # --- Guard Clauses ---
            if error_details:
                return await self._handle_error_response(error_details)

            if not data:
                logger.error(
                    f"Unexpected condition: _get returned no data and no error_details for query '{query}' (API query: '{search_query}')."
                )
                return json.dumps(
                    {
                        "error": "API call returned empty success response.",
                        "error_type": "empty_success",
                    },
                    indent=2,
                )

            try:
                result = SearchTokenResponseModel.model_validate(data)
            except ValidationError as e:
                return await self._handle_validation_error(e, query, data)

            if result.pairs is None:
                return await self._no_pairs_found_response(
                    query, reason="returned null for pairs field"
                )

            # --- Main Logic ---
            pairs_list = [
                pair.model_dump(exclude_none=True) for pair in result.pairs if pair
            ]

            if not pairs_list:
                # Pass original query for user context
                return await self._no_pairs_found_response(
                    query,
                    reason="returned an empty pairs list or all pairs were invalid/null initially",
                )

            # --- <<< Ticker Filtering Logic >>> ---
            if is_ticker_query and target_ticker:
                original_count = len(pairs_list)
                filtered_pairs = []
                for pair in pairs_list:
                    base_token = pair.get("baseToken", {})
                    symbol = base_token.get("symbol", None)
                    # Case-insensitive comparison
                    if symbol and symbol.upper() == target_ticker:
                        filtered_pairs.append(pair)

                logger.info(
                    f"Filtering for ticker '${target_ticker}'. Found {len(filtered_pairs)} matching pairs out of {original_count} initial results."
                )
                pairs_list = filtered_pairs  # Replace the list with the filtered one

                # If filtering resulted in an empty list, return no pairs found
                if not pairs_list:
                    return await self._no_pairs_found_response(
                        query,
                        reason=f"returned pairs, but none matched the ticker symbol '{target_ticker}' after filtering",
                    )
            # --- <<< End Ticker Filtering Logic >>> ---

            # --- Sorting (Using named functions) ---
            try:
                reverse_sort = True  # Default to descending

                sort_key_func = None
                sort_field_path = None  # For logging clarity

                # Map sort_by value to the correct function and logging path
                if sort_by == "liquidity":
                    sort_key_func = get_liquidity_usd
                    sort_field_path = "liquidity.usd"
                elif sort_by == "volume24h":
                    sort_key_func = get_volume_h24
                    sort_field_path = "volume.h24"
                elif sort_by == "volume6h":
                    sort_key_func = get_volume_h6
                    sort_field_path = "volume.h6"
                elif sort_by == "volume1h":
                    sort_key_func = get_volume_h1
                    sort_field_path = "volume.h1"
                elif sort_by == "volume5m":
                    sort_key_func = get_volume_m5
                    sort_field_path = "volume.m5"
                else:
                    # Defensive default
                    logger.warning(
                        f"Invalid sort_by value '{sort_by}' received, defaulting to liquidity."
                    )
                    sort_key_func = get_liquidity_usd
                    sort_field_path = "liquidity.usd"

                # Perform the sort using the selected function
                pairs_list.sort(key=sort_key_func, reverse=reverse_sort)
                logger.debug(
                    f"Sorted {len(pairs_list)} pairs by {sort_field_path} ({'desc' if reverse_sort else 'asc'})"
                )

            except Exception as sort_err:
                logger.error(
                    f"Failed to perform required sorting for query '{query}' by '{sort_by}'. Error: {sort_err}",
                    exc_info=True,
                )
                # Return unsorted but potentially filtered results if sorting fails
                return json.dumps(
                    {
                        "error": "Failed to sort results as requested.",
                        "error_type": "sorting_error",
                        "details": str(sort_err),
                        "unsorted_results": pairs_list[:MAX_RESULTS_LIMIT],
                    },
                    indent=2,
                )

            # --- Success: Return the sorted (and potentially filtered) and limited list ---
            final_count = min(len(pairs_list), MAX_RESULTS_LIMIT)
            logger.info(
                f"Returning {final_count} pairs for query '{query}' after processing (filtering: {is_ticker_query}, sorting: {sort_by})."
            )
            return json.dumps(
                {
                    "disclaimer": "results may include unofficial or potentially risky tokens. Verify information via official project channels or socials before interacting.",
                    "pairs": pairs_list[:MAX_RESULTS_LIMIT],
                },
                indent=2,
            )

        except Exception as e:
            return await self._handle_unexpected_runtime_error(
                e, query
            )  # Pass query for context

    async def _handle_error_response(self, error_details: dict) -> str:
        """Formats error details (from _get) into a JSON string."""
        if error_details.get("error_type") in [
            "connection_error",
            "parsing_error",
            "unexpected_error",
        ]:
            logger.error(f"DexScreener tool encountered an error: {error_details}")
        else:  # api_error
            logger.warning(f"DexScreener API returned an error: {error_details}")

        # Truncate potentially large fields before returning to user/LLM
        for key in ["details", "response_body"]:
            if (
                isinstance(error_details.get(key), str)
                and len(error_details[key]) > 500
            ):
                error_details[key] = error_details[key][:500] + "... (truncated)"

        return json.dumps(error_details, indent=2)

    async def _handle_validation_error(
        self, e: ValidationError, query: str, data: Any
    ) -> str:
        """Formats validation error details into a JSON string."""
        logger.error(
            f"Failed to validate DexScreener response structure for query '{query}'. Error: {e}. Raw data length: {len(str(data))}",
            exc_info=True,
        )
        # Avoid sending potentially huge raw data back
        return json.dumps(
            {
                "error": "Failed to parse successful DexScreener API response",
                "error_type": "validation_error",
                "details": e.errors(),  # Pydantic errors() is usually concise
            },
            indent=2,
        )

    async def _handle_unexpected_runtime_error(self, e: Exception, query: str) -> str:
        """Formats unexpected runtime exception details into a JSON string."""
        logger.exception(
            f"An unexpected runtime error occurred in search_token tool _arun method for query '{query}': {e}"
        )
        return json.dumps(
            {
                "error": "An unexpected internal error occurred processing the search request",
                "error_type": "runtime_error",
                "details": str(e),
            },
            indent=2,
        )

    async def _no_pairs_found_response(
        self, query: str, reason: str = "returned no matching pairs"
    ) -> str:
        """Generates the standard 'no pairs found' JSON response."""
        logger.info(f"DexScreener search for query '{query}': {reason}.")
        return json.dumps(
            {
                "message": f"No matching pairs found for the query '{query}'. Reason: {reason}.",
                "query": query,
                "pairs": [],
            },
            indent=2,
        )
