import asyncio
import logging
from os import getenv
import sys
from app.db import init_db
from app.config import config
import signal
from tg.bot.pool import BotPool
from tg.schedule.agent import AgentScheduler

BASE_URL = getenv("TG_BASE_URL")
WEB_SERVER_HOST = getenv("TG_SERVER_HOST", "127.0.0.1")
WEB_SERVER_PORT = getenv("TG_SERVER_PORT", "8081")
TG_NEW_AGENT_POLL_INTERVAL = getenv("TG_NEW_AGENT_POLL_INTERVAL", "60")

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

    bot_pool = BotPool(BASE_URL)

    bot_pool.init_god_bot()
    bot_pool.init_all_dispatchers()

    scheduler = AgentScheduler(bot_pool)

    loop = asyncio.new_event_loop()
    loop.create_task(scheduler.start(int(TG_NEW_AGENT_POLL_INTERVAL)))

    bot_pool.start(loop, WEB_SERVER_HOST, int(WEB_SERVER_PORT))


if __name__ == "__main__":
    run_telegram_server()
