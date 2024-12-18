import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Path, Request, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from langchain_core.messages import HumanMessage
from sqlmodel import Session, select

from app.ai import initialize_agent
from app.config import config
from app.db import init_db,get_db,Agent

if config.env == "local":
    # Set up logging configuration
    logging.basicConfig()
    logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

# Global variable to cache all agent executors
agents = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # this will run before the API server start
    init_db(**config.db)
    logging.info("API server start")
    yield
    # Clean up will run after the API server shutdown
    print("Cleaning up and shutdown...")

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/{aid}/chat", response_class=PlainTextResponse)
def chat(
        request: Request,
        aid: str = Path(..., description="instance id"),
        q: str = Query(None, description="Query string"),
        db: Session = Depends(get_db)):
    # Run agent with the user's input in chat mode
    # get thread_id from request ip
    thread_id = f'{aid}-{request.client.host}'
    config = {"configurable": {"thread_id": thread_id}}
    logging.debug(f"thread id: {thread_id}")
    print(aid)
    if aid not in agents:
        agent = db.exec(select(Agent).filter(Agent.id == aid)).first()
        if agent is None:
            raise HTTPException(status_code=404, detail="Agent not found")
        agents[aid] = initialize_agent(agent.id)
    executor = agents[aid]
    resp = []
    for chunk in executor.stream(
        {"messages": [HumanMessage(content=q)]}, config
    ):
        if "agent" in chunk:
            resp.append(chunk["agent"]["messages"][0].content)
        elif "tools" in chunk:
            resp.append(chunk["tools"]["messages"][0].content)
        resp.append("-------------------")
    print("\n".join(resp))
    return "\n".join(resp)

@app.post("/create", status_code=201)
def create_agent(agent: Agent, db: Session = Depends(get_db)) -> Agent:
    """Create a new agent, if it exists, just update it"""
    agent.create_or_update(db)
    return agent
