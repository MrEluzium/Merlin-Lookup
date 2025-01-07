import os
from typing import Callable
from functools import wraps
from datetime import datetime, UTC
from dataclasses import dataclass

import asyncpg
from aiogram.types import User
from asyncpg import Pool

from utils.config_parser import read_config

ACCURACY_THRESHOLD = 0.6
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SQL_DIR = os.path.join(PROJECT_ROOT, 'sql')
pool: Pool | None = None

class SQLFiles:
    INSERT_USER = "users/insert_user.sql"
    GET_USER_BY_USER_ID = "users/get_user_by_user_id.sql"
    GET_USER_BY_USER_NAME = "users/get_user_by_user_name.sql"
    CHECK_USER_BY_USER_ID = "users/check_user_by_user_id.sql"
    UPDATE_USERNAME = "users/update_username.sql"

    UPDATE_PAID_TOKENS = "users/update_paid_tokens.sql"
    UPDATE_FREE_TOKENS = "users/update_free_tokens.sql"
    UPDATE_PAID_TOKENS_SPENT = "users/update_paid_tokens_spent.sql"

    INCREASE_PAID_TOKENS = "users/increase_paid_tokens.sql"
    INCREASE_FREE_TOKENS = "users/increase_free_tokens.sql"
    INCREASE_PAID_TOKENS_SPENT = "users/increase_paid_tokens_spent.sql"

    DECREASE_PAID_TOKENS = "users/decrease_paid_tokens.sql"
    DECREASE_FREE_TOKENS = "users/decrease_free_tokens.sql"

    INSERT_FRAGMENT_RECORD = "fragments/insert_fragment_record.sql"

    BOOKS_FUZZY_SEARCH = "library/books_fuzzy_search.sql"
    AUTHORS_FUZZY_SEARCH = "library/authors_fuzzy_search.sql"
    BOOKS_TITLE_FUZZY_SEARCH = "library/books_title_fuzzy_search.sql"

    SELECT_BOOK_BY_ID = "library/select_book_by_id.sql"
    SELECT_BOOK_BY_URL = "library/select_book_by_url.sql"
    SELECT_BOOKS_BY_AUTHOR = "library/select_books_by_author.sql"


@dataclass
class UchibotUserData:
    id: int
    user_id: int
    user_name: str
    registration_date: datetime = datetime.now(UTC)
    paid_tokens: int = 0
    free_tokens: int = 3
    total_paid_tokens_spent: int = 0


class SearchResultSimilarityCheck:
    def __init__(self, similarity: float):
        self.similarity = similarity

    def accurate_enough(self) -> bool:
        """
        Checks if the search result is accurate enough to its query.
        """
        return self.similarity >= ACCURACY_THRESHOLD


class BookSearchResult(SearchResultSimilarityCheck):
    def __init__(self, id: int = None, title: str = None, author: str = None, url: str = None, similarity: float = .0):
        super().__init__(similarity)
        self.id: int = id
        self.title: str = title
        self.author: str = author
        self.archive: str = url.split('/')[-2]
        self.filename: str = url.split('/')[-1]

    def __iter__(self):
        return iter((self.id, self.title, self.author, self.archive, self.filename, self.similarity))


class AuthorSearchResult(SearchResultSimilarityCheck):
    def __init__(self, author: str, similarity: float):
        super().__init__(similarity)
        self.author: str = author

    def __iter__(self):
        return iter((self.author, self.similarity))


async def load_sql(filename: str):
    file_path = os.path.join(SQL_DIR, filename)
    with open(file_path, 'r') as file:
        return file.read()


async def connect_to_db_pool():
    config = read_config("config.ini")
    return await asyncpg.create_pool(
        host=config["Database"]["db_host"],
        port=config["Database"]["db_port"],
        user=config["Database"]["db_user"],
        password=config["Database"]["db_password"],
        database=config["Database"]["db_name"]
    )


async def init_pool():
    global pool
    pool = await connect_to_db_pool()


