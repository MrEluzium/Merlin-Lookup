import re
from functools import wraps
from typing import Callable

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery, InlineKeyboardMarkup, User, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from utils import database
from utils.database import UchibotUserData
from utils.l18n import l18n
from utils.config_parser import read_config, write_config
from utils.keyboards import CANCEL_BUTTON, get_admin_keyboard

profile_router = Router()


class AdminUserLookup(StatesGroup):
    specify_user = State()
    show_user = State()
    add_tokens = State()


class ChangeAdmin(StatesGroup):
    specify_new_admin = State()
    specify_old_admin = State()


def only_admin(func: Callable):
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        config = read_config("config.ini")
        if message.from_user.username in config["Bot"]["admin_users"]:
            return await func(message, *args, **kwargs)
    return wrapper


def only_admin_callback(func: Callable):
    @wraps(func)
    async def wrapper(callback_query: CallbackQuery, *args, **kwargs):
        config = read_config("config.ini")
        if callback_query.message.chat.username in config["Bot"]["admin_users"]:
            return await func(callback_query, *args, **kwargs)
    return wrapper


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
    await database.user_increase_paid_tokens(callback_query.from_user, 12)
    await callback_query.answer()
    user_data = await database.get_user_by_name(callback_query.message.chat.username)
    await callback_query.message.edit_text(
        l18n.get("ru", "messages", "profile", "data").format(
            name=callback_query.message.chat.full_name,
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


@profile_router.message(F.text.casefold() == l18n.get("ru", "buttons", "start", "admin_panel").casefold())
@only_admin
async def admin_menu(message: Message) -> None:

    await message.answer(
        l18n.get("ru", "messages", "admin", "admin_panel"),
        reply_markup=get_admin_keyboard()
    )


@profile_router.callback_query(F.data == "add_admin")
@only_admin_callback
async def add_admin_callback(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ChangeAdmin.specify_new_admin)
    await callback_query.answer()
    await callback_query.message.answer(
        l18n.get("ru", "messages", "admin", "specify_user"),
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[CANCEL_BUTTON]],
            resize_keyboard=True,
            input_field_placeholder="Укажите пользователя: @nickname"
        )
    )


@profile_router.message(ChangeAdmin.specify_new_admin)
@only_admin
async def add_admin(message: Message, state: FSMContext) -> None:
    if not bool(re.match(r"^@[a-zA-Z0-9_]+$", message.text)):
        await message.answer(
            l18n.get("ru", "messages", "admin", "wrong_username_format"),
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[CANCEL_BUTTON]],
                resize_keyboard=True,
                input_field_placeholder="Укажите пользователя: @nickname"
            )
        )
        return
    username = message.text[1:]
    config = read_config("config.ini")
    admins = config["Bot"]["admin_users"][1:-1].split(", ")

    if username in admins:
        await state.clear()
        await message.answer(
            l18n.get("ru", "messages", "admin", "already_admin").format(
                username=username
            )
        )
        return

    admins.append(username)
    config["Bot"]["admin_users"] = '[' + ", ".join(admins) + ']'
    write_config("config.ini", config)
    await state.clear()
    await message.answer(
        l18n.get("ru", "messages", "admin", "admin_added").format(
            username=username,
        ),
        reply_markup=get_admin_keyboard()
    )


@profile_router.callback_query(F.data == "remove_admin")
@only_admin_callback
async def remove_admin_callback(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ChangeAdmin.specify_old_admin)
    await callback_query.answer()
    await callback_query.message.answer(
        l18n.get("ru", "messages", "admin", "specify_user"),
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[CANCEL_BUTTON]],
            resize_keyboard=True,
            input_field_placeholder="Укажите пользователя: @nickname"
        )
    )


@profile_router.message(ChangeAdmin.specify_old_admin)
@only_admin
async def remove_admin(message: Message, state: FSMContext) -> None:
    if not bool(re.match(r"^@[a-zA-Z0-9_]+$", message.text)):
        await message.answer(
            l18n.get("ru", "messages", "admin", "wrong_username_format"),
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[CANCEL_BUTTON]],
                resize_keyboard=True,
                input_field_placeholder="Укажите пользователя: @nickname"
            )
        )
        return
    username = message.text[1:]
    config = read_config("config.ini")
    admins = config["Bot"]["admin_users"][1:-1].split(", ")

    if username not in admins:
        await message.answer(
            l18n.get("ru", "messages", "admin", "admin_not_found").format(
                username=username
            )
        )
        await message.answer(
            l18n.get("ru", "messages", "admin", "wrong_username_format"),
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[CANCEL_BUTTON]],
                resize_keyboard=True,
                input_field_placeholder="Укажите пользователя: @nickname"
            )
        )

    admins.remove(username)
    config["Bot"]["admin_users"] = '[' + ", ".join(admins) + ']'
    write_config("config.ini", config)
    await state.clear()
    await message.answer(
        l18n.get("ru", "messages", "admin", "admin_removed").format(
            username=username,
        ),
        reply_markup=get_admin_keyboard()
    )


