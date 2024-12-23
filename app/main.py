import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Path, Request, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from langchain_core.messages import HumanMessage
from sqlmodel import Session, select

from app.ai import initialize_agent, execute_agent
from app.config import config
from app.db import init_db, get_db, Agent, AgentQuota
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
    # This part will run before the API server start
    init_db(**config.db)
    logger.info("API server start")
    yield
    # Clean up will run after the API server shutdown
    logger.info("Cleaning up and shutdown...")


app = FastAPI(lifespan=lifespan)


@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "healthy"}


@app.get("/{aid}/chat", response_class=PlainTextResponse)
def chat(
    request: Request,
    aid: str = Path(..., description="instance id"),
    q: str = Query(None, description="Query string"),
    db: Session = Depends(get_db),
):
    """Run agent with the user's input in chat mode"""
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

    # reduce message quota
    quota.add_message(db)
    return "\n".join(resp)


@app.post("/agents", status_code=201)
def create_agent(agent: Agent, db: Session = Depends(get_db)) -> Agent:
    """Create a new agent, if it exists, just update it"""
    if not all(c.islower() or c.isdigit() or c == "-" for c in agent.id):
        raise HTTPException(
            status_code=400,
            detail="Agent ID must contain only lowercase letters, numbers, and hyphens.",
        )
    agent.create_or_update(db)
    # Get the latest agent from the database
    latest_agent = db.exec(select(Agent).filter(Agent.id == agent.id)).one()
    latest_agent.cdp_wallet_data = "forbidden"
    for key in latest_agent.skill_sets:
        latest_agent.skill_sets[key] = {}
    # TODO: change here when multiple instances deploy
    initialize_agent(agent.id)
    return latest_agent
