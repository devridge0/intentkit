import logging
import signal
import sys

from apscheduler.schedulers.blocking import BlockingScheduler

from app.config.config import config
from app.entrypoints.twitter import run_twitter_agents
from models.db import init_db

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Initialize infrastructure
    init_db(**config.db)

    # Create scheduler
    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_twitter_agents, "interval", minutes=config.twitter_entrypoint_interval
    )

    # Register signal handlers
    def signal_handler(signum, frame):
        scheduler.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
