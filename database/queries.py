def add_user(user_id: int, name: str, lang: str | None = None):
    from .db import get_db_connection
    with get_db_connection() as conn:
        conn.execute(
            """INSERT INTO users (user_id, nickname, language) VALUES (%s, %s, %s)
               ON CONFLICT (user_id) DO UPDATE
               SET nickname=EXCLUDED.nickname, language=EXCLUDED.language""",
            (user_id, name, lang),
        )
