"""Create the CRM analytics database, datasets, charts and dashboard in Superset.

This uses Superset's public REST API so the demo can be recreated without
clicking through the UI. Credentials are read only from environment variables.
"""

from __future__ import annotations

import http.cookiejar
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request


class SupersetApi:
    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )
        self.token = self._request(
            "/api/v1/security/login",
            "POST",
            {"username": username, "password": password, "provider": "db", "refresh": True},
            auth=False,
        )["access_token"]
        self.csrf = self._request("/api/v1/security/csrf_token/")["result"]

    def _request(self, path: str, method: str = "GET", payload: dict | None = None, *, auth: bool = True):
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"} if body else {}
        if auth:
            headers["Authorization"] = f"Bearer {self.token}"
            if method != "GET":
                headers["X-CSRFToken"] = self.csrf
        request = urllib.request.Request(
            self.base_url + path, data=body, headers=headers, method=method
        )
        try:
            with self.opener.open(request) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Superset API {method} {path} failed ({exc.code}): {detail}") from exc
        return result

    def list(self, resource: str) -> list[dict]:
        result = self._request(f"/api/v1/{resource}/?q=(page:0,page_size:100)")
        return result.get("result", [])

    def upsert(
        self,
        resource: str,
        identity: str,
        payload: dict,
        *,
        key: str,
        extra: dict | None = None,
        update_existing: bool = True,
    ) -> dict:
        for item in self.list(resource):
            if item.get(key) == identity:
                item_id = item["id"]
                if not update_existing:
                    return item
                updated = dict(payload)
                if extra:
                    updated.update(extra)
                return self._request(f"/api/v1/{resource}/{item_id}", "PUT", updated).get(
                    "result", item
                ) | {"id": item_id}
        created = self._request(f"/api/v1/{resource}/", "POST", payload)
        result = created.get("result", {})
        return result | {"id": created.get("id", result.get("id"))}


DATASETS = [
    ("customer_monthly", "Khách hàng theo tháng và phân khúc"),
    ("lead_pipeline", "Phễu yêu cầu tư vấn"),
    ("care_task_summary", "Việc chăm sóc và quá hạn"),
    ("revenue_transactions", "Giao dịch doanh thu"),
]


def sum_metric(column: str) -> dict:
    """Return a Superset adhoc SUM metric for a physical dataset column."""
    return {
        "aggregate": "SUM",
        "column": {"column_name": column},
        "expressionType": "SIMPLE",
        "hasCustomMetric": False,
        "label": f"SUM({column})",
        "optionName": f"metric_sum_{column}",
    }

