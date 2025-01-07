from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.config.config import config
from app.core.engine import initialize_agent
from app.models.agent import Agent, AgentQuota
from app.models.db import get_db
from utils.middleware import create_jwt_middleware

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
    agent.create_or_update(db)
    # Get the latest agent from the database
    latest_agent = db.exec(select(Agent).filter(Agent.id == agent.id)).one()
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
