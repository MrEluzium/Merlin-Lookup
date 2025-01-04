import re

from aiogram import Router, F
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, \
    CallbackQuery, InlineKeyboardMarkup, LinkPreviewOptions
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils import library
from utils.l18n import l18n
from utils.translate import translate_words_in_text
from utils.database import search_books, search_authors, get_book_by_id
from handlers.start import command_start_handler


class FragmentSearchStateGroup(StatesGroup):
    ask_author = State()
    search_author = State()
    select_author = State()
    ask_title = State()
    search_book = State()
    select_book = State()
    ask_words = State()
    search_fragment = State()


class BookCallbackFactory(CallbackData, prefix="book"):
    id: int


class AuthorCallbackFactory(CallbackData, prefix="author"):
    name: str


fragment_router = Router()
CANCEL_BUTTON = KeyboardButton(text=l18n.get("ru", "buttons", "cancel"))
MENU_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=l18n.get("ru", "buttons", "start", "fragment_search"))]],
    resize_keyboard=True,
    is_persistent=True
)


@fragment_router.callback_query(F.data == "cancel")
async def cancel_callback(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await cancel_handler(callback_query.message, state)


@fragment_router.message(F.text.casefold() == l18n.get("ru", "buttons", "cancel").casefold())
async def cancel_handler(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    # if current_state is None:
    #     return
    await state.clear()
    await command_start_handler(message)


@fragment_router.message(F.text.casefold() == l18n.get("ru", "buttons", "start", "fragment_search").casefold())
async def fragment_handler(message: Message, state: FSMContext) -> None:
    await ask_author(message, state)


@fragment_router.callback_query(F.data == "ask_author")
async def ask_author_callback(callback_query: CallbackQuery, state: FSMContext) -> None:
    await callback_query.answer()
    await ask_author(callback_query.message, state)


async def ask_author(message: Message, state: FSMContext) -> None:
    await state.set_state(FragmentSearchStateGroup.ask_author)
    await message.answer(
        l18n.get("ru", "messages", "fragment", "specify_author"),
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[CANCEL_BUTTON]],
            resize_keyboard=True,
            input_field_placeholder="Укажите имя автора"
        )
    )


@fragment_router.message(FragmentSearchStateGroup.ask_author)
async def process_author(message: Message, state: FSMContext) -> None:
    if message.text == '-' or message.text.lower() == "не знаю":
        await state.update_data(author="")
        await ask_title(message, state)
        return

    author_name = message.text
    await state.set_state(FragmentSearchStateGroup.search_author)
    await message.answer(
        l18n.get("ru", "messages", "fragment", "author_processing"),
        reply_markup=ReplyKeyboardRemove()
    )

    search = await search_authors(author_name)
    if not search:
        await state.update_data(author="")

        builder = InlineKeyboardBuilder()
        builder.adjust()
        builder.row(InlineKeyboardButton(
            text=l18n.get("ru", "buttons", "continue_to_title"),
            callback_data="ask_title")
        )
        builder.row(InlineKeyboardButton(
            text=l18n.get("ru", "buttons", "start_again"),
            callback_data="ask_author")
        )
        builder.row(InlineKeyboardButton(
            text=l18n.get("ru", "buttons", "cancel"),
            callback_data="cancel")
        )
        await message.answer(
            l18n.get("ru", "messages", "fragment", "author_not_found").format(
                author=author_name
            ),
            reply_markup=builder.as_markup()
        )
        return

    if search[0].accurate_enough():
        author_name = search[0].author
        await state.update_data(author=author_name)
        await message.answer(
            l18n.get("ru", "messages", "fragment", "author_found").format(
                author=author_name
            ),
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[CANCEL_BUTTON]],
                resize_keyboard=True
            )
        )
        await ask_title(message, state)

    else:
        builder = InlineKeyboardBuilder()
        builder.adjust()
        for author in search:
            builder.row(InlineKeyboardButton(
                text=f"{author.author}",
                callback_data=AuthorCallbackFactory(name=author.author).pack())
            )
        await message.answer(
            l18n.get("ru", "messages", "fragment", "author_select").format(
                author=author_name
            ),
            reply_markup=builder.as_markup()
        )


