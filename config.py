"""Load settings from the .env file. Keep secrets out of HTML and JavaScript."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env")

SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "").strip()
MYMEMORY_EMAIL = os.getenv("MYMEMORY_EMAIL", "").strip()

DATA_DIR = ROOT_DIR / "data"
DATABASE_PATH = DATA_DIR / "linguaai.db"

# Modest limit so a single request cannot overload the APIs.
MAX_INPUT_CHARS = 2000

SUPPORTED_LANGUAGES = {
    "en": "English",
    "kn": "Kannada",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "es": "Spanish",
    "fr": "French",
}

SOURCE_LANGUAGES = {"auto": "Auto Detect", **SUPPORTED_LANGUAGES}
