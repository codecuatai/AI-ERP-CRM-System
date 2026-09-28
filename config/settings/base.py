"""
Base configuration for the application.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Application definition
INSTALLED_APPS = [
    # Wagtail
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.contrib.settings",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",

    # ModelCluster (dùng cho ClusterableModel / InlinePanel)
    "modelcluster",
    "taggit",

    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.humanize",
    "django.contrib.staticfiles",

    # Ứng dụng CRM của doanh nghiệp cung cấp giải pháp chuyển đổi số
    "crm",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "crm" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "wagtail.contrib.settings.context_processors.settings",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "vi"
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Wagtail Settings ────────────────────────────────────────
WAGTAIL_SITE_NAME = "AI CRM — CRM chuyển đổi số"
WAGTAILADMIN_BASE_URL = "http://localhost:8000"
WAGTAILADMIN_USER_LOGIN_FORM = "crm.forms.VietnameseWagtailLoginForm"
PUBLIC_BRAND_NAME = os.getenv("PUBLIC_BRAND_NAME", "DigiFlow")
PUBLIC_SITE_URL = os.getenv("PUBLIC_SITE_URL", "http://127.0.0.1:8000").rstrip("/")
LEAD_FOLLOW_UP_LINK_TTL_DAYS = int(os.getenv("LEAD_FOLLOW_UP_LINK_TTL_DAYS", "7"))
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "false").lower() == "true"
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "10"))
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "DigiFlow <no-reply@example.com>")
PUBLIC_CONTACT_EMAIL = os.getenv("PUBLIC_CONTACT_EMAIL", "")
PUBLIC_DATA_CONTROLLER_NAME = os.getenv(
    "PUBLIC_DATA_CONTROLLER_NAME",
    "DigiFlow (đơn vị vận hành bản demo)",
)
PUBLIC_PRIVACY_EMAIL = os.getenv("PUBLIC_PRIVACY_EMAIL") or PUBLIC_CONTACT_EMAIL
PUBLIC_DATA_RETENTION_NOTICE = os.getenv(
    "PUBLIC_DATA_RETENTION_NOTICE",
    "Bản demo: dữ liệu được lưu trong cơ sở dữ liệu local cho đến khi người vận hành xóa. "
    "Đơn vị vận hành cần xác định thời hạn lưu cụ thể trước khi dùng dữ liệu thật.",
)

# Tắt kiểm tra password quá nghiêm ngặt ở môi trường dev
WAGTAIL_PASSWORD_REQUIRED_TEMPLATE = "wagtailcore/password_required.html"

# ── Logging ─────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {module}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "crm": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
