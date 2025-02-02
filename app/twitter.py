import asyncio
import logging
import signal
import sys

import sentry_sdk
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config.config import config
from app.entrypoints.twitter import run_twitter_agents
from models.db import init_db

logger = logging.getLogger(__name__)

if config.sentry_dsn:
    sentry_sdk.init(
        dsn=config.sentry_dsn,
        traces_sample_rate=config.sentry_traces_sample_rate,
        profiles_sample_rate=config.sentry_profiles_sample_rate,
        environment=config.env,
        release=config.release,
    )

if __name__ == "__main__":
    async def main():
        # Initialize infrastructure
        await init_db(**config.db)

        # Create scheduler
        scheduler = AsyncIOScheduler()
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
            # Keep the main thread running
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            pass

    # Run the async main function
    asyncio.run(main())
