"""QA regression coverage using synthetic data and Django's isolated test database."""

import csv
from html.parser import HTMLParser
from io import StringIO
from unittest.mock import patch
from urllib.parse import urlsplit

from django.contrib.auth.models import Permission, User
from django.contrib.staticfiles import finders
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape

from crm.models import AIAnalysis, CareTask, Customer, Interaction, LeadRequest
from crm.services.ai_service import analyze_customer
from crm.services.email_draft_service import create_email_draft


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = set()

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            if href.startswith("/") and not href.startswith("//"):
                self.links.add(href)


@override_settings(GEMINI_API_KEY="", EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class QAEdgeCaseTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser(username="qa-synthetic", email="qa@example.test")
        cls.customer = Customer.objects.create(full_name="Nguyễn QA", email="customer@example.test")
        cls.lead = LeadRequest.objects.create(
            customer=cls.customer, solution_interest="CRM", request_text="Tư vấn CRM cho doanh nghiệp."
        )
        cls.task = CareTask.objects.create(
            customer=cls.customer, title="Gọi demo CRM", due_at=timezone.localdate()
        )

    def lead_payload(self, **changes):
        return {
            "full_name": "Trần QA", "email": "new@example.test", "phone": "",
            "company": "Công ty QA", "solution_interest": "CRM", "request_text": "Cần tư vấn CRM.",
            "consent": "on", "ai_processing_consent": "", "website": "", **changes,
        }

    def task_payload(self, **changes):
        return {
            "customer": self.customer.pk, "title": "Hẹn demo", "description": "",
            "kind": CareTask.Kind.CALL, "due_at": timezone.localdate().isoformat(),
            "priority": CareTask.Priority.MEDIUM, "status": CareTask.Status.TODO, **changes,
        }

    def screens(self):
        return [
            reverse("landing_page"), reverse("privacy_notice"), reverse("crm:lead_request"),
            reverse("crm:lead_request_success"), reverse("crm:dashboard"), reverse("crm:customers"),
            reverse("crm:customer_detail", args=[self.customer.pk]), reverse("crm:priority_customers"),
            reverse("crm:lead_requests"), reverse("crm:care_tasks"), reverse("crm:care_task_create"),
            reverse("crm:care_task_edit", args=[self.task.pk]),
            reverse("crm:customer_care_task_create", args=[self.customer.pk]),
            reverse("crm:customer_email_draft", args=[self.customer.pk]), reverse("crm:report"),
            reverse("crm:lead_follow_up", args=[self.lead.pk]),
        ]

    def test_screens_and_rendered_internal_links_resolve(self):
        self.client.force_login(self.user)
        links = set()
        for url in self.screens():
            with self.subTest(screen=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                parser = LinkParser()
                parser.feed(response.content.decode())
                links.update(parser.links)
        for href in sorted(links):
            with self.subTest(link=href):
                self.assertEqual(self.client.get(href, follow=True).status_code, 200)
                self.assertFalse(urlsplit(href).netloc)

    def test_static_assets_exist(self):
        for asset in ("crm/css/app.css", "crm/js/app.js"):
            with self.subTest(asset=asset):
                self.assertIsNotNone(finders.find(asset))

    def test_snippet_list_add_edit_inspect_screens(self):
        self.client.force_login(self.user)
        interaction = Interaction.objects.create(customer=self.customer, subject="QA", content="Demo")
        analysis = AIAnalysis.objects.create(customer=self.customer, segment="POTENTIAL", score=75)
        for obj in (self.customer, self.lead, self.task, interaction, analysis):
            base = f"/admin/snippets/crm/{obj._meta.model_name}/"
            for suffix in ("", "add/", f"edit/{obj.pk}/", f"inspect/{obj.pk}/"):
                with self.subTest(url=base + suffix):
                    self.assertEqual(self.client.get(base + suffix).status_code, 200)

    def test_required_fields_reject_empty_and_whitespace(self):
        before = (Customer.objects.count(), LeadRequest.objects.count(), Interaction.objects.count())
        for field in ("full_name", "email", "solution_interest", "request_text", "consent"):
            for value in ("", "   ") if field != "consent" else ("",):
                with self.subTest(field=field, value=value):
                    response = self.client.post(reverse("crm:lead_request"), self.lead_payload(**{field: value}))
                    self.assertEqual(response.status_code, 200)
                    self.assertIn(field, response.context["form"].errors)
        self.assertEqual(before, (Customer.objects.count(), LeadRequest.objects.count(), Interaction.objects.count()))

    def test_invalid_email_and_solution_are_rejected(self):
        for values in ({"email": "not-an-email"}, {"solution_interest": "INVALID"}):
            with self.subTest(values=values):
                response = self.client.post(reverse("crm:lead_request"), self.lead_payload(**values))
                self.assertEqual(response.status_code, 200)
                self.assertIn(next(iter(values)), response.context["form"].errors)
        self.assertEqual(LeadRequest.objects.count(), 1)

    def test_public_field_lengths_at_and_over_limit(self):
        for field, limit in (("full_name", 160), ("phone", 30), ("company", 160), ("request_text", 2000)):
            with self.subTest(field=field):
                before = LeadRequest.objects.count()
                valid = self.client.post(reverse("crm:lead_request"), self.lead_payload(**{field: "x" * limit}))
                self.assertEqual(valid.status_code, 302)
                invalid = self.client.post(reverse("crm:lead_request"), self.lead_payload(**{field: "x" * (limit + 1)}))
                self.assertIn(field, invalid.context["form"].errors)
                self.assertEqual(LeadRequest.objects.count(), before + 1)

    def test_special_characters_round_trip_and_are_html_escaped(self):
        payload = self.lead_payload(
            full_name="Nguyễn O'QA & Đối tác", request_text='<script>alert("qa")</script> Tư vấn CRM & POS'
        )
        self.assertEqual(self.client.post(reverse("crm:lead_request"), payload).status_code, 302)
        lead = LeadRequest.objects.get(customer__email=payload["email"])
        self.assertEqual(lead.request_text, payload["request_text"])
        self.client.force_login(self.user)
        response = self.client.get(reverse("crm:customer_detail", args=[lead.customer_id]))
        self.assertContains(response, escape(payload["request_text"]))
        self.assertNotContains(response, payload["request_text"])

    def test_public_post_requires_csrf(self):
        response = Client(enforce_csrf_checks=True).post(reverse("crm:lead_request"), self.lead_payload())
        self.assertEqual(response.status_code, 403)
        self.assertEqual(LeadRequest.objects.count(), 1)

    def test_internal_screens_require_login_and_permission(self):
        unassigned = User.objects.create_user(username="qa-no-permissions")
        internal = [url for url in self.screens() if url.startswith("/crm/")]
        # Exclude the public success/form URLs explicitly for clarity.
        internal = [url for url in internal if url not in (
            reverse("crm:lead_request"), reverse("crm:lead_request_success"),
            reverse("crm:lead_follow_up", args=[self.lead.pk]),
        )]
        for url in internal:
            with self.subTest(url=url):
                self.client.logout()
                self.assertEqual(self.client.get(url).status_code, 302)
                self.client.force_login(unassigned)
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_access_permission_alone_cannot_analyze_export_or_manage(self):
        viewer = User.objects.create_user(username="qa-viewer", is_staff=True)
        viewer.user_permissions.add(Permission.objects.get(codename="access_crm"))
        self.client.force_login(viewer)
        for url, data in (
            (reverse("crm:analyze_customer", args=[self.customer.pk]), {}),
            (reverse("crm:update_lead_request_status", args=[self.lead.pk]), {"status": "COMPLETED"}),
            (reverse("crm:care_task_create"), self.task_payload()),
            (reverse("crm:lead_follow_up", args=[self.lead.pk]), {"question_text": "QA"}),
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url, data).status_code, 403)
        self.assertEqual(self.client.get(reverse("crm:export_customers_csv")).status_code, 403)
        self.assertFalse(AIAnalysis.objects.exists())
        self.assertEqual(CareTask.objects.count(), 1)
        self.assertFalse(mail.outbox)

    def test_post_only_actions_reject_get(self):
        self.client.force_login(self.user)
        for url in (
            reverse("crm:analyze_customer", args=[self.customer.pk]),
            reverse("crm:update_lead_request_status", args=[self.lead.pk]),
            reverse("crm:revoke_lead_follow_up", args=[self.lead.pk, 99999]),
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 405)
        self.assertFalse(AIAnalysis.objects.exists())

    def test_missing_objects_return_404(self):
        self.client.force_login(self.user)
        for name in ("customer_detail", "care_task_edit", "lead_follow_up", "customer_email_draft"):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(f"crm:{name}", args=[99999])).status_code, 404)

    def test_invalid_pagination_and_search_do_not_crash(self):
        self.client.force_login(self.user)
        for name in ("customers", "lead_requests", "care_tasks", "priority_customers"):
            for page in ("abc", "-1", "99999"):
                with self.subTest(name=name, page=page):
                    response = self.client.get(reverse(f"crm:{name}"), {"q": "' <script> & QA", "page": page})
                    self.assertEqual(response.status_code, 200)
                    self.assertGreaterEqual(response.context["page"].number, 1)

    def test_customer_pagination_keeps_filters(self):
        self.client.force_login(self.user)
        Customer.objects.bulk_create([
            Customer(full_name=f"QA & POS {i:02}", email=f"page{i}@example.test", ai_segment="VIP")
            for i in range(16)
        ])
        response = self.client.get(reverse("crm:customers"), {"q": "QA & POS", "segment": "VIP"})
        self.assertEqual(response.context["page"].paginator.count, 16)
        # Pagination links are relative, so inspect their escaped HTML directly.
        self.assertContains(response, "q=QA%20%26%20POS&amp;segment=VIP&amp;page=2")
        second = self.client.get(reverse("crm:customers"), {"q": "QA & POS", "segment": "VIP", "page": 2})
        self.assertEqual(len(second.context["customers"]), 1)

    def test_invalid_task_fields_do_not_save(self):
        self.client.force_login(self.user)
        for changes in ({"title": "   "}, {"due_at": "2026-02-30"}, {"priority": "INVALID"}, {"customer": 99999}):
            with self.subTest(changes=changes):
                response = self.client.post(reverse("crm:care_task_create"), self.task_payload(**changes))
                self.assertEqual(response.status_code, 200)
                self.assertIn(next(iter(changes)), response.context["form"].errors)
        self.assertEqual(CareTask.objects.count(), 1)

    def test_customer_bound_task_ignores_tampered_customer(self):
        self.client.force_login(self.user)
        other = Customer.objects.create(full_name="Other QA", email="other@example.test")
        response = self.client.post(
            reverse("crm:customer_care_task_create", args=[self.customer.pk]),
            self.task_payload(customer=other.pk),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CareTask.objects.get(title="Hẹn demo").customer_id, self.customer.pk)

    def test_invalid_lead_status_preserves_data(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("crm:update_lead_request_status", args=[self.lead.pk]), {"status": "INVALID"}, follow=True)
        self.assertContains(response, "Trạng thái yêu cầu không hợp lệ")
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.status, LeadRequest.Status.NEW)

    def test_empty_email_confirmation_does_not_log_or_send(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("crm:customer_email_draft", args=[self.customer.pk]), {
            "goal": "thanks", "tone": "formal", "length": "ngắn", "action": "record_sent", "draft": "   ",
        })
        self.assertIn("draft", response.context["form"].errors)
        self.assertFalse(Interaction.objects.exists())
        self.assertFalse(mail.outbox)

    def test_csv_filters_and_special_characters(self):
        self.client.force_login(self.user)
        Customer.objects.create(full_name='QA, "Đối tác"\nCRM', email="csv@example.test", company="A & B", ai_segment="VIP")
        Customer.objects.create(full_name="QA inactive", email="inactive@example.test", ai_segment="VIP", is_active=False)
        response = self.client.get(reverse("crm:export_customers_csv"), {"q": "QA", "segment": "VIP", "active": "1"})
        rows = list(csv.reader(StringIO(response.content.decode("utf-8-sig"))))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][0], 'QA, "Đối tác"\nCRM')
        self.assertEqual(rows[1][1], "csv@example.test")

    @override_settings(GEMINI_API_KEY="qa-placeholder-never-sent")
    def test_gemini_errors_and_malformed_output_fall_back(self):
        customer = Customer.objects.create(full_name="AI QA", email="ai@example.test")
        for output in ("", "not-json", '{"segment":"INVALID"}', '{"segment":"VIP","score":"oops"}'):
            with self.subTest(output=output), patch("crm.services.ai_service._request_gemini", return_value=output):
                self.assertEqual(analyze_customer(customer)["provider"], "rules")
        with patch("crm.services.ai_service._request_gemini", side_effect=TimeoutError("QA timeout")):
            self.assertEqual(analyze_customer(customer)["provider"], "rules")
        with patch("google.genai.Client", side_effect=TimeoutError("QA timeout")):
            self.assertEqual(create_email_draft(customer, "thanks")["provider"], "rules")
