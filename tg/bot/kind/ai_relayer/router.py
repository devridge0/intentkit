from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from app.core.ai import execute_agent
from tg.bot import pool
from tg.bot.filter.chat_type import GroupOnlyFilter

general_router = Router()


class GeneralForm(StatesGroup):
    name = State()
    like_bots = State()
    language = State()


## group commands and messages


@general_router.message(GroupOnlyFilter(), CommandStart())
async def gp_command_start(message: Message):
    group_title = message.from_user.first_name
    await message.answer(
        text=f"🤖 Hi Everybody, {group_title}! 🎉\nGreetings, traveler of the digital realm! You've just awakened the mighty powers of this chat bot. Brace yourself for an adventure filled with wit, wisdom, and possibly a few jokes.",
    )


@general_router.message(GroupOnlyFilter())
async def gp_process_message(message: Message) -> None:
    bot = await message.bot.get_me()
    if (
        message.reply_to_message
        and message.reply_to_message.from_user.id == message.bot.id
    ) or bot.username in message.text:
        agent_id = pool.bot_by_token(message.bot.token)["agent_id"]
        thread_id = pool.agent_thread_id(agent_id, message.chat.id)
        response = execute_agent(agent_id, message.text, thread_id)
        await message.answer(
            text="\n".join(response),
            reply_to_message_id=message.message_id,
        )


@general_router.message(CommandStart())
async def command_start(message: Message, state: FSMContext) -> None:
    first_name = message.from_user.first_name
    await message.answer(
        text=f"🤖 Hi, {first_name}! 🎉\nGreetings, traveler of the digital realm! You've just awakened the mighty powers of this chat bot. Brace yourself for an adventure filled with wit, wisdom, and possibly a few jokes.",
    )


@general_router.message()
async def process_message(message: Message, state: FSMContext) -> None:
    agent_id = pool.bot_by_token(message.bot.token)["agent_id"]
    thread_id = pool.agent_thread_id(agent_id, message.chat.id)
    response = execute_agent(agent_id, message.text, thread_id)
    await message.answer(
        text="\n".join(response),
        reply_to_message_id=message.message_id,
    )


# @general_router.message()
# async def process_name_group(message: Message, state: FSMContext) -> None:
#     await state.update_data(name=message.text)
#     await state.set_state(GeneralForm.like_bots)
#     await message.answer(
#         f"Nice to meet you, {html.quote(message.text)}!\nDid you like to write bots?",
#         reply_markup=ReplyKeyboardMarkup(
#             keyboard=[
#                 [
#                     KeyboardButton(text="Yes"),
#                     KeyboardButton(text="No"),
#                 ]
#             ],
#             resize_keyboard=True,
#         ),
#     )


# @general_router.message(Command("cancel"))
# @general_router.message(F.text.casefold() == "cancel")
# async def cancel_handler(message: Message, state: FSMContext) -> None:
#     """
#     Allow user to cancel any action
#     """
#     current_state = await state.get_state()
#     if current_state is None:
#         return

#     logging.info("Cancelling state %r", current_state)
#     await state.clear()
#     await message.answer(
#         "Cancelled.",
#         reply_markup=ReplyKeyboardRemove(),
#     )


# @general_router.message(GeneralForm.name)
# async def process_name(message: Message, state: FSMContext) -> None:
#     await state.update_data(name=message.text)
#     await state.set_state(GeneralForm.like_bots)
#     await message.answer(
#         f"Nice to meet you, {html.quote(message.text)}!\nDid you like to write bots?",
#         reply_markup=ReplyKeyboardMarkup(
#             keyboard=[
#                 [
#                     KeyboardButton(text="Yes"),
#                     KeyboardButton(text="No"),
#                 ]
#             ],
#             resize_keyboard=True,
#         ),
#     )


# @general_router.message(GeneralForm.like_bots, F.text.casefold() == "no")
# async def process_dont_like_write_bots(message: Message, state: FSMContext) -> None:
#     data = await state.get_data()
#     await state.clear()
#     await message.answer(
#         "Not bad not terrible.\nSee you soon.",
#         reply_markup=ReplyKeyboardRemove(),
#     )
#     await show_summary(message=message, data=data, positive=False)


# @general_router.message(GeneralForm.like_bots, F.text.casefold() == "yes")
# async def process_like_write_bots(message: Message, state: FSMContext) -> None:
#     await state.set_state(GeneralForm.language)

#     await message.reply(
#         "Cool! I'm too!\nWhat programming language did you use for it?",
#         reply_markup=ReplyKeyboardRemove(),
#     )


# @general_router.message(GeneralForm.like_bots)
# async def process_unknown_write_bots(message: Message) -> None:
#     await message.reply("I don't understand you :(")


# @general_router.message(GeneralForm.language)
# async def process_language(message: Message, state: FSMContext) -> None:
#     data = await state.update_data(language=message.text)
#     await state.clear()

#     if message.text.casefold() == "python":
#         await message.reply(
#             "Python, you say? That's the language that makes my circuits light up! 😉"
#         )

#     await show_summary(message=message, data=data)


# async def show_summary(
#     message: Message, data: Dict[str, Any], positive: bool = True
# ) -> None:
#     name = data["name"]
#     language = data.get("language", "<something unexpected>")
#     text = f"I'll keep in mind that, {html.quote(name)}, "
#     text += (
#         f"you like to write bots with {html.quote(language)}."
#         if positive
#         else "you don't like to write bots, so sad..."
#     )
#     await message.answer(text=text, reply_markup=ReplyKeyboardRemove())
