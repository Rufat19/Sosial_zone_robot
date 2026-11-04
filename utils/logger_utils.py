"""Kiçik logger utility — `logging_config.py`-a yüngül wrapper.

İstifadə:
    from utils.logger_utils import init_logger, get_logger
    init_logger()  # env LOG_LEVEL varsa onu istifadə edir
    logger = get_logger(__name__)
    logger.info("hazır")
"""
import logging
from typing import Optional
from .logging_config import setup_logging
import datetime
from .timezone_utils import get_baku_time_str
from database.db import add_user_activity

LOG_FILE = "user_activity.log"


def log_event(user_id: int, username: str, action: str, language: str = "unknown"):
    now = get_baku_time_str()
    add_user_activity(user_id, username, action, now, language)


def _parse_level(level_str: Optional[str]) -> int:
    if not level_str:
        return logging.INFO
    level_str = level_str.upper()
    return getattr(logging, level_str, logging.INFO)


def init_logger(level: Optional[str] = None):
    """Initialize root logger.

    - If `level` is provided (e.g. 'DEBUG'), it will be used.
    - Otherwise the `LOG_LEVEL` env var is used or default INFO.
    """
    env_level = level or os.getenv("LOG_LEVEL")
    lvl = _parse_level(env_level)
    setup_logging(level=lvl)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a logger for `name` (or root logger if None)."""
    return logging.getLogger(name)
