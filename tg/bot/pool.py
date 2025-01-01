import logging

import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import (SimpleRequestHandler,
                                            TokenBasedRequestHandler,
                                            setup_application)
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
    return _agent_bots.get(agent_id)


def agent_thread_id(agent_id, chat_id):
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
            logger.info("{kind} router initialized...".format(kind=kind))

    async def init_new_bot(self, agent_id, kind, token):
        try:
            bot = Bot(
                token=token,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            )
            await bot.delete_webhook(drop_pending_updates=True)
            await bot.set_webhook(self.base_url.format(kind=kind, bot_token=token))

            _bots[token] = {"agent_id": agent_id, "kind": kind, "bot": bot}
            _agent_bots[agent_id] = {"token": token, "kind": kind, "bot": bot}
            logger.info("Bot with token {token} initialized...".format(token=token))

        except Exception as e:
            logger.error(
                "failed to init new bot for agent {agent_id}.".format(agent_id=agent_id)
            )

    async def change_bot_token(self, agent_id, new_token):
        try:
            old_cached_bot = bot_by_agent_id(agent_id)
            kind = old_cached_bot["kind"]

            old_bot = Bot(
                token=old_cached_bot["token"],
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

            del _bots[old_cached_bot["token"]]
            _bots[new_token] = {"agent_id": agent_id, "kind": kind, "bot": new_bot}
            _agent_bots[agent_id] = {"token": new_token, "kind": kind, "bot": new_bot}
            logger.info(
                "bot for agent {agent_id} with token {token} changed to {new_token}...".format(
                    agent_id=agent_id,
                    token=old_cached_bot["token"],
                    new_token=new_token,
                ),
            )
        except aiohttp.ClientError:
            pass
        except Exception as e:
            logger.error(
                "failed to change bot token for agent {agent_id}.".format(
                    agent_id=agent_id
                )
            )

    def start(self, asyncio_loop, host, port):
        web.run_app(self.app, loop=asyncio_loop, host=host, port=port)
