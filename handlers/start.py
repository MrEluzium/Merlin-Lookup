from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup

from utils.l18n import l18n
from utils.database import get_user_data

start_router = Router()


@start_router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await get_user_data(message.from_user)  # Make sure to create user on first use
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=l18n.get("ru", "buttons", "start", "fragment_search"))],
            [KeyboardButton(text=l18n.get("ru", "buttons", "start", "profile"))]
        ],
        resize_keyboard=True,
        is_persistent=True
    )
    await message.answer(
        l18n.get("ru", "messages", "start"),
        reply_markup=keyboard
    )
