import os
from dotenv import load_dotenv

# .env faylını oxu
load_dotenv()

# Layihənin əsas qovluğunu tapırıq
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Əsas dəyişənlər ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 6520873307))  # .env-də olmasa, default
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")
PAYMENT_CURRENCY = os.getenv("PAYMENT_CURRENCY", "USD").upper()

# --- Versiya / informasiya ---
APP_VERSION = os.getenv("APP_VERSION", "dev")
REPO_NAME = os.getenv("REPO_NAME", "Yeni_Repo")

# --- Persistent PostgreSQL storage ---
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]

# Paths used only to import existing local data into PostgreSQL once.
DATA_DIR = os.getenv("DATA_DIR")
if not DATA_DIR:
    DATA_DIR = "/mnt/data" if os.path.isdir("/mnt/data") else os.path.join(BASE_DIR, "data")
_legacy_db = os.getenv("DB_PATH", "database.db")
LEGACY_DB_PATH = _legacy_db if os.path.isabs(_legacy_db) else os.path.join(DATA_DIR, _legacy_db)

# --- Təhlükəsizlik yoxlaması ---
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN .env faylında təyin olunmalıdır.")
