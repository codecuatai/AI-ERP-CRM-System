"""Server-side authorization for the fixed CRM live chart dashboards."""

import os

from django.core.cache import cache
from superset.bootstrap_superset import CHARTS, SupersetApi


DASHBOARD_SLUG = "crm-ai-intelligence-dashboard"
LIVE_CHARTS = [
    {"key": key, "title": title, "local_id": local_id, "chart_name": definition["name"], "slug": f"crm-live-{key}"}
    for (key, title, local_id), definition in zip([
        ("leads", "Mức ưu tiên lead", "chartLeadTier"),
        ("solutions", "Giá trị cơ hội theo giải pháp", "chartSolutions"),
        ("sentiment", "Cảm xúc tương tác", "chartSentimentChurn"),
        ("churn", "Rủi ro cần chăm sóc", "chartChurn"),
        ("rfm", "Phân nhóm chăm sóc RFM", "chartRfm"),
        ("forecast", "Dự báo doanh thu", "chartForecast"),
        ("xai", "Đóng góp vào điểm ưu tiên", "chartXai"),
        ("anomalies", "Cảnh báo bất thường", "chartAnomalies"),
    ], CHARTS[4:])
]


def superset_api(*, authoring=False):
    port = os.environ.get("SUPERSET_HOST_PORT", "18088")
    return SupersetApi(
        os.environ.get("SUPERSET_URL") or f"http://127.0.0.1:{port}",
        (None if authoring else os.environ.get("SUPERSET_EMBED_USERNAME")) or os.environ.get("SUPERSET_ADMIN_USERNAME", "admin"),
        (None if authoring else os.environ.get("SUPERSET_EMBED_PASSWORD")) or os.environ.get("SUPERSET_ADMIN_PASSWORD", "admin"),
        timeout=5,
    )


def dashboard_embedding(api, slug=DASHBOARD_SLUG):
    # Never accept a dashboard ID, resource, SQL expression or RLS from the client.
    dashboard = api._request(f"/api/v1/dashboard/{slug}")["result"]
    embedded = api._request(f"/api/v1/dashboard/{dashboard['id']}/embedded")["result"]
    return str(embedded["uuid"])


def guest_session(user):
    api = superset_api()
    cache_key = "crm-live-embeddings:" + api.base_url
    widgets = cache.get(cache_key)
    if widgets is None:
        widgets = [{"key": chart["key"], "id": dashboard_embedding(api, chart["slug"])} for chart in LIVE_CHARTS]
        cache.set(cache_key, widgets, 300)
    token = api._request("/api/v1/security/guest_token/", "POST", {
        "user": {"username": f"crm-{user.pk}", "first_name": "CRM", "last_name": "Viewer"},
        "resources": [{"type": "dashboard", "id": widget["id"]} for widget in widgets],
        "rls": [],
    })["token"]
    return {"widgets": widgets, "token": token}
