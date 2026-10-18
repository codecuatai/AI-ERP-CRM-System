"""Local Docker configuration for the CRM analytics demo."""

import os
import hashlib
from copy import deepcopy
from urllib.parse import quote_plus

from superset.config import TALISMAN_CONFIG as DEFAULT_TALISMAN_CONFIG


SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]
meta_password = quote_plus(os.environ["SUPERSET_META_PASSWORD"])
SQLALCHEMY_DATABASE_URI = (
    f"postgresql://superset_meta:{meta_password}@superset-meta-db:5432/superset_meta"
)
WTF_CSRF_ENABLED = True

# The dashboard is authorized by a short-lived guest token, not a Superset cookie.
FEATURE_FLAGS = {"EMBEDDED_SUPERSET": True}
GUEST_ROLE_NAME = "Gamma"
GUEST_TOKEN_JWT_SECRET = os.environ.get("SUPERSET_GUEST_TOKEN_SECRET") or hashlib.sha256(
    (SECRET_KEY + ":crm-embedded-dashboard").encode()
).hexdigest()
GUEST_TOKEN_JWT_AUDIENCE = "crm-superset"
GUEST_TOKEN_JWT_EXP_SECONDS = 300

# Preserve the default CSP/nonces. Replace SAMEORIGIN with a bounded CSP allowlist.
EMBED_ORIGINS = [origin.strip().rstrip("/") for origin in os.environ.get(
    "SUPERSET_EMBED_ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000"
).split(",") if origin.strip()]
TALISMAN_CONFIG = deepcopy(DEFAULT_TALISMAN_CONFIG)
TALISMAN_CONFIG["frame_options"] = None
TALISMAN_CONFIG["content_security_policy"]["frame-ancestors"] = ["'self'", *EMBED_ORIGINS]
