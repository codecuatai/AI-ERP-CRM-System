"""Enable embedding for the fixed CRM AI dashboard; run after Superset bootstrap."""

import os
from urllib.parse import urlsplit

from django.core.management.base import BaseCommand, CommandError

from crm.services.superset_embed import DASHBOARD_SLUG, superset_api


class Command(BaseCommand):
    help = "Cho phép nhúng dashboard AI vào các origin CRM đã cấu hình."

    def handle(self, *args, **options):
        origins = [value.strip().rstrip("/") for value in os.environ.get(
            "SUPERSET_EMBED_ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000"
        ).split(",") if value.strip()]
        if not origins or any(
            urlsplit(origin).scheme not in {"http", "https"}
            or not urlsplit(origin).netloc
            or urlsplit(origin).path
            or urlsplit(origin).query
            or urlsplit(origin).fragment
            or urlsplit(origin).username
            or "*" in origin
            for origin in origins
        ):
            raise CommandError("SUPERSET_EMBED_ALLOWED_ORIGINS cần danh sách origin HTTP(S), không có path hoặc wildcard.")
        try:
            api = superset_api()
            dashboard = api._request(f"/api/v1/dashboard/{DASHBOARD_SLUG}")["result"]
            api._request(f"/api/v1/dashboard/{dashboard['id']}/embedded", "POST", {"allowed_domains": origins})
        except Exception as exc:
            raise CommandError("Không cấu hình được embedding. Kiểm tra Superset, tài khoản dịch vụ và bootstrap dashboard.") from exc
        self.stdout.write(self.style.SUCCESS("Đã bật nhúng dashboard AI cho: " + ", ".join(origins)))
