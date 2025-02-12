"""IntentKit Web API Router."""

import logging
from typing import List

from epyxid import XID
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi.responses import PlainTextResponse
from sqlmodel import desc, select
from sqlmodel.ext.asyncio.session import AsyncSession

from abstracts.engine import AgentMessageInput
from app.config.config import config
from app.core.engine import execute_agent
from models.agent import Agent, AgentQuota
from models.chat import (
    AuthorType,
    ChatMessage,
    ChatMessageAttachmentType,
    ChatMessageRequest,
)
from models.db import get_db

# init logger
logger = logging.getLogger(__name__)

chat_router = APIRouter()
chat_router_readonly = APIRouter()


@chat_router.get("/{aid}/chat", tags=["Debug"], response_class=PlainTextResponse)
async def chat(
    request: Request,
    aid: str = Path(..., description="instance id"),
    q: str = Query(None, description="Query string"),
    debug: bool = Query(None, description="Enable debug mode"),
    thread: str = Query(None, description="Thread ID for conversation tracking"),
    db: AsyncSession = Depends(get_db),
):
    """Debug mode: Chat with an AI agent.

    This endpoint:
    1. Validates agent quota
    2. Creates a thread-specific context
    3. Executes the agent with the query
    4. Updates quota usage

    Args:
      - request: FastAPI request object
      - aid: Agent ID
      - q: User's input query
      - debug: Enable debug mode
      - thread: Thread ID for conversation tracking
      - db: Database session

    Returns:
      - str: Formatted chat response

    Raises:
      - HTTPException:
          - 404: Agent not found
          - 429: Quota exceeded
          - 500: Internal server error
    """
    if not q:
        raise HTTPException(status_code=400, detail="Query string cannot be empty")

    # Get agent and validate quota
    agent = await Agent.get(aid)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {aid} not found")

    # Check quota
    quota = await AgentQuota.get(aid)
    if quota and not quota.has_message_quota():
        raise HTTPException(status_code=429, detail="Quota exceeded")

    # get thread_id from request ip
    chat_id = thread if thread else request.client.host
    message = ChatMessage(
        id=str(XID()),
        agent_id=aid,
        chat_id=chat_id,
        author_id="debug",
        author_type=AuthorType.WEB,
        message=q,
    )

    debug = debug if debug is not None else config.debug_resp

    # Execute agent and get response
    resp = await execute_agent(message, debug=debug)

    # only log if not in debug mode
    if not config.debug_resp:
        logger.info(resp)
    # reduce message quota
    await quota.add_message()
    return "\n".join(resp)


@chat_router_readonly.get(
    "/agents/{aid}/chat/history", tags=["Chat"], response_model=List[ChatMessage]
)
async def get_chat_history(
    aid: str = Path(..., description="Agent ID"),
    chat_id: str = Query(..., description="Chat ID to get history for"),
    db: AsyncSession = Depends(get_db),
) -> List[ChatMessage]:
    """Get chat history for a specific chat.

    Args:
      - aid: Agent ID
      - chat_id: Chat ID to get history for
      - db: Database session

    Returns:
      - List[ChatMessage]: List of chat messages, ordered by creation time ascending

    Raises:
      - HTTPException:
          - 404: Agent not found
    """
    # Get agent and check if exists
    result = await db.exec(select(Agent).where(Agent.id == aid))
    agent = result.first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Get chat messages (last 50 in DESC order)
    result = await db.exec(
        select(ChatMessage)
        .where(ChatMessage.agent_id == aid, ChatMessage.chat_id == chat_id)
        .order_by(desc(ChatMessage.created_at))
        .limit(50)
    )
    messages = result.all()

    # Reverse messages to get chronological order
    messages.reverse()

    return messages


