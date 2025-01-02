from aiogram.filters import BaseFilter
from aiogram.types import Message


class NoBotFilter(BaseFilter):
    def __init__(self):
        pass

    async def __call__(self, message: Message) -> bool:
        return not message.from_user.is_bot
