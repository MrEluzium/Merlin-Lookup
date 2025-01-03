import os

import asyncpg

from utils.config_parser import read_config

ACCURACY_THRESHOLD = 0.6
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SQL_DIR = os.path.join(PROJECT_ROOT, 'sql')

class SQLFiles:
    BOOKS_FUZZY_SEARCH = "books_fuzzy_search.sql"
    AUTHORS_FUZZY_SEARCH = "authors_fuzzy_search.sql"
    BOOKS_TITLE_FUZZY_SEARCH = "books_title_fuzzy_search.sql"
    SELECT_BOOK_BY_ID = "select_book_by_id.sql"
    SELECT_BOOKS_BY_AUTHOR = "select_books_by_author.sql"

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


def load_sql(filename: str):
    file_path = os.path.join(SQL_DIR, filename)
    with open(file_path, 'r') as file:
        return file.read()


async def connect_to_db():
    config = read_config("config.ini")
    return await asyncpg.connect(
        host=config["Database"]["db_host"],
        port=config["Database"]["db_port"],
        user=config["Database"]["db_user"],
        password=config["Database"]["db_password"],
        database=config["Database"]["db_name"]
    )


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
    conn = await connect_to_db()
    try:
        sql_query = load_sql(query)
        rows = await conn.fetch(sql_query, query_var)
        for row in rows:
            results.append(BookSearchResult(*row.values()))
    finally:
        await conn.close()
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
    conn = await connect_to_db()
    try:
        sql_query = load_sql(SQLFiles.AUTHORS_FUZZY_SEARCH)
        rows = await conn.fetch(sql_query, author_name)
        for row in rows:
            results.append(AuthorSearchResult(*row.values()))
    finally:
        await conn.close()
    return results

async def get_book_by_id(book_id: int) -> BookSearchResult:
    conn = await connect_to_db()
    try:
        sql_query = load_sql(SQLFiles.SELECT_BOOK_BY_ID)
        row = await conn.fetchrow(sql_query, book_id)
    finally:
        await conn.close()
    return BookSearchResult(*row, 1)
