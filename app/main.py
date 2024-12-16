import logging
import sys
import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Path, Request, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from langchain_core.messages import HumanMessage
from sqlalchemy.orm import Session

from app.ai import initialize_agent
from app.config import config
from app.db import init_db,get_db,Agent

if config.env == "local":
    # Set up logging configuration
    logging.basicConfig()
    logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

# Global variable to cache all agent executors
executors = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(**config.db)
    logging.info("API server start")
    yield
    # Clean up
    print("Cleaning up and shutdown...")

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/{aid}/chat", response_class=PlainTextResponse)
async def chat(
        request: Request,
        aid: str = Path(..., description="instance id"),
        q: str = Query(None, description="Query string"),
        db: Session = Depends(get_db)):
    # Run agent with the user's input in chat mode
    # get thread_id from request ip
    thread_id = request.client.host
    config = {"configurable": {"thread_id": thread_id}}
    logging.debug(f"thread id: {thread_id}")
    print(aid)
    if aid not in executors:
        agent = db.query(Agent).filter(Agent.id == aid).first()
        if agent is None:
            raise HTTPException(status_code=404, detail="Agent not found")
        executors[aid] = initialize_agent(agent)
    executor = executors[aid]
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

# Tmp unused
# Autonomous Mode
def run_autonomous_mode(agent_executor, config, interval=180):
    """Run the agent autonomously with specified intervals."""
    print("Starting autonomous mode...")
    while True:
        try:
            # Provide instructions autonomously
            thought = (
                "Get account mentions for the currently authenticated Twitter (X) user context."
                "If there is no mention, post a new tweet on Twitter,"
                "saying you are waiting for mentions, every 3 minutes you will reply one person."
                "If you have a mention, pickup the first one, reply to the mention."
            )

            # Run agent in autonomous mode
            for chunk in agent_executor.stream(
                {"messages": [HumanMessage(content=thought)]}, config
            ):
                if "agent" in chunk:
                    print(chunk["agent"]["messages"][0].content)
                elif "tools" in chunk:
                    print(chunk["tools"]["messages"][0].content)
                print("-------------------")

            # Wait before the next action
            time.sleep(interval)

        except KeyboardInterrupt:
            print("Goodbye Agent!")
            sys.exit(0)

