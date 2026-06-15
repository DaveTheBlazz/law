"""Application configuration loaded from .env file."""

import os
from dotenv import load_dotenv

load_dotenv()

# AI / LLM Settings
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.openai.com/v1")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")
AI_EMBEDDING_MODEL = os.getenv("AI_EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))

# App Settings
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
APP_TITLE = os.getenv("APP_TITLE", "پایگاه نظریات حقوقی")

# Data
CSV_PATH = os.getenv("CSV_PATH", "opinions.csv")
DB_PATH = os.getenv("DB_PATH", "law.db")
SEMANTIC_TOP_K = int(os.getenv("SEMANTIC_TOP_K", "20"))

DEFAULT_SYSTEM_PROMPT = """تو یک دستیار حقوقی هستی. بر اساس نظریات زیر به سوال کاربر پاسخ بده.
قوانین: فقط بر اساس نظریات داده‌شده پاسخ بده. شماره نظریه را ذکر کن. کوتاه و دقیق پاسخ بده."""

SYSTEM_PROMPT = os.getenv("CHAT_SYSTEM_PROMPT") or DEFAULT_SYSTEM_PROMPT


def ai_available() -> bool:
    """Check if AI features are configured."""
    return bool(AI_API_KEY and AI_BASE_URL and AI_MODEL)
