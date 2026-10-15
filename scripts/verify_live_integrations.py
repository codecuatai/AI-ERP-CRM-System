"""Read-only checks of the running Superset stack and its stdio MCP endpoint.

Run with .venv/Scripts/python.exe scripts/verify_live_integrations.py [--browser].
SQL is executed with superset_ro. Browser navigation never edits CRM data.
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

from superset.bootstrap_superset import CHARTS, SupersetApi
from superset.mcp_server import SupersetMCPServer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--browser", action="store_true")
    args = parser.parse_args()
    url = os.environ.get("SUPERSET_URL") or "http://127.0.0.1:" + os.environ.get("SUPERSET_HOST_PORT", "18088")
    api = SupersetApi(url, os.environ["SUPERSET_ADMIN_USERNAME"], os.environ["SUPERSET_ADMIN_PASSWORD"])
    datasets = {item["table_name"]: item for item in api.list("dataset")}
    charts = {item["slice_name"]: item for item in api.list("chart")}
    dashboards = api.list("dashboard")
    checks = []
    definitions = list(CHARTS)
    for chart in charts.values():
        if chart["slice_name"] in {item["name"] for item in CHARTS}:
            continue
        detail = api._request(f"/api/v1/chart/{chart['id']}")["result"]
        source = next((name for name, item in datasets.items() if item["id"] == detail.get("datasource_id")), None)
        if source:
            definitions.append({"name": chart["slice_name"], "dataset": source, "params": json.loads(detail["params"])})
    for chart in definitions:
        params = chart["params"]
        columns = params.get("groupby") or ([params["x_axis"]] if params.get("x_axis") else [])
        metrics = params.get("metrics") or [params["metric"]]
        query = {"columns": columns, "metrics": metrics, "filters": [], "row_limit": 1000,
                 "time_range": "No filter", "extras": {}}
        payload = {"datasource": {"id": datasets[chart["dataset"]]["id"], "type": "table"},
                   "queries": [query], "result_format": "json", "result_type": "full"}
        try:
            response = api._request("/api/v1/chart/data", "POST", payload)
            result = response["result"][0]
            checks.append({"chart": chart["name"], "id": charts[chart["name"]]["id"],
                           "status": result.get("status"), "rows": result.get("rowcount"), "error": result.get("error")})
        except Exception as exc:
            checks.append({"chart": chart["name"], "status": "failed", "error": str(exc)[:500]})
    server = SupersetMCPServer()
    role = server.execute_sql("SELECT current_user AS role")
    denied = server.execute_sql("SELECT count(*) FROM public.crm_customer")
    requests = [
        {"jsonrpc":"2.0", "id":1, "method":"initialize", "params":{"protocolVersion":"2025-06-18", "capabilities":{}, "clientInfo":{"name":"live-verification", "version":"1"}}},
        {"jsonrpc":"2.0", "method":"notifications/initialized"},
        {"jsonrpc":"2.0", "id":2, "method":"tools/list"},
        {"jsonrpc":"2.0", "id":3, "method":"ping"},
    ]
    process = subprocess.run([sys.executable, "manage.py", "run_superset_mcp"], cwd=ROOT,
        input="\n".join(json.dumps(x) for x in requests)+"\n", capture_output=True, text=True, encoding="utf-8", timeout=30)
    rpc_responses = [json.loads(line) for line in process.stdout.splitlines() if line.strip()]
    report = {"datasets": len(datasets), "charts": len(charts),
        "dashboards": [{"id": d["id"], "slug": d.get("slug"), "published": d.get("published")} for d in dashboards],
        "chart_queries": checks, "mcp_role": role, "mcp_source_table_access": denied,
        "mcp_stdio": {"exit_code": process.returncode, "response_ids": [x.get("id") for x in rpc_responses],
                      "initialization_ok": bool(rpc_responses and "serverInfo" in rpc_responses[0].get("result", {}))}}
    if args.browser:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width":1440,"height":1000})
            page.goto(url + "/login/", wait_until="networkidle")
            page.locator('#username').fill(os.environ["SUPERSET_ADMIN_USERNAME"])
            page.locator('#password').fill(os.environ["SUPERSET_ADMIN_PASSWORD"])
            page.locator('button[type="submit"], input[type="submit"]').first.click()
            page.wait_for_url(lambda address: "/login" not in address)
            rendered = []
            for dashboard in report["dashboards"]:
                page.goto(url + "/superset/dashboard/" + dashboard["slug"] + "/", wait_until="networkidle")
                page.locator('.dashboard-component-chart-holder').first.wait_for(timeout=30000)
                # ECharts draws its entrance animation after networkidle; wait
                # for it before saving visual evidence or checking late errors.
                page.wait_for_timeout(1500)
                page.screenshot(path=str(ROOT / "docs" / "validation" / (dashboard["slug"] + ".png")), full_page=True)
                errors = page.locator('.ant-alert-error:visible, .alert-danger:visible').all_text_contents()
                rendered.append({"slug":dashboard["slug"], "chart_holders":page.locator('.dashboard-component-chart-holder').count(), "visible_errors":errors})
            report["browser"] = rendered
            browser.close()
    path = ROOT / "docs" / "validation" / "superset-live.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    assert len(checks) >= len(CHARTS) and all(c["status"] == "success" and not c["error"] for c in checks), "Superset chart query failed"
    if args.browser:
        assert all(item["chart_holders"] > 0 and not item["visible_errors"] for item in report["browser"]), "Superset dashboard render failed"
    assert role["status"] == "SUCCESS" and role["data"][0]["role"] == "superset_ro", "MCP SQL must use the reader role"
    assert denied["status"] == "ERROR", "MCP must not read raw CRM tables"
    assert report["mcp_stdio"]["response_ids"] == [1, 2, 3] and report["mcp_stdio"]["initialization_ok"], "Invalid MCP stdio"


if __name__ == "__main__":
    main()