@chat_router.get("/agents/{aid}/chat/retry", tags=["Chat"], response_model=ChatMessage)
async def retry_chat(
    aid: str = Path(..., description="Agent ID"),
    chat_id: str = Query(..., description="Chat ID to retry last message"),
    db: AsyncSession = Depends(get_db),
) -> ChatMessage:
    """Retry the last message in a chat.

    If the last message is from the agent, return it directly.
    If the last message is from a user, generate a new agent response.

    Args:
      - aid: Agent ID
      - chat_id: Chat ID to retry
      - db: Database session

    Returns:
      - ChatMessage: Agent's response message

    Raises:
      - HTTPException:
          - 404: Agent not found or no messages found
          - 429: Quota exceeded
          - 500: Internal server error
    """
    # Get agent and check if exists
    result = await db.exec(select(Agent).where(Agent.id == aid))
    agent = result.first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Get last message
    result = await db.exec(
        select(ChatMessage)
        .where(ChatMessage.agent_id == aid, ChatMessage.chat_id == chat_id)
        .order_by(desc(ChatMessage.created_at))
        .limit(1)
    )
    last_message = result.first()

    if not last_message:
        raise HTTPException(status_code=404, detail="No messages found")

    # If last message is from agent, return it
    if last_message.author_type == AuthorType.AGENT:
        return last_message

    # Check quota before generating new response
    quota = await AgentQuota.get(aid)
    if not quota.has_message_quota():
        raise HTTPException(status_code=429, detail="Message quota exceeded")

    try:
        # Extract image URLs from last message
        image_urls = [
            attachment.url
            for attachment in (last_message.attachments or [])
            if attachment.type == ChatMessageAttachmentType.IMAGE
        ]

        # Execute agent
        agent_input = AgentMessageInput(text=last_message.message, images=image_urls)
        response_lines = await execute_agent(aid, agent_input, f"{aid}-{chat_id}")

        # Create agent's response message
        response_message = ChatMessage(
            id=str(XID()),
            agent_id=aid,
            chat_id=chat_id,
            author_id=aid,
            author_type=AuthorType.AGENT,
            message="\n".join(response_lines),
            attachments=None,
        )
        db.add(response_message)

        # Update quota
        await quota.add_message()
        await db.commit()
        await db.refresh(response_message)

        return response_message

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.post("/agents/{aid}/chat", tags=["Chat"], response_model=ChatMessage)
async def create_chat(
    request: ChatMessageRequest,
    aid: str = Path(..., description="Agent ID"),
    db: AsyncSession = Depends(get_db),
) -> ChatMessage:
    """Create a chat message and get agent's response.

    This endpoint:
    1. Validates agent quota
    2. Creates a thread-specific context
    3. Executes the agent with the query
    4. Updates quota usage
    5. Saves both input and output messages

    Args:
      - request: Chat message request
      - aid: Agent ID
      - db: Database session

    Returns:
      - ChatMessage: Agent's response message

    Raises:
      - HTTPException:
          - 404: Agent not found
          - 429: Quota exceeded
          - 500: Internal server error
    """
    # Get agent and validate quota
    agent = await Agent.get(aid)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {aid} not found")

    # Check quota
    quota = await AgentQuota.get(aid)
    if quota and not quota.has_message_quota():
        raise HTTPException(status_code=429, detail="Quota exceeded")

    # Create user message
    user_message = ChatMessage(
        id=str(XID()),
        agent_id=aid,
        chat_id=request.chat_id,
        author_id=request.user_id,
        author_type=AuthorType.WEB,
        message=request.message,
        attachments=request.attachments,
    )
    db.add(user_message)
    await db.commit()

    try:
        # Execute agent
        response_lines = await execute_agent(user_message)

        # Create agent's response message
        response_message = ChatMessage(
            id=str(XID()),
            agent_id=aid,
            chat_id=request.chat_id,
            author_id=aid,
            author_type=AuthorType.AGENT,
            message="\n".join(response_lines),
            attachments=None,
        )
        db.add(response_message)

        # Update quota
        await quota.add_message()
        await db.commit()
        await db.refresh(response_message)

        return response_message

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
