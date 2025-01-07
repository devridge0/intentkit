"""Core Client Module.

This module provides client functions for core API endpoints with environment-aware routing.
"""

import httpx

from abstracts.engine import AgentMessageInput
from app.config.config import config
from app.core.engine import execute_agent as local_execute_agent


def execute_agent(aid: str, message: AgentMessageInput, thread_id: str) -> list[str]:
    """Execute an agent with environment-aware routing.

    In local environment, directly calls the local execute_agent function.
    In other environments, makes HTTP request to the core API endpoint.

    Args:
        aid (str): Agent ID to execute
        message (AgentMessageInput): Input message containing text and optional images
        thread_id (str): Thread ID for conversation tracking

    Returns:
        list[str]: Formatted response lines from agent execution

    Raises:
        HTTPException: For API errors (in non-local environment)
        Exception: For other execution errors
    """
    if config.env == "local":
        return local_execute_agent(aid, message, thread_id)

    # Make HTTP request in non-local environment
    url = f"{config.internal_base_url}/core/execute"
    response = httpx.post(
        url,
        json={
            "aid": aid,
            "message": message.model_dump(),
            "thread_id": thread_id,
        },
        timeout=100,
    )
    response.raise_for_status()
    return response.json()
