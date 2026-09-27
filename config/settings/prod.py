"""Production-oriented settings. Set DJANGO_SETTINGS_MODULE=config.settings.prod."""

import os
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

from .dev import *  # noqa: F403, F401


secret_key = os.environ.get("DJANGO_SECRET_KEY", "").strip()
if len(secret_key) < 50 or secret_key.startswith("django-insecure-"):
    raise ImproperlyConfigured(
        "Production requires a strong DJANGO_SECRET_KEY of at least 50 characters."
    )
SECRET_KEY = secret_key

DEBUG = False

ALLOWED_HOSTS = [host.strip() for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if host.strip()]
if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("Set DJANGO_ALLOWED_HOSTS to explicit production hostnames.")

CSRF_TRUSTED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

PUBLIC_SITE_URL = os.environ.get("PUBLIC_SITE_URL", "").strip().rstrip("/")
parsed_public_url = urlsplit(PUBLIC_SITE_URL)
if parsed_public_url.scheme != "https" or not parsed_public_url.netloc:
    raise ImproperlyConfigured("PUBLIC_SITE_URL must be an HTTPS URL in production.")
if parsed_public_url.hostname not in ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must include the hostname from PUBLIC_SITE_URL.")
if not any(
    urlsplit(origin).scheme == "https"
    and urlsplit(origin).hostname == parsed_public_url.hostname
    for origin in CSRF_TRUSTED_ORIGINS
):
    raise ImproperlyConfigured(
        "DJANGO_CSRF_TRUSTED_ORIGINS must include an HTTPS origin for PUBLIC_SITE_URL."
    )

WAGTAILADMIN_BASE_URL = os.environ.get("WAGTAILADMIN_BASE_URL", PUBLIC_SITE_URL)
if EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend":  # noqa: F405
    raise ImproperlyConfigured("Configure a real EMAIL_BACKEND for production; console email is for local development.")
SECURE_SSL_REDIRECT = True
if os.environ.get("DJANGO_BEHIND_TLS_PROXY", "false").lower() == "true":
    # Only enable when the trusted proxy overwrites this header and the app
    # cannot be reached directly from untrusted clients.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", "false"
).lower() == "true"
SECURE_HSTS_PRELOAD = os.environ.get("SECURE_HSTS_PRELOAD", "false").lower() == "true"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"

# Production logs should not emit customer-related debug details.
LOGGING["loggers"]["crm"]["level"] = "INFO"  # noqa: F405
