import logging
import signal
import sys
from datetime import datetime, timedelta

from apscheduler.schedulers.blocking import BlockingScheduler
from sqlmodel import Session, select

from app.config.config import config
from app.core.ai import execute_agent
from app.models.agent import Agent, AgentQuota
from app.models.db import get_engine, init_db
from utils.slack import init_slack

logger = logging.getLogger(__name__)


def run_autonomous_agents():
    """Get all agents from the database which autonomous is enabled,
    get the quota of each agent, check the last run time, together with the autonomous_minutes in agent,
    decide whether to run them.
    If the quota check passes, run them autonomously."""
    engine = get_engine()
    with Session(engine) as db:
        # Get all autonomous agents
        agents = db.exec(
            select(Agent).where(
                Agent.autonomous_enabled == True,  # noqa: E712
                Agent.autonomous_prompt != None,  # noqa: E711
                Agent.autonomous_minutes != None,  # noqa: E711
            )
        ).all()

        for agent in agents:
            try:
                # Get agent quota
                quota = AgentQuota.get(agent.id, db)

                # Check if agent has quota
                if not quota.has_autonomous_quota(db):
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
                    run_autonomous_action(agent.id, agent.autonomous_prompt)
                    # Update quota after successful run
                    quota.add_autonomous(db)
                except Exception as e:
                    logger.error(
                        f"Error in autonomous action for agent {agent.id}: {str(e)}"
                    )

            except Exception as e:
                logger.error(f"Error processing autonomous agent {agent.id}: {str(e)}")
                continue


def run_autonomous_action(aid: str, prompt: str):
    """Run the agent autonomously with specified intervals."""
    logger.info(f"[{aid}] autonomous action started...")
    # get thread_id from request ip
    thread_id = f"{aid}-autonomous"

    # Execute agent and get response
    resp = execute_agent(aid, prompt, thread_id)

    # Log the response
    logger.info("\n".join(resp))


if __name__ == "__main__":
    # Initialize infrastructure
    init_db(**config.db)
    init_slack(config.slack_token, config.slack_channel)

    # Initialize scheduler
    scheduler = BlockingScheduler()

    # Add job to run every minute
    scheduler.add_job(run_autonomous_agents, "interval", minutes=1)

    # Signal handler for graceful shutdown
    def signal_handler(signum, frame):
        logger.info("Received termination signal. Shutting down gracefully...")
        scheduler.shutdown()
        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        logger.info("Starting autonomous agents scheduler...")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped. Exiting...")
