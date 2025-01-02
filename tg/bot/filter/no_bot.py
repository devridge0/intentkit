from aiogram.filters import BaseFilter
from aiogram.types import Message
from tg.bot import pool


class NoBotFilter(BaseFilter):
    def __init__(self):
        pass

    async def __call__(self, message: Message) -> bool:
        return message.from_user.is_bot == False
