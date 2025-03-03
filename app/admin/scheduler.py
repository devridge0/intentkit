"""Scheduler for periodic tasks."""

import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import update

from app.config.config import config
from app.services.twitter.oauth2_refresh import refresh_expiring_tokens
from models.agent import AgentQuotaTable
from models.db import get_session, init_db


async def reset_daily_quotas():
    """Reset daily quotas for all agents at UTC 00:00.
    Resets message_count_daily and twitter_count_daily to 0.
    """
    async with get_session() as session:
        stmt = update(AgentQuotaTable).values(
            message_count_daily=0, twitter_count_daily=0
        )
        await session.exec(stmt)
        await session.commit()


async def reset_monthly_quotas():
    """Reset monthly quotas for all agents at the start of each month.
    Resets message_count_monthly and autonomous_count_monthly to 0.
    """
    async with get_session() as session:
        stmt = update(AgentQuotaTable).values(
            message_count_monthly=0, autonomous_count_monthly=0
        )
        await session.exec(stmt)
        await session.commit()


def create_scheduler():
    """Create and configure the APScheduler with all periodic tasks."""
    scheduler = AsyncIOScheduler()

    # Reset daily quotas at UTC 00:00
    scheduler.add_job(
        reset_daily_quotas,
        trigger=CronTrigger(hour=0, minute=0, timezone="UTC"),
        id="reset_daily_quotas",
        name="Reset daily quotas",
        replace_existing=True,
    )

    # Reset monthly quotas at UTC 00:00 on the first day of each month
    scheduler.add_job(
        reset_monthly_quotas,
        trigger=CronTrigger(day=1, hour=0, minute=0, timezone="UTC"),
        id="reset_monthly_quotas",
        name="Reset monthly quotas",
        replace_existing=True,
    )

    # Check for expiring tokens every 5 minutes
    scheduler.add_job(
        refresh_expiring_tokens,
        trigger=CronTrigger(minute="*/5", timezone="UTC"),  # Run every 5 minutes
        id="refresh_twitter_tokens",
        name="Refresh expiring Twitter tokens",
        replace_existing=True,
    )

    return scheduler


def start_scheduler():
    """Create, configure and start the APScheduler."""
    scheduler = create_scheduler()
    scheduler.start()
    return scheduler


if __name__ == "__main__":
    # Initialize infrastructure
    init_db(**config.db)

    scheduler = start_scheduler()
    try:
        # Keep the script running with asyncio event loop
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
