"""Apache Superset MCP (Model Context Protocol) Server.

Enables AI Agents and LLMs to interact with Apache Superset and the CRM AI Analytics
Data Mart via standard MCP tool calls:
- superset_list_dashboards: Enumerate dashboards and URLs.
- superset_execute_sql: Run analytical queries on CRM analytics schema.
- superset_query_ai_insights: Extract high-level insights from AI models.
- superset_trigger_pipeline: Trigger AI recalculation pipeline.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List

import urllib.request
import urllib.error


class SupersetMCPServer:
    """Lightweight Model Context Protocol (MCP) server for Apache Superset."""

    def __init__(self) -> None:
        port = os.environ.get("SUPERSET_HOST_PORT", "18088")
        default_url = os.environ.get("SUPERSET_URL") or f"http://127.0.0.1:{port}"
        self.superset_url = default_url.rstrip("/")
        self.username = os.environ.get("SUPERSET_ADMIN_USERNAME", "admin")
        self.password = os.environ.get("SUPERSET_ADMIN_PASSWORD", "admin")

    def _get_auth_headers(self) -> Dict[str, str]:
        login_url = f"{self.superset_url}/api/v1/security/login"
        payload = json.dumps({
            "username": self.username,
            "password": self.password,
            "provider": "db",
            "refresh": True,
        }).encode("utf-8")
        req = urllib.request.Request(login_url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                token = data.get("access_token", "")
                return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        except Exception as exc:
            raise RuntimeError("Không đăng nhập được Superset.") from exc

    def list_dashboards(self) -> List[Dict[str, Any]]:
        """List all published dashboards in Superset."""
        try:
            headers = self._get_auth_headers()
            req = urllib.request.Request(f"{self.superset_url}/api/v1/dashboard/?q=(page:0,page_size:50)", headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                results = []
                for item in data.get("result", []):
                    results.append({
                        "id": item.get("id"),
                        "title": item.get("dashboard_title"),
                        "slug": item.get("slug"),
                        "url": f"{self.superset_url}/superset/dashboard/{item.get('slug') or item.get('id')}/",
                        "status": "published" if item.get("published") else "draft",
                    })
                return results
        except Exception as exc:
            raise RuntimeError("Không kết nối được Superset; chưa xác minh dashboard.") from exc

    def query_ai_insights(self, domain: str = "all") -> Dict[str, Any]:
        """Query synthesized AI insights directly from the analytical data mart."""
        try:
            from django.db import connection
            insights = {}
            has_analytics_tables = False
            
            if connection.vendor == "postgresql":
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT count(*) FROM information_schema.tables 
                            WHERE table_schema = 'analytics' AND table_name = 'ai_lead_predictions'
                        """)
                        row = cursor.fetchone()
                        has_analytics_tables = bool(row and row[0] > 0)
                except Exception:
                    has_analytics_tables = False

            if has_analytics_tables:
                with connection.cursor() as cursor:
                    # 1. Lead Scoring Insights
                    if domain in ("all", "leads"):
                        cursor.execute("""
                            SELECT tier, count(*), coalesce(sum(expected_won_value), 0)::numeric
                            FROM analytics.ai_lead_predictions
                            GROUP BY tier
                        """)
                        insights["lead_tiers"] = [
                            {"tier": r[0], "count": r[1], "expected_won_revenue": float(r[2])}
                            for r in cursor.fetchall()
                        ]

                    # 2. Sentiment & Churn Insights
                    if domain in ("all", "sentiment"):
                        cursor.execute("""
                            SELECT churn_risk_level, count(*)
                            FROM analytics.ai_sentiment_churn
                            GROUP BY churn_risk_level
                        """)
                        insights["churn_risk_summary"] = [
                            {"risk_level": r[0], "count": r[1]} for r in cursor.fetchall()
                        ]

                    # 3. Revenue Forecast
                    if domain in ("all", "forecast"):
                        cursor.execute("""
                            SELECT forecast_date, predicted_revenue, trend_direction
                            FROM analytics.ai_revenue_forecast
                            ORDER BY forecast_date
                        """)
                        insights["revenue_forecast"] = [
                            {"month": str(r[0]), "predicted_revenue": float(r[1]), "trend": r[2]}
                            for r in cursor.fetchall()
                        ]

                    # 4. Anomaly Alerts
                    if domain in ("all", "anomalies"):
                        cursor.execute("""
                            SELECT entity_type, severity, description
                            FROM analytics.ai_anomaly_alerts
                            LIMIT 5
                        """)
                        insights["critical_anomalies"] = [
                            {"type": r[0], "severity": r[1], "description": r[2]}
                            for r in cursor.fetchall()
                        ]
            else:
                from crm.analytics.pipeline import AnalyticsPipeline
                pipe = AnalyticsPipeline()
                if domain in ("all", "leads"):
                    leads = pipe.process_lead_predictions()
                    t_counts = {}
                    for l in leads:
                        item = t_counts.setdefault(l["tier"], {"tier": l["tier"], "count": 0, "expected_won_revenue": 0.0})
                        item["count"] += 1
                        item["expected_won_revenue"] += l["expected_won_value"]
                    insights["lead_tiers"] = list(t_counts.values())
                if domain in ("all", "sentiment"):
                    sents = pipe.process_sentiments()
                    r_counts = {}
                    for s in sents:
                        r = s["churn_risk_level"]
                        r_counts[r] = r_counts.get(r, 0) + 1
                    insights["churn_risk_summary"] = [{"risk_level": k, "count": v} for k, v in r_counts.items()]
                if domain in ("all", "forecast"):
                    fc = pipe.process_revenue_forecast()
                    insights["revenue_forecast"] = [{"month": str(x["forecast_date"]), "predicted_revenue": x["predicted_revenue"], "trend": x["trend_direction"]} for x in fc]
                if domain in ("all", "anomalies"):
                    insights["critical_anomalies"] = pipe.process_anomalies()

            return {"status": "SUCCESS", "insights": insights}
        except Exception as exc:
            return {"status": "ERROR", "message": str(exc)}

    def execute_sql(self, sql_query: str) -> Dict[str, Any]:
        """Use the database read-only role, never Django's application credentials."""
        import sqlparse
        from django.conf import settings
        from django.db import connection
        statements = sqlparse.parse(sql_query)
        if len(statements) != 1 or statements[0].get_type() != "SELECT":
            return {"status": "ERROR", "message": "Chỉ cho phép một truy vấn SELECT chỉ đọc."}
        if connection.vendor != "postgresql":
            return {"status": "ERROR", "message": "SQL analytics yêu cầu PostgreSQL và role superset_ro."}
        password = os.environ.get("SUPERSET_READONLY_PASSWORD", "")
        if not password:
            return {"status": "ERROR", "message": "Chưa cấu hình tài khoản analytics chỉ đọc."}
        try:
            import psycopg
            db = settings.DATABASES["default"]
            with psycopg.connect(host=db["HOST"], port=db.get("PORT") or 5432,
                                dbname=db["NAME"], user="superset_ro", password=password,
                                connect_timeout=5) as reader:
                with reader.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SET LOCAL statement_timeout = '5s'")
                    cursor.execute("SET LOCAL search_path = analytics")
                    cursor.execute(sql_query)
                    cols = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchmany(100)
                    return {"status": "SUCCESS", "columns": cols, "rows_count": len(rows),
                            "data": [dict(zip(cols, row)) for row in rows]}
        except Exception as exc:
            return {"status": "ERROR", "message": str(exc)}


