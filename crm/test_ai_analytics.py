"""Unit and integration tests for the AI Analytics Engine and Superset MCP Server."""

from decimal import Decimal
import json
from datetime import date
from unittest.mock import patch
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from crm.analytics.ai_engine import (
    AnomalyDetectionEngine,
    ExplainableAIEngine,
    LeadWinRateModel,
    RevenueForecastingEngine,
    RFMSegmentationModel,
    SentimentChurnEngine,
)
from crm.analytics.pipeline import AnalyticsPipeline
from crm.models import Customer, LeadRequest, Interaction, SalesRecord
from superset.mcp_server import SupersetMCPServer, handle_mcp_rpc


class AIAnalyticsEngineTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            full_name="Công ty TNHH Giải Pháp Việt",
            email="contact@giaiphapviet.test",
            phone="0987654321",
            company="Giải Pháp Việt",
            total_spent=Decimal("50000000"),
            ai_score=85,
        )
        self.lead = LeadRequest.objects.create(
            customer=self.customer,
            solution_interest="CRM",
            request_text="Cần tư vấn triển khai gấp hệ thống CRM cho 20 nhân sự bán hàng",
            status="NEW",
            ai_processing_consent=True,
        )
        self.interaction = Interaction.objects.create(
            customer=self.customer,
            subject="Demo giải pháp",
            ai_processing_consent=True,
            content="Khách hàng rất hài lòng về bản demo, đồng ý thảo luận hợp đồng sớm",
        )

    def test_lead_win_rate_model(self):
        model = LeadWinRateModel()
        res = model.predict(
            lead_id=self.lead.id,
            solution_interest="CRM",
            priority_score=85,
            interaction_count=3,
            has_phone=True,
            has_company=True,
            request_text_length=60,
            response_time_hours=1.5,
        )
        self.assertGreaterEqual(res.win_probability, 0.50)
        self.assertIn(res.tier, ["HOT", "WARM"])
        self.assertGreater(res.expected_won_value, 0)
        self.assertTrue(len(res.key_drivers) > 0)

    def test_sentiment_churn_engine_positive(self):
        engine = SentimentChurnEngine()
        res = engine.analyze(
            interaction_id=1,
            content="Khách hàng rất hài lòng và đồng ý ký hợp đồng nhanh chóng",
            days_since_last_contact=2,
            unresolved_tasks_count=0,
        )
        self.assertEqual(res.sentiment_label, "POSITIVE")
        self.assertGreater(res.sentiment_score, 0.0)
        self.assertEqual(res.churn_risk_level, "LOW")

    def test_sentiment_churn_engine_negative_and_churn(self):
        engine = SentimentChurnEngine()
        res = engine.analyze(
            interaction_id=2,
            content="Hệ thống bị lỗi chậm và phức tạp, chúng tôi rất thất vọng và muốn hoãn",
            days_since_last_contact=45,
            unresolved_tasks_count=3,
        )
        self.assertEqual(res.sentiment_label, "NEGATIVE")
        self.assertLess(res.sentiment_score, 0.0)
        self.assertEqual(res.churn_risk_level, "HIGH")

    def test_rfm_segmentation_model(self):
        model = RFMSegmentationModel()
        # VIP point: recent, high frequency, high spend
        vip_res = model.segment(customer_id=1, recency_days=5, frequency=15, monetary_amount=250_000_000.0)
        self.assertEqual(vip_res.cluster_id, 0)
        self.assertIn("VIP", vip_res.cluster_name)

        # Dormant point: long ago, zero frequency, zero spend
        dormant_res = model.segment(customer_id=2, recency_days=170, frequency=0, monetary_amount=0.0)
        self.assertEqual(dormant_res.cluster_id, 3)
        self.assertIn("đóng băng", dormant_res.cluster_name)

    def test_revenue_forecasting_engine(self):
        engine = RevenueForecastingEngine()
        forecasts = engine.forecast_next_months([(date(2026, i, 1), i * 10000000) for i in range(1, 4)], months_ahead=3)
        self.assertEqual(len(forecasts), 3)
        for f in forecasts:
            self.assertGreater(f.predicted_revenue, 0)
            self.assertGreaterEqual(f.upper_bound_95, f.predicted_revenue)
            self.assertLessEqual(f.lower_bound_95, f.predicted_revenue)

    def test_explainable_ai_engine(self):
        xai = ExplainableAIEngine()
        explanations = xai.explain_lead_scoring(
            priority_score=90,
            interaction_count=4,
            solution_interest="ERP",
            has_verified_contact=True,
        )
        self.assertEqual(len(explanations), 4)
        for exp in explanations:
            self.assertIn("feature", exp)
            self.assertIn("impact_percentage", exp)

    def test_anomaly_detection_engine(self):
        engine = AnomalyDetectionEngine()
        # Stalled high-priority lead
        alert = engine.detect_lead_anomalies(
            lead_id=10,
            lead_name="VIP Lead",
            priority_score=92,
            days_stalled=7,
            status="NEW",
        )
        self.assertIsNotNone(alert)
        self.assertEqual(alert.severity, "HIGH")

    def test_analytics_pipeline_execution(self):
        pipeline = AnalyticsPipeline()
        summary = pipeline.run_all()
        self.assertEqual(summary["status"], "SUCCESS")
        self.assertGreaterEqual(summary["leads_analyzed"], 1)
        self.assertGreaterEqual(summary["customers_segmented"], 1)

    def test_run_ai_analytics_command(self):
        output = StringIO()
        call_command("run_ai_analytics", "--evaluate", stdout=output)
        self.assertIn('"sample_size": 20', output.getvalue())
        self.assertNotIn("Accuracy:  0.884", output.getvalue())

    @patch.object(SupersetMCPServer, "list_dashboards", return_value=[{"id": 1}])
    def test_superset_mcp_server(self, dashboards_mock):
        server = SupersetMCPServer()
        dashboards = server.list_dashboards()
        self.assertGreaterEqual(len(dashboards), 1)

        insights = server.query_ai_insights()
        self.assertEqual(insights["status"], "SUCCESS")

        rpc_res = json.loads(handle_mcp_rpc(json.dumps({
            "jsonrpc": "2.0", "id": 1, "method": "tools/list"
        })))
        tools = rpc_res["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        self.assertIn("superset_list_dashboards", tool_names)
        self.assertIn("superset_query_ai_insights", tool_names)
        self.assertIn("superset_execute_sql", tool_names)
