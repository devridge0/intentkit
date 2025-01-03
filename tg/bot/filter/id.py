from aiogram.filters import BaseFilter
from aiogram.types import Message

from tg.bot import pool


class WhitelistedChatIDsFilter(BaseFilter):
    def __init__(self):
        pass

    async def __call__(self, message: Message) -> bool:
        cached_bot = pool.bot_by_token(message.bot.token)
        if cached_bot is None:
            return False

        whitelist = cached_bot["cfg"].get("whitelist_chat_ids")
        if whitelist is not None and len(whitelist) > 0:
            return str(message.chat.id) in whitelist

        return True
