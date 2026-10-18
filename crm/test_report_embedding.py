from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from crm.services.report_insights import report_insights
from crm.services.superset_embed import guest_session


class ReportInsightTests(SimpleTestCase):
    def test_empty_data_does_not_invent_revenue_or_customer_satisfaction(self):
        text = " ".join(item["text"] for item in report_insights({}))
        self.assertIn("Chưa đủ lịch sử", text)
        self.assertIn("Không xem thiếu dữ liệu", text)
        self.assertNotIn("nan", text)
        self.assertEqual(len(report_insights({})), 6)

    def test_commentary_uses_counts_correct_units_and_forecast_direction(self):
        rows = report_insights({
            "lead_tiers": [{"tier": "HOT", "count": 2}, {"tier": "WARM", "count": 3}],
            "sentiment": [{"label": "NEGATIVE", "count": 3}],
            "churn_risk": [{"level": "HIGH", "count": 2}],
            "forecast": [
                {"date": "2026-12-01", "predicted": 0, "trend": "Baseline"},
                {"date": "2026-11-01", "predicted": 1000000, "trend": "Baseline"},
            ],
        })
        self.assertIn("2/5", rows[0]["text"])
        self.assertIn("40%", rows[0]["text"])
        self.assertIn("giảm", rows[2]["text"])
        self.assertIn("1.000.000 VNĐ đến 0 VNĐ", rows[2]["text"])
        self.assertIn("3/3 lượt tương tác", rows[3]["text"])
        self.assertIn("cùng một khách hàng", rows[3]["text"])

    @patch("crm.services.superset_embed.superset_api")
    def test_token_is_scoped_to_fixed_dashboard_without_contact_information(self, factory):
        api = factory.return_value
        api._request.side_effect = [{"result": {"id": 4}}, {"result": {"uuid": "fixed-uuid"}}, {"token": "short-token"}]
        from types import SimpleNamespace
        result = guest_session(SimpleNamespace(pk=9, email="private@example.test"))
        self.assertEqual(result, {"id": "fixed-uuid", "token": "short-token"})
        payload = api._request.call_args.args[2]
        self.assertEqual(payload["resources"], [{"type": "dashboard", "id": "fixed-uuid"}])
        self.assertNotIn("private@example.test", str(payload))

    @patch.dict("os.environ", {"SUPERSET_EMBED_ALLOWED_ORIGINS": "*"})
    @patch("crm.management.commands.setup_superset_embedding.superset_api")
    def test_embedding_setup_refuses_wildcard_origin(self, factory):
        with self.assertRaises(CommandError):
            call_command("setup_superset_embedding", stdout=StringIO())
        factory.assert_not_called()


class ReportEmbeddingPermissionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="report-reader", password="isolated-test-password")
        self.url = reverse("crm:superset_guest_session")

    @patch("crm.services.superset_embed.guest_session")
    def test_anonymous_and_users_without_crm_permission_cannot_obtain_tokens(self, mint):
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        mint.assert_not_called()

    def grant_access(self):
        self.user.user_permissions.add(Permission.objects.get(codename="access_crm"))
        self.client.force_login(self.user)

    @patch("crm.services.superset_embed.guest_session", return_value={"id": "fixed", "token": "short-lived"})
    def test_authorized_token_is_not_cached_and_client_cannot_choose_resource(self, mint):
        self.grant_access()
        response = self.client.get(self.url, {"dashboard_id": "unrelated", "rls": "1=1"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], "fixed")
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.assertEqual(len(mint.call_args.args), 1)
        self.assertEqual(mint.call_args.args[0].pk, self.user.pk)
        self.assertEqual(self.client.post(self.url).status_code, 405)

    @patch("crm.services.superset_embed.guest_session", side_effect=RuntimeError("sensitive upstream details"))
    def test_outage_returns_safe_message_and_local_analysis_remains_available(self, mint):
        self.grant_access()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 503)
        self.assertNotContains(response, "sensitive", status_code=503)
        self.assertIn("no-store", response.headers["Cache-Control"])
        report = self.client.get(reverse("crm:report"))
        self.assertContains(report, "Phân tích biểu đồ và gợi ý chăm sóc")
        self.assertContains(report, "superset-embedded-sdk.js")
        self.assertNotContains(report, "supersetLiveFrame")
