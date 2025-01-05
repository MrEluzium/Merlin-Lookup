from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup

from utils.l18n import l18n

start_router = Router()


@start_router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
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
