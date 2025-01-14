from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session, update

from app.config.config import config
from models.agent import AgentQuota
from models.db import get_engine, init_db


def reset_daily_quotas():
    """Reset daily quotas for all agents at UTC 00:00.
    Resets message_count_daily and twitter_count_daily to 0.
    """
    with Session(get_engine()) as session:
        stmt = update(AgentQuota).values(message_count_daily=0, twitter_count_daily=0)
        session.exec(stmt)
        session.commit()


def reset_monthly_quotas():
    """Reset monthly quotas for all agents at the start of each month.
    Resets message_count_monthly and autonomous_count_monthly to 0.
    """
    with Session(get_engine()) as session:
        stmt = update(AgentQuota).values(
            message_count_monthly=0, autonomous_count_monthly=0
        )
        session.exec(stmt)
        session.commit()


def start_scheduler():
    """Start the APScheduler to run quota reset jobs."""
    scheduler = BackgroundScheduler()

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

    scheduler.start()
    return scheduler


if __name__ == "__main__":
    # Initialize infrastructure
    init_db(**config.db)

    scheduler = start_scheduler()
    try:
        # Keep the script running
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
