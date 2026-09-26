from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from crm.models import AIAnalysis, Customer, LeadRequest


class CRMViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="crm-tester",
            password="test-password-123",
        )
        self.customer = Customer.objects.create(
            full_name="Công ty kiểm thử",
            email="company@example.com",
            company="Công ty Kiểm thử",
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("crm:dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_authenticated_dashboard_can_search_customer(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("crm:customers"), {"q": "Kiểm thử"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.customer.full_name)

    def test_dashboard_shows_summary_and_separate_work_areas(self):
        self.client.force_login(self.user)
        LeadRequest.objects.create(
            customer=self.customer,
            request_text="Tư vấn phần mềm quản lý kho",
            solution_interest=LeadRequest.SolutionInterest.ERP,
        )

        response = self.client.get(reverse("crm:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bạn muốn làm gì?")
        self.assertContains(response, "Yêu cầu tư vấn gần đây")
        self.assertContains(response, reverse("crm:customers"))
        self.assertContains(response, reverse("crm:lead_requests"))

    def test_lead_request_list_filters_by_status(self):
        self.client.force_login(self.user)
        new_request = LeadRequest.objects.create(
            customer=self.customer,
            request_text="Yêu cầu mới",
            solution_interest=LeadRequest.SolutionInterest.CRM,
        )
        completed_request = LeadRequest.objects.create(
            customer=self.customer,
            request_text="Yêu cầu đã xử lý",
            solution_interest=LeadRequest.SolutionInterest.CRM,
            status=LeadRequest.Status.COMPLETED,
        )

        response = self.client.get(reverse("crm:lead_requests"), {"status": LeadRequest.Status.NEW})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, new_request.request_text)
        self.assertNotContains(response, completed_request.request_text)

    def test_staff_can_update_lead_request_status(self):
        self.client.force_login(self.user)
        lead_request = LeadRequest.objects.create(
            customer=self.customer,
            request_text="Cần tư vấn",
            solution_interest=LeadRequest.SolutionInterest.CRM,
        )

        response = self.client.post(
            reverse("crm:update_lead_request_status", args=[lead_request.pk]),
            {"status": LeadRequest.Status.CONTACTED},
        )

        self.assertRedirects(response, reverse("crm:lead_requests"))
        lead_request.refresh_from_db()
        self.assertEqual(lead_request.status, LeadRequest.Status.CONTACTED)

    def test_customer_with_public_lead_without_ai_consent_cannot_be_analyzed(self):
        self.client.force_login(self.user)
        LeadRequest.objects.create(
            customer=self.customer,
            request_text="Tôi muốn tìm hiểu CRM.",
            solution_interest=LeadRequest.SolutionInterest.CRM,
            ai_processing_consent=False,
        )

        response = self.client.post(reverse("crm:analyze_customer", args=[self.customer.pk]))

        self.assertRedirects(response, reverse("crm:customer_detail", args=[self.customer.pk]))
        self.assertFalse(AIAnalysis.objects.exists())

    @override_settings(GEMINI_API_KEY="")
    def test_customer_analysis_uses_only_requests_with_ai_consent(self):
        self.client.force_login(self.user)
        LeadRequest.objects.create(
            customer=self.customer,
            request_text="Quan tâm báo giá giải pháp CRM.",
            solution_interest=LeadRequest.SolutionInterest.CRM,
            ai_processing_consent=True,
        )

        response = self.client.post(reverse("crm:analyze_customer", args=[self.customer.pk]))

        self.assertRedirects(response, reverse("crm:customer_detail", args=[self.customer.pk]))
        self.assertEqual(AIAnalysis.objects.get().provider, "rules")
        self.assertEqual(AIAnalysis.objects.get().segment, Customer.Segment.POTENTIAL)
