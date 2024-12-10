import sys
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.responses import PlainTextResponse
from langchain_core.messages import HumanMessage

from app.ai import initialize_agent

executor = None
config = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    global executor,config
    executor,config = initialize_agent()
    print(executor)
    yield
    # Clean up
    print("Cleaning up and shutdown...")

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/chat", response_class=PlainTextResponse)
async def chat(q: str = Query(None, description="Query string")):
    print(executor)
    # Run agent with the user's input in chat mode
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