@fragment_router.callback_query(AuthorCallbackFactory.filter())
async def choose_author_callback(callback: CallbackQuery, callback_data: AuthorCallbackFactory, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(FragmentSearchStateGroup.select_author)
    author_name = callback_data.name
    await state.update_data(author=author_name)
    await callback.message.answer(
        l18n.get("ru", "messages", "fragment", "author_found").format(
            author=author_name
        ),
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[CANCEL_BUTTON]],
            resize_keyboard=True
        )
    )
    await ask_title(callback.message, state)


@fragment_router.callback_query(F.data == "ask_title")
async def ask_title_callback(callback_query: CallbackQuery, state: FSMContext) -> None:
    await callback_query.answer()
    await ask_title(callback_query.message, state)


async def ask_title(message: Message, state: FSMContext) -> None:
    await state.set_state(FragmentSearchStateGroup.ask_title)
    data = await state.get_data()
    if not data["author"]:
        await message.answer(
            l18n.get("ru", "messages", "fragment", "specify_title_no_author"),
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[CANCEL_BUTTON]],
                resize_keyboard=True,
                input_field_placeholder="Укажите название книги"
            )
        )
    else:
        builder = InlineKeyboardBuilder()
        builder.adjust()
        builder.row(InlineKeyboardButton(
            text=l18n.get("ru", "buttons", "books_by_author"),
            callback_data="books_by_author"
        ))
        await message.answer(
            l18n.get("ru", "messages", "fragment", "specify_title_author_selected"),
            reply_markup=builder.as_markup()
        )


@fragment_router.callback_query(F.data == "books_by_author")
async def books_by_author_callback(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(FragmentSearchStateGroup.select_book)
    data = await state.get_data()
    search = await search_books(author_name=data["author"])
    if not search:
        raise Exception(f"No books found for author {data['author']}, but author already selected.")

    builder = InlineKeyboardBuilder()
    builder.adjust()
    for book in search:
        builder.row(InlineKeyboardButton(
            text=f"{book.author} - {book.title}",
            callback_data=BookCallbackFactory(id=book.id).pack()
        ))
    await callback_query.answer()
    await callback_query.message.answer(
        l18n.get("ru", "messages", "fragment", "author_book_list").format(
            author=data["author"]
        ),
        reply_markup=builder.as_markup()
    )


@fragment_router.message(FragmentSearchStateGroup.ask_title)
async def process_title(message: Message, state: FSMContext) -> None:
    await state.set_state(FragmentSearchStateGroup.search_book)
    data = await state.get_data()

    await message.answer(
        l18n.get("ru", "messages", "fragment", "book_processing"),
        reply_markup=ReplyKeyboardRemove()
    )

    if data["author"]:
        search = await search_books(title=message.text, author_name=data["author"])
    else:
        search = await search_books(title=message.text)

    if not search:
        await state.clear()
        builder = InlineKeyboardBuilder()
        builder.adjust()
        builder.row(InlineKeyboardButton(
            text=l18n.get("ru", "buttons", "start_again"),
            callback_data="ask_author")
        )
        builder.row(InlineKeyboardButton(
            text=l18n.get("ru", "buttons", "cancel"),
            callback_data="cancel")
        )

        if data["author"]:
            await message.answer(
                l18n.get("ru", "messages", "fragment", "book_not_found").format(
                    author=data["author"],
                    title=message.text
                ),
                reply_markup=builder.as_markup()
            )
        else:
            await message.answer(
                l18n.get("ru", "messages", "fragment", "book_not_found_title").format(
                    title=message.text
                ),
                reply_markup=builder.as_markup()
            )
        return

    if len(search) == 1:
        await state.update_data(title=search[0].title)
        await state.update_data(book_id=search[0].id)
        await message.answer(
            l18n.get("ru", "messages", "fragment", "book_selected").format(
                title=search[0].title,
                author=search[0].author
            ),
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[CANCEL_BUTTON]],
                resize_keyboard=True
            )
        )
        await ask_words(message, state)

    else:
        builder = InlineKeyboardBuilder()
        builder.adjust()
        for book in search:
            builder.row(InlineKeyboardButton(
                text=f"{book.author} - {book.title}",
                callback_data=BookCallbackFactory(id=book.id).pack()
            ))

        if data["author"]:
            query = data["author"] + ' - ' + message.text
        else:
            query = message.text

        await message.answer(
            l18n.get("ru", "messages", "fragment", "low_accuracy").format(
                query=query
            ),
            reply_markup=builder.as_markup()
        )


