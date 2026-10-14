"""Create the CRM analytics and AI Intelligence database, datasets, charts and dashboards in Superset.

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
    ("ai_lead_predictions", "Dự báo tiềm năng & xác suất chốt Lead (AI Win-Rate)"),
    ("ai_sentiment_churn", "Phân tích cảm xúc tương tác & cảnh báo Churn (NLP)"),
    ("ai_customer_rfm_segments", "Phân khúc khách hàng đa chiều RFM K-Means"),
    ("ai_revenue_forecast", "Dự báo doanh thu chuỗi thời gian 4 tháng tới (Prophet)"),
    ("ai_explainability_summary", "Giải thích trọng số đóng góp đặc trưng (XAI)"),
    ("ai_anomaly_alerts", "Cảnh báo bất thường vận hành & giao dịch"),
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


def count_metric(column: str | None = None) -> dict:
    """Return a Superset adhoc COUNT metric."""
    if column:
        return {
            "aggregate": "COUNT",
            "column": {"column_name": column},
            "expressionType": "SIMPLE",
            "hasCustomMetric": False,
            "label": f"COUNT({column})",
            "optionName": f"metric_count_{column}",
        }
    return {
        "expressionType": "SQL",
        "sqlExpression": "COUNT(*)",
        "label": "COUNT(*)",
        "optionName": "metric_count_star",
    }


def avg_metric(column: str) -> dict:
    """Return a Superset adhoc AVG metric."""
    return {
        "aggregate": "AVG",
        "column": {"column_name": column},
        "expressionType": "SIMPLE",
        "hasCustomMetric": False,
        "label": f"AVG({column})",
        "optionName": f"metric_avg_{column}",
    }


CHARTS = [
    # ── 1. CÁC BIỂU ĐỒ CRM VẬN HÀNH CƠ BẢN ────────────────────────────────────
    {
        "name": "CRM — Khách hàng theo phân khúc",
        "dataset": "customer_monthly",
        "viz_type": "pie",
        "description": "Phân bổ khách hàng theo phân khúc AI.",
        "params": {
            "adhoc_filters": [], "color_scheme": "supersetColors", "groupby": ["segment"],
            "metric": sum_metric("customer_count"), "order_desc": True, "row_limit": 10000,
            "show_legend": True, "label_type": "key_value", "time_range": "No filter", "viz_type": "pie",
        },
    },
    {
        "name": "CRM — Lead theo trạng thái",
        "dataset": "lead_pipeline",
        "viz_type": "echarts_timeseries_bar",
        "description": "Số yêu cầu tư vấn theo trạng thái.",
        "params": {
            "adhoc_filters": [], "color_scheme": "supersetColors", "x_axis": "status",
            "metrics": [sum_metric("lead_count")], "order_desc": True, "row_limit": 10000,
            "show_legend": True, "show_value": True, "time_range": "No filter", "viz_type": "echarts_timeseries_bar",
        },
    },
    {
        "name": "CRM — Việc chăm sóc quá hạn",
        "dataset": "care_task_summary",
        "viz_type": "echarts_timeseries_bar",
        "description": "Tổng việc và số việc quá hạn theo trạng thái.",
        "params": {
            "adhoc_filters": [], "color_scheme": "supersetColors", "x_axis": "status",
            "metrics": [sum_metric("task_count"), sum_metric("overdue_count")], "order_desc": True,
            "row_limit": 10000, "show_legend": True, "show_value": True,
            "time_range": "No filter", "viz_type": "echarts_timeseries_bar",
        },
    },
    {
        "name": "CRM — Doanh thu đã chốt theo tháng",
        "dataset": "revenue_transactions",
        "viz_type": "echarts_timeseries_line",
        "description": "Doanh thu WON theo tháng; giao dịch VOID có giá trị bằng 0.",
        "params": {
            "adhoc_filters": [], "color_scheme": "supersetColors", "x_axis": "closed_at",
            "metrics": [sum_metric("won_revenue")], "row_limit": 10000, "time_grain_sqla": "P1M",
            "time_range": "No filter", "viz_type": "echarts_timeseries_line",
        },
    },

    # ── 2. CÁC BIỂU ĐỒ AI PHÂN TÍCH & DỰ BÁO THÔNG MINH (TH2) ──────────────────
    {
        "name": "AI — Phân bố Tiềm năng Lead (HOT / WARM / COLD)",
        "dataset": "ai_lead_predictions",
        "viz_type": "pie",
        "description": "Mô hình Win-Rate Classifier xếp hạng mức độ tiềm năng chuyển đổi của Lead.",
        "params": {
            "adhoc_filters": [], "color_scheme": "echartsColors", "groupby": ["tier"],
            "metric": count_metric(), "order_desc": True, "row_limit": 1000,
            "show_legend": True, "label_type": "key_value", "time_range": "No filter", "viz_type": "pie",
        },
    },
    {
        "name": "AI — Doanh thu Kỳ vọng theo Giải pháp (Expected Won)",
        "dataset": "ai_lead_predictions",
        "viz_type": "echarts_timeseries_bar",
        "description": "Giá trị hợp đồng kỳ vọng tính bằng Giá trị dự kiến * Xác suất thắng P(Win).",
        "params": {
            "adhoc_filters": [], "color_scheme": "supersetColors", "x_axis": "solution_interest",
            "metrics": [sum_metric("expected_won_value"), sum_metric("estimated_deal_value")],
            "order_desc": True, "row_limit": 1000, "show_legend": True, "show_value": True,
            "time_range": "No filter", "viz_type": "echarts_timeseries_bar",
        },
    },
    {
        "name": "AI — Phân bổ Cảm xúc Tương tác (NLP Sentiment)",
        "dataset": "ai_sentiment_churn",
        "viz_type": "pie",
        "description": "Phân tích sắc thái cảm xúc khách hàng qua các phiên trao đổi và ghi chú chăm sóc.",
        "params": {
            "adhoc_filters": [], "color_scheme": "googleCategory20c", "groupby": ["sentiment_label"],
            "metric": count_metric(), "order_desc": True, "row_limit": 1000,
            "show_legend": True, "label_type": "key_value", "time_range": "No filter", "viz_type": "pie",
        },
    },
    {
        "name": "AI — Cảnh báo Rủi ro Rời bỏ Khách hàng (Churn Risk)",
        "dataset": "ai_sentiment_churn",
        "viz_type": "echarts_timeseries_bar",
        "description": "Phát hiện sớm các tài khoản có nguy cơ churn dựa trên sắc thái âm tính và độ trễ liên hệ.",
        "params": {
            "adhoc_filters": [], "color_scheme": "d3Category20", "x_axis": "churn_risk_level",
            "metrics": [count_metric()], "order_desc": True, "row_limit": 1000,
            "show_legend": True, "show_value": True, "time_range": "No filter", "viz_type": "echarts_timeseries_bar",
        },
    },
    {
        "name": "AI — Phân cụm Khách hàng K-Means RFM",
        "dataset": "ai_customer_rfm_segments",
        "viz_type": "pie",
        "description": "Phân khúc khách hàng 4 cụm dựa trên Recency, Frequency, Monetary.",
        "params": {
            "adhoc_filters": [], "color_scheme": "supersetColors", "groupby": ["cluster_name"],
            "metric": count_metric(), "order_desc": True, "row_limit": 1000,
            "show_legend": True, "label_type": "key_value", "time_range": "No filter", "viz_type": "pie",
        },
    },
    {
        "name": "AI — Dự báo Doanh thu Chuỗi thời gian (Prophet Forecast)",
        "dataset": "ai_revenue_forecast",
        "viz_type": "echarts_timeseries_line",
        "description": "Dự báo doanh thu các tháng tiếp theo kèm dải tin cậy 95% (Lower / Upper Bound).",
        "params": {
            "adhoc_filters": [], "color_scheme": "supersetColors", "x_axis": "forecast_date",
            "metrics": [sum_metric("predicted_revenue"), sum_metric("upper_bound_95"), sum_metric("lower_bound_95")],
            "row_limit": 100, "time_grain_sqla": "P1M", "time_range": "No filter", "viz_type": "echarts_timeseries_line",
        },
    },
    {
        "name": "AI — Trọng số Đóng góp Đặc trưng (Explainable AI - XAI)",
        "dataset": "ai_explainability_summary",
        "viz_type": "echarts_timeseries_bar",
        "description": "Mức độ đóng góp của từng đặc trưng (SHAP-style) vào quyết định chấm điểm của mô hình.",
        "params": {
            "adhoc_filters": [], "color_scheme": "echartsColors", "x_axis": "feature_name",
            "metrics": [sum_metric("importance_weight")], "order_desc": True, "row_limit": 100,
            "show_legend": True, "show_value": True, "time_range": "No filter", "viz_type": "echarts_timeseries_bar",
        },
    },
    {
        "name": "AI — Cảnh báo Bất thường Vận hành (Anomaly Detection)",
        "dataset": "ai_anomaly_alerts",
        "viz_type": "echarts_timeseries_bar",
        "description": "Số lượng cảnh báo bất thường phát hiện theo mức độ nghiêm trọng (Severity).",
        "params": {
            "adhoc_filters": [], "color_scheme": "d3Category20", "x_axis": "severity",
            "metrics": [count_metric()], "order_desc": True, "row_limit": 100,
            "show_legend": True, "show_value": True, "time_range": "No filter", "viz_type": "echarts_timeseries_bar",
        },
    },
]


def create_grid_position(chart_slice_ids: list[int], api: SupersetApi) -> dict:
    """Builds a responsive 2-column grid layout position dictionary for Superset dashboard."""
    position = {"DASHBOARD_VERSION_KEY": "v2"}
    position["ROOT_ID"] = {"id": "ROOT_ID", "type": "ROOT", "children": ["GRID_ID"]}
    position["GRID_ID"] = {"id": "GRID_ID", "type": "GRID", "parents": ["ROOT_ID"], "children": []}

    rows = []
    for i in range(0, len(chart_slice_ids), 2):
        row_id = f"ROW-AUTO-{i // 2 + 1}"
        rows.append(row_id)
        pair = chart_slice_ids[i : i + 2]
        children = []

        position[row_id] = {
            "id": row_id,
            "type": "ROW",
            "parents": ["ROOT_ID", "GRID_ID"],
            "children": children,
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
        }

        for c_id in pair:
            node_id = f"CHART-{c_id}"
            children.append(node_id)
            chart_detail = api._request(f"/api/v1/chart/{c_id}")["result"]
            position[node_id] = {
                "id": node_id,
                "type": "CHART",
                "children": [],
                "parents": ["ROOT_ID", "GRID_ID", row_id],
                "meta": {
                    "chartId": c_id,
                    "uuid": chart_detail.get("uuid", ""),
                    "sliceName": chart_detail.get("slice_name", ""),
                    "height": 50,
                    "width": 6,
                },
            }

    position["GRID_ID"]["children"] = rows
    return position


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

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

    # 1. Connect Database
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

    # 2. Register Datasets
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

    # 3. Create or Update Charts
    chart_ids = []
    ai_chart_ids = []
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
        c_id = saved["id"]
        chart_ids.append(c_id)
        if chart["name"].startswith("AI —"):
            ai_chart_ids.append(c_id)
        print(f"CHART {chart['name']}: id={c_id}")

    # 4. Create Dashboard 1: General CRM & Business Analytics
    dash_pos_1 = create_grid_position(chart_ids[:8], api)
    dashboard_1 = api.upsert(
        "dashboard",
        "crm-analytics-dashboard",
        {
            "dashboard_title": "CRM Analytics — Tổng hợp kinh doanh & AI",
            "slug": "crm-analytics-dashboard",
            "published": True,
            "position_json": json.dumps(dash_pos_1, separators=(",", ":")),
            "json_metadata": json.dumps({"timed_refresh_immune_slices": [], "expanded_slices": {}}),
        },
        key="slug",
    )
    for cid in chart_ids[:8]:
        api._request(f"/api/v1/chart/{cid}", "PUT", {"dashboards": [dashboard_1["id"]]})
    print(f"DASHBOARD 1 id={dashboard_1['id']} slug=crm-analytics-dashboard")

    # 5. Create Dashboard 2: AI Intelligence & Predictive Analytics (TH2 Specialization)
    dash_pos_2 = create_grid_position(ai_chart_ids, api)
    dashboard_2 = api.upsert(
        "dashboard",
        "crm-ai-intelligence-dashboard",
        {
            "dashboard_title": "CRM AI Intelligence — Phân tích Dữ liệu Thông minh & Dự báo (TH2)",
            "slug": "crm-ai-intelligence-dashboard",
            "published": True,
            "position_json": json.dumps(dash_pos_2, separators=(",", ":")),
            "json_metadata": json.dumps({"timed_refresh_immune_slices": [], "expanded_slices": {}}),
        },
        key="slug",
    )
    for cid in ai_chart_ids:
        api._request(f"/api/v1/chart/{cid}", "PUT", {"dashboards": [dashboard_2["id"]]})
    print(f"DASHBOARD 2 id={dashboard_2['id']} slug=crm-ai-intelligence-dashboard")

    print("\n[SUCCESS] Bootstrap Superset hoàn tất!")
    print("👉 Dashboard 1: /superset/dashboard/crm-analytics-dashboard/")
    print("👉 Dashboard 2 (AI TH2): /superset/dashboard/crm-ai-intelligence-dashboard/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
