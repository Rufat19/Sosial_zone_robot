## Alien_BiBOT — Copilot instructions

This file gives focused, actionable guidance to an AI coding agent editing or extending this repository.

- Entry point: `run.py` — the bot initializes database via `handlers.db_utils.init_db()` and `database/db.create_tables()` then includes routers from `handlers/*` and starts polling with aiogram.
- Configuration: `config.py` loads `BOT_TOKEN` and `ADMIN_ID` from environment (`.env` via python-dotenv). Changes that rely on credentials should use these env vars. If missing, `run.py` raises a ValueError.

- Architecture overview:
  - handlers/ : each active feature is a Router module (e.g., `start.py`, `balance.py`, `news_handler.py`). Add new features as independent routers and include them in `run.py` via `dp.include_router(...)`.
  - database/ : PostgreSQL helper in `database/db.py`. Use `get_db_connection()` and `create_tables()` for schema changes.

- Conventions & patterns to follow (concrete):
  - Routers: export `router = Router()` at module top. Handlers use `@router.message(...)` or `@router.callback_query(...)` with `aiogram.F` filters. Example: `handlers/start.py` defines `get_main_buttons()` and uses `@router.message(F.text == "/start")`.
  - Inline keyboards: return InlineKeyboardMarkup objects from helper functions (see `get_main_buttons()` in `handlers/start.py`). Keep callbacks short and consistent strings like `balance_menu`, `main_menu`, `news_menu`.
  - DB access: use `database.db.get_db_connection()` which sets `row_factory=sqlite3.Row`. Use context managers (`with get_db_connection() as conn:`) and `conn.execute(...)` then `conn.commit()`.
  - Config and secrets: put BOT_TOKEN and other secrets into a `.env` file read by `config.py`.

- Developer workflows (how to run & test):
  - Install dependencies: `pip install -r requirements.txt`.
  - Start bot locally: set `BOT_TOKEN` and `ADMIN_ID` in `.env`, then run `python run.py`.
  - Database: `run.py` will call `create_tables()` automatically. To inspect DB, open `database.db` with sqlite3 or DB Browser.

- Integration points & external dependencies:
  - Telegram Bot API via `aiogram` (v3). Handlers rely on aiogram Router/Dispatcher patterns.
  - Optional: `redis` is listed in requirements but not required for basic run; confirm usage before adding caching code.
  - Payment and card config read from `config.py` (e.g., `CARD_NUMBER`).

- Common pitfalls & quick fixes observed in codebase:
  - `handlers/entry.py` may be empty — check for unused import attempts elsewhere before removing.
  - Balance and user histories are persisted in PostgreSQL; do not reintroduce local-file storage for persistent data.
  - `config.py` currently raises if `ADMIN_ID` not set; during tests you can set `ADMIN_ID` to a numeric test value.

- When editing code, follow these micro-rules:
  1. Add new handlers as `handlers/<feature>.py` exporting `router` and include it in `run.py`.
 2. Use existing callback_data strings where appropriate to reuse UI flows (see `handlers/start.py`).
 3. Prefer `get_db_connection()` for relational data; reserve JSON files for small, non-critical caches.

If anything here is unclear or you want more coverage (CI commands, deployment, or message schemas), tell me what to add and I will iterate.
