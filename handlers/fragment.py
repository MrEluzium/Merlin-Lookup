from aiogram import Router, F
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, \
    CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils import library
from utils.l18n import l18n
from utils.database import search_books, get_book_by_id
from handlers.start import command_start_handler

class FragmentSearch(StatesGroup):
    author = State()
    title = State()
    words = State()
    search = State()


class BookCallbackFactory(CallbackData, prefix="book"):
    id: int


fragment_router = Router()
CANCEL_BUTTON = KeyboardButton(text=l18n.get("ru", "buttons", "cancel"))
MENU_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=l18n.get("ru", "buttons", "start", "fragment_search"))]],
    resize_keyboard=True,
    is_persistent=True
)


@fragment_router.message(F.text.casefold() == l18n.get("ru", "buttons", "cancel").casefold())
async def cancel_handler(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await command_start_handler(message)


@fragment_router.message(F.text.casefold() == l18n.get("ru", "buttons", "start", "fragment_search").casefold())
async def fragment_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(FragmentSearch.author)
    await message.answer(
        l18n.get("ru", "messages", "fragment", "specify_author"),
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[CANCEL_BUTTON]],
            resize_keyboard=True,
            input_field_placeholder="Укажите имя автора"
        )
    )


@fragment_router.message(FragmentSearch.author)
async def process_author(message: Message, state: FSMContext) -> None:
    await state.update_data(author=message.text)
    await state.set_state(FragmentSearch.title)
    await message.answer(
        l18n.get("ru", "messages", "fragment", "specify_title"),
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[CANCEL_BUTTON]],
            resize_keyboard=True,
            input_field_placeholder="Укажите название книги"
        )
    )


@fragment_router.message(FragmentSearch.title)
async def process_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text)
    await state.set_state(FragmentSearch.words)
    await message.answer(
        l18n.get("ru", "messages", "fragment", "specify_words_query"),
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[CANCEL_BUTTON]],
            resize_keyboard=True,
            input_field_placeholder="Введите три существительных через пробел"
        )
    )


@fragment_router.message(FragmentSearch.words)
async def process_words(message: Message, state: FSMContext) -> None:
    await state.update_data(words=message.text)
    await state.set_state(FragmentSearch.search)
    await message.answer(
        l18n.get("ru", "messages", "fragment", "processing"),
        reply_markup=ReplyKeyboardRemove()
    )

    data = await state.get_data()
    search = search_books(data["title"] + ' ' + data["author"])
    if not search:
        await state.clear()
        await message.answer(
            l18n.get("ru", "messages", "fragment", "not_found").format(
                title=data["title"],
                author=data["author"]
            ),
            reply_markup=MENU_KEYBOARD
        )
        return

    if search[0].accurate_enough():
        book = search[0]
        fragment = library.process_fragment_search(book.archive, book.filename, data["words"].split(' '))

        await state.clear()
        await message.answer(
            l18n.get("ru", "messages", "fragment", "fragment").format(
                title=book.title,
                author=book.author,
                words_query=data["words"],
                fragment=fragment
            ),
            reply_markup=MENU_KEYBOARD
        )
    else:
        builder = InlineKeyboardBuilder()
        builder.adjust()
        for book in search:
            builder.row(InlineKeyboardButton(
                text=f"{book.author} - {book.title}",
                callback_data=BookCallbackFactory(id=book.id).pack())
            )

        await message.answer(
            l18n.get("ru", "messages", "fragment", "low_accuracy").format(
                title=data["title"],
                author=data["author"]
            ),
            reply_markup=builder.as_markup()
        )


@fragment_router.callback_query(BookCallbackFactory.filter())
async def choose_book(callback: CallbackQuery, callback_data: BookCallbackFactory, state: FSMContext) -> None:
    data = await state.get_data()
    book = get_book_by_id(callback_data.id)
    fragment = library.process_fragment_search(book.archive, book.filename, data["words"].split(' '))

    await state.clear()
    await callback.message.edit_text(
        l18n.get("ru", "messages", "fragment", "fragment").format(
            title=book.title,
            author=book.author,
            words_query=data["words"],
            fragment=fragment
        )
    )
