import asyncio
import logging
import signal
import sys
from os import getenv

from app.config import config
from app.db import init_db
from tg.bot.pool import BotPool
from tg.schedule.agent import AgentScheduler


logger = logging.getLogger(__name__)


def run_telegram_server() -> None:
    # Initialize database connection
    init_db(**config.db)

    # Signal handler for graceful shutdown
    def signal_handler(signum, frame):
        logger.info("Received termination signal. Shutting down gracefully...")
        scheduler.shutdown()
        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    bot_pool = BotPool(config.tg_base_url)

    bot_pool.init_god_bot()
    bot_pool.init_all_dispatchers()

    scheduler = AgentScheduler(bot_pool)

    loop = asyncio.new_event_loop()
    loop.create_task(scheduler.start(int(config.tg_new_agent_poll_interval)))

    bot_pool.start(loop, config.tg_server_host, int(config.tg_server_port))


if __name__ == "__main__":
    run_telegram_server()
