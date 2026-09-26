"""
ai_erp/settings/dev.py
Settings cho môi trường phát triển (development).
Đọc biến môi trường từ .env bằng python-dotenv.
"""
import os
from pathlib import Path
from .base import *  # noqa: F403, F401

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")  # noqa: F405
except ImportError:
    pass

# ── Security ─────────────────────────────────────────────────
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-key-please-change-in-production-52xgn8q",
)

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# ── Database: SQLite (không cần cài thêm gì) ─────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}

# ── AI API Keys (đọc từ .env) ────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL   = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

# ── Email: console backend (không gửi thật) ──────────────────
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ── Tắt cache (dev đơn giản) ─────────────────────────────────
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# ── Wagtail ──────────────────────────────────────────────────
WAGTAILADMIN_BASE_URL = "http://localhost:8000"
LOGIN_URL = "/admin/login/"