def check_user(func: Callable):
    @wraps(func)
    async def wrapper(user: User, *args, **kwargs):
        if user.is_bot:
            return await func(user, *args, **kwargs)
        async with pool.acquire() as conn:
            user_exists = (await conn.fetchrow((await load_sql(SQLFiles.CHECK_USER_BY_USER_ID)), user.id))["exists"]

            if not user_exists:
                print(f"User {user.username}({user.id}) does not exist. Creating it...")
                await conn.execute((await load_sql(SQLFiles.INSERT_USER)), user.id, user.username)
            else:
                user_data = await conn.fetchrow((await load_sql(SQLFiles.GET_USER_BY_USER_ID)), user.id)
                if user_data["user_name"] != user.username:
                    print(f"Username for {user.username}({user.id}) does not match. Updating...")
                    sql_query = await load_sql(SQLFiles.UPDATE_USERNAME)
                    await conn.execute(sql_query, user.id, user.username)

            return await func(user, *args, **kwargs)
    return wrapper


@check_user
async def get_user_data(user: User) -> UchibotUserData | None:
    user_data = None
    async with pool.acquire() as conn:
        sql_query = await load_sql(SQLFiles.GET_USER_BY_USER_ID)
        user = await conn.fetchrow(sql_query, user.id)
        if user:
            user_data = UchibotUserData(
                id=user["id"],
                user_id=user["user_id"],
                user_name=user["user_name"],
                registration_date=user["registration_date"],
                paid_tokens=user["paid_tokens"],
                free_tokens=user["free_tokens"],
                total_paid_tokens_spent=user["total_paid_tokens_spent"],
            )
    return user_data


async def get_user_by_name(username: str) -> UchibotUserData | None:
    user_data = None
    async with pool.acquire() as conn:
        sql_query = await load_sql(SQLFiles.GET_USER_BY_USER_NAME)
        user = await conn.fetchrow(sql_query, username)
        if user:
            user_data = UchibotUserData(
                id=user["id"],
                user_id=user["user_id"],
                user_name=user["user_name"],
                registration_date=user["registration_date"],
                paid_tokens=user["paid_tokens"],
                free_tokens=user["free_tokens"],
                total_paid_tokens_spent=user["total_paid_tokens_spent"],
            )
    return user_data


@check_user
async def user_set_paid_tokens(user: User, new_tokens: int) -> None:
    """
    Sets the exact number of paid tokens for a user.
    :param user: User to process
    :param new_tokens: Nuber of tokens to set
    """
    async with pool.acquire() as conn:
        sql_query = await load_sql(SQLFiles.UPDATE_PAID_TOKENS)
        await conn.execute(sql_query, user.id, new_tokens)


@check_user
async def user_increase_paid_tokens(user: User, add_tokens: int) -> int:
    """
    Increase the number of paid tokens of user.
    :param user: User to process
    :param add_tokens: Tokens to add
    :return: Number of paid tokens after increase
    """
    async with pool.acquire() as conn:
        sql_query = await load_sql(SQLFiles.INCREASE_PAID_TOKENS)
        return await conn.fetchval(sql_query, user.id, add_tokens)


async def user_increase_paid_tokens_by_id(user_id: int, add_tokens: int) -> int:
    """
    Increase the number of paid tokens of user.
    :param user_id: ID of user to process
    :param add_tokens: Tokens to add
    :return: Number of paid tokens after increase
    """
    async with pool.acquire() as conn:
        sql_query = await load_sql(SQLFiles.INCREASE_PAID_TOKENS)
        return await conn.fetchval(sql_query, user_id, add_tokens)


@check_user
async def user_decrease_paid_tokens(user: User, del_tokens: int) -> bool:
    """
    Try to decrease the number of paid tokens if enough.
    :param user: User to process
    :param del_tokens: Tokens to remove
    :return: If was enough tokens to decrease, return True
    """
    async with pool.acquire() as conn:
        sql_query = await load_sql(SQLFiles.DECREASE_PAID_TOKENS)
        return await conn.fetchval(sql_query, user.id, del_tokens)


@check_user
async def user_set_free_tokens(user: User, new_tokens: int) -> None:
    """
    Sets the exact number of free tokens for a user.
    :param user: User to process
    :param new_tokens: Nuber of tokens to set
    """
    async with pool.acquire() as conn:
        sql_query = await load_sql(SQLFiles.UPDATE_FREE_TOKENS)
        await conn.execute(sql_query, user.id, new_tokens)


