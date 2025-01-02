import logging

import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    TokenBasedRequestHandler,
    setup_application,
)
from aiohttp import web

from tg.bot.kind.ai_relayer.router import general_router
from tg.bot.kind.god.router import god_router
from tg.bot.kind.god.startup import GOD_BOT_PATH, GOD_BOT_TOKEN, on_startup
from tg.bot.types.kind import Kind
from tg.bot.types.router_obj import RouterObj

logger = logging.getLogger(__name__)

BOTS_PATH = "/webhook/tgbot/{kind}/{bot_token}"

_bots = {}
_agent_bots = {}


def bot_by_token(token):
    return _bots.get(token)


def bot_by_agent_id(agent_id):
    agent = _agent_bots.get(agent_id)
    if agent is not None:
        return bot_by_token(agent["token"])


def agent_thread_id(agent_id, is_public, chat_id):
    if is_public:
        return f"{agent_id}-telegram-public"
    return f"{agent_id}-telegram-{chat_id}"


async def health_handler(request):
    """Health check endpoint handler."""
    return web.json_response({"status": "healthy"})


class BotPool:
    def __init__(self, base_url):
        self.app = web.Application()
        self.app.router.add_get("/health", health_handler)
        self.base_url = f"{base_url}{BOTS_PATH}"
        self.routers = {
            Kind.AiRelayer: RouterObj(general_router),
        }

    def init_god_bot(self):
        if GOD_BOT_TOKEN is not None:
            logger.info("Initialize god bot...")
            self.god_bot = Bot(
                token=GOD_BOT_TOKEN,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            )
            storage = MemoryStorage()
            # In order to use RedisStorage you need to use Key Builder with bot ID:
            # storage = RedisStorage.from_url(TG_REDIS_DSN, key_builder=DefaultKeyBuilder(with_bot_id=True))
            dp = Dispatcher(storage=storage)
            dp.include_router(god_router)
            dp.startup.register(on_startup)
            SimpleRequestHandler(dispatcher=dp, bot=self.god_bot).register(
                self.app, path=GOD_BOT_PATH
            )
            setup_application(self.app, dp, bot=self.god_bot)

    def init_all_dispatchers(self):
        logger.info("Initialize all dispatchers...")
        for kind, b in self.routers.items():
            storage = MemoryStorage()
            # In order to use RedisStorage you need to use Key Builder with bot ID:
            # storage = RedisStorage.from_url(TG_REDIS_DSN, key_builder=DefaultKeyBuilder(with_bot_id=True))
            b.set_dispatcher(Dispatcher(storage=storage))
            b.get_dispatcher().include_router(b.get_router())
            TokenBasedRequestHandler(
                dispatcher=b.get_dispatcher(),
                default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            ).register(
                self.app,
                path=BOTS_PATH.format(kind=kind.value, bot_token="{bot_token}"),
            )
            setup_application(self.app, b.get_dispatcher())
            logger.info(f"{kind} router initialized...")

    async def init_new_bot(self, agent):
        try:
            cfg = agent.telegram_config
            token = cfg["token"]
            bot = Bot(
                token=token,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            )
            await bot.delete_webhook(drop_pending_updates=True)
            await bot.set_webhook(
                self.base_url.format(kind=cfg["kind"], bot_token=token)
            )

            _bots[token] = {
                "agent_id": agent.id,
                "is_public": agent.ai_thread_public,
                "cfg": cfg,
                "bot": bot,
            }
            _agent_bots[agent.id] = {
                "token": token,
                "last_modified": agent.last_modified,
            }
            logger.info(f"Bot with token {token} initialized...")

        except Exception as e:
            logger.error(
                "failed to init new bot for agent {agent_id}: {err}".format(
                    agent_id=agent.id, err=e
                )
            )

    async def change_bot_token(self, agent):
        try:
            old_cached_bot = bot_by_agent_id(agent.id)
            kind = old_cached_bot["cfg"]["kind"]

            new_token = agent.telegram_config["token"]

            old_bot = Bot(
                token=old_cached_bot["cfg"]["token"],
                default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            )
            await old_bot.session.close()
            await old_bot.delete_webhook(drop_pending_updates=True)

            new_bot = Bot(
                token=new_token,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            )
            await new_bot.set_webhook(
                self.base_url.format(kind=kind, bot_token=new_token)
            )

            del _bots[old_cached_bot["cfg"]["token"]]
            _bots[new_token] = {
                "agent_id": agent.id,
                "is_public": agent.ai_thread_public,
                "cfg": agent.telegram_config,
                "bot": new_bot,
            }
            _agent_bots[agent.id] = {
                "token": agent.telegram_config["token"],
                "last_modified": agent.last_modified,
            }
            logger.info(
                "bot for agent {agent_id} with token {token} changed to {new_token}...".format(
                    agent_id=agent.id,
                    token=old_cached_bot["cfg"]["token"],
                    new_token=new_token,
                ),
            )
        except aiohttp.ClientError:
            pass
        except Exception as e:
            logger.error(f"failed to change bot token for agent {agent.id}: {str(e)}")

    async def stop_bot(self, agent):
        try:
            token = agent.telegram_config["token"]
            bot = Bot(
                token=token,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            )
            await bot.session.close()
            await bot.delete_webhook(drop_pending_updates=True)

            del _agent_bots[agent.id]
            del _bots[token]

            logger.info(f"Bot with token {token} for agent {agent.id} stopped...")

        except Exception as e:
            logger.error(f"failed to stop the bot for agent {agent.id}: {e}")

    async def modify_config(self, agent):
        if agent.telegram_enabled == False:
            await self.stop_bot(agent)
            return

        try:
            old_cached_bot = bot_by_agent_id(agent.id)
            _bots[old_cached_bot["cfg"]["token"]]["cfg"] = agent.telegram_config
            _agent_bots[old_cached_bot["agent_id"]][
                "last_modified"
            ] = agent.last_modified
            if old_cached_bot["cfg"]["kind"] != agent.telegram_config["kind"]:
                await self.stop_bot(agent)
                await self.init_new_bot(agent)
            logger.info(
                f"configurations of the bot with token {agent.telegram_config["token"]} for agent {agent.id} updated..."
            )
        except Exception as e:
            logger.error(
                f"failed to change the configs of the bot for agent {agent.id}: {str(e)}"
            )

    def start(self, asyncio_loop, host, port):
        web.run_app(self.app, loop=asyncio_loop, host=host, port=port)
