"""Explicit re-test suite for OPEN bugs; intentionally fails until member 2 fixes them.

Run: python manage.py test crm.qa_known_bugs --verbosity=2
This module is separate from test*.py discovery; see docs/qa/bug-tracker.md.
After a fix, move its passing test into the regular regression suite.
"""

import csv
from io import StringIO

from bs4 import BeautifulSoup
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from crm.models import Customer, Interaction, LeadFollowUp, LeadRequest


@override_settings(
    GEMINI_API_KEY="", EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    PUBLIC_SITE_URL="https://crm.example.test",
)
class KnownBugReTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser(username="qa-retest", email="qa@example.test")
        cls.customer = Customer.objects.create(full_name="QA B2B", email="retest@example.test")

    def setUp(self):
        self.client.force_login(self.user)

    def test_bug_001_csv_preserves_zero(self):
        response = self.client.get(reverse("crm:export_customers_csv"))
        self.assertEqual(response.status_code, 200)
        rows = list(csv.reader(StringIO(response.content.decode("utf-8-sig"))))
        self.assertEqual((rows[1][6], rows[1][8]), ("0", "0"))

    def test_bug_002_replayed_email_confirmation_logs_once(self):
        url = reverse("crm:customer_email_draft", args=[self.customer.pk])
        payload = {
            "goal": "thanks", "tone": "formal", "length": "ngắn", "action": "record_sent",
            "draft": "Kính gửi anh/chị, cảm ơn đã trao đổi về CRM.",
        }
        # Replay the same submitted form, as with a double click or POST retry.
        for _ in range(2):
            self.assertEqual(self.client.post(url, payload).status_code, 302)
        self.assertFalse(mail.outbox)
        self.assertEqual(Interaction.objects.filter(customer=self.customer, kind="EMAIL").count(), 1)

    def test_bug_003_replayed_follow_up_sends_once(self):
        lead = LeadRequest.objects.create(customer=self.customer, solution_interest="CRM", request_text="Demo CRM")
        url = reverse("crm:lead_follow_up", args=[lead.pk])
        for _ in range(2):
            self.assertEqual(self.client.post(url, {"question_text": "Vui lòng bổ sung nhu cầu CRM."}).status_code, 302)
        self.assertEqual(
            (len(mail.outbox), LeadFollowUp.objects.count(), LeadFollowUp.objects.filter(status="REVOKED").count()),
            (1, 1, 0),
        )

    def test_bug_004_report_breadcrumb_identifies_report(self):
        response = self.client.get(reverse("crm:report"))
        self.assertEqual(response.status_code, 200)
        breadcrumb = BeautifulSoup(response.content, "html.parser").select_one(".topbar-label")
        self.assertIsNotNone(breadcrumb)
        self.assertEqual(breadcrumb.get_text(" ", strip=True), "CRM / Báo cáo")
