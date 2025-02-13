"""Core API Router.

This module provides the core API endpoints for agent execution and management.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound

from abstracts.engine import AgentMessageInput
from app.core.engine import execute_agent
from models.chat import ChatMessage

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
async def execute(message: ChatMessage, debug: bool = False) -> list[ChatMessage]:
    """Execute an agent with the given input and return response lines.

    Args:
        message (ChatMessage): The chat message containing agent_id, chat_id and message content
        debug (bool): Enable debug mode

    Returns:
        list[str]: Formatted response lines from agent execution

    Raises:
        HTTPException:
            - 400: If input parameters are invalid
            - 404: If agent not found
            - 500: For other server-side errors
    """
    # Validate input parameters
    if not message.agent_id or not message.agent_id.strip():
        raise HTTPException(status_code=400, detail="Agent ID cannot be empty")
    if not message.chat_id or not message.chat_id.strip():
        raise HTTPException(status_code=400, detail="Chat ID cannot be empty")
    if not message.message or not message.message.strip():
        raise HTTPException(status_code=400, detail="Message text cannot be empty")

    try:
        return await execute_agent(message, debug)
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail=f"Agent {message.agent_id} not found"
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