def handle_mcp_rpc(request_json: str) -> str:
    """Processes JSON-RPC 2.0 requests for the Superset MCP protocol."""
    server = SupersetMCPServer()
    req_id = None
    try:
        req = json.loads(request_json)
        if not isinstance(req, dict) or req.get("jsonrpc") != "2.0" or not isinstance(req.get("method"), str):
            return json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}})
        req_id = req.get("id", 1)
        method = req.get("method", "")
        params = req.get("params", {})
        if not isinstance(params, dict):
            return json.dumps({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": "Invalid params"}})

        if method == "initialize":
            return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": {
                "protocolVersion": "2025-06-18", "capabilities": {"tools": {}},
                "serverInfo": {"name": "crm-superset", "version": "1.1.0"}}})
        if method.startswith("notifications/"):
            return ""
        if method == "ping":
            return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": {}})
        if method == "tools/list":
            return json.dumps({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": [
                        {"name": "superset_trigger_pipeline", "description": "Làm mới dữ liệu dẫn xuất sau khi nhân viên xác nhận.",
                         "inputSchema": {"type": "object", "required": ["confirm"], "properties": {"confirm": {"type": "boolean", "const": True}}},
                         "annotations": {"readOnlyHint": False}},
                        {
                            "name": "superset_list_dashboards",
                            "description": "Danh sách các dashboard trên Apache Superset.",
                            "inputSchema": {"type": "object", "properties": {}},
                        },
                        {
                            "name": "superset_query_ai_insights",
                            "description": "Truy vấn các kết quả phân tích AI và dự báo.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"domain": {"type": "string", "enum": ["all", "leads", "sentiment", "forecast", "anomalies"]}},
                            },
                        },
                        {
                            "name": "superset_execute_sql",
                            "description": "Thực thi truy vấn SQL phân tích trên schema analytics.",
                            "inputSchema": {
                                "type": "object",
                                "required": ["sql_query"],
                                "properties": {"sql_query": {"type": "string"}},
                            },
                        },
                    ]
                },
            })

        elif method == "tools/call":
            tool_name = params.get("name", "")
            args = params.get("arguments", {})
            if not isinstance(args, dict):
                return json.dumps({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": "Invalid arguments"}})

            if tool_name == "superset_trigger_pipeline":
                if args.get("confirm") is not True:
                    res = {"status": "ERROR", "message": "Cần nhân viên xác nhận confirm=true trước khi làm mới dữ liệu."}
                else:
                    from crm.analytics.pipeline import AnalyticsPipeline
                    res = AnalyticsPipeline().run_all()
            elif tool_name == "superset_list_dashboards":
                res = server.list_dashboards()
            elif tool_name == "superset_query_ai_insights":
                res = server.query_ai_insights(domain=args.get("domain", "all"))
            elif tool_name == "superset_execute_sql":
                res = server.execute_sql(args.get("sql_query", ""))
            else:
                return json.dumps({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Tool '{tool_name}' not found"},
                })

            return json.dumps({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(res, ensure_ascii=False, default=str)}],
                           "isError": isinstance(res, dict) and res.get("status") == "ERROR"},
            })

        return json.dumps({
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": "Method not supported"},
        })

    except json.JSONDecodeError:
        return json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}})
    except Exception as e:
        return json.dumps({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": str(e)}})


if __name__ == "__main__":
    # Test execution or Stdio mode
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        s = SupersetMCPServer()
        print("Dashboards:", s.list_dashboards())
        print("AI Insights:", s.query_ai_insights())
    else:
        # Standard MCP Stdio Loop
        for line in sys.stdin:
            if line.strip():
                response = handle_mcp_rpc(line)
                if response:
                    print(response)
                    sys.stdout.flush()
