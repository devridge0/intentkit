import logging
from datetime import datetime, timedelta

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from abstracts.engine import AgentMessageInput
from app.config.config import config
from app.core.client import execute_agent
from models.agent import Agent, AgentQuota
from models.db import get_engine

logger = logging.getLogger(__name__)


async def run_autonomous_agents():
    """Get all agents from the database which autonomous is enabled,
    get the quota of each agent, check the last run time, together with the autonomous_minutes in agent,
    decide whether to run them.
    If the quota check passes, run them autonomously."""
    engine = get_engine()
    async with AsyncSession(engine) as db:
        # Get all autonomous agents
        agents = await db.exec(
            select(Agent).where(
                Agent.autonomous_enabled == True,  # noqa: E712
                Agent.autonomous_prompt != None,  # noqa: E711
                Agent.autonomous_minutes != None,  # noqa: E711
            )
        )

        for agent in agents.all():
            try:
                # Get agent quota
                quota = await AgentQuota.get(agent.id, db)

                # Check if agent has quota
                if not quota.has_autonomous_quota():
                    logger.warning(
                        f"Agent {agent.id} has no autonomous quota. "
                        f"Monthly: {quota.autonomous_count_monthly}/{quota.autonomous_limit_monthly}, "
                        f"Total: {quota.autonomous_count_total}/{quota.autonomous_limit_total}"
                    )
                    continue

                # Check if it's time to run
                if quota.last_autonomous_time:
                    next_run = quota.last_autonomous_time + timedelta(
                        minutes=agent.autonomous_minutes
                    )
                    if datetime.now() < next_run:
                        logger.debug(
                            f"Agent {agent.id} next run at {next_run}, "
                            f"minutes: {agent.autonomous_minutes}"
                        )
                        continue

                # Run the autonomous action
                try:
                    await run_autonomous_action(agent.id, agent.autonomous_prompt)
                    # Update quota after successful run
                    quota.add_autonomous(db)
                except Exception as e:
                    logger.error(
                        f"Error in autonomous action for agent {agent.id}: {str(e)}"
                    )

            except Exception as e:
                logger.error(f"Error processing autonomous agent {agent.id}: {str(e)}")
                continue


async def run_autonomous_action(aid: str, prompt: str):
    """Run the agent autonomously with specified intervals."""
    logger.info(f"[{aid}] autonomous action started...")
    # get thread_id from request ip
    thread_id = f"{aid}-autonomous"
    if config.autonomous_memory_public:
        thread_id = f"{aid}-public"

    # Execute agent and get response
    resp = await execute_agent(aid, AgentMessageInput(text=prompt), thread_id)

    # Log the response
    logger.info("\n".join(resp))
