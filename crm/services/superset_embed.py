"""Server-side authorization for the single CRM AI dashboard."""

import os

from superset.bootstrap_superset import SupersetApi


DASHBOARD_SLUG = "crm-ai-intelligence-dashboard"


def superset_api():
    port = os.environ.get("SUPERSET_HOST_PORT", "18088")
    return SupersetApi(
        os.environ.get("SUPERSET_URL") or f"http://127.0.0.1:{port}",
        os.environ.get("SUPERSET_EMBED_USERNAME") or os.environ.get("SUPERSET_ADMIN_USERNAME", "admin"),
        os.environ.get("SUPERSET_EMBED_PASSWORD") or os.environ.get("SUPERSET_ADMIN_PASSWORD", "admin"),
        timeout=5,
    )


def dashboard_embedding(api):
    # Never accept a dashboard ID, resource, SQL expression or RLS from the client.
    dashboard = api._request(f"/api/v1/dashboard/{DASHBOARD_SLUG}")["result"]
    embedded = api._request(f"/api/v1/dashboard/{dashboard['id']}/embedded")["result"]
    return str(embedded["uuid"])


def guest_session(user):
    api = superset_api()
    embedded_id = dashboard_embedding(api)
    token = api._request("/api/v1/security/guest_token/", "POST", {
        "user": {"username": f"crm-{user.pk}", "first_name": "CRM", "last_name": "Viewer"},
        "resources": [{"type": "dashboard", "id": embedded_id}],
        "rls": [],
    })["token"]
    return {"id": embedded_id, "token": token}
