import inspect
import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.core.ai import execute_agent
from tg.bot import pool
from tg.bot.filter.chat_type import GroupOnlyFilter
from tg.bot.filter.content_type import TextOnlyFilter
from tg.bot.filter.id import WhitelistedChatIDsFilter
from tg.bot.filter.no_bot import NoBotFilter

logger = logging.getLogger(__name__)


def cur_func_name():
    return inspect.stack()[1][3]


def cur_mod_name():
    return inspect.getmodule(inspect.stack()[1][0]).__name__


general_router = Router()


@general_router.message(Command("chat_id"), NoBotFilter(), TextOnlyFilter())
async def command_chat_id(message: Message) -> None:
    try:
        await message.answer(text=str(message.chat.id))
    except Exception as e:
        logger.warning(
            f"error processing in function:{cur_func_name()}, for agent:{pool.bot_by_token(message.bot.token)["agent_id"]} token:{message.bot.token} err: {str(e)}"
        )


## group commands and messages


@general_router.message(
    CommandStart(),
    NoBotFilter(),
    WhitelistedChatIDsFilter(),
    GroupOnlyFilter(),
    TextOnlyFilter(),
)
async def gp_command_start(message: Message):
    try:
        group_title = message.from_user.first_name
        await message.answer(
            text=f"🤖 Hi Everybody, {group_title}! 🎉\nGreetings, traveler of the digital realm! You've just awakened the mighty powers of this chat bot. Brace yourself for an adventure filled with wit, wisdom, and possibly a few jokes.",
        )
    except Exception as e:
        logger.warning(
            f"error processing in function:{cur_func_name()}, for agent:{pool.bot_by_token(message.bot.token)["agent_id"]} token:{message.bot.token} err: {str(e)}"
        )


@general_router.message(
    WhitelistedChatIDsFilter(), NoBotFilter(), GroupOnlyFilter(), TextOnlyFilter()
)
async def gp_process_message(message: Message) -> None:
    bot = await message.bot.get_me()
    if (
        message.reply_to_message
        and message.reply_to_message.from_user.id == message.bot.id
    ) or bot.username in message.text:
        cached_bot = pool.bot_by_token(message.bot.token)
        if cached_bot is None:
            logger.warning(f"bot with token {message.bot.token} not found in cache.")
            return

        try:
            agent_id = cached_bot["agent_id"]
            thread_id = pool.agent_thread_id(
                agent_id, cached_bot["is_public"], message.chat.id
            )
            response = execute_agent(agent_id, message.text, thread_id)
            await message.answer(
                text="\n".join(response),
                reply_to_message_id=message.message_id,
            )
        except Exception as e:
            logger.warning(
                f"error processing in function:{cur_func_name()}, for agent:{cached_bot["agent_id"]} token:{message.bot.token}, err={str(e)}"
            )


## direct commands and messages


@general_router.message(
    CommandStart(), NoBotFilter(), WhitelistedChatIDsFilter(), TextOnlyFilter()
)
async def command_start(message: Message) -> None:
    try:
        first_name = message.from_user.first_name
        await message.answer(
            text=f"🤖 Hi, {first_name}! 🎉\nGreetings, traveler of the digital realm! You've just awakened the mighty powers of this chat bot. Brace yourself for an adventure filled with wit, wisdom, and possibly a few jokes.",
        )
    except Exception as e:
        logger.warning(
            f"error processing in function:{cur_func_name()}, for agent:{pool.bot_by_token(message.bot.token)["agent_id"]} token:{message.bot.token} err: {str(e)}"
        )


@general_router.message(
    TextOnlyFilter(),
    NoBotFilter(),
    WhitelistedChatIDsFilter(),
)
async def process_message(message: Message) -> None:
    cached_bot = pool.bot_by_token(message.bot.token)
    if cached_bot is None:
        logger.warning(f"bot with token {message.bot.token} not found in cache.")
        return

    try:
        agent_id = cached_bot["agent_id"]
        thread_id = pool.agent_thread_id(
            agent_id, cached_bot["is_public"], message.chat.id
        )
        response = execute_agent(agent_id, message.text, thread_id)
        await message.answer(
            text="\n".join(response),
            reply_to_message_id=message.message_id,
        )
    except Exception as e:
        logger.warning(
            f"error processing in function:{cur_func_name()}, for agent:{cached_bot["agent_id"]} token:{message.bot.token} err:{str(e)}"
        )
