from .db import get_db_connection
from utils.timezone_utils import baku_now_for_history


def _get_conn():
	return get_db_connection()


def add_news_to_db(title, content, admin_id):
	"""Insert a news item and return its id."""
	with _get_conn() as conn:
		cur = conn.execute(
			"INSERT INTO news (title, content, admin_id, created_at) VALUES (%s, %s, %s, %s) RETURNING id",
			(title, content, admin_id, baku_now_for_history()),
		)
		return cur.fetchone()["id"]


def get_all_news():
	"""Return list of news dicts ordered by newest first."""
	with _get_conn() as conn:
		rows = conn.execute("SELECT id, title, content, admin_id, created_at FROM news ORDER BY created_at DESC").fetchall()
		return rows


def get_news_by_id(news_id):
	with _get_conn() as conn:
		row = conn.execute("SELECT id, title, content, admin_id, created_at FROM news WHERE id=%s", (news_id,)).fetchone()
		return row


def get_all_users():
	"""Return list of users as dicts {'id': user_id} for broadcasting."""
	with _get_conn() as conn:
		rows = conn.execute("SELECT user_id FROM users").fetchall()
		return [{"id": r["user_id"]} for r in rows]

