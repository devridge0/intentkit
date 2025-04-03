"""Scheduler process entry point.

This module runs the scheduler in a separate process, using the implementation
from app.admin.scheduler.
"""

import asyncio
import logging
import signal
import sys

import sentry_sdk

from app.admin.scheduler import create_scheduler
from app.config.config import config
from models.db import init_db
from models.redis import init_redis

logger = logging.getLogger(__name__)

if config.sentry_dsn:
    sentry_sdk.init(
        dsn=config.sentry_dsn,
        sample_rate=config.sentry_sample_rate,
        traces_sample_rate=config.sentry_traces_sample_rate,
        profiles_sample_rate=config.sentry_profiles_sample_rate,
        environment=config.env,
        release=config.release,
        server_name="intent-scheduler",
    )


if __name__ == "__main__":

    async def main():
        # Initialize database
        await init_db(**config.db)

        # Initialize Redis if configured
        if config.redis_host:
            await init_redis(
                host=config.redis_host,
                port=config.redis_port,
            )

        # Initialize scheduler
        scheduler = create_scheduler()

        # Signal handler for graceful shutdown
        def signal_handler(signum, frame):
            logger.info("Received termination signal. Shutting down gracefully...")
            scheduler.shutdown()
            sys.exit(0)

        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            logger.info("Starting scheduler process...")
            scheduler.start()
            # Keep the main thread running
            while True:
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error in scheduler process: {e}")
            scheduler.shutdown()
            sys.exit(1)

    # Run the async main function
    asyncio.run(main())
