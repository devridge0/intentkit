"""IntentKit Web API Router."""

import logging
import secrets
from typing import List

from epyxid import XID
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
    status,
)
from fastapi.responses import PlainTextResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from langchain_core.messages import BaseMessage
from sqlmodel import desc, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.engine import execute_agent, thread_stats
from models.agent import Agent, AgentQuota
from models.chat import (
    AuthorType,
    ChatMessage,
    ChatMessageRequest,
)
from models.db import get_db

# init logger
logger = logging.getLogger(__name__)

chat_router = APIRouter()
chat_router_readonly = APIRouter()

# Add security scheme
security = HTTPBasic()


# Add credentials checker
def verify_debug_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    from app.config.config import config

    if not config.debug_auth_enabled:
        return None

    if not config.debug_username or not config.debug_password:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Debug credentials not configured",
        )

    is_username_correct = secrets.compare_digest(
        credentials.username.encode("utf8"), config.debug_username.encode("utf8")
    )
    is_password_correct = secrets.compare_digest(
        credentials.password.encode("utf8"), config.debug_password.encode("utf8")
    )

    if not (is_username_correct and is_password_correct):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@chat_router.get(
    "/debug/{agent_id}/chats/{chat_id}",
    tags=["Debug"],
    response_model=List[BaseMessage],
    dependencies=[Depends(verify_debug_credentials)],
    operation_id="debug_chat_history",
    summary="Chat History",
)
async def chat_history(
    agent_id: str = Path(..., description="Agent id"),
    chat_id: str = Path(..., description="Chat id"),
) -> List[BaseMessage]:
    return await thread_stats(agent_id, chat_id)


@chat_router.get(
    "/{aid}/chat", tags=["Debug"], response_class=PlainTextResponse, deprecated=True
)
@chat_router.get(
    "/debug/{aid}/chat",
    tags=["Debug"],
    response_class=PlainTextResponse,
    dependencies=[Depends(verify_debug_credentials)],
    operation_id="debug_chat",
    summary="Chat",
)
async def debug_chat(
    request: Request,
    aid: str = Path(..., description="Agent ID"),
    q: str = Query(None, description="Query string"),
    debug: bool = Query(None, description="Enable debug mode"),
    thread: str = Query(
        None, description="Thread ID for conversation tracking", deprecated=True
    ),
    chat_id: str = Query(None, description="Chat ID for conversation tracking"),
) -> str:
    """Debug mode: Chat with an AI agent.

    **Process Flow:**
    1. Validates agent quota
    2. Creates a thread-specific context
    3. Executes the agent with the query
    4. Updates quota usage

    **Parameters:**
    * `aid` - Agent ID
    * `q` - User's input query
    * `debug` - Enable debug mode (show whole skill response)
    * `thread` - Thread ID for conversation tracking

    **Returns:**
    * `str` - Formatted chat response

    **Raises:**
    * `404` - Agent not found
    * `429` - Quota exceeded
    * `500` - Internal server error
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
    user_input = ChatMessage(
        id=str(XID()),
        agent_id=aid,
        chat_id=chat_id,
        author_id="debug",
        author_type=AuthorType.WEB,
        message=q,
    )

    # Execute agent and get response
    messages = await execute_agent(user_input, debug=debug)

    resp = f"Agent ID:\t{aid}\n\nChat ID:\t{chat_id}\n\n-------------------\n\n"
    resp += "[ Input: ]\n\n"
    resp += f" {q} \n\n-------------------\n\n"
    for message in messages:
        if message.cold_start_cost:
            resp += "[ Agent cold start ... ]\n"
            resp += f"\n------------------- start cost: {message.cold_start_cost:.3f} seconds\n\n"
        if message.author_type == AuthorType.SKILL:
            resp += "[ Calling skills ... ]\n\n"
            for skill_call in message.skill_calls:
                resp += f" {skill_call['name']}: {skill_call['parameters']}\n"
                if skill_call["success"]:
                    resp += f"  Success: {skill_call.get('response', '')}\n"
                else:
                    resp += f"  Failed: {skill_call.get('error_message', '')}\n"
            resp += (
                f"\n------------------- skill cost: {message.time_cost:.3f} seconds\n\n"
            )
        if message.author_type == AuthorType.AGENT:
            resp += "[ Agent: ]\n\n"
            resp += f" {message.message}\n"
            resp += (
                f"\n------------------- agent cost: {message.time_cost:.3f} seconds\n\n"
            )

    resp += "Total time cost: {:.3f} seconds".format(
        sum([message.time_cost + message.cold_start_cost for message in messages])
    )

    # reduce message quota
    await quota.add_message()

    return resp


@chat_router_readonly.get(
    "/agents/{aid}/chat/history",
    tags=["Chat"],
    response_model=List[ChatMessage],
    operation_id="get_chat_history",
    summary="Chat History",
)
async def get_chat_history(
    aid: str = Path(..., description="Agent ID"),
    chat_id: str = Query(..., description="Chat ID to get history for"),
    db: AsyncSession = Depends(get_db),
) -> List[ChatMessage]:
    """Get chat history for a specific chat.

    **Special Chat IDs:**
    * `autonomous` - Autonomous log
    * `public` - Public chat history in X and TG groups
    * `owner` - Owner chat history (coming soon)

    **Parameters:**
    * `aid` - Agent ID
    * `chat_id` - Chat ID to get history for

    **Returns:**
    * `List[ChatMessage]` - List of chat messages, ordered by creation time ascending

    **Raises:**
    * `404` - Agent not found
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


