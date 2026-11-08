import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from decimal import Decimal

from config import DATABASE_URL


def get_db_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL PostgreSQL bağlantısı təyin edilməyib.")
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def clear_all_data():
    with get_db_connection() as conn:
        rows = conn.execute(
            """SELECT tablename FROM pg_tables
               WHERE schemaname = current_schema()
                 AND tablename <> 'storage_migrations'
               ORDER BY tablename"""
        ).fetchall()
        tables = [row["tablename"] for row in rows]
        if not tables:
            return []

        table_list = sql.SQL(", ").join(sql.Identifier(table) for table in tables)
        conn.execute(sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(table_list))
        return tables


def _ensure_money_column(conn, table, column):
    row = conn.execute(
        """SELECT data_type, numeric_scale FROM information_schema.columns
           WHERE table_schema = current_schema() AND table_name = %s AND column_name = %s""",
        (table, column),
    ).fetchone()
    if row and (row["data_type"] != "numeric" or row["numeric_scale"] != 2):
        identifier = sql.Identifier
        conn.execute(
            sql.SQL("ALTER TABLE {} ALTER COLUMN {} TYPE NUMERIC(12, 2) USING {}::NUMERIC(12, 2)").format(
                identifier(table), identifier(column), identifier(column)
            )
        )


def create_tables():
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                nickname TEXT,
                score BIGINT NOT NULL DEFAULT 0,
                balance NUMERIC(12, 2) NOT NULL DEFAULT 0,
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
        _ensure_money_column(conn, "users", "balance")
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
            CREATE TABLE IF NOT EXISTS balance_history (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                ts TEXT NOT NULL,
                event_type TEXT NOT NULL,
                delta NUMERIC(12, 2) NOT NULL,
                prev_balance NUMERIC(12, 2) NOT NULL,
                new_balance NUMERIC(12, 2) NOT NULL,
                reason TEXT,
                source TEXT,
                meta JSONB NOT NULL DEFAULT '{}'::jsonb
            )
        """)
        for column in ("delta", "prev_balance", "new_balance"):
            _ensure_money_column(conn, "balance_history", column)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quiz_rewards (
                user_id BIGINT NOT NULL,
                quiz_id TEXT NOT NULL,
                question_index INTEGER NOT NULL,
                amount NUMERIC(12, 2) NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, quiz_id, question_index)
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


def award_quiz_reward(user_id: int, quiz_id: str, question_index: int, amount: Decimal):
    with get_db_connection() as conn:
        awarded = conn.execute(
            """INSERT INTO quiz_rewards (user_id, quiz_id, question_index, amount)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (user_id, quiz_id, question_index) DO NOTHING
               RETURNING user_id""",
            (user_id, quiz_id, question_index, amount),
        ).fetchone()
        if not awarded:
            return None

        row = conn.execute(
            """INSERT INTO users (user_id, balance) VALUES (%s, %s)
               ON CONFLICT (user_id) DO UPDATE
               SET balance = users.balance + EXCLUDED.balance
               RETURNING balance""",
            (user_id, amount),
        ).fetchone()
        new_balance = row["balance"]
        previous_balance = new_balance - amount
        conn.execute(
            """INSERT INTO balance_history
               (user_id, ts, event_type, delta, prev_balance, new_balance, reason, source, meta)
               VALUES (%s, CURRENT_TIMESTAMP::text, %s, %s, %s, %s, %s, %s, %s)""",
            (
                user_id,
                "quiz_reward",
                amount,
                previous_balance,
                new_balance,
                "Quiz sualına düzgün cavab mükafatı",
                "handlers.fast_test.answer_handler",
                Jsonb({"quiz_id": quiz_id, "question_index": question_index}),
            ),
        )
        return new_balance