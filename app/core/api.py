"""Core API Router.

This module provides the core API endpoints for agent execution and management.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound

from abstracts.engine import AgentMessageInput
from app.core.engine import execute_agent

core_router = APIRouter(prefix="/core", tags=["core"])


class ExecuteRequest(BaseModel):
    """Request model for agent execution endpoint.

    Attributes:
        aid (str): Agent ID to execute
        message (AgentMessageInput): Input message containing text and optional images
        thread_id (str): Thread ID for conversation tracking
    """

    aid: str
    message: AgentMessageInput
    thread_id: str


@core_router.post("/execute")
async def execute(request: ExecuteRequest) -> list[str]:
    """Execute an agent with the given input and return response lines.

    Args:
        request (ExecuteRequest): The execution request containing agent ID, message, and thread ID

    Returns:
        list[str]: Formatted response lines from agent execution

    Raises:
        HTTPException:
            - 400: If input parameters are invalid (empty aid, thread_id, or message text)
            - 404: If agent not found
            - 500: For other server-side errors
    """
    # Validate input parameters
    if not request.aid or not request.aid.strip():
        raise HTTPException(status_code=400, detail="Agent ID cannot be empty")
    if not request.thread_id or not request.thread_id.strip():
        raise HTTPException(status_code=400, detail="Thread ID cannot be empty")
    if not request.message.text or not request.message.text.strip():
        raise HTTPException(status_code=400, detail="Message text cannot be empty")

    try:
        return await execute_agent(request.aid, request.message, request.thread_id)
    except NoResultFound:
        raise HTTPException(status_code=404, detail=f"Agent {request.aid} not found")
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
