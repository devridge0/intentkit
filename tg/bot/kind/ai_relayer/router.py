import inspect
import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from app.core.ai import execute_agent
from tg.bot import pool
from tg.bot.filter.chat_type import GroupOnlyFilter
from tg.bot.filter.content_type import TextOnlyFilter

logger = logging.getLogger(__name__)


def cur_func_name():
    return inspect.stack()[1][3]


def cur_mod_name():
    return inspect.getmodule(inspect.stack()[1][0]).__name__


general_router = Router()


class GeneralForm(StatesGroup):
    name = State()
    like_bots = State()
    language = State()


## group commands and messages


@general_router.message(GroupOnlyFilter(), TextOnlyFilter(), CommandStart())
async def gp_command_start(message: Message):
    if message.from_user.is_bot:
        return

    try:
        group_title = message.from_user.first_name
        await message.answer(
            text=f"🤖 Hi Everybody, {group_title}! 🎉\nGreetings, traveler of the digital realm! You've just awakened the mighty powers of this chat bot. Brace yourself for an adventure filled with wit, wisdom, and possibly a few jokes.",
        )
    except Exception as e:
        logger.warning(
            "error processing in function:{func}, for agent:{agent_id} token:{token}".format(
                func=cur_func_name,
                agent_id=pool.bot_by_token(message.bot.token).get("agent_id"),
                token=message.bot.token,
            )
        )


@general_router.message(GroupOnlyFilter(), TextOnlyFilter())
async def gp_process_message(message: Message) -> None:
    if message.from_user.is_bot:
        return

    bot = await message.bot.get_me()
    if (
        message.reply_to_message
        and message.reply_to_message.from_user.id == message.bot.id
    ) or bot.username in message.text:
        cached_bot = pool.bot_by_token(message.bot.token)
        if cached_bot is None:
            logger.warning(
                "bot with token {token} not found in cache.".format(
                    token=message.bot.token
                )
            )
            return

        try:
            agent_id = cached_bot["agent_id"]
            thread_id = pool.agent_thread_id(agent_id, message.chat.id)
            response = execute_agent(agent_id, message.text, thread_id)
            await message.answer(
                text="\n".join(response),
                reply_to_message_id=message.message_id,
            )
        except Exception as e:
            logger.warning(
                "error processing in function:{func}, for agent:{agent_id} token:{token}".format(
                    func=cur_func_name(),
                    agent_id=cached_bot.get("agent_id"),
                    token=message.bot.token,
                )
            )


## direct commands and messages


@general_router.message(CommandStart(), TextOnlyFilter())
async def command_start(message: Message, state: FSMContext) -> None:
    if message.from_user.is_bot:
        return

    try:
        first_name = message.from_user.first_name
        await message.answer(
            text=f"🤖 Hi, {first_name}! 🎉\nGreetings, traveler of the digital realm! You've just awakened the mighty powers of this chat bot. Brace yourself for an adventure filled with wit, wisdom, and possibly a few jokes.",
        )
    except Exception as e:
        logger.warning(
            "error processing in function:{func}, for agent:{agent_id} token:{token}".format(
                func=cur_func_name(),
                agent_id=pool.bot_by_token(message.bot.token).get("agent_id"),
                token=message.bot.token,
            )
        )


@general_router.message(
    TextOnlyFilter(),
)
async def process_message(message: Message, state: FSMContext) -> None:
    if message.from_user.is_bot:
        return

    cached_bot = pool.bot_by_token(message.bot.token)
    if cached_bot is None:
        logger.warning(
            "bot with token {token} not found in cache.".format(token=message.bot.token)
        )
        return

    try:
        agent_id = cached_bot["agent_id"]
        thread_id = pool.agent_thread_id(agent_id, message.chat.id)
        response = execute_agent(agent_id, message.text, thread_id)
        await message.answer(
            text="\n".join(response),
            reply_to_message_id=message.message_id,
        )
    except Exception as e:
        logger.warning(
            "error processing in function:{func}, for agent:{agent_id} token:{token}".format(
                func=cur_func_name(),
                agent_id=cached_bot.get("agent_id"),
                token=message.bot.token,
            )
        )
