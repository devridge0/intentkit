import json
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramUnauthorizedError
from cdp import Wallet
from cdp.cdp import Cdp
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config.config import config
from app.core.engine import clean_agent_memory
from models.agent import Agent, AgentData, AgentResponse
from models.db import get_db
from utils.middleware import create_jwt_middleware
from utils.slack_alert import send_slack_message

admin_router_readonly = APIRouter()
admin_router = APIRouter()

# Create JWT middleware with admin config
verify_jwt = create_jwt_middleware(config.admin_auth_enabled, config.admin_jwt_secret)

logger = logging.getLogger(__name__)


@admin_router.post("/agents", tags=["Agent"], status_code=201)
async def create_agent(
    request: Request,
    agent: Agent = Body(Agent, description="Agent configuration"),
    subject: str = Depends(verify_jwt),
) -> AgentResponse:
    """Create or update an agent.

    This endpoint:
    1. Validates agent ID format
    2. Creates or updates agent configuration
    3. Reinitializes agent if already in cache
    4. Masks sensitive data in response

    Args:
      - agent: Agent configuration
      - db: Database session

    Returns:
      - AgentResponse: Updated agent configuration with additional processed data

    Raises:
      - HTTPException:
          - 400: Invalid agent ID format
          - 500: Database error
    """
    body = await request.body()
    logger.info(f"Raw request body for create_agent: {body.decode()}")
    if subject:
        agent.owner = subject

    # Get the latest agent from create_or_update
    latest_agent, is_new = await agent.create_or_update()

    has_wallet = False
    agent_data = None
    if is_new:
        message = "Agent Created"
    else:
        message = "Agent Updated"
        agent_data = await AgentData.get(latest_agent.id)
        if agent_data and agent_data.cdp_wallet_data:
            has_wallet = True
            wallet_data = json.loads(agent_data.cdp_wallet_data)
    if not has_wallet:
        # create the wallet
        Cdp.configure(
            api_key_name=config.cdp_api_key_name,
            private_key=config.cdp_api_key_private_key.replace("\\n", "\n"),
        )
        wallet = Wallet.create(network_id=latest_agent.cdp_network_id)
        wallet_data = wallet.export_data().to_dict()
        wallet_data["default_address_id"] = wallet.default_address.address_id
        if not agent_data:
            agent_data = AgentData(
                id=latest_agent.id, cdp_wallet_data=json.dumps(wallet_data)
            )
        else:
            agent_data.cdp_wallet_data = json.dumps(wallet_data)
        await agent_data.save()
        logger.info(
            "Wallet created for agent %s: %s",
            latest_agent.id,
            wallet_data["default_address_id"],
        )

    if agent.telegram_config:
        tg_bot_token = agent.telegram_config.get("token")
        if tg_bot_token:
            try:
                bot = Bot(token=tg_bot_token)
                bot_info = await bot.get_me()
                agent_data.telegram_id = str(bot_info.id)
                agent_data.telegram_username = bot_info.username
                agent_data.telegram_name = bot_info.first_name
                await agent_data.save()
                try:
                    await bot.close()
                except Exception as e:
                    logger.info(
                        f"failed to close bot with token {tg_bot_token} connection: {e}"
                    )
            except TelegramUnauthorizedError as req_err:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unauthorized err getting telegram bot username with token {tg_bot_token}: {req_err}",
                )
            except Exception as e:
                raise Exception(
                    f"Error getting telegram bot username with token {tg_bot_token}: {e}"
                )

    # Send Slack notification
    send_slack_message(
        message,
        attachments=[
            {
                "color": "good",
                "fields": [
                    {"title": "ENV", "short": True, "value": config.env},
                    {"title": "Total", "short": True, "value": await Agent.count()},
                    {"title": "ID", "short": True, "value": latest_agent.id},
                    {"title": "Name", "short": True, "value": latest_agent.name},
                    {"title": "Model", "short": True, "value": latest_agent.model},
                    {
                        "title": "Enso Enabled",
                        "short": True,
                        "value": str(latest_agent.enso_enabled),
                    },
                    {
                        "title": "CDP Enabled",
                        "short": True,
                        "value": str(latest_agent.cdp_enabled),
                    },
                    {
                        "title": "CDP Network",
                        "short": True,
                        "value": latest_agent.cdp_network_id or "Default",
                    },
                    {
                        "title": "Autonomous",
                        "short": True,
                        "value": str(latest_agent.autonomous_enabled),
                    },
                    {
                        "title": "Autonomous Interval",
                        "short": True,
                        "value": str(latest_agent.autonomous_minutes),
                    },
                    {
                        "title": "Twitter Entrypoint",
                        "short": True,
                        "value": str(latest_agent.twitter_entrypoint_enabled),
                    },
                    {
                        "title": "Telegram Entrypoint",
                        "short": True,
                        "value": str(latest_agent.telegram_entrypoint_enabled),
                    },
                    {
                        "title": "Twitter Skills",
                        "value": str(latest_agent.twitter_skills),
                    },
                    {
                        "title": "CDP Wallet Address",
                        "value": wallet_data.get("default_address_id"),
                    },
                ],
            }
        ],
    )

    # Mask sensitive data in response
    if latest_agent.skill_sets is not None:
        for key in latest_agent.skill_sets:
            latest_agent.skill_sets[key] = {}

    # Convert to AgentResponse
    return AgentResponse.from_agent(latest_agent, agent_data)


