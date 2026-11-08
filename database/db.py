import psycopg
from psycopg.rows import dict_row

from config import DATABASE_URL


def get_db_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL PostgreSQL bağlantısı təyin edilməyib.")
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def create_tables():
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                nickname TEXT,
                score BIGINT NOT NULL DEFAULT 0,
                balance BIGINT NOT NULL DEFAULT 0,
                time_spent BIGINT NOT NULL DEFAULT 0,
                name TEXT,
                phone TEXT,
                username TEXT,
                language TEXT
            )
        """)
        conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS name TEXT")
        conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone TEXT")
        conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS username TEXT")
        conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS language TEXT")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT,
                name TEXT,
                phone TEXT,
                product_name TEXT,
                color TEXT,
                status TEXT DEFAULT 'Yeni',
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS news (
                id BIGSERIAL PRIMARY KEY,
                title TEXT,
                content TEXT,
                admin_id BIGINT,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS excel_access (
                user_id BIGINT PRIMARY KEY,
                full_name TEXT,
                phone TEXT,
                access_granted BOOLEAN NOT NULL DEFAULT FALSE
            )
        """)
        conn.execute("ALTER TABLE excel_access ADD COLUMN IF NOT EXISTS full_name TEXT")
        conn.execute("ALTER TABLE excel_access ADD COLUMN IF NOT EXISTS phone TEXT")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS balance_history (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                ts TEXT NOT NULL,
                event_type TEXT NOT NULL,
                delta BIGINT NOT NULL,
                prev_balance BIGINT NOT NULL,
                new_balance BIGINT NOT NULL,
                reason TEXT,
                source TEXT,
                meta JSONB NOT NULL DEFAULT '{}'::jsonb
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bot_orders (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                full_name TEXT,
                phone TEXT,
                details TEXT,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_starts (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                started_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_activity (
                id BIGSERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                username TEXT,
                action TEXT,
                occurred_at TEXT NOT NULL,
                language TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS storage_migrations (
                migration_key TEXT PRIMARY KEY,
                completed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


def add_user(user_id, nickname):
    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO users (user_id, nickname) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING",
            (user_id, nickname),
        )


def get_all_users():
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM users").fetchall()
        return [dict(row) for row in rows]


def add_user_start(user_id, started_at):
    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO user_starts (user_id, started_at) VALUES (%s, %s)",
            (user_id, started_at),
        )


def get_latest_user_start_id():
    with get_db_connection() as conn:
        row = conn.execute("SELECT COALESCE(MAX(id), 0) AS id FROM user_starts").fetchone()
        return row["id"]


def get_user_starts_after(start_id):
    with get_db_connection() as conn:
        return conn.execute(
            "SELECT id, user_id, started_at FROM user_starts WHERE id > %s ORDER BY id",
            (start_id,),
        ).fetchall()


def add_user_activity(user_id, username, action, occurred_at, language):
    with get_db_connection() as conn:
        conn.execute(
            """INSERT INTO user_activity (user_id, username, action, occurred_at, language)
               VALUES (%s, %s, %s, %s, %s)""",
            (str(user_id), username, action, occurred_at, language),
        )


def get_all_user_activity():
    with get_db_connection() as conn:
        return conn.execute(
            "SELECT user_id, username, action, occurred_at, language FROM user_activity ORDER BY id"
        ).fetchall()


def add_bot_order(user_id, full_name, phone, details, created_at):
    with get_db_connection() as conn:
        conn.execute(
            """INSERT INTO bot_orders (user_id, full_name, phone, details, created_at)
               VALUES (%s, %s, %s, %s, %s)""",
            (user_id, full_name, phone, details, created_at),
        )