from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from utils.l18n import l18n
from utils.database import get_user_data
from utils.keyboards import get_menu_keyboard

start_router = Router()


@start_router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await get_user_data(message.from_user)  # Make sure to create user on first use
    if message.chat.type != "private":
        raise Exception("Not allowed to use outside of private chat")

    await message.answer(
        l18n.get("ru", "messages", "start"),
        reply_markup=get_menu_keyboard(message.chat.username)
    )


@start_router.callback_query(F.data == "cancel")
async def cancel_callback(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await cancel_handler(callback_query.message, state)


@start_router.message(F.text.casefold() == l18n.get("ru", "buttons", "cancel").casefold())
async def cancel_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await command_start_handler(message)
