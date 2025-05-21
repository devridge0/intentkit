"""
Constants for the CookieFun skills.
"""

# API Base URL
BASE_URL = "https://api.staging.cookie.fun/v3"

# API Endpoints
ENDPOINTS = {
    "sectors": f"{BASE_URL}/sector/list",
    "account_details": f"{BASE_URL}/account/query/one",
    "smart_followers": f"{BASE_URL}/account/smart_followers",
    "search_accounts": f"{BASE_URL}/account/query",
    "account_feed": f"{BASE_URL}/account/feed",
}

# Default Headers
DEFAULT_HEADERS = {
    "Content-Type": "application/json"
} 