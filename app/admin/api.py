from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, func, select

from app.config.config import config
from app.core.engine import initialize_agent
from models.agent import Agent, AgentQuota
from models.db import get_db
from utils.middleware import create_jwt_middleware
from utils.slack_alert import send_slack_message

admin_router = APIRouter()


# Create JWT middleware with admin config
verify_jwt = create_jwt_middleware(config.admin_auth_enabled, config.admin_jwt_secret)


@admin_router.post("/agents", status_code=201, dependencies=[Depends(verify_jwt)])
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

    # Get the latest agent from create_or_update
    latest_agent = agent.create_or_update(db)

    # Send Slack notification only for new agents
    total_agents = db.exec(select(func.count()).select_from(Agent)).one()
    if (
        total_agents == 1
        or not db.exec(select(Agent).filter(Agent.id == agent.id)).first()
    ):
        send_slack_message(
            "New agent created ",
            attachments=[
                {
                    "color": "good",
                    "fields": [
                        {"title": "ENV", "short": True, "value": config.env},
                        {"title": "Total", "short": True, "value": total_agents},
                        {"title": "ID", "short": True, "value": latest_agent.id},
                        {"title": "Name", "short": True, "value": latest_agent.name},
                        {"title": "Model", "short": True, "value": latest_agent.model},
                        {
                            "title": "Autonomous",
                            "short": True,
                            "value": str(latest_agent.autonomous_enabled),
                        },
                        {
                            "title": "Twitter",
                            "short": True,
                            "value": str(latest_agent.twitter_enabled),
                        },
                        {
                            "title": "Telegram",
                            "short": True,
                            "value": str(latest_agent.telegram_enabled),
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
                    ],
                }
            ],
        )

    # Mask sensitive data in response
    latest_agent.cdp_wallet_data = "forbidden"
    if latest_agent.skill_sets is not None:
        for key in latest_agent.skill_sets:
            latest_agent.skill_sets[key] = {}

    # TODO: change here when multiple instances deploy
    initialize_agent(agent.id)
    return latest_agent


@admin_router.get("/agents", dependencies=[Depends(verify_jwt)])
def get_agents(db: Session = Depends(get_db)) -> list:
    """Get all agents with their quota information.

    Args:
        db: Database session

    Returns:
        list: List of agents with their quota information
    """
    # Query agents and quotas together
    query = select(Agent.id, Agent.name, AgentQuota).join(
        AgentQuota, Agent.id == AgentQuota.id, isouter=True
    )

    results = db.exec(query).all()

    # Format the response
    agents = []
    for result in results:
        agent_data = {
            "id": result.id,
            "name": result.name,
            "quota": {
                "plan": result[2].plan if result[2] else "none",
                "message_count_total": (
                    result[2].message_count_total if result[2] else 0
                ),
                "message_limit_total": (
                    result[2].message_limit_total if result[2] else 0
                ),
                "last_message_time": result[2].last_message_time if result[2] else None,
                "last_autonomous_time": (
                    result[2].last_autonomous_time if result[2] else None
                ),
            },
        }
        agents.append(agent_data)

    return agents
