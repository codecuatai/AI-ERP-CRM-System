"""Create 20 additional, reproducible CRM charts in a separate Superset dashboard.

Run after bootstrap_superset.py. This script only writes Superset metadata; all
charts query the existing read-only analytics datasets.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from bootstrap_superset import SupersetApi, avg_metric, count_metric, create_grid_position, sum_metric


DASHBOARD_SLUG = "crm-20-bieu-do-mo-rong"
DASHBOARD_TITLE = "CRM — 20 biểu đồ mở rộng"
MANAGED_DESCRIPTION = "Bộ 20 biểu đồ CRM mở rộng; nguồn analytics chỉ đọc."


def chart(name: str, dataset: str, kind: str, group: str, metric: dict,
          description: str, *, won_only: bool = False) -> dict:
    viz_type = {"bar": "echarts_timeseries_bar", "line": "echarts_timeseries_line", "pie": "pie"}[kind]
    params = {
        "viz_type": viz_type,
        "adhoc_filters": ([{
            "expressionType": "SIMPLE", "subject": "status", "operator": "==",
            "comparator": "WON", "clause": "WHERE", "filterOptionName": "filter_won",
        }] if won_only else []),
        "color_scheme": "supersetColors",
        "row_limit": 1000,
        "time_range": "No filter",
        "show_legend": True,
    }
    if kind == "pie":
        params.update({"groupby": [group], "metric": metric, "order_desc": True,
                       "label_type": "key_value"})
    else:
        params.update({"x_axis": group, "metrics": [metric], "groupby": [],
                       "show_value": kind == "bar"})
        if kind == "line":
            params["time_grain_sqla"] = "P1M"
    return {"name": name, "dataset": dataset, "viz_type": viz_type,
            "description": description, "params": params}


CHARTS = [
    chart("CRM 20 — Khách hàng mới theo tháng", "customer_monthly", "bar", "month",
          sum_metric("customer_count"), "Số hồ sơ khách hàng được tạo theo tháng."),
    chart("CRM 20 — Chi tiêu ghi nhận theo phân khúc", "customer_monthly", "bar", "segment",
          sum_metric("recorded_customer_spend"), "Tổng chi tiêu ghi trong hồ sơ, không phải doanh thu giao dịch."),
    chart("CRM 20 — Chi tiêu ghi nhận theo tháng tạo hồ sơ", "customer_monthly", "bar", "month",
          sum_metric("recorded_customer_spend"), "Chi tiêu tích lũy của khách được nhóm theo tháng tạo hồ sơ."),
    chart("CRM 20 — Yêu cầu tư vấn theo giải pháp", "lead_pipeline", "bar", "solution_interest",
          sum_metric("lead_count"), "Số yêu cầu tư vấn theo giải pháp chuyển đổi số."),
    chart("CRM 20 — Yêu cầu tư vấn theo tháng", "lead_pipeline", "bar", "month",
          sum_metric("lead_count"), "Số yêu cầu tư vấn được tạo theo tháng."),
    chart("CRM 20 — Việc chăm sóc theo loại", "care_task_summary", "bar", "kind",
          sum_metric("task_count"), "Khối lượng việc theo hình thức chăm sóc."),
    chart("CRM 20 — Việc chăm sóc theo ưu tiên", "care_task_summary", "bar", "priority",
          sum_metric("task_count"), "Khối lượng việc theo mức ưu tiên."),
    chart("CRM 20 — Tỷ trọng trạng thái việc", "care_task_summary", "pie", "status",
          sum_metric("task_count"), "Cơ cấu việc chăm sóc theo trạng thái."),
    chart("CRM 20 — Việc quá hạn theo ưu tiên", "care_task_summary", "bar", "priority",
          sum_metric("overdue_count"), "Việc chưa hoàn tất có hạn trước ngày hiện tại, theo ưu tiên."),
    chart("CRM 20 — Việc chăm sóc tạo theo tháng", "care_task_summary", "bar", "month",
          sum_metric("task_count"), "Số việc chăm sóc được tạo theo tháng."),
    chart("CRM 20 — Giao dịch theo trạng thái", "revenue_transactions", "pie", "status",
          count_metric(), "Số giao dịch demo theo trạng thái, kể cả giao dịch hủy."),
    chart("CRM 20 — Giá trị trung bình giao dịch chốt theo tháng", "revenue_transactions", "line", "closed_at",
          avg_metric("amount"), "Giá trị trung bình giao dịch WON theo tháng đóng; dữ liệu demo.", won_only=True),
    chart("CRM 20 — Xác suất chốt trung bình theo mức lead", "ai_lead_predictions", "bar", "tier",
          avg_metric("win_probability"), "Trung bình xác suất theo công thức chấm điểm, không phải tỷ lệ chốt thực tế."),
    chart("CRM 20 — Lead được phân tích theo giải pháp", "ai_lead_predictions", "pie", "solution_interest",
          count_metric(), "Chỉ gồm lead được phép phân tích AI và đã vào bảng kết quả."),
    chart("CRM 20 — Xác suất chốt trung bình theo giải pháp", "ai_lead_predictions", "bar", "solution_interest",
          avg_metric("win_probability"), "Trung bình xác suất theo công thức trên lead được phép phân tích."),
    chart("CRM 20 — Tương tác được phân tích theo loại", "ai_sentiment_churn", "bar", "kind",
          count_metric(), "Số tương tác được phép phân tích sắc thái theo loại."),
    chart("CRM 20 — Điểm sắc thái trung bình theo loại tương tác", "ai_sentiment_churn", "bar", "kind",
          avg_metric("sentiment_score"), "Điểm sắc thái trung bình từ quy tắc hiện hành; không phải nhãn độc lập."),
    chart("CRM 20 — Mức khẩn cấp trung bình theo rủi ro rời bỏ", "ai_sentiment_churn", "bar", "churn_risk_level",
          avg_metric("urgency_score"), "Điểm khẩn cấp trung bình theo nhóm rủi ro tính bằng quy tắc."),
    chart("CRM 20 — Chi tiêu RFM trung bình theo nhóm", "ai_customer_rfm_segments", "bar", "cluster_name",
          avg_metric("monetary"), "Giá trị monetary trung bình theo nhóm RFM tham chiếu."),
    chart("CRM 20 — Cảnh báo bất thường theo đối tượng", "ai_anomaly_alerts", "bar", "entity_type",
          count_metric(), "Số cảnh báo theo loại đối tượng do quy tắc/Z-score phát hiện."),
]


def main() -> None:
    env_file = Path(__file__).resolve().parents[1] / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line and not line.lstrip().startswith("#") and "=" in line:
                name, value = line.split("=", 1)
                os.environ.setdefault(name.strip(), value.strip().strip('"'))
    username = os.environ.get("SUPERSET_ADMIN_USERNAME")
    password = os.environ.get("SUPERSET_ADMIN_PASSWORD")
    if not username or not password:
        raise RuntimeError("Cần SUPERSET_ADMIN_USERNAME và SUPERSET_ADMIN_PASSWORD trong môi trường hoặc .env")
    url = os.environ.get("SUPERSET_URL") or f"http://127.0.0.1:{os.environ.get('SUPERSET_HOST_PORT', '18088')}"
    api = SupersetApi(url, username, password)
    api.login_web_session(username, password)
    datasets = {item["table_name"]: item["id"] for item in api.list("dataset")
                if item.get("schema") == "analytics"}
    missing = {item["dataset"] for item in CHARTS} - datasets.keys()
    if missing:
        raise RuntimeError(f"Thiếu dataset: {', '.join(sorted(missing))}. Chạy bootstrap_superset.py trước.")
    names = [item["name"] for item in CHARTS]
    if len(CHARTS) != 20 or len(set(names)) != 20:
        raise RuntimeError("Bộ mở rộng phải có đúng 20 biểu đồ khác tên.")

    existing = {item["slice_name"]: item for item in api.list("chart")}
    ids = []
    for item in CHARTS:
        previous = existing.get(item["name"])
        if previous:
            detail = api._request(f"/api/v1/chart/{previous['id']}")["result"]
            if not (detail.get("description") or "").startswith(MANAGED_DESCRIPTION):
                raise RuntimeError(f"Tên biểu đồ đã được sử dụng: {item['name']}")
        payload = {"slice_name": item["name"], "viz_type": item["viz_type"],
                   "datasource_id": datasets[item["dataset"]], "datasource_type": "table",
                   "params": json.dumps(item["params"], ensure_ascii=False),
                   "description": f"{MANAGED_DESCRIPTION} {item['description']}"}
        saved = api.upsert("chart", item["name"], payload, key="slice_name")
        ids.append(saved["id"])
        print(f"CHART {len(ids):02d}/20 id={saved['id']} {item['name']}")

    dashboard = next((item for item in api.list("dashboard") if item.get("slug") == DASHBOARD_SLUG), None)
    if dashboard:
        detail = api._request(f"/api/v1/dashboard/{dashboard['id']}")["result"]
        if detail.get("dashboard_title") != DASHBOARD_TITLE:
            raise RuntimeError(f"Dashboard slug đã được sử dụng: {DASHBOARD_SLUG}")
    payload = {"dashboard_title": DASHBOARD_TITLE, "slug": DASHBOARD_SLUG, "published": True,
               "position_json": json.dumps(create_grid_position(ids, api, columns=1)),
               "json_metadata": json.dumps({"timed_refresh_immune_slices": [], "expanded_slices": {}})}
    saved = api.upsert("dashboard", DASHBOARD_SLUG, payload, key="slug")
    dashboard_id = saved["id"]
    for chart_id in ids:
        detail = api._request(f"/api/v1/chart/{chart_id}")["result"]
        memberships = {item["id"] if isinstance(item, dict) else item
                       for item in detail.get("dashboards", [])}
        if dashboard_id not in memberships:
            api._request(f"/api/v1/chart/{chart_id}", "PUT",
                         {"dashboards": sorted(memberships | {dashboard_id})})
    print(f"DASHBOARD {url}/superset/dashboard/{DASHBOARD_SLUG}/")


if __name__ == "__main__":
    main()
