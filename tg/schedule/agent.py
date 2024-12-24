import asyncio
from sqlmodel import select, Session

from app.db import get_db, Agent


class AgentScheduler:
    def __init__(self, bot_pool):
        self.bot_pool = bot_pool

    def check_new_bots(self):
        db: Session = next(get_db())
        # Get all telegram agents
        agents = db.exec(
            select(Agent).where(
                Agent.telegram_enabled == True,
            )
        ).all()

        new_bots = []
        for agent in agents:
            if agent.telegram_config["token"] not in self.bot_pool.bots:
                new_bots.append(agent.telegram_config)
        return new_bots

    async def start(self, interval):
        while True:
            print("check for new bots...")
            await asyncio.sleep(interval)
            if self.check_new_bots() != None:
                for new_bot in self.check_new_bots():
                    await self.bot_pool.init_new_bot(new_bot["kind"], new_bot["token"])
