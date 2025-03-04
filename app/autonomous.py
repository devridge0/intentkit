import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Dict

import sentry_sdk
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.config.config import config
from app.entrypoints.autonomous import run_autonomous_agents, run_autonomous_task
from models.agent import Agent, AgentTable
from models.db import get_session, init_db

logger = logging.getLogger(__name__)

# Global dictionary to store task_id and last updated time
autonomous_tasks_updated_at: Dict[str, datetime] = {}

if config.sentry_dsn:
    sentry_sdk.init(
        dsn=config.sentry_dsn,
        sample_rate=config.sentry_sample_rate,
        traces_sample_rate=config.sentry_traces_sample_rate,
        profiles_sample_rate=config.sentry_profiles_sample_rate,
        environment=config.env,
        release=config.release,
        server_name="intent-autonomous",
    )


async def schedule_agent_autonomous_tasks(scheduler: AsyncIOScheduler):
    """
    Find all agents with autonomous tasks and schedule them.
    This function is called periodically to update the scheduler with new or modified tasks.
    """
    logger.info("Checking for agent autonomous tasks...")

    async with get_session() as db:
        # Get all agents with autonomous configuration
        query = select(AgentTable).where(AgentTable.autonomous != None)  # noqa: E711
        agents = await db.scalars(query)

        for item in agents:
            agent = Agent.model_validate(item)
            if not agent.autonomous or len(agent.autonomous) == 0:
                continue

            for autonomous in agent.autonomous:
                if not autonomous.enabled:
                    continue

                # Create a unique task ID for this autonomous task
                task_id = f"{agent.id}-{autonomous.id}"

                # Check if task exists and needs updating
                if (
                    task_id in autonomous_tasks_updated_at
                    and autonomous_tasks_updated_at[task_id] >= agent.updated_at
                ):
                    # Task exists and agent hasn't been updated, skip
                    continue

                # Schedule new job based on minutes or cron
                if autonomous.cron:
                    logger.info(
                        f"Scheduling cron task {task_id} with cron: {autonomous.cron}"
                    )
                    scheduler.add_job(
                        run_autonomous_task,
                        CronTrigger.from_crontab(autonomous.cron),
                        id=task_id,
                        args=[agent.id, agent.owner, autonomous.id, autonomous.prompt],
                        replace_existing=True,
                    )
                elif autonomous.minutes is not None:
                    logger.info(
                        f"Scheduling interval task {task_id} every {autonomous.minutes} minutes"
                    )
                    scheduler.add_job(
                        run_autonomous_task,
                        "interval",
                        id=task_id,
                        args=[agent.id, agent.owner, autonomous.id, autonomous.prompt],
                        minutes=autonomous.minutes,
                        replace_existing=True,
                    )
                else:
                    logger.error(
                        f"Invalid autonomous configuration for task {task_id}: {autonomous}"
                    )

                # Update the last updated time
                autonomous_tasks_updated_at[task_id] = agent.updated_at


if __name__ == "__main__":

    async def main():
        # Initialize database
        await init_db(**config.db)

        # Initialize scheduler
        scheduler = AsyncIOScheduler()

        # Add job to run legacy autonomous agents every minute
        scheduler.add_job(run_autonomous_agents, "interval", minutes=100)

        # Add job to schedule agent autonomous tasks every 5 minutes
        # Run it immediately on startup and then every 5 minutes
        scheduler.add_job(
            schedule_agent_autonomous_tasks,
            "interval",
            args=[scheduler],
            minutes=5,
            next_run_time=datetime.now(),
        )

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
            # Keep the main thread running
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped. Exiting...")

    # Run the async main function
    asyncio.run(main())
