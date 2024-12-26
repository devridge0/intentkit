"""IntentKit REST API Server.

This module implements the REST API for IntentKit, providing endpoints for:
- Agent chat interactions
- Agent creation and management
- Health monitoring

The API uses FastAPI for high performance and automatic OpenAPI documentation.
Database connections and agent state are managed throughout the application lifecycle.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request
from fastapi.responses import PlainTextResponse
from sqlmodel import Session, select

from app.config.config import config
from app.core.ai import execute_agent, initialize_agent
from app.models.db import Agent, AgentQuota, get_db, init_db
from utils.logging import JsonFormatter

# init logger
logger = logging.getLogger(__name__)

# Configure uvicorn access logger to use our JSON format in non-local env
if config.env != "local" and not config.debug:
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers = []  # Remove default handlers
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    uvicorn_access.addHandler(handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle.

    This context manager:
    1. Initializes database connection
    2. Performs any necessary startup tasks
    3. Handles graceful shutdown

    Args:
        app: FastAPI application instance
    """
    # This part will run before the API server start
    init_db(**config.db)
    logger.info("API server start")
    yield
    # Clean up will run after the API server shutdown
    logger.info("Cleaning up and shutdown...")


app = FastAPI(lifespan=lifespan)


@app.get("/health", include_in_schema=False)
async def health_check():
    """Check API server health.

    Returns:
        dict: Health status
    """
    return {"status": "healthy"}


@app.get("/{aid}/chat", response_class=PlainTextResponse)
def chat(
    request: Request,
    aid: str = Path(..., description="instance id"),
    q: str = Query(None, description="Query string"),
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

    # get thread_id from request ip
    thread_id = f"{aid}-{request.client.host}"
    logger.debug(f"thread id: {thread_id}")

    # Execute agent and get response
    resp = execute_agent(aid, q, thread_id)

    logger.info(resp)
    # reduce message quota
    quota.add_message(db)
    return "\n".join(resp)


@app.post("/agents", status_code=201)
def create_agent(agent: Agent, db: Session = Depends(get_db)) -> Agent:
    """Create or update an agent.

    This endpoint:
    1. Validates agent ID format
    2. Creates or updates agent configuration
    3. Reinitializes agent if already in cache
    4. Masks sensitive data in response

    Args:
        agent: Agent configuration
        db: Database session

    Returns:
        Agent: Updated agent configuration

    Raises:
        HTTPException:
            - 400: Invalid agent ID format
            - 500: Database error
    """
    if not all(c.islower() or c.isdigit() or c == "-" for c in agent.id):
        raise HTTPException(
            status_code=400,
            detail="Agent ID must contain only lowercase letters, numbers, and hyphens.",
        )
    agent.create_or_update(db)
    # Get the latest agent from the database
    latest_agent = db.exec(select(Agent).filter(Agent.id == agent.id)).one()
    latest_agent.cdp_wallet_data = "forbidden"
    if latest_agent.skill_sets is not None:
        for key in latest_agent.skill_sets:
            latest_agent.skill_sets[key] = {}
    # TODO: change here when multiple instances deploy
    initialize_agent(agent.id)
    return latest_agent
