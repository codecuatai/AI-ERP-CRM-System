"""Exercise confirmed MCP mutations on fictional analytics, preserving existing dashboards.

Creates two reusable charts and a draft dashboard; never changes CRM records or
sends messages. Re-running with identical parameters reuses the created objects.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
import django
django.setup()


def call_tool(name, arguments):
    messages = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "crm-mcp-authoring-verification", "version": "1"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": name, "arguments": arguments}},
    ]
    completed = subprocess.run([sys.executable, "manage.py", "run_superset_mcp"], cwd=ROOT,
        input="\n".join(json.dumps(item) for item in messages) + "\n", capture_output=True, text=True,
        encoding="utf-8", timeout=120, check=True)
    responses = [json.loads(line) for line in completed.stdout.splitlines() if line.strip()]
    response = next(item for item in responses if item.get("id") == 2)
    if "error" in response or response["result"].get("isError"):
        raise RuntimeError(json.dumps(response, ensure_ascii=False))
    return json.loads(response["result"]["content"][0]["text"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all-kinds", action="store_true", help="Kiểm tra thêm bar/table/number trên dashboard thư viện nháp.")
    options = parser.parse_args()
    datasets = {item["table_name"]: item for item in call_tool("superset_list_datasets", {})}
    requests = [
        {"confirm": True, "replace_existing": True, "title": "MCP — Phân nhóm chăm sóc khách hàng", "dataset_id": datasets["ai_customer_rfm_segments"]["id"],
         "kind": "pie", "group_by": "cluster_name", "metric": "count"},
        {"confirm": True, "replace_existing": True, "title": "MCP — Dự báo doanh thu có baseline", "dataset_id": datasets["ai_revenue_forecast"]["id"],
         "kind": "line", "group_by": "forecast_date", "metric": "sum", "metric_column": "predicted_revenue"},
    ]
    if options.all_kinds:
        requests.extend([
            {"confirm": True, "title": "MCP — Giá trị ước tính theo giải pháp", "dataset_id": datasets["ai_lead_predictions"]["id"],
             "kind": "bar", "group_by": "solution_interest", "metric": "sum", "metric_column": "expected_won_value"},
            {"confirm": True, "title": "MCP — Bảng nhóm rủi ro tương tác", "dataset_id": datasets["ai_sentiment_churn"]["id"],
             "kind": "table", "group_by": "churn_risk_level", "metric": "count"},
            {"confirm": True, "title": "MCP — Tổng doanh thu dự báo bốn tháng", "dataset_id": datasets["ai_revenue_forecast"]["id"],
             "kind": "number", "metric": "sum", "metric_column": "predicted_revenue"},
        ])
    charts = [call_tool("superset_create_chart", args) for args in requests]
    replay = [call_tool("superset_create_chart", args) for args in requests]
    assert [item["id"] for item in charts] == [item["id"] for item in replay]
    assert all(not item["created"] for item in replay), "Identical calls must not create duplicates"
    dashboard_args = {"confirm": True, "title": "CRM MCP — Phân tích chăm sóc và dự báo", "slug": "crm-mcp-consultations",
                      "chart_ids": [item["id"] for item in charts], "published": False}
    if options.all_kinds:
        dashboard_args.update({"title": "CRM MCP — Thư viện năm loại biểu đồ", "slug": "crm-mcp-visualization-gallery"})
    dashboard = call_tool("superset_create_dashboard", dashboard_args)
    dashboard_replay = call_tool("superset_create_dashboard", dashboard_args)
    assert dashboard_replay["id"] == dashboard["id"] and not dashboard_replay["created"]
    report = {"transport": "MCP stdio with initialize and explicit confirm=true", "charts": charts,
              "repeated_charts": replay, "dashboard": dashboard, "repeated_dashboard": dashboard_replay,
              "data_source": "CRM analytics with authored demo records; no real customer data imported"}
    path = ROOT / "docs" / "validation" / ("mcp-authoring-gallery.json" if options.all_kinds else "mcp-authoring-live.json")
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
