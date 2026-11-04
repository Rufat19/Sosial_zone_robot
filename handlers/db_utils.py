from database.db import create_tables, get_db_connection
from utils.history_logger import log_balance_change

def init_db():
    create_tables()

def set_nickname(user_id, nickname):
    with get_db_connection() as conn:
        conn.execute(
            """INSERT INTO users (user_id, nickname) VALUES (%s, %s)
               ON CONFLICT (user_id) DO UPDATE SET nickname=EXCLUDED.nickname""",
            (user_id, nickname),
        )

def update_user(user_id, score, balance, time_spent):
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE users SET score=%s, balance=%s, time_spent=%s WHERE user_id=%s",
            (score, balance, time_spent, user_id),
        )

def get_top10():
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT nickname, score, balance FROM users ORDER BY score DESC, balance DESC LIMIT 10"
        ).fetchall()
        return [tuple(row.values()) for row in rows]

# --- BALANCE FUNCTIONS ---
def get_balance(user_id):
    with get_db_connection() as conn:
        row = conn.execute("SELECT balance FROM users WHERE user_id=%s", (user_id,)).fetchone()
        return row["balance"] if row else 0

def set_balance(user_id, balance):
    with get_db_connection() as conn:
        row = conn.execute("SELECT balance FROM users WHERE user_id=%s", (user_id,)).fetchone()
        prev_balance = row["balance"] if row else 0
        conn.execute(
            """INSERT INTO users (user_id, balance) VALUES (%s, %s)
               ON CONFLICT (user_id) DO UPDATE SET balance=EXCLUDED.balance""",
            (user_id, balance),
        )

    try:
        log_balance_change(user_id=user_id, prev_balance=prev_balance, new_balance=balance)
    except Exception:
        # Logging should not break balance updates
        pass
