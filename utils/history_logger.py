from psycopg.types.json import Jsonb

from database.db import get_db_connection
from utils.timezone_utils import baku_now_for_history


def log_balance_change(user_id: int, prev_balance: int, new_balance: int, reason: str = None, source: str = None, meta: dict | None = None):
    """Append a balance change event for a user.

    Event shape:
    {
      "ts": ISO8601,
      "type": "balance_change",
      "delta": int,
      "prev": int,
      "new": int,
      "reason": str | null,
      "source": str | null,
      "meta": { ... }
    }
    """
    delta = int(new_balance) - int(prev_balance)
    with get_db_connection() as conn:
        conn.execute(
            """INSERT INTO balance_history
               (user_id, ts, event_type, delta, prev_balance, new_balance, reason, source, meta)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                user_id,
                baku_now_for_history(),
                "balance_change",
                delta,
                int(prev_balance),
                int(new_balance),
                reason,
                source or "db_utils.set_balance",
                Jsonb(meta or {}),
            ),
        )


def get_user_history(user_id: int) -> list:
    with get_db_connection() as conn:
        rows = conn.execute(
            """SELECT ts, event_type, delta, prev_balance, new_balance, reason, source, meta
               FROM balance_history WHERE user_id=%s ORDER BY id""",
            (user_id,),
        ).fetchall()
    return [
        {
            "ts": row["ts"],
            "type": row["event_type"],
            "delta": row["delta"],
            "prev": row["prev_balance"],
            "new": row["new_balance"],
            "reason": row["reason"],
            "source": row["source"],
            "meta": row["meta"],
        }
        for row in rows
    ]


def summarize_user_history(user_id: int) -> dict:
    events = get_user_history(user_id)
    total_topup = sum(e.get("delta", 0) for e in events if e.get("delta", 0) > 0)
    total_spent = -sum(e.get("delta", 0) for e in events if e.get("delta", 0) < 0)
    first_ts = events[0]["ts"] if events else None
    last_ts = events[-1]["ts"] if events else None
    return {
        "count": len(events),
        "total_topup": total_topup,
        "total_spent": total_spent,
        "first_ts": first_ts,
        "last_ts": last_ts,
    }
