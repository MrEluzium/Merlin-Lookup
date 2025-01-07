from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from utils.l18n import l18n
from utils.config_parser import read_config

CANCEL_BUTTON = KeyboardButton(text=l18n.get("ru", "buttons", "cancel"))


def get_menu_keyboard(username: str) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=l18n.get("ru", "buttons", "start", "fragment_search")))
    builder.row(KeyboardButton(text=l18n.get("ru", "buttons", "start", "profile")))

    config = read_config("config.ini")
    if username in config["Bot"]["admin_users"]:
        builder.row(KeyboardButton(text=l18n.get("ru", "buttons", "start", "admin_panel")))

    markup = builder.as_markup()
    markup.resize_keyboard = True
    return markup

def get_admin_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=l18n.get("ru", "buttons", "admin", "user_lookup"),
        callback_data="user_lookup")
    )
    builder.row(InlineKeyboardButton(
        text=l18n.get("ru", "buttons", "admin", "add_admin"),
        callback_data="add_admin")
    )
    builder.row(InlineKeyboardButton(
        text=l18n.get("ru", "buttons", "admin", "remove_admin"),
        callback_data="remove_admin")
    )
    # builder.row(InlineKeyboardButton(
    #     text=l18n.get("ru", "buttons", "cancel"),
    #     callback_data="cancel")
    # )
    return builder.as_markup()
