import json
import logging
import os
import sqlite3

from psycopg.types.json import Jsonb

from config import BASE_DIR, DATA_DIR, LEGACY_DB_PATH
from .db import get_db_connection

logger = logging.getLogger(__name__)


def _already_migrated(conn, key):
    return conn.execute(
        "SELECT 1 FROM storage_migrations WHERE migration_key=%s", (key,)
    ).fetchone() is not None


def _run_once(key, migrate):
    with get_db_connection() as conn:
        if _already_migrated(conn, key):
            return
        migrate(conn)
        conn.execute("INSERT INTO storage_migrations (migration_key) VALUES (%s)", (key,))


def _migrate_json(key, path, migrate, empty_value):
    if not os.path.isfile(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as source:
            contents = source.read()
        data = json.loads(contents) if contents.strip() else empty_value
        _run_once(key, lambda conn: migrate(conn, data))
        logger.info("Imported legacy data from %s", path)
    except Exception:
        logger.exception("Could not import legacy data from %s", path)
        raise


def _migrate_sqlite_database():
    if not os.path.isfile(LEGACY_DB_PATH):
        return

    def migrate(conn):
        with sqlite3.connect(LEGACY_DB_PATH) as legacy:
            legacy.row_factory = sqlite3.Row
            tables = {
                row[0]
                for row in legacy.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }

            if "users" in tables:
                for row in legacy.execute("SELECT * FROM users"):
                    user = dict(row)
                    conn.execute(
                        """INSERT INTO users
                           (user_id, nickname, score, balance, time_spent, name, phone, username, language)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (user_id) DO NOTHING""",
                        (
                            user["user_id"], user.get("nickname"), user.get("score", 0) or 0,
                            user.get("balance", 0) or 0, user.get("time_spent", 0) or 0,
                            user.get("name"), user.get("phone"), user.get("username"),
                            user.get("language"),
                        ),
                    )

            if "orders" in tables:
                for row in legacy.execute("SELECT * FROM orders"):
                    order = dict(row)
                    conn.execute(
                        """INSERT INTO orders
                           (user_id, name, phone, product_name, color, status, created_at)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        tuple(order.get(field) for field in (
                            "user_id", "name", "phone", "product_name", "color", "status", "created_at"
                        )),
                    )

            if "news" in tables:
                for row in legacy.execute("SELECT * FROM news"):
                    news = dict(row)
                    conn.execute(
                        """INSERT INTO news (title, content, admin_id, created_at)
                           VALUES (%s, %s, %s, %s)""",
                        tuple(news.get(field) for field in ("title", "content", "admin_id", "created_at")),
                    )

            if "excel_access" in tables:
                for row in legacy.execute("SELECT * FROM excel_access"):
                    access = dict(row)
                    conn.execute(
                        """INSERT INTO excel_access (user_id, full_name, phone, access_granted)
                           VALUES (%s, %s, %s, %s)
                           ON CONFLICT (user_id) DO NOTHING""",
                        (
                            access["user_id"], access.get("full_name"), access.get("phone"),
                            bool(access.get("access_granted", False)),
                        ),
                    )

    _run_once("sqlite_database", migrate)
    logger.info("Imported legacy SQLite database from %s", LEGACY_DB_PATH)


def _migrate_balance_history(conn, data):
    for user_id, events in data.items():
        for event in events or []:
            conn.execute(
                """INSERT INTO balance_history
                   (user_id, ts, event_type, delta, prev_balance, new_balance, reason, source, meta)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    int(user_id), event.get("ts", ""), event.get("type", "balance_change"),
                    int(event.get("delta", 0)), int(event.get("prev", 0)),
                    int(event.get("new", 0)), event.get("reason"), event.get("source"),
                    Jsonb(event.get("meta") or {}),
                ),
            )


def _migrate_balances(conn, balances):
    for user_id, balance in balances.items():
        if not str(user_id).isdigit():
            continue
        try:
            amount = int(balance)
        except (TypeError, ValueError):
            continue
        conn.execute(
            """INSERT INTO users (user_id, balance) VALUES (%s, %s)
               ON CONFLICT (user_id) DO NOTHING""",
            (int(user_id), amount),
        )


def _migrate_bot_orders(conn, orders):
    for order in orders or []:
        conn.execute(
            """INSERT INTO bot_orders (user_id, full_name, phone, details, created_at)
               VALUES (%s, %s, %s, %s, %s)""",
            (
                int(order["user_id"]), order.get("full_name"), order.get("phone"),
                order.get("details"), order.get("timestamp"),
            ),
        )


def _migrate_news(conn, items):
    for item in items or []:
        conn.execute(
            "INSERT INTO news (title, content) VALUES (%s, %s)",
            (item.get("title", ""), item.get("content", "")),
        )


def _migrate_starts(conn, path):
    with open(path, "r", encoding="utf-8") as source:
        for line in source:
            user_id, separator, started_at = line.strip().partition("|")
            if separator and user_id.isdigit():
                conn.execute(
                    "INSERT INTO user_starts (user_id, started_at) VALUES (%s, %s)",
                    (int(user_id), started_at),
                )


def _migrate_activity(conn, path):
    with open(path, "r", encoding="utf-8") as source:
        for line in source:
            parts = line.rstrip("\n").split("|", 4)
            if len(parts) == 5:
                conn.execute(
                    """INSERT INTO user_activity (user_id, username, action, occurred_at, language)
                       VALUES (%s, %s, %s, %s, %s)""",
                    tuple(parts),
                )


def migrate_legacy_data():
    _migrate_sqlite_database()
    _migrate_json(
        "user_balance_json", os.path.join(BASE_DIR, "user_balance.json"),
        _migrate_balances, {},
    )
    _migrate_json(
        "balance_history_json", os.path.join(DATA_DIR, "user_history.json"),
        _migrate_balance_history, {},
    )
    _migrate_json(
        "bot_orders_json", os.path.join(BASE_DIR, "orders.json"), _migrate_bot_orders, [],
    )
    _migrate_json(
        "news_json", os.path.join(DATA_DIR, "news.json"), _migrate_news, [],
    )
    starts_path = os.path.join(BASE_DIR, "user_start_history.log")
    if os.path.isfile(starts_path):
        _run_once("user_starts_log", lambda conn: _migrate_starts(conn, starts_path))
    activity_path = os.path.join(BASE_DIR, "user_activity.log")
    if os.path.isfile(activity_path):
        _run_once("user_activity_log", lambda conn: _migrate_activity(conn, activity_path))
