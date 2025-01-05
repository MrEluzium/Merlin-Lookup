from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery, InlineKeyboardMarkup

from utils import database
from utils.l18n import l18n

profile_router = Router()


@profile_router.message(F.text.casefold() == l18n.get("ru", "buttons", "start", "profile").casefold())
async def profile_handler(message: Message) -> None:
    user_data = await database.get_user_data(message.from_user)
    await message.answer(
        l18n.get("ru", "messages", "profile", "data").format(
            name=message.from_user.full_name,
            free_tokens=user_data.free_tokens,
            paid_tokens=user_data.paid_tokens
        ),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(
                    text=l18n.get("ru", "buttons", "profile", "pay"),
                    callback_data="pay"
                )
            ]])
    )


@profile_router.callback_query(F.data == "pay")
async def pay_callback_query(callback_query: CallbackQuery) -> None:
    new_tokens = await database.user_increase_paid_tokens(callback_query.from_user, 15)
    await callback_query.answer()
    await callback_query.message.answer(
        f"+15 = {new_tokens}"
    )