@check_user
async def user_increase_free_tokens(user: User, add_tokens: int) -> int:
    """
    Increase the number of free tokens of user.
    :param user: User to process
    :param add_tokens: Tokens to add
    :return: Number of free tokens after increase
    """
    async with pool.acquire() as conn:
        sql_query = await load_sql(SQLFiles.INCREASE_FREE_TOKENS)
        return await conn.fetchval(sql_query, user.id, add_tokens)


@check_user
async def user_decrease_free_tokens(user: User, del_tokens: int) -> bool:
    """
    Try to decrease the number of free tokens if enough.
    :param user: User to process
    :param del_tokens: Tokens to remove
    :return: If was enough tokens to decrease, return True
    """
    async with pool.acquire() as conn:
        sql_query = await load_sql(SQLFiles.DECREASE_FREE_TOKENS)
        return await conn.fetchval(sql_query, user.id, del_tokens)


@check_user
async def user_set_paid_tokens_spent(user: User, new_tokens: int) -> None:
    """
    Sets the exact number of user's total paid tokens spent.
    :param user: User to process
    :param new_tokens: Nuber of tokens to set
    """
    async with pool.acquire() as conn:
        sql_query = await load_sql(SQLFiles.UPDATE_PAID_TOKENS_SPENT)
        await conn.execute(sql_query, user.id, new_tokens)


@check_user
async def user_increase_paid_tokens_spent(user: User, add_tokens: int) -> int:
    """
    Increase the number of user's total paid tokens spent.
    :param user: User to process
    :param add_tokens: Tokens to add
    :return: Number of paid tokens spent after increase
    """
    async with pool.acquire() as conn:
        sql_query = await load_sql(SQLFiles.INCREASE_PAID_TOKENS_SPENT)
        return await conn.fetchval(sql_query, user.id, add_tokens)


@check_user
async def add_fragment_record(user: User, book_id: int, word_list: list[str], text_fragment: str) -> None:
    async with pool.acquire() as conn:
        sql_query = await load_sql(SQLFiles.INSERT_FRAGMENT_RECORD)
        await conn.execute(sql_query, user.id, book_id, word_list, text_fragment)


async def search_books(title: str = None, author_name: str = None) -> list[BookSearchResult] | None:
    """
    Search books by title and author with fuzzy matching.

    Args:
        title (str): Title of the book.
        author_name (str): Author name of the book.

    Returns:
        list[BookSearchResult]: Matched books and accuracy.
    """
    if title and author_name:
        query = SQLFiles.BOOKS_FUZZY_SEARCH
        query_var = title + " " + author_name
    elif not author_name:
        query = SQLFiles.BOOKS_TITLE_FUZZY_SEARCH
        query_var = title
    elif not title:
        query = SQLFiles.SELECT_BOOKS_BY_AUTHOR
        query_var = author_name
    else:
        return None

    results = []
    async with pool.acquire() as conn:
        sql_query = await load_sql(query)
        rows = await conn.fetch(sql_query, query_var)
        for row in rows:
            results.append(BookSearchResult(*row.values()))
    return results


async def search_authors(author_name: str) -> list[AuthorSearchResult]:
    """
    Search authors by name with fuzzy matching.

    Args:
        author_name (str): The search query (e.g., author name).

    Returns:
        list[AuthorSearchResult]: Matched authors and accuracy.
    """
    results = []
    async with pool.acquire() as conn:
        sql_query = await load_sql(SQLFiles.AUTHORS_FUZZY_SEARCH)
        rows = await conn.fetch(sql_query, author_name)
        for row in rows:
            results.append(AuthorSearchResult(*row.values()))
    return results

async def get_book_by_id(book_id: int) -> BookSearchResult:
    async with pool.acquire() as conn:
        sql_query = await load_sql(SQLFiles.SELECT_BOOK_BY_ID)
        row = await conn.fetchrow(sql_query, book_id)
    return BookSearchResult(*row, 1)


async def get_book_by_url(url: str) -> BookSearchResult:
    async with pool.acquire() as conn:
        sql_query = await load_sql(SQLFiles.SELECT_BOOK_BY_URL)
        row = await conn.fetchrow(sql_query, url)
    return BookSearchResult(*row, 1)


async def refund_all_free_tokens():
    async with pool.acquire() as conn:
        await conn.execute('''UPDATE public.uchibot_users SET free_tokens = 3;''')
