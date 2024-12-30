import os

import psycopg2
from psycopg2.extras import RealDictCursor

from utils.config_parser import read_config


class SQLFiles:
    BOOKS_FUZZY_SEARCH = "books_fuzzy_search.sql"
    SELECT_BOOK_BY_ID = "select_book_by_id.sql"


class BookSearchResult:
    ACCURACY_THRESHOLD = 0.6
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    SQL_DIR = os.path.join(PROJECT_ROOT, 'sql')

    def __init__(self, id: int, title: str, author: str, url: str, similarity: float):
        self.id: int = id
        self.title: str = title
        self.author: str = author
        self.similarity: float = similarity
        self.archive: str = url.split('/')[-2]
        self.filename: str = url.split('/')[-1]

    def __iter__(self):
        return iter((self.id, self.title, self.author, self.archive, self.filename, self.similarity))

    def accurate_enough(self) -> bool:
        """
        Checks if the book search result is accurate enough to its query.
        """
        return self.similarity >= BookSearchResult.ACCURACY_THRESHOLD


def load_sql(filename: str):
    file_path = os.path.join(BookSearchResult.SQL_DIR, filename)
    with open(file_path, 'r') as file:
        return file.read()


def connect_to_db():
    config = read_config("config.ini")
    return psycopg2.connect(
        host=config["Database"]["db_host"],
        port=config["Database"]["db_port"],
        user=config["Database"]["db_user"],
        password=config["Database"]["db_password"],
        database=config["Database"]["db_name"]
    )


def search_books(query: str) -> list[BookSearchResult]:
    """
    Search books by title and author with fuzzy matching.

    Args:
        query (str): The search query (e.g., title or author).

    Returns:
        list[BookSearchResult]: Matched books and accuracy.
    """
    results = []
    conn = connect_to_db()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            sql_query = load_sql(SQLFiles.BOOKS_FUZZY_SEARCH)
            cursor.execute(sql_query, [query, query])
            books = cursor.fetchall()
            for book in books:
                results.append(BookSearchResult(*book.values()))
    finally:
        conn.close()
        return results


def get_book_by_id(book_id: int) -> BookSearchResult:
    book: tuple | None = None
    conn = connect_to_db()
    try:
        with conn.cursor() as cursor:
            sql_query = load_sql(SQLFiles.SELECT_BOOK_BY_ID)
            cursor.execute(sql_query, [book_id])
            book = cursor.fetchone()
    finally:
        conn.close()
        return BookSearchResult(*book, 1)
