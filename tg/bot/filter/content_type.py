from aiogram.filters import BaseFilter
from aiogram.types import Message, ContentType


class ContentTypeFilter(BaseFilter):
    def __init__(self, content_types: ContentType | list):
        self.content_types = content_types

    async def __call__(self, message: Message) -> bool:
        return message.content_type in self.content_types


class TextOnlyFilter(ContentTypeFilter):
    def __init__(self):
        super().__init__([ContentType.TEXT])
