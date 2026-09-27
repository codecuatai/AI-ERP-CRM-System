import re

from django.contrib.auth.models import Permission, User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from crm.models import (
    AIAnalysis,
    CareTask,
    Customer,
    LeadFollowUp,
    LeadFollowUpResponse,
    LeadRequest,
)


@override_settings(
    DEFAULT_FROM_EMAIL="DigiFlow <no-reply@example.test>",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    GEMINI_API_KEY="",
    PUBLIC_SITE_URL="https://crm.example.test",
)
class CRMEndToEndFlowTests(TestCase):
    def test_public_lead_to_ai_analysis_and_tracked_care_task(self):
        landing_page = self.client.get(reverse("landing_page"))
        self.assertEqual(landing_page.status_code, 200)
        self.assertContains(landing_page, "DigiFlow (đơn vị vận hành bản demo)")
        self.assertNotContains(landing_page, "thay bang ten don vi that")

        public_payload = {
            "full_name": "Nguyễn Minh Anh",
            "email": "minhanh-e2e@example.test",
            "phone": "0900000000",
            "company": "Công ty E2E",
            "solution_interest": LeadRequest.SolutionInterest.CRM,
            "request_text": "Đội ngũ muốn tìm hiểu CRM và cần tư vấn demo.",
            "consent": "on",
            "ai_processing_consent": "on",
            "website": "",
        }

        submitted = self.client.post(reverse("crm:lead_request"), public_payload)
        self.assertRedirects(submitted, reverse("crm:lead_request_success"))

        customer = Customer.objects.get(email=public_payload["email"])
        lead_request = LeadRequest.objects.get(customer=customer)
        self.assertEqual(customer.interactions.count(), 1)
        self.assertTrue(lead_request.ai_processing_consent)

        staff = User.objects.create_user(
            username="e2e-sales",
            password="test-only-password",
            is_staff=True,
        )
        staff.user_permissions.add(*Permission.objects.filter(content_type__app_label="crm"))
        self.client.force_login(staff)

        follow_up_url = reverse("crm:lead_follow_up", args=[lead_request.pk])
        sent = self.client.post(follow_up_url, {
            "question_text": "Bạn có thể chia sẻ thêm về quy trình bán hàng hiện tại không?",
        })
        self.assertRedirects(sent, follow_up_url)
        self.assertEqual(len(mail.outbox), 1)

        follow_up = LeadFollowUp.objects.get(lead_request=lead_request)
        token_match = re.search(
            r"/crm/bo-sung-thong-tin/([A-Za-z0-9_-]{43})/",
            str(mail.outbox[0].body),
        )
        self.assertIsNotNone(token_match)
        token = token_match.group(1)
        self.assertEqual(follow_up.status, LeadFollowUp.Status.SENT)

        response_url = reverse("crm:lead_follow_up_reply", kwargs={"token": token})
        response_page = self.client.get(response_url)
        self.assertEqual(response_page.status_code, 200)
        self.assertContains(response_page, "Khó khăn hoặc quy trình hiện tại")

        customer_reply = self.client.post(response_url, {
            "current_challenge": "Khách hàng và cơ hội đang nằm rải rác trên nhiều bảng tính.",
            "desired_outcome": "Tập trung lịch sử tư vấn và theo dõi cơ hội.",
            "implementation_timing": LeadFollowUpResponse.ImplementationTiming.ONE_TO_THREE_MONTHS,
            "preferred_contact_time": "Buổi sáng",
            "ai_processing_consent": "on",
        })
        self.assertRedirects(customer_reply, response_url)
        lead_response = LeadFollowUpResponse.objects.get(follow_up=follow_up)
        self.assertTrue(lead_response.ai_processing_consent)
        follow_up.refresh_from_db()
        self.assertEqual(follow_up.status, LeadFollowUp.Status.ANSWERED)

        analysis = self.client.post(reverse("crm:analyze_customer", args=[customer.pk]))
        self.assertRedirects(analysis, reverse("crm:customer_detail", args=[customer.pk]))
        result = AIAnalysis.objects.get(customer=customer)
        self.assertEqual(result.provider, "rules")
        self.assertIn(result.segment, dict(Customer.Segment.choices))

        task_url = reverse("crm:customer_care_task_create", args=[customer.pk])
        task_response = self.client.post(task_url, {
            "title": "Gọi trao đổi về demo CRM",
            "description": result.recommendation,
            "kind": CareTask.Kind.CALL,
            "due_at": timezone.localdate().isoformat(),
            "priority": CareTask.Priority.HIGH,
            "status": CareTask.Status.TODO,
        })
        self.assertRedirects(task_response, reverse("crm:customer_detail", args=[customer.pk]))
        task = CareTask.objects.get(customer=customer)
        self.assertEqual(task.assignee, staff)

        dashboard = self.client.get(reverse("crm:dashboard"))
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, "Gọi trao đổi về demo CRM")
        self.assertContains(dashboard, "Hôm nay")
