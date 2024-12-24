from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.bot import DefaultBotProperties
from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    TokenBasedRequestHandler,
    setup_application,
)

from bot.types.router_obj import RouterObj
from bot.types.kind import Kind
from bot.kind.general.router import general_router
from bot.kind.god.router import god_router
from bot.kind.god.startup import on_startup, GOD_BOT_TOKEN, GOD_BOT_PATH

BOTS_PATH = "/webhook/bot/{kind}/{bot_token}"


class BotPool:
    def __init__(self, base_url):
        self.app = web.Application()
        self.base_url = f"{base_url}{BOTS_PATH}"
        self.routers = {
            Kind.General: RouterObj(general_router),
        }

        self.bots = {}

    def init_god_bot(self):
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
                self.app, path=BOTS_PATH.format(kind=kind, bot_token="{bot_token}")
            )
            setup_application(self.app, b.get_dispatcher())

    async def init_new_bot(self, kind, token):
        bot = Bot(
            token=token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_webhook(self.base_url.format(kind=kind, bot_token=token))
        self.bots[token] = bot

    def start(self, asyncio_loop, host, port):
        web.run_app(self.app, loop=asyncio_loop, host=host, port=port)
