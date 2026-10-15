"""Regression coverage for correctness, consent, malformed requests and MCP interoperability."""

import json
from datetime import date, timedelta
from decimal import Decimal
from io import StringIO
from unittest.mock import patch
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.db import connection

from crm.analytics.ai_engine import RevenueForecastingEngine, SentimentChurnEngine
from crm.analytics.evaluation import evaluate_quality
from crm.analytics.pipeline import AnalyticsPipeline
from crm.models import AIAnalysis, Customer, Interaction, LeadRequest, SalesRecord
from crm.services.ai_chat_service import answer_customer_question
from crm.services.ai_service import analyze_customer
from superset.mcp_server import SupersetMCPServer, handle_mcp_rpc


@override_settings(GEMINI_API_KEY="")
class QualityRegressionTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(full_name="Hồ sơ kiểm thử", email="quality@example.test", ai_score=90)

    def test_forecast_uses_amounts_excludes_void_and_fills_missing_months(self):
        for reference, month, amount, status in [
            ("A", 11, 100_000_000, "WON"), ("B", 1, 300_000_000, "WON"), ("C", 1, 900_000_000, "VOID"),
        ]:
            SalesRecord.objects.create(customer=self.customer, reference=reference, closed_at=date(2025 if month == 11 else 2026, month, 1), amount=amount, status=status)
        pipe = AnalyticsPipeline()
        self.assertEqual(pipe.revenue_history(), [(date(2025, 11, 1), 100_000_000), (date(2025, 12, 1), 0), (date(2026, 1, 1), 300_000_000)])
        before = pipe.process_revenue_forecast()
        self.assertEqual(before[0]["forecast_date"], date(2026, 2, 1))
        SalesRecord.objects.filter(reference="B").update(amount=600_000_000)
        self.assertGreater(pipe.process_revenue_forecast()[0]["predicted_revenue"], before[0]["predicted_revenue"])

    def test_forecast_refuses_to_invent_history(self):
        engine = RevenueForecastingEngine()
        self.assertEqual(engine.forecast_next_months([]), [])
        self.assertEqual(engine.forecast_next_months([(date(2026, 1, 1), 0)]), [])
        points = engine.forecast_next_months([(date(2026, i, 1), 0) for i in range(1, 4)])
        self.assertTrue(all(x.predicted_revenue == 0 for x in points))

    def test_sentiment_handles_negation_and_word_boundaries(self):
        engine = SentimentChurnEngine()
        for text, expected in [("không hài lòng", "NEGATIVE"), ("không tốt", "NEGATIVE"),
                               ("không còn lỗi", "POSITIVE"), ("đăng ký lịch khảo sát", "NEUTRAL")]:
            with self.subTest(text=text):
                self.assertEqual(engine.analyze(1, text).sentiment_label, expected)

    def test_pipeline_excludes_unconsented_and_completed_leads(self):
        denied = LeadRequest.objects.create(customer=self.customer, request_text="Nội dung không đồng ý AI")
        done = LeadRequest.objects.create(customer=self.customer, request_text="Đã xử lý CRM", ai_processing_consent=True, status="COMPLETED")
        self.assertEqual(AnalyticsPipeline().process_lead_predictions(), [])
        self.assertEqual(AnalyticsPipeline().process_anomalies(), [])

    def test_new_contact_prevents_false_stalled_alert(self):
        lead = LeadRequest.objects.create(customer=self.customer, request_text="CRM", ai_processing_consent=True)
        LeadRequest.objects.filter(pk=lead.pk).update(created_at=timezone.now()-timedelta(days=30))
        Interaction.objects.create(customer=self.customer, subject="Liên hệ hôm nay", content="Đã gọi", ai_processing_consent=True)
        self.assertEqual(AnalyticsPipeline().process_anomalies(), [])

    def test_task_completion_timestamp_is_consistent_for_admin_and_frontend(self):
        from crm.models import CareTask
        task = CareTask.objects.create(customer=self.customer, title="Hoàn tất qua admin", due_at=timezone.localdate(), status="DONE")
        self.assertIsNotNone(task.completed_at)
        task.status = "IN_PROGRESS"
        task.save(update_fields=["status"])
        task.refresh_from_db()
        self.assertIsNone(task.completed_at)

    def test_pipeline_does_not_analyze_legacy_or_denied_public_chats(self):
        LeadRequest.objects.create(customer=self.customer, request_text="CRM", ai_processing_consent=True)
        for consent in (None, False, True):
            Interaction.objects.create(customer=self.customer, subject="Chat", content="không hài lòng", ai_processing_consent=consent)
        self.assertEqual(len(AnalyticsPipeline().process_sentiments()), 1)

    @override_settings(GEMINI_API_KEY="configured")
    @patch("crm.services.ai_service._request_gemini")
    def test_mixed_consent_chat_never_leaks_into_gemini(self, request):
        lead = LeadRequest.objects.create(customer=self.customer, request_text="CRM cho đội sales", ai_processing_consent=True)
        Interaction.objects.create(customer=self.customer, subject="Lịch sử trao đổi cùng Trợ lý AI", content="DENIED_PRIVATE_CHAT", ai_processing_consent=False)
        Interaction.objects.create(customer=self.customer, subject="Lịch sử trao đổi cùng Trợ lý AI", content="LEGACY_PRIVATE_CHAT")
        Interaction.objects.create(customer=self.customer, subject="Lịch sử trao đổi cùng Trợ lý AI", content="ALLOWED_CONTEXT", ai_processing_consent=True)
        request.return_value = json.dumps({"segment":"POTENTIAL", "score":70, "summary":"Nhu cầu CRM", "recommendation":"Khảo sát nhu cầu"})
        analyze_customer(self.customer, permitted_requests=[lead])
        prompt = request.call_args.args[0]
        self.assertIn("ALLOWED_CONTEXT", prompt)
        self.assertNotIn("DENIED_PRIVATE_CHAT", prompt)
        self.assertNotIn("LEGACY_PRIVATE_CHAT", prompt)

    @override_settings(GEMINI_API_KEY="configured")
    @patch("crm.services.ai_service._request_gemini")
    def test_malformed_gemini_results_fall_back(self, request):
        for value in ["[]", "null", "not json", '{"segment":"VIP","score":true}',
                      '{"segment":"VIP","score":90,"summary":null,"recommendation":""}']:
            with self.subTest(value=value):
                request.return_value = value
                self.assertEqual(analyze_customer(self.customer)["provider"], "rules")

    def test_risk_precedes_vip_and_postponed_demand_is_not_hot(self):
        self.customer.total_spent = Decimal("100000000")
        self.customer.save()
        Interaction.objects.create(customer=self.customer, subject="Hỗ trợ", content="không hài lòng và muốn hủy hợp đồng")
        self.assertEqual(analyze_customer(self.customer)["segment"], "CHURN_RISK")
        self.customer.interactions.all().delete()
        Interaction.objects.create(customer=self.customer, subject="CRM", content="Tạm dừng vì chưa có ngân sách, quý sau liên hệ lại")
        self.assertEqual(analyze_customer(self.customer)["segment"], "HIBERNATING")

    def test_chat_invalid_json_shapes_and_message_types_return_400(self):
        for payload in (None, [], "text", 5, {"message": None}, {"message": 12}, {"message": "x"*1001}):
            with self.subTest(payload=payload):
                response = self.client.post(reverse("crm:ai_chat_consultant"), data=json.dumps(payload), content_type="application/json")
                self.assertEqual(response.status_code, 400)

    def test_chat_ignores_bad_history_entries_and_keeps_context(self):
        response = self.client.post(reverse("crm:ai_chat_consultant"), data=json.dumps({
            "message": "Chi phí bao nhiêu?", "history": [None, 2, {"role": [], "content":"bad"}, {"role":"user", "content":"3 kho và 2 POS"}]}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["suggested_solution"], "ERP")
        self.assertIn("khảo sát", response.json()["reply"])

    def test_ai_substring_in_vietnamese_is_not_an_ai_intent(self):
        self.assertEqual(answer_customer_question("Xin liên hệ lại vào ngày mai")["suggested_solution"], "OTHER")

    @override_settings(GEMINI_API_KEY="configured")
    @patch("crm.services.ai_chat_service._call_gemini_chat", side_effect=TimeoutError)
    def test_chat_timeout_falls_back_with_context(self, request):
        result = answer_customer_question("Thời gian bao lâu?", [{"role":"user", "content":"CRM cho 12 sales"}])
        self.assertEqual(result["provider"], "rules")
        self.assertEqual(result["suggested_solution"], "CRM")
        self.assertNotIn("2 đến 4 tuần", result["reply"])

    def test_sync_is_post_only_and_requires_analysis_permission(self):
        user = get_user_model().objects.create_user("viewer")
        user.user_permissions.add(Permission.objects.get(codename="access_crm"))
        self.client.force_login(user)
        url = reverse("crm:sync_ai_analytics")
        self.assertEqual(self.client.post(url).status_code, 403)
        user.user_permissions.add(Permission.objects.get(codename="analyze_customer"))
        self.assertEqual(self.client.get(url).status_code, 405)
        with patch.object(AnalyticsPipeline, "run_all", return_value={"leads_analyzed":1,"sentiments_analyzed":2,"forecast_months":0}) as run:
            self.assertEqual(self.client.post(url).status_code, 302)
            run.assert_called_once()

    def test_empty_report_has_no_fabricated_chart_data(self):
        user = get_user_model().objects.create_superuser("report", password="test-only")
        self.client.force_login(user)
        response = self.client.get(reverse("crm:report"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["chart_data"]["lead_tiers"], [])
        self.assertEqual(response.context["chart_data"]["forecast"], [])
        self.assertNotContains(response, "815940000")
        self.assertNotContains(response, "0.582")

    def test_scenario_seed_is_idempotent_and_never_analyzes_denied_lead(self):
        for _ in range(2):
            call_command("seed_consultation_scenarios", "--analyze", "--rules-only", stdout=StringIO())
        self.assertEqual(Customer.objects.filter(source="Tình huống tư vấn minh họa").count(), 8)
        self.assertEqual(AIAnalysis.objects.count(), 7)
        self.assertFalse(AIAnalysis.objects.filter(customer__email="scenario.no-consent@consultation.test").exists())

    def test_evaluation_computes_metrics_and_reports_limits(self):
        report = evaluate_quality()
        self.assertEqual(report["sentiment"]["sample_size"], 20)
        self.assertEqual(report["revenue_backtest"]["sample_size"], 0)
        self.assertIsNone(report["revenue_backtest"]["mae"])
        self.assertIn("không suy rộng", report["limitations"])

    def test_mcp_initialization_notifications_ping_and_missing_confirmation(self):
        def rpc(method, params=None):
            return handle_mcp_rpc(json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params or {}}))
        self.assertIn("serverInfo", json.loads(rpc("initialize"))["result"])
        self.assertEqual(rpc("notifications/initialized"), "")
        self.assertEqual(json.loads(rpc("ping"))["result"], {})
        res = json.loads(rpc("tools/call", {"name":"superset_trigger_pipeline"}))["result"]
        self.assertIn("ERROR", res["content"][0]["text"])

    @patch("urllib.request.urlopen", side_effect=ConnectionError)
    def test_offline_superset_is_not_reported_as_published(self, request):
        with self.assertRaises(RuntimeError):
            SupersetMCPServer().list_dashboards()
        result = json.loads(handle_mcp_rpc(json.dumps({"jsonrpc":"2.0", "id":77,
            "method":"tools/call", "params":{"name":"superset_list_dashboards"}})))
        self.assertEqual(result["id"], 77)
        self.assertIn("error", result)

    def test_mcp_sql_rejects_multiple_or_write_statements(self):
        server = SupersetMCPServer()
        for sql in ("DELETE FROM analytics.ai_lead_predictions", "SELECT 1; SELECT 2", ""):
            self.assertEqual(server.execute_sql(sql)["status"], "ERROR")

@skipUnless(connection.vendor == "postgresql", "Requires the PostgreSQL reader role")
class PostgreSQLReaderRoleTests(TransactionTestCase):
    def test_mcp_reader_role_can_read_analytics_but_not_raw_customer_data(self):
        AnalyticsPipeline().run_all()
        server = SupersetMCPServer()
        self.assertEqual(server.execute_sql("SELECT count(*) FROM analytics.ai_lead_predictions")["status"], "SUCCESS")
        self.assertEqual(server.execute_sql("SELECT current_user AS role")["data"][0]["role"], "superset_ro")
        self.assertEqual(server.execute_sql("SELECT count(*) FROM public.crm_customer")["status"], "ERROR")