CHARTS = [
    {
        "name": "CRM — Khách hàng theo phân khúc",
        "dataset": "customer_monthly",
        "viz_type": "pie",
        "description": "Phân bổ khách hàng theo phân khúc AI.",
        "params": {
            "adhoc_filters": [], "color_scheme": "supersetColors", "groupby": ["segment"],
            "metrics": [sum_metric("customer_count")], "order_desc": True, "row_limit": 10000,
            "show_legend": True, "show_value": True, "time_range": "No filter", "viz_type": "pie",
        },
    },
    {
        "name": "CRM — Lead theo trạng thái",
        "dataset": "lead_pipeline",
        "viz_type": "bar",
        "description": "Số yêu cầu tư vấn theo trạng thái.",
        "params": {
            "adhoc_filters": [], "color_scheme": "supersetColors", "groupby": ["status"],
            "metrics": [sum_metric("lead_count")], "order_desc": True, "row_limit": 10000,
            "show_legend": True, "show_value": True, "time_range": "No filter", "viz_type": "bar",
        },
    },
    {
        "name": "CRM — Việc chăm sóc quá hạn",
        "dataset": "care_task_summary",
        "viz_type": "bar",
        "description": "Tổng việc và số việc quá hạn theo trạng thái.",
        "params": {
            "adhoc_filters": [], "color_scheme": "supersetColors", "groupby": ["status"],
            "metrics": [sum_metric("task_count"), sum_metric("overdue_count")], "order_desc": True,
            "row_limit": 10000, "show_legend": True, "show_value": True,
            "time_range": "No filter", "viz_type": "bar",
        },
    },
    {
        "name": "CRM — Doanh thu đã chốt theo tháng",
        "dataset": "revenue_transactions",
        "viz_type": "line",
        "description": "Doanh thu WON theo tháng; giao dịch VOID có giá trị bằng 0.",
        "params": {
            "adhoc_filters": [], "color_scheme": "supersetColors", "granularity_sqla": "closed_at",
            "metrics": [sum_metric("won_revenue")], "row_limit": 10000, "time_grain_sqla": "P1M",
            "time_range": "No filter", "viz_type": "line", "x_axis": "closed_at",
        },
    },
]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    # Allow the documented host-side command to use the project's .env without
    # requiring users to copy secrets into their PowerShell session.
    env_file = Path(__file__).resolve().parents[1] / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if not line or line.lstrip().startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip().strip('"'))
    required = ["SUPERSET_ADMIN_USERNAME", "SUPERSET_ADMIN_PASSWORD", "SUPERSET_READONLY_PASSWORD"]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        print("Thiếu biến môi trường: " + ", ".join(missing), file=sys.stderr)
        return 2

    api = SupersetApi(
        os.environ.get("SUPERSET_URL", "http://127.0.0.1:8088"),
        os.environ["SUPERSET_ADMIN_USERNAME"],
        os.environ["SUPERSET_ADMIN_PASSWORD"],
    )
    crm_host = os.environ.get("SUPERSET_CRM_HOST", "crm-db")
    crm_name = os.environ.get("CRM_DB_NAME", "crm")
    readonly_password = urllib.parse.quote(os.environ["SUPERSET_READONLY_PASSWORD"], safe="")
    database = api.upsert(
        "database",
        "CRM Analytics",
        {
            "database_name": "CRM Analytics",
            "sqlalchemy_uri": f"postgresql://superset_ro:{readonly_password}@{crm_host}:5432/{crm_name}",
            "expose_in_sqllab": True,
            "allow_ctas": False,
            "allow_cvas": False,
            "allow_dml": False,
            "allow_multi_catalog": False,
            "allow_file_upload": False,
            "extra": json.dumps({"metadata_params": {}, "engine_params": {}}),
        },
        key="database_name",
    )
    database_id = database["id"]
    datasets = {}
    for table_name, description in DATASETS:
        dataset = api.upsert(
            "dataset",
            table_name,
            {"database": database_id, "schema": "analytics", "table_name": table_name},
            key="table_name",
            update_existing=False,
        )
        datasets[table_name] = dataset["id"]
        print(f"DATASET {table_name}: id={dataset['id']} — {description}")

    chart_ids = []
    for chart in CHARTS:
        params = dict(chart["params"])
        payload = {
            "slice_name": chart["name"],
            "viz_type": chart["viz_type"],
            "datasource_id": datasets[chart["dataset"]],
            "datasource_type": "table",
            "params": json.dumps(params, separators=(",", ":")),
            "description": chart["description"],
        }
        saved = api.upsert("chart", chart["name"], payload, key="slice_name")
        chart_ids.append(saved["id"])
        print(f"CHART {chart['name']}: id={saved['id']}")

    children = []
    position = {"DASHBOARD_VERSION_KEY": "v2"}
    for index, chart_id in enumerate(chart_ids):
        node_id = f"CHART-{chart_id}"
        children.append(node_id)
        position[node_id] = {
            "id": node_id,
            "type": "CHART",
            "children": [],
            "parents": ["ROOT_ID"],
            "meta": {"chartId": chart_id, "height": 50, "width": 6},
        }
    position["ROOT_ID"] = {"id": "ROOT_ID", "type": "ROOT", "children": children}
    dashboard = api.upsert(
        "dashboard",
        "crm-analytics-dashboard",
        {
            "dashboard_title": "CRM Analytics — Tổng hợp kinh doanh",
            "slug": "crm-analytics-dashboard",
            "published": True,
            "position_json": json.dumps(position, separators=(",", ":")),
            "json_metadata": json.dumps({"timed_refresh_immune_slices": [], "expanded_slices": {}}),
        },
        key="slug",
    )
    print(f"DASHBOARD id={dashboard['id']} slug=crm-analytics-dashboard")
    print("Bootstrap Superset hoàn tất. Mở /superset/dashboard/crm-analytics-dashboard/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