@fragment_router.callback_query(BookCallbackFactory.filter())
async def choose_book_callback(callback: CallbackQuery, callback_data: BookCallbackFactory, state: FSMContext) -> None:
    await state.set_state(FragmentSearchStateGroup.select_book)
    book = await get_book_by_id(callback_data.id)

    if not book:
        raise Exception(f"No books found by selected ID {callback_data.id}.")

    await state.update_data(book_id=book.id)
    await callback.answer()
    await callback.message.answer(
        l18n.get("ru", "messages", "fragment", "book_selected").format(
            title=book.title,
            author=book.author
        ),
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[CANCEL_BUTTON]],
            resize_keyboard=True
        )
    )
    await ask_words(callback.message, state)


@fragment_router.callback_query(F.data == "ask_words")
async def ask_words_callback(callback_query: CallbackQuery, state: FSMContext) -> None:
    await callback_query.answer()
    await ask_words(callback_query.message, state)


async def ask_words(message: Message, state: FSMContext) -> None:
    await state.set_state(FragmentSearchStateGroup.ask_words)
    await message.answer(
        l18n.get("ru", "messages", "fragment", "specify_words_query"),
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[CANCEL_BUTTON]],
            resize_keyboard=True,
            input_field_placeholder="Введите три существительных"
        )
    )


@fragment_router.message(FragmentSearchStateGroup.ask_words)
async def process_words(message: Message, state: FSMContext) -> None:
    words = message.text.split(" ")
    clean_words = []
    for word in words:
        clean_word = re.sub(r'[^a-zA-Zа-яА-ЯёЁ]', '', word)
        if clean_word.isalpha():
            clean_words.append(clean_word)

    if len(clean_words) != 3:
        await message.answer(
            l18n.get("ru", "messages", "fragment", "words_wrong_format"),
            reply_markup=ReplyKeyboardRemove()
        )
        await ask_words(message, state)
        return

    await state.update_data(words=clean_words)
    await search_fragment(message, state)


async def search_fragment(message: Message, state: FSMContext) -> None:
    await state.set_state(FragmentSearchStateGroup.search_fragment)
    await message.answer(
        l18n.get("ru", "messages", "fragment", "fragment_processing"),
        reply_markup=ReplyKeyboardRemove()
    )

    data = await state.get_data()
    if data["book_id"]:
        book = await get_book_by_id(data["book_id"])
    else:
        raise Exception(f"ID is not specified by the time to get fragment.")

    if not book:
        await state.clear()
        await message.answer(
            l18n.get("ru", "messages", "fragment", "book_not_found").format(
                title=data["title"],
                author=data["author"]
            ),
            reply_markup=MENU_KEYBOARD
        )
        return

    header_string = l18n.get("ru", "messages", "fragment", "fragment").format(
                title=book.title,
                author=book.author,
                words_query=', '.join(data["words"]),
                fragment=""
    )
    fragment = await library.process_fragment_search(
        book.archive,
        book.filename,
        data["words"],
        max_length=4049-len(header_string)
    )

    await state.clear()
    if not fragment:
        await message.answer(
            l18n.get("ru", "messages", "fragment", "fragment_not_found").format(
                title=book.title,
                author=book.author,
                words_query=', '.join(data["words"])
            ),
            reply_markup=MENU_KEYBOARD
        )
    else:
        translated_fragment = await translate_words_in_text(fragment, data["words"])
        await message.answer(
            l18n.get("ru", "messages", "fragment", "fragment").format(
                title=book.title,
                author=book.author,
                words_query=', '.join(data["words"]),
                fragment=translated_fragment
            ),
            reply_markup=MENU_KEYBOARD,
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )
