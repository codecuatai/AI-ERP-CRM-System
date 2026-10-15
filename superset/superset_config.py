"""Local Docker configuration for the CRM analytics demo."""

import os
from urllib.parse import quote_plus


SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]
meta_password = quote_plus(os.environ["SUPERSET_META_PASSWORD"])
SQLALCHEMY_DATABASE_URI = (
    f"postgresql://superset_meta:{meta_password}@superset-meta-db:5432/superset_meta"
)
WTF_CSRF_ENABLED = True

# ── Cho phép nhúng Superset vào iframe CRM ────────────────────────
FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True,
}

ENABLE_CORS = True
CORS_OPTIONS = {
    "supports_credentials": True,
    "allow_headers": ["*"],
    "resources": ["*"],
    "origins": [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:18088",
        "http://127.0.0.1:18088",
    ],
}

# Cấu hình Talisman CSP để trình duyệt không chặn iframe (gỡ X-Frame-Options SAMEORIGIN)
TALISMAN_ENABLED = True
TALISMAN_CONFIG = {
    "content_security_policy": {
        "frame-ancestors": [
            "'self'",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:*",
            "http://127.0.0.1:*",
        ],
    },
    "frame_options": None,
    "force_https": False,
    "session_cookie_secure": False,
}
TALISMAN_DEV_CONFIG = TALISMAN_CONFIG

# Cho phép người dùng xem dashboard trong iframe
PUBLIC_ROLE_LIKE = "Gamma"
GUEST_ROLE_NAME = "Gamma"

# Cấu hình cookie hỗ trợ iframe
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
