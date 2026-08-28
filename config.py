import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
BASE_DIR = Path(__file__).parent.resolve()
load_dotenv(BASE_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "20"))
NOTIFY_ALL_EMAILS = os.getenv("NOTIFY_ALL_EMAILS", "true").lower() in ("true", "1", "yes")
CREDENTIALS_FILE = BASE_DIR / os.getenv("CREDENTIALS_FILE", "credential.json")
TOKEN_FILE = BASE_DIR / os.getenv("TOKEN_FILE", "token.json")
PROCESSED_DB_FILE = BASE_DIR / "processed_emails.json"

# AI Model to use on Groq
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

# Gmail API scopes
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify"
]
