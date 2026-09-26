"""
Settings cho môi trường phát triển.
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

PUBLIC_BRAND_NAME = os.environ.get("PUBLIC_BRAND_NAME", "DigiFlow")
PUBLIC_CONTACT_EMAIL = os.environ.get("PUBLIC_CONTACT_EMAIL", "")
PUBLIC_DATA_CONTROLLER_NAME = os.environ.get(
    "PUBLIC_DATA_CONTROLLER_NAME",
    "DigiFlow (tên đơn vị mẫu — cần thay bằng tên đơn vị vận hành thật)",
)
PUBLIC_PRIVACY_EMAIL = os.environ.get("PUBLIC_PRIVACY_EMAIL") or PUBLIC_CONTACT_EMAIL
PUBLIC_DATA_RETENTION_NOTICE = os.environ.get(
    "PUBLIC_DATA_RETENTION_NOTICE",
    "Bản demo: dữ liệu được lưu trong cơ sở dữ liệu local cho đến khi người vận hành xóa. "
    "Đơn vị vận hành cần xác định thời hạn lưu cụ thể trước khi dùng dữ liệu thật.",
)

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