@admin_router_readonly.get(
    "/agents", tags=["Agent"], dependencies=[Depends(verify_jwt)]
)
async def get_agents(db: AsyncSession = Depends(get_db)) -> list[AgentResponse]:
    """Get all agents with their quota information.

    Args:
        db: Database session

    Returns:
        list[AgentResponse]: List of agents with their quota information and additional processed data
    """
    # Query all agents first
    agents = (await db.exec(select(Agent))).all()

    # Batch get agent data
    agent_ids = [agent.id for agent in agents]
    agent_data_list = (
        await db.exec(select(AgentData).where(AgentData.id.in_(agent_ids)))
    ).all()
    agent_data_map = {data.id: data for data in agent_data_list}

    # Convert to AgentResponse objects
    return [
        AgentResponse.from_agent(agent, agent_data_map.get(agent.id))
        for agent in agents
    ]


@admin_router_readonly.get(
    "/agents/{agent_id}", tags=["Agent"], dependencies=[Depends(verify_jwt)]
)
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)) -> AgentResponse:
    """Get a single agent by ID.

    Args:
        agent_id: ID of the agent to retrieve
        db: Database session

    Returns:
        AgentResponse: Agent configuration with additional processed data

    Raises:
        HTTPException:
            - 404: Agent not found
    """
    agent = (await db.exec(select(Agent).where(Agent.id == agent_id))).first()
    if not agent:
        raise HTTPException(
            status_code=404,
            detail=f"Agent with id {agent_id} not found",
        )

    # Get agent data
    agent_data = (
        await db.exec(select(AgentData).where(AgentData.id == agent_id))
    ).first()

    return AgentResponse.from_agent(agent, agent_data)


class MemCleanRequest(BaseModel):
    """Request model for agent memory cleanup endpoint.

    Attributes:
        agent_id (str): Agent ID to clean
        thread_id (str): Thread ID to clean
        clean_skills_memory (bool): To clean the skills data.
        clean_agent_memory (bool): To clean the agent memory.
    """

    agent_id: str
    clean_agent_memory: bool
    clean_skills_memory: bool
    thread_id: str | None = Field("")


@admin_router.post(
    "/agents/clean-memory",
    tags=["Agent"],
    status_code=201,
    dependencies=[Depends(verify_jwt)],
)
async def clean_memory(
    request: MemCleanRequest = Body(
        MemCleanRequest, description="Agent memory cleanup requestd"
    ),
    db: AsyncSession = Depends(get_db),
) -> str:
    """Clear an agent memory.

    Args:
        request (MemCleanRequest): The execution request containing agent ID, message, and thread ID

    Returns:
        str: Formatted response lines from agent memory cleanup

    Raises:
        HTTPException:
            - 400: If input parameters are invalid (empty agent_id, thread_id, or message text)
            - 404: If agent not found
            - 500: For other server-side errors
    """
    # Validate input parameters
    if not request.agent_id or not request.agent_id.strip():
        raise HTTPException(status_code=400, detail="Agent ID cannot be empty")

    try:
        agent = (
            await db.exec(select(Agent).where(Agent.id == request.agent_id))
        ).first()
        if not agent:
            raise HTTPException(
                status_code=404,
                detail=f"Agent with id {request.agent_id} not found",
            )

        return await clean_agent_memory(
            request.agent_id,
            request.thread_id,
            clean_agent_memory=request.clean_agent_memory,
            clean_skills_memory=request.clean_skills_memory,
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail=f"Agent {request.agent_id} not found"
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
