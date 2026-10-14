"""
Settings cho môi trường phát triển.
Đọc biến môi trường từ .env bằng python-dotenv.
"""
import os
from pathlib import Path
from urllib.parse import urlsplit, unquote
from django.core.management.utils import get_random_secret_key
from .base import *  # noqa: F403, F401

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")  # noqa: F405
except ImportError:
    pass

PUBLIC_BRAND_NAME = os.environ.get("PUBLIC_BRAND_NAME", "DigiFlow")
PUBLIC_SITE_URL = os.environ.get("PUBLIC_SITE_URL", "http://127.0.0.1:8000").rstrip("/")
LEAD_FOLLOW_UP_LINK_TTL_DAYS = int(os.environ.get("LEAD_FOLLOW_UP_LINK_TTL_DAYS", "7"))
PUBLIC_CONTACT_EMAIL = os.environ.get("PUBLIC_CONTACT_EMAIL", "")
PUBLIC_DATA_CONTROLLER_NAME = os.environ.get(
    "PUBLIC_DATA_CONTROLLER_NAME",
    "DigiFlow (đơn vị vận hành bản demo)",
)
PUBLIC_PRIVACY_EMAIL = os.environ.get("PUBLIC_PRIVACY_EMAIL") or PUBLIC_CONTACT_EMAIL
PUBLIC_DATA_RETENTION_NOTICE = os.environ.get(
    "PUBLIC_DATA_RETENTION_NOTICE",
    "Bản demo: dữ liệu được lưu trong cơ sở dữ liệu local cho đến khi người vận hành xóa. "
    "Đơn vị vận hành cần xác định thời hạn lưu cụ thể trước khi dùng dữ liệu thật.",
)

# ── Security ─────────────────────────────────────────────────
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "").strip() or get_random_secret_key()

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0", "crm-web"]
extra_hosts = [h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if h.strip()]
for host in extra_hosts:
    if host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(host)

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://0.0.0.0:8000",
    "http://localhost:5433",
    "http://127.0.0.1:5433",
]
extra_origins = [o.strip().rstrip("/") for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]
for origin in extra_origins:
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

# ── Database: PostgreSQL 16 (chuẩn hóa toàn bộ hệ thống qua Docker) ──
database_url = os.environ.get("DJANGO_DATABASE_URL", "").strip()
if not database_url:
    db_user = os.environ.get("CRM_DB_USER", "crm_app")
    db_pass = os.environ.get("CRM_DB_PASSWORD", "crm_password")
    db_host = os.environ.get("CRM_DB_HOST", "crm-db")
    db_port = os.environ.get("CRM_DB_PORT", "5432")
    db_name = os.environ.get("CRM_DB_NAME", "crm")
    database_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

parsed_database_url = urlsplit(database_url)
if parsed_database_url.scheme not in {"postgres", "postgresql"}:
    raise ValueError("DJANGO_DATABASE_URL must use the postgres:// or postgresql:// scheme.")
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(parsed_database_url.path.lstrip("/")),
        "USER": unquote(parsed_database_url.username or ""),
        "PASSWORD": unquote(parsed_database_url.password or ""),
        "HOST": parsed_database_url.hostname or "localhost",
        "PORT": parsed_database_url.port or 5432,
        "OPTIONS": {"sslmode": "require"} if parsed_database_url.query == "sslmode=require" else {},
    }
}
if "django.contrib.postgres" not in INSTALLED_APPS:
    INSTALLED_APPS.append("django.contrib.postgres")

# ── AI API Keys (đọc từ .env) ────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")

# ── Email: console local mặc định; cấu hình SMTP qua .env khi cần gửi thật ──
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "true").lower() == "true"
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "false").lower() == "true"
EMAIL_TIMEOUT = int(os.environ.get("EMAIL_TIMEOUT", "10"))
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "DigiFlow <no-reply@example.com>")

# ── Tắt cache (dev đơn giản) ─────────────────────────────────
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# ── Wagtail ──────────────────────────────────────────────────
WAGTAILADMIN_BASE_URL = "http://localhost:8000"
LOGIN_URL = "/admin/login/"
