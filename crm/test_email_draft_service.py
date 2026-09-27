from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase, override_settings

from crm.models import Customer, LeadRequest
from crm.services.email_draft_service import create_email_draft


class EmailDraftServiceTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            full_name="Nguyễn Minh Anh", email="private@example.com", company="Công ty Minh Anh"
        )

    @override_settings(GEMINI_API_KEY="")
    def test_rules_fallback_creates_vietnamese_draft(self):
        result = create_email_draft(self.customer, "check_in")

        self.assertEqual(result["provider"], "rules")
        self.assertIn("Kính gửi", result["draft"])
        self.assertIn("nhu cầu", result["draft"])

    @override_settings(GEMINI_API_KEY="configured")
    @patch("google.genai.Client")
    def test_unconsented_public_lead_is_never_sent_to_gemini(self, client_class):
        LeadRequest.objects.create(
            customer=self.customer,
            request_text="Nội dung riêng chưa đồng ý AI.",
            ai_processing_consent=False,
        )

        result = create_email_draft(self.customer, "check_in")

        self.assertEqual(result["provider"], "rules")
        client_class.assert_not_called()

    @override_settings(GEMINI_API_KEY="configured")
    @patch("google.genai.Client")
    def test_prompt_uses_only_consented_need_and_excludes_contact_details(self, client_class):
        LeadRequest.objects.create(
            customer=self.customer,
            request_text="Đang tìm hiểu CRM cho nhóm kinh doanh.",
            ai_processing_consent=True,
        )
        client = client_class.return_value
        client.models.generate_content.return_value = SimpleNamespace(
            text="Kính gửi Anh/Chị, xin phép trao đổi thêm về nhu cầu CRM của doanh nghiệp."
        )

        result = create_email_draft(self.customer, "meeting")

        self.assertEqual(result["provider"], "gemini")
        prompt = client.models.generate_content.call_args.kwargs["contents"]
        self.assertIn("Đang tìm hiểu CRM", prompt)
        self.assertNotIn(self.customer.full_name, prompt)
        self.assertNotIn(self.customer.email, prompt)
        self.assertNotIn(self.customer.company, prompt)
