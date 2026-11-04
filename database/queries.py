from . import add_news_to_db, get_all_news as _db_get_all_news, get_news_by_id as _db_get_news_by_id
from .db import get_all_users as _db_get_all_users

# ========== İSTİFADƏÇİLƏR ÜÇÜN ==========
def add_user(user_id: int, name: str, lang: str | None = None):
    from .db import get_db_connection
    with get_db_connection() as conn:
        conn.execute(
            """INSERT INTO users (user_id, nickname, language) VALUES (%s, %s, %s)
               ON CONFLICT (user_id) DO UPDATE
               SET nickname=EXCLUDED.nickname, language=EXCLUDED.language""",
            (user_id, name, lang),
        )


def get_all_users():
    """Bütün istifadəçiləri PostgreSQL-dən göstər."""
    return _db_get_all_users()


# ========== YENİLİKLƏR ÜÇÜN ==========

def load_news():
    return _db_get_all_news()


def save_news(news_list):
    from .db import get_db_connection
    with get_db_connection() as conn:
        conn.execute("DELETE FROM news")
        for item in news_list:
            conn.execute(
                "INSERT INTO news (title, content) VALUES (%s, %s)",
                (item.get("title", ""), item.get("content", "")),
            )


def add_news(title: str, content: str):
    return add_news_to_db(title, content, None)


def get_all_news():
    return _db_get_all_news()


def get_news_by_id(news_id: int):
    return _db_get_news_by_id(news_id)
