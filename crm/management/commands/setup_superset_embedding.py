"""Enable embedding for the fixed CRM AI dashboard; run after Superset bootstrap."""

import os
from urllib.parse import urlsplit

from django.core.management.base import BaseCommand, CommandError

from django.core.cache import cache
from crm.services.superset_embed import DASHBOARD_SLUG, LIVE_CHARTS, superset_api
from superset.bootstrap_superset import create_grid_position
import json


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
            api = superset_api(authoring=True)
            api.login_web_session(
                os.environ.get("SUPERSET_ADMIN_USERNAME", "admin"),
                os.environ.get("SUPERSET_ADMIN_PASSWORD", "admin"),
            )
            dashboard = api._request(f"/api/v1/dashboard/{DASHBOARD_SLUG}")["result"]
            api._request(f"/api/v1/dashboard/{dashboard['id']}/embedded", "POST", {"allowed_domains": origins})
            charts = {chart["slice_name"]: chart for chart in api.list("chart")}
            for widget in LIVE_CHARTS:
                chart = charts[widget["chart_name"]]
                position = create_grid_position([chart["id"]], api)
                position[f"CHART-{chart['id']}"]["meta"].update({"width": 12, "height": 45})
                saved = api.upsert("dashboard", widget["slug"], {
                    "dashboard_title": "CRM Live — " + widget["title"], "slug": widget["slug"],
                    "published": True, "position_json": json.dumps(position),
                    "json_metadata": json.dumps({"expanded_slices": {}}),
                }, key="slug")
                detail = api._request(f"/api/v1/chart/{chart['id']}")["result"]
                memberships = {item["id"] if isinstance(item, dict) else item for item in detail.get("dashboards", [])}
                api._request(f"/api/v1/chart/{chart['id']}", "PUT", {"dashboards": sorted(memberships | {saved['id']})})
                api._request(f"/api/v1/dashboard/{saved['id']}/embedded", "POST", {"allowed_domains": origins})
            cache.delete("crm-live-embeddings:" + api.base_url)
        except Exception as exc:
            raise CommandError("Không cấu hình được embedding. Kiểm tra Superset, tài khoản dịch vụ và bootstrap dashboard.") from exc
        self.stdout.write(self.style.SUCCESS("Đã bật nhúng dashboard AI cho: " + ", ".join(origins)))
