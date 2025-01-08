"""IntentKit Web API Router."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi.responses import PlainTextResponse
from sqlmodel import Session

from abstracts.engine import AgentMessageInput
from app.config.config import config
from app.core.engine import execute_agent
from app.models.agent import AgentQuota
from app.models.db import get_db

# init logger
logger = logging.getLogger(__name__)

chat_router = APIRouter()


@chat_router.get("/{aid}/chat", response_class=PlainTextResponse)
def chat(
    request: Request,
    aid: str = Path(..., description="instance id"),
    q: str = Query(None, description="Query string"),
    debug: bool = Query(None, description="Enable debug mode"),
    thread: str = Query(None, description="Thread ID for conversation tracking"),
    db: Session = Depends(get_db),
):
    """Chat with an AI agent.

    This endpoint:
    1. Validates agent quota
    2. Creates a thread-specific context
    3. Executes the agent with the query
    4. Updates quota usage

    Args:
        request: FastAPI request object
        aid: Agent ID
        q: User's input query
        debug: Enable debug mode
        thread: Thread ID for conversation tracking
        db: Database session

    Returns:
        str: Formatted chat response

    Raises:
        HTTPException:
            - 404: Agent not found
            - 429: Quota exceeded
            - 500: Internal server error
    """
    # check if the agent quota is exceeded
    quota = AgentQuota.get(aid, db)
    if not quota.has_message_quota(db):
        raise HTTPException(
            status_code=429,
            detail=(
                "Message quota exceeded. Please upgrade your plan. "
                f"Daily: {quota.message_count_daily}/{quota.message_limit_daily}, "
                f"Monthly: {quota.message_count_monthly}/{quota.message_limit_monthly}, "
                f"Total: {quota.message_count_total}/{quota.message_limit_total}"
            ),
        )

    # get thread_id from query or request ip
    thread_id = (
        f"{aid}-{thread}" if thread is not None else f"{aid}-{request.client.host}"
    )
    logger.debug(f"thread id: {thread_id}")

    debug = debug if debug is not None else config.debug_resp

    # Execute agent and get response
    resp = execute_agent(aid, AgentMessageInput(text=q), thread_id, debug=debug)

    logger.info(resp)
    # reduce message quota
    quota.add_message(db)
    return "\n".join(resp)
