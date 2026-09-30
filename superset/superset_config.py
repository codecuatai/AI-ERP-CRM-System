"""Local Docker configuration for the CRM analytics demo."""

import os
from urllib.parse import quote_plus


SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]
meta_password = quote_plus(os.environ["SUPERSET_META_PASSWORD"])
SQLALCHEMY_DATABASE_URI = (
    f"postgresql://superset_meta:{meta_password}@superset-meta-db:5432/superset_meta"
)
WTF_CSRF_ENABLED = True
