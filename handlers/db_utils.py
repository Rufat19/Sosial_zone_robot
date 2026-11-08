from database.db import get_db_connection
from utils.history_logger import log_balance_change

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