@chat_router.get(
    "/agents/{aid}/chat/retry",
    tags=["Chat"],
    response_model=ChatMessage,
    deprecated=True,
    summary="Retry Chat",
)
async def retry_chat_deprecated(
    aid: str = Path(..., description="Agent ID"),
    chat_id: str = Query(..., description="Chat ID to retry last message"),
    db: AsyncSession = Depends(get_db),
) -> ChatMessage:
    """Retry the last message in a chat.

    If the last message is from the agent, return it directly.
    If the last message is from a user, generate a new agent response.

    **Parameters:**
    * `aid` - Agent ID
    * `chat_id` - Chat ID to retry

    **Returns:**
    * `ChatMessage` - Agent's response message

    **Raises:**
    * `404` - Agent not found or no messages found
    * `429` - Quota exceeded
    * `500` - Internal server error
    """
    # Get agent and check if exists
    agent = await Agent.get(aid)
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
    if (
        last_message.author_type == AuthorType.AGENT
        or last_message.author_type == AuthorType.SYSTEM
    ):
        return last_message

    if last_message.author_type == AuthorType.SKILL:
        error_message = ChatMessage(
            id=str(XID()),
            agent_id=aid,
            chat_id=chat_id,
            author_id=aid,
            author_type=AuthorType.SYSTEM,
            message="You were interrupted after executing a skill. Please retry with caution to avoid repeating the skill.",
            attachments=None,
        )
        await error_message.save()
        return error_message

    # If last message is from user, generate a new agent response
    return await create_chat_deprecated()


@chat_router.put(
    "/agents/{aid}/chat/retry/v2",
    tags=["Chat"],
    response_model=list[ChatMessage],
    operation_id="retry_chat",
    summary="Retry Chat",
)
async def retry_chat(
    aid: str = Path(..., description="Agent ID"),
    chat_id: str = Query(..., description="Chat ID to retry last message"),
    db: AsyncSession = Depends(get_db),
) -> list[ChatMessage]:
    """Retry the last message in a chat.

    If the last message is from the agent, return it directly.
    If the last message is from a user, generate a new agent response.

    **Parameters:**
    * `aid` - Agent ID
    * `chat_id` - Chat ID to retry

    **Returns:**
    * `List[ChatMessage]` - List of chat messages including the retried response

    **Raises:**
    * `404` - Agent not found or no messages found
    * `429` - Quota exceeded
    * `500` - Internal server error
    """
    # Get agent and check if exists
    agent = await Agent.get(aid)
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
    if (
        last_message.author_type == AuthorType.AGENT
        or last_message.author_type == AuthorType.SYSTEM
    ):
        return [last_message]

    if last_message.author_type == AuthorType.SKILL:
        error_message = ChatMessage(
            id=str(XID()),
            agent_id=aid,
            chat_id=chat_id,
            author_id=aid,
            author_type=AuthorType.SYSTEM,
            message="You were interrupted after executing a skill. Please retry with caution to avoid repeating the skill.",
            attachments=None,
        )
        await error_message.save()
        return [last_message, error_message]

    # If last message is from user, generate a new agent response
    return await create_chat()


@chat_router.post(
    "/agents/{aid}/chat",
    tags=["Chat"],
    response_model=ChatMessage,
    deprecated=True,
    summary="Chat",
)
async def create_chat_deprecated(
    request: ChatMessageRequest,
    aid: str = Path(..., description="Agent ID"),
) -> ChatMessage:
    """Create a private chat message and get agent's response.

    **Process Flow:**
    1. Validates agent quota
    2. Creates a thread-specific context
    3. Executes the agent with the query
    4. Updates quota usage
    5. Saves both input and output messages

    > **Note:** This is for internal/private use and may have additional features or fewer
    > restrictions compared to the public endpoint.

    **Parameters:**
    * `aid` - Agent ID
    * `request` - Chat message request object

    **Returns:**
    * `List[ChatMessage]` - List of chat messages including both user input and agent response

    **Raises:**
    * `404` - Agent not found
    * `429` - Quota exceeded
    * `500` - Internal server error
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

    try:
        # Execute agent
        response_messages = await execute_agent(user_message)

        # Update quota
        await quota.add_message()

        return response_messages[-1]

    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.post(
    "/agents/{aid}/chat/v2",
    tags=["Chat"],
    response_model=list[ChatMessage],
    operation_id="chat",
    summary="Chat",
)
async def create_chat(
    request: ChatMessageRequest,
    aid: str = Path(..., description="Agent ID"),
) -> list[ChatMessage]:
    """Create a chat message and get agent's response.

    **Process Flow:**
    1. Validates agent quota
    2. Creates a thread-specific context
    3. Executes the agent with the query
    4. Updates quota usage
    5. Saves both input and output messages

    > **Note:** This is the public-facing endpoint with appropriate rate limiting
    > and security measures.

    **Parameters:**
    * `aid` - Agent ID
    * `request` - Chat message request object

    **Returns:**
    * `List[ChatMessage]` - List of chat messages including both user input and agent response

    **Raises:**
    * `404` - Agent not found
    * `429` - Quota exceeded
    * `500` - Internal server error
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

    try:
        # Execute agent
        response_messages = await execute_agent(user_message)

        # Update quota
        await quota.add_message()

        return response_messages

    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(e))
