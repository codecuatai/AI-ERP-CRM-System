"""Regression checks for MCP authoring and the conservative forecast policy."""

import json
from datetime import date
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from crm.analytics.ai_engine import LeadWinRateModel, RevenueForecastingEngine, SentimentChurnEngine
from crm.services.ai_chat_service import answer_customer_question
from crm.services.consultation import customer_chat_text
from superset.authoring import SupersetAuthoring
from superset.mcp_server import handle_mcp_rpc


class ForecastPolicyTests(SimpleTestCase):
    def test_assistant_suggestions_do_not_become_customer_statements(self):
        text = ("Khách hàng: Cần tư vấn CRM.\nCho đội 12 sales.\n"
                "DigiFlow AI: Nếu mất dữ liệu hay muốn hủy hợp đồng cần báo nhân viên.\n"
                "Khách hàng: Xin demo trước.")
        extracted = customer_chat_text(text)
        self.assertIn("12 sales", extracted)
        self.assertNotIn("hủy", extracted)
        self.assertEqual(SentimentChurnEngine().analyze(1, extracted).sentiment_label, "NEUTRAL")

    def test_missing_response_measurement_does_not_invent_fast_response(self):
        model = LeadWinRateModel()
        kwargs = {"lead_id": 1, "solution_interest": "CRM", "priority_score": 60,
                  "interaction_count": 1, "has_phone": True, "has_company": True, "request_text_length": 50}
        unknown = model.predict(**kwargs)
        measured = model.predict(**kwargs, response_time_hours=2)
        self.assertLess(unknown.win_probability, measured.win_probability)
        self.assertFalse(any("<4h" in reason for reason in unknown.key_drivers))
        self.assertTrue(any("<4h" in reason for reason in measured.key_drivers))

    def test_short_histories_use_baseline_instead_of_unvalidated_trend(self):
        engine = RevenueForecastingEngine()
        history = [(date(2026, month, 1), month * 1000) for month in range(1, 13)]
        points = engine.forecast_next_months(history)
        self.assertEqual({point.model_name for point in points}, {"NAIVE"})
        self.assertEqual([point.predicted_revenue for point in points], [12000] * 4)
        self.assertEqual(points[0].forecast_date, date(2027, 1, 1))

    def test_consistent_long_trend_must_beat_baseline_on_past_folds(self):
        engine = RevenueForecastingEngine()
        values = [1000 * month for month in range(1, 25)]
        selected = engine.select_model(values)
        self.assertEqual(selected["model"], "LINEAR")
        self.assertLess(selected["mae"]["LINEAR"], selected["mae"]["NAIVE"])
        history = [(date(2024 + i // 12, i % 12 + 1, 1), value) for i, value in enumerate(values)]
        self.assertEqual(engine.forecast_next_months(history)[0].predicted_revenue, 25000)

    def test_constant_history_keeps_baseline_and_has_nonnegative_bands(self):
        engine = RevenueForecastingEngine()
        self.assertEqual(engine.select_model([0] * 30)["model"], "NAIVE")
        for point in engine.forecast_next_months([(date(2026, i, 1), 0) for i in range(1, 4)]):
            self.assertEqual(point.predicted_revenue, 0)
            self.assertGreaterEqual(point.lower_bound_95, 0)
            self.assertGreaterEqual(point.upper_bound_95, point.predicted_revenue)

    def test_rhetorical_denials_do_not_count_as_satisfied_customers(self):
        engine = SentimentChurnEngine()
        for text in ("Hài lòng gì mà ngày nào cũng lỗi.", "Tốt gì mà hệ thống chậm liên tục.", "Phần mềm tốt đâu."):
            with self.subTest(text=text):
                self.assertEqual(engine.analyze(1, text).sentiment_label, "NEGATIVE")

    @override_settings(GEMINI_API_KEY="configured")
    @patch("crm.services.ai_chat_service._call_gemini_chat")
    def test_unverified_commercial_questions_never_reach_generative_model(self, model):
        for text in ("Chi phí bao nhiêu?", "Thời gian triển khai bao lâu?", "Báo giá CRM cho tôi"):
            with self.subTest(text=text):
                response = answer_customer_question(text, [{"role": "user", "content": "CRM cho 12 sales"}])
                self.assertEqual(response["provider"], "rules")
                self.assertEqual(response["suggested_solution"], "CRM")
                self.assertIn("khảo sát", response["reply"])
        model.assert_not_called()
        model.return_value = "Cần đánh giá AI trên bộ dữ liệu độc lập và đo mức sửa bản nháp."
        result = answer_customer_question("Đánh giá AI và giá trị dữ liệu như thế nào?")
        self.assertEqual(result["provider"], "gemini")
        model.assert_called_once()


class MCPAuthoringTests(SimpleTestCase):
    def setUp(self):
        patcher = patch("superset.authoring.SupersetApi")
        self.factory = patcher.start()
        self.addCleanup(patcher.stop)
        self.api = self.factory.return_value
        self.api.base_url = "http://superset.test"
        self.datasets = [{"id": 9, "schema": "analytics", "table_name": "ai_lead_predictions",
                          "database": {"database_name": "CRM Analytics"}},
                         {"id": 99, "schema": "public", "table_name": "crm_customer", "database": {"database_name": "CRM Analytics"}},
                         {"id": 100, "schema": "analytics", "table_name": "ai_lead_predictions", "database": {"database_name": "Other database"}}]
        self.charts, self.dashboards = [], []
        self.api.list.side_effect = lambda resource: {"dataset": self.datasets, "chart": self.charts, "dashboard": self.dashboards}[resource]
        self.dataset_detail = {"columns": [{"column_name": "tier", "type": "VARCHAR"},
                                            {"column_name": "expected_won_value", "type": "NUMERIC"}]}
        self.author = SupersetAuthoring("http://superset.test", "test-user", "test-only")
        self.api._request.side_effect = self.request

    def request(self, path, method="GET", payload=None):
        if path == "/api/v1/dataset/9":
            return {"result": self.dataset_detail}
        if path == "/api/v1/chart/" and method == "POST":
            return {"id": 51}
        if path == "/api/v1/dashboard/" and method == "POST":
            return {"id": 7}
        if path.startswith("/api/v1/chart/"):
            return {"result": {"datasource_id": 9, "datasource_type": "table", "dashboards": [{"id": 1}, {"id": 2}],
                               "uuid": "example-chart", "slice_name": "Chart"}}
        return {"result": {}}

    def writes(self):
        return [call for call in self.api._request.call_args_list if len(call.args) > 1 and call.args[1] != "GET"]

    def test_discovery_only_returns_managed_dataset_metadata(self):
        data = self.author.list_datasets(include_columns=True)
        self.assertEqual([item["id"] for item in data], [9])
        self.assertEqual(data[0]["columns"][1]["name"], "expected_won_value")
        self.assertNotIn("database", data[0])

    def test_creates_real_superset_payload_with_validated_metric(self):
        result = self.author.create_chart("Ưu tiên bán hàng", 9, "pie", "tier", "sum", "expected_won_value")
        self.assertEqual(result["id"], 51)
        payload = self.writes()[0].args[2]
        self.assertEqual(payload["datasource_id"], 9)
        self.assertEqual(json.loads(payload["params"])["metric"]["aggregate"], "SUM")
        self.assertNotIn("metrics", json.loads(payload["params"]))

    def test_rejects_unmanaged_datasets_bad_columns_and_arbitrary_sql_without_writes(self):
        for args in ({"dataset_id": 99}, {"dataset_id": True}, {"kind": "invalid"}, {"group_by": "unknown"},
                     {"metric": "sum", "metric_column": "tier"}, {"metric": "sum", "metric_column": "amount); DROP TABLE x"}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                self.author.create_chart(**({"title": "Test", "dataset_id": 9, "kind": "bar", "group_by": "tier"} | args))
        self.assertEqual(self.writes(), [])

    def test_existing_chart_is_reused_but_never_silently_overwritten(self):
        self.author.create_chart("Test", 9, "pie", "tier")
        payload = self.writes()[0].args[2]
        self.charts.append({"id": 51, "slice_name": "Test"})
        self.api._request.side_effect = lambda path, *args: {"result": self.dataset_detail if path.startswith("/api/v1/dataset/") else payload}
        self.api._request.reset_mock()
        self.assertFalse(self.author.create_chart("Test", 9, "pie", "tier")["created"])
        with self.assertRaises(ValueError):
            self.author.create_chart("Test", 9, "bar", "tier")
        self.assertEqual(self.writes(), [])
        self.assertTrue(self.author.create_chart("Test", 9, "bar", "tier", replace_existing=True)["updated"])
        payload["description"] = "Biểu đồ người dùng tạo thủ công"
        with self.assertRaises(ValueError):
            self.author.create_chart("Test", 9, "bar", "tier", replace_existing=True)

    def test_dashboard_memberships_are_preserved_and_publishing_is_explicit(self):
        result = self.author.create_dashboard("Tư vấn B2B", "crm-mcp-consultations", [51, 52])
        self.assertFalse(result["published"])
        self.assertFalse(next(call.args[2] for call in self.writes() if call.args[0] == "/api/v1/dashboard/")["published"])
        for call in self.writes():
            if call.args[1] == "PUT":
                self.assertEqual(call.args[2]["dashboards"], [1, 2, 7])

    def test_dashboard_rejects_invalid_ids_slug_duplicates_and_publishing_type(self):
        for args in ({"chart_ids": [True]}, {"chart_ids": [51, 51]}, {"slug": "crm-analytics-dashboard"},
                     {"chart_ids": []}, {"published": "true"}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                self.author.create_dashboard(**({"title": "Test", "slug": "crm-mcp-test", "chart_ids": [51]} | args))
        self.assertEqual(self.writes(), [])

    @patch("superset.mcp_server.SupersetMCPServer.authoring")
    def test_rpc_requires_confirmation_before_authentication_or_mutation(self, author):
        for name in ("superset_create_chart", "superset_create_dashboard"):
            response = json.loads(handle_mcp_rpc(json.dumps({"jsonrpc": "2.0", "id": 12, "method": "tools/call", "params": {"name": name, "arguments": {"confirm": False}}})))
            self.assertTrue(response["result"]["isError"])
        author.assert_not_called()

    @patch("superset.mcp_server.SupersetMCPServer.authoring")
    def test_rpc_routes_confirmed_creation_and_reports_service_errors(self, factory):
        factory.return_value.create_chart.return_value = {"status": "SUCCESS", "id": 51}
        request = {"jsonrpc": "2.0", "id": 13, "method": "tools/call", "params": {"name": "superset_create_chart", "arguments": {"confirm": True, "title": "Test", "dataset_id": 9, "kind": "number"}}}
        response = json.loads(handle_mcp_rpc(json.dumps(request)))
        self.assertFalse(response["result"]["isError"])
        factory.return_value.create_chart.assert_called_once_with(title="Test", dataset_id=9, kind="number")
        factory.return_value.create_chart.side_effect = RuntimeError("Superset offline")
        self.assertTrue(json.loads(handle_mcp_rpc(json.dumps(request)))["result"]["isError"])
