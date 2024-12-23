import logging
import time
import signal
import sys
from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
from sqlmodel import select, Session

from langchain_core.messages import HumanMessage

from app.ai import initialize_agent
from app.db import get_db, Agent, AgentQuota, init_db
from app.config import config

logger = logging.getLogger(__name__)

# Global variable to cache all agent executors
agents = {}


def run_autonomous_agents():
    """Get all agents from the database which autonomous is enabled,
    get the quota of each agent, check the last run time, together with the autonomous_minutes in agent,
    decide whether to run them.
    If the quota check passes, run them autonomously."""
    db: Session = next(get_db())
    try:
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

    except Exception as e:
        logger.error(f"Error in autonomous runner: {str(e)}")
    finally:
        db.close()


def run_autonomous_action(aid: str, prompt: str):
    """Run the agent autonomously with specified intervals."""
    logger.info(f"[{aid}] autonomous action started...")
    # get thread_id from request ip
    thread_id = f"{aid}-autonomous"
    config = {"configurable": {"thread_id": thread_id}}
    # prepare response
    resp = []
    start = time.perf_counter()
    last = start
    # user input
    resp.append(f"[ Autonomous: ]\n\n {prompt}\n\n-------------------\n")
    # cold start
    if aid not in agents:
        agents[aid] = initialize_agent(aid)
        resp.append(f"[ Agent cold start ... ]")
        resp.append(
            f"\n------------------- start Cost: {time.perf_counter() - last:.3f} seconds\n"
        )
        last = time.perf_counter()
    executor = agents[aid]
    # run
    for chunk in executor.stream({"messages": [HumanMessage(content=prompt)]}, config):
        if "agent" in chunk:
            v = chunk["agent"]["messages"][0].content
            if v:
                resp.append("[ Agent: ]\n")
                resp.append(v)
            else:
                resp.append("[ Agent is thinking ... ]")
            resp.append(
                f"\n------------------- agent Cost: {time.perf_counter() - last:.3f} seconds\n"
            )
            last = time.perf_counter()
        elif "tools" in chunk:
            resp.append("[ Skill running ... ]\n")
            resp.append(chunk["tools"]["messages"][0].content)
            resp.append(
                f"\n------------------- skill Cost: {time.perf_counter() - last:.3f} seconds\n"
            )
            last = time.perf_counter()
    resp.append(f"Total time cost: {time.perf_counter() - start:.3f} seconds")
    logger.info("\n".join(resp))


if __name__ == "__main__":
    # Initialize database connection
    init_db(**config.db)
    
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