@profile_router.callback_query(F.data == "user_lookup")
@only_admin_callback
async def admin_user_lookup_callback(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminUserLookup.specify_user)
    await callback_query.answer()
    await callback_query.message.answer(
        l18n.get("ru", "messages", "admin", "specify_user"),
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[CANCEL_BUTTON]],
            resize_keyboard=True,
            input_field_placeholder="Укажите пользователя: @nickname"
        )
    )


@profile_router.message(AdminUserLookup.specify_user)
@only_admin
async def admin_user_lookup(message: Message, state: FSMContext) -> None:
    if not bool(re.match(r"^@[a-zA-Z0-9_]+$", message.text)):
        await message.answer(
            l18n.get("ru", "messages", "admin", "wrong_username_format"),
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[CANCEL_BUTTON]],
                resize_keyboard=True,
                input_field_placeholder="Укажите пользователя: @nickname"
            )
        )
        return

    username = message.text[1:]
    await state.update_data(username=username)

    user_data = await database.get_user_by_name(username)
    if not user_data:
        await message.answer(
            l18n.get("ru", "messages", "admin", "user_not_found").format(
                username=username
            ),
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[CANCEL_BUTTON]],
                resize_keyboard=True,
                input_field_placeholder="Укажите пользователя: @nickname"
            )
        )
        return

    await show_user_info(state, message, user_data)


@profile_router.callback_query(F.data == "show_user_info")
@only_admin_callback
async def show_user_info_callback(callback_query: CallbackQuery, state: FSMContext) -> None:
    await callback_query.answer()
    await show_user_info(state)


async def show_user_info(state: FSMContext, message: Message | None = None, user_data: UchibotUserData | None = None) -> None:
    await state.set_state(AdminUserLookup.show_user)
    data = await state.get_data()
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=l18n.get("ru", "buttons", "admin", "add_tokens"),
        callback_data="add_tokens")
    )

    if user_data and message:
        user_info_message = await message.answer(
            l18n.get("ru", "messages", "admin", "user_data").format(
                username=user_data.user_name,
                free_tokens=user_data.free_tokens,
                paid_tokens=user_data.paid_tokens,
                paid_tokens_spent=user_data.total_paid_tokens_spent,
                registration_date=user_data.registration_date.strftime("%H:%M %d.%m.%Y")
            ),
            reply_markup=builder.as_markup()
        )
        await state.update_data(user_info_message=user_info_message)
        return

    user_info_message: Message = data["user_info_message"]
    username = data["username"]
    user_data = await database.get_user_by_name(username)
    if user_info_message and user_data:
        await user_info_message.edit_text(
            l18n.get("ru", "messages", "admin", "user_data").format(
                username=user_data.user_name,
                free_tokens=user_data.free_tokens,
                paid_tokens=user_data.paid_tokens,
                paid_tokens_spent=user_data.total_paid_tokens_spent,
                registration_date=user_data.registration_date.strftime("%H:%M %d.%m.%Y")
            ),
            reply_markup=builder.as_markup()
        )
        return

    raise Exception("No user info to show!")


@profile_router.callback_query(F.data == "add_tokens")
@only_admin_callback
async def add_tokens_callback(callback_query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    try:
        username = data["username"]
        user_data = await database.get_user_by_name(username)
    except KeyError:
        return

    await state.set_state(AdminUserLookup.add_tokens)
    await callback_query.answer()

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="Отмена",
        callback_data="show_user_info")
    )
    await callback_query.message.edit_text(
        l18n.get("ru", "messages", "admin", "specify_tokens_amount").format(username=user_data.user_name),
        reply_markup=builder.as_markup()
    )


@profile_router.message(AdminUserLookup.add_tokens)
@only_admin
async def add_tokens_to_user(message: Message, state: FSMContext) -> None:
    tokens_amount = message.text
    data = await state.get_data()
    user_data = await database.get_user_by_name(data["username"])
    if not tokens_amount.isdigit():
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="Отмена",
            callback_data="show_user_info")
        )
        await message.answer(
            l18n.get("ru", "messages", "admin", "specify_tokens_amount").format(username=user_data.user_name),
            reply_markup=builder.as_markup()
        )
    await database.user_increase_paid_tokens_by_id(user_data.user_id, int(tokens_amount))
    user_data = await database.get_user_by_name(data["username"])
    await show_user_info(state, message=message, user_data=user_data)
