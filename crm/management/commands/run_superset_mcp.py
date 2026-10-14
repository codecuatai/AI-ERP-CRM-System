"""Django management command to execute or test the Apache Superset MCP Server."""

import json
import sys
from django.core.management.base import BaseCommand
from superset.mcp_server import SupersetMCPServer, handle_mcp_rpc

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


class Command(BaseCommand):
    help = "Chạy kiểm thử hoặc khởi động Apache Superset MCP (Model Context Protocol) Server."

    def add_arguments(self, parser):
        parser.add_argument(
            "--test",
            action="store_true",
            help="Chạy kiểm thử các tools của Superset MCP Server và in kết quả.",
        )

    def handle(self, *args, **options):
        server = SupersetMCPServer()

        if options.get("test"):
            self.stdout.write("==> Đang kiểm thử Apache Superset MCP Server Tools...")
            
            dashboards = server.list_dashboards()
            self.stdout.write(self.style.SUCCESS(f"✔ [Tool: superset_list_dashboards]: Tìm thấy {len(dashboards)} dashboards:"))
            for d in dashboards:
                self.stdout.write(f"   - {d['title']} ({d['url']})")

            insights = server.query_ai_insights()
            self.stdout.write(self.style.SUCCESS(f"✔ [Tool: superset_query_ai_insights]: Trích xuất insights AI thành công:"))
            self.stdout.write(json.dumps(insights, indent=2, ensure_ascii=False, default=str))

            test_sql = "SELECT tier, count(*) as count FROM analytics.ai_lead_predictions GROUP BY tier"
            sql_res = server.execute_sql(test_sql)
            self.stdout.write(self.style.SUCCESS(f"✔ [Tool: superset_execute_sql]: Chạy query thành công:"))
            self.stdout.write(json.dumps(sql_res, indent=2, ensure_ascii=False, default=str))

            # Test JSON-RPC MCP request
            rpc_req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
            rpc_res = handle_mcp_rpc(rpc_req)
            self.stdout.write(self.style.SUCCESS(f"✔ [JSON-RPC Protocol: tools/list]: Phản hồi chuẩn MCP thành công."))
            return

        self.stdout.write("Khởi động Superset MCP Server ở chế độ Stdio...")
        import sys
        for line in sys.stdin:
            if line.strip():
                self.stdout.write(handle_mcp_rpc(line))
                self.stdout.flush()
