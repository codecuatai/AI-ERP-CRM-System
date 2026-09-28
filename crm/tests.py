from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Customer, Interaction, LeadRequest


class PublicLeadRequestTests(TestCase):
    def setUp(self):
        self.url = reverse("crm:lead_request")
        self.payload = {
            "full_name": "Nguyễn Minh Anh",
            "email": "minhanh@example.com",
            "phone": "0900000000",
            "company": "Công ty Minh Anh",
            "solution_interest": "CRM",
            "request_text": "Tôi muốn tìm hiểu gói tư vấn phù hợp.",
            "consent": "on",
            "ai_processing_consent": "",
            "website": "",
        }

    def test_public_form_is_available_without_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gửi yêu cầu tư vấn")

    def test_landing_page_introduces_solutions_and_includes_lead_form(self):
        response = self.client.get(reverse("landing_page"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Giải pháp")
        self.assertContains(response, "Quản lý kho &amp; bán hàng")
        self.assertContains(response, "id_request_text")
        self.assertContains(response, "id_solution_interest")
        self.assertContains(response, "id_ai_processing_consent")
        self.assertContains(response, reverse("privacy_notice"))

    @override_settings(PUBLIC_PRIVACY_EMAIL="")
    def test_privacy_notice_discloses_demo_placeholders(self):
        response = self.client.get(reverse("privacy_notice"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Thông báo quyền riêng tư")
        self.assertContains(response, "PUBLIC_PRIVACY_EMAIL")
        self.assertContains(response, "rút lại đồng ý")

    @override_settings(
        PUBLIC_CONTACT_EMAIL="demo-contact@digiflow.test",
        PUBLIC_PRIVACY_EMAIL="privacy@digiflow.test",
    )
    def test_demo_email_addresses_are_never_presented_as_live_contact_channels(self):
        landing = self.client.get(reverse("landing_page"))
        privacy = self.client.get(reverse("privacy_notice"))

        self.assertContains(landing, "Email minh họa — không nhận thư")
        self.assertNotContains(landing, "demo-contact@digiflow.test")
        self.assertContains(privacy, "không nhận thư")
        self.assertNotContains(privacy, "mailto:privacy@digiflow.test")

    @override_settings(
        PUBLIC_CONTACT_EMAIL="hello@digiflow.example.org",
        PUBLIC_PRIVACY_EMAIL="privacy@digiflow.example.org",
    )
    def test_real_contact_addresses_are_clickable(self):
        landing = self.client.get(reverse("landing_page"))
        privacy = self.client.get(reverse("privacy_notice"))

        self.assertContains(landing, 'href="mailto:hello@digiflow.example.org"')
        self.assertContains(privacy, 'href="mailto:privacy@digiflow.example.org"')

    def test_privacy_notice_has_a_scannable_summary_and_section_links(self):
        response = self.client.get(reverse("privacy_notice"))

        self.assertContains(response, 'aria-label="Mục lục thông báo quyền riêng tư"')
        self.assertContains(response, 'href="#du-lieu"')
        self.assertContains(response, 'href="#ai"')
        self.assertContains(response, 'href="#luu-tru"')
        self.assertContains(response, 'href="#quyen"')

    def test_landing_page_form_uses_the_same_lead_capture_flow(self):
        response = self.client.post(reverse("landing_page"), self.payload)

        self.assertRedirects(response, reverse("crm:lead_request_success"))
        self.assertEqual(Customer.objects.count(), 1)
        self.assertEqual(LeadRequest.objects.count(), 1)
        self.assertEqual(Interaction.objects.count(), 1)

    def test_submission_creates_customer_request_and_interaction(self):
        response = self.client.post(self.url, self.payload)

        self.assertRedirects(response, reverse("crm:lead_request_success"))
        customer = Customer.objects.get(email="minhanh@example.com")
        lead_request = LeadRequest.objects.get(customer=customer)
        interaction = Interaction.objects.get(customer=customer)
        self.assertEqual(customer.source, "Website")
        self.assertEqual(lead_request.status, LeadRequest.Status.NEW)
        self.assertIsNotNone(lead_request.consent_at)
        self.assertEqual(lead_request.consent_version, "v2")
        self.assertEqual(lead_request.get_solution_interest_display(), "CRM & chăm sóc khách hàng")
        self.assertFalse(lead_request.ai_processing_consent)
        self.assertIsNone(lead_request.ai_processing_consent_at)
        self.assertEqual(interaction.content, self.payload["request_text"])

    def test_ai_consent_is_optional_and_recorded_separately(self):
        response = self.client.post(self.url, {**self.payload, "ai_processing_consent": "on"})

        self.assertRedirects(response, reverse("crm:lead_request_success"))
        lead_request = LeadRequest.objects.get()
        self.assertTrue(lead_request.ai_processing_consent)
        self.assertIsNotNone(lead_request.ai_processing_consent_at)
        self.assertEqual(lead_request.ai_processing_consent_version, "v1")

    def test_consent_is_required(self):
        payload = {**self.payload, "consent": ""}
        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Customer.objects.exists())
        self.assertFalse(LeadRequest.objects.exists())

    def test_repeat_email_adds_request_without_duplicate_customer(self):
        Customer.objects.create(full_name="Tên đã lưu", email="minhanh@example.com", source="Admin")
        response = self.client.post(self.url, self.payload)

        self.assertRedirects(response, reverse("crm:lead_request_success"))
        self.assertEqual(Customer.objects.count(), 1)
        self.assertEqual(LeadRequest.objects.count(), 1)
        self.assertEqual(Interaction.objects.count(), 1)
        self.assertEqual(Customer.objects.get().full_name, "Tên đã lưu")

    def test_repeat_email_reuses_customer_case_insensitively(self):
        Customer.objects.create(full_name="Tên đã lưu", email="MINHANH@EXAMPLE.COM", source="Admin")
        response = self.client.post(self.url, self.payload)

        self.assertRedirects(response, reverse("crm:lead_request_success"))
        self.assertEqual(Customer.objects.count(), 1)
        self.assertEqual(LeadRequest.objects.count(), 1)
        self.assertEqual(Customer.objects.get().full_name, "Tên đã lưu")

    def test_honeypot_submission_is_rejected(self):
        payload = {**self.payload, "website": "spam"}
        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Customer.objects.exists())
