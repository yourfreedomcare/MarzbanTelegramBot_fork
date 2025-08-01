import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# === BOT DATABASE === (Uses official MySQL variable names)
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

BOT_DB_URL = (
    f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
)

bot_engine = create_engine(BOT_DB_URL, pool_pre_ping=True)
BotSession = sessionmaker(bind=bot_engine, expire_on_commit=False)

# === MARZBAN DATABASE === (Custom names)
MARZBAN_DB_USER = os.getenv("MARZBAN_DB_USER")
MARZBAN_DB_PASS = os.getenv("MARZBAN_DB_PASS")
MARZBAN_DB_HOST = os.getenv("MARZBAN_DB_HOST", "127.0.0.1")
MARZBAN_DB_PORT = os.getenv("MARZBAN_DB_PORT", "3306")
MARZBAN_DB_NAME = os.getenv("MARZBAN_DB_NAME")

MARZBAN_DB_URL = (
    f"mysql+mysqlconnector://{MARZBAN_DB_USER}:{MARZBAN_DB_PASS}"
    f"@{MARZBAN_DB_HOST}:{MARZBAN_DB_PORT}/{MARZBAN_DB_NAME}?charset=utf8mb4"
)

marzban_engine = create_engine(MARZBAN_DB_URL, pool_pre_ping=True)
MarzbanSession = sessionmaker(bind=marzban_engine, expire_on_commit=False)

# Only use for Bot DB models (for Alembic migrations, etc.)
Base = declarative_base()

# Optional alias if you only need one main session
SQL_CONNECTION_STRING = BOT_DB_URL
Session = BotSession
