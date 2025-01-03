import asyncio
import logging
import signal
import sys

from sqlmodel import Session, select

from app.config.config import config
from app.models.agent import Agent
from app.models.db import get_engine, init_db
from tg.bot import pool
from tg.bot.pool import BotPool

logger = logging.getLogger(__name__)


class AgentScheduler:
    def __init__(self, bot_pool):
        self.bot_pool = bot_pool

    async def sync(self):
        with Session(get_engine()) as db:
            # Get all telegram agents
            agents = db.exec(select(Agent)).all()

            new_agents = []
            token_changed_agents = []
            modified_agents = []
            for agent in agents:
                token = agent.telegram_config["token"]

                if agent.id not in pool._agent_bots:
                    if (
                        agent.telegram_enabled
                        and agent.telegram_config
                        and agent.telegram_config["token"]
                    ):
                        token_changed_agents.append(agent)
                        new_agents.append(agent)
                        logger.info(f"New agent with id {agent.id} found...")
                        await self.bot_pool.init_new_bot(agent)
                else:
                    cached_agent = pool._agent_bots[agent.id]
                    if cached_agent["updated_at"] != agent.updated_at:
                        if token not in pool._bots:
                            await self.bot_pool.change_bot_token(agent)
                        else:
                            await self.bot_pool.modify_config(agent)

            return new_agents, token_changed_agents, modified_agents

    async def start(self, interval):
        logger.info("New agent addition tracking started...")
        while True:
            logger.info("sync agents...")
            await asyncio.sleep(interval)
            await self.sync()


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

    logger.info("Initialize bot pool...")
    bot_pool = BotPool(config.tg_base_url)

    bot_pool.init_god_bot()
    bot_pool.init_all_dispatchers()

    scheduler = AgentScheduler(bot_pool)

    loop = asyncio.new_event_loop()
    loop.create_task(scheduler.start(int(config.tg_new_agent_poll_interval)))

    bot_pool.start(loop, config.tg_server_host, int(config.tg_server_port))


if __name__ == "__main__":
    run_telegram_server()
