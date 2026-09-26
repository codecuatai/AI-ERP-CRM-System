from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings

from crm.models import Customer, Interaction, LeadRequest
from crm.services.ai_service import AIConsentRequired, _rule_based_analysis, analyze_customer


class RuleBasedAnalysisTests(TestCase):
    def make_customer(self, **kwargs):
        defaults = {
            "full_name": "Khách hàng kiểm thử",
            "email": "test@example.com",
            "total_spent": Decimal("0"),
        }
        defaults.update(kwargs)
        return Customer.objects.create(**defaults)

    def test_high_spending_customer_is_vip(self):
        customer = self.make_customer(total_spent=Decimal("20000000"))

        result = _rule_based_analysis(customer, [])

        self.assertEqual(result["segment"], Customer.Segment.VIP)
        self.assertEqual(result["score"], 90)

    def test_sales_keyword_marks_customer_as_potential(self):
        customer = self.make_customer()
        interaction = Interaction(
            customer=customer,
            kind=Interaction.Kind.EMAIL,
            subject="Hỏi báo giá",
            content="Khách muốn xem demo và báo giá giải pháp.",
        )

        result = _rule_based_analysis(customer, [interaction])

        self.assertEqual(result["segment"], Customer.Segment.POTENTIAL)
        self.assertEqual(result["score"], 75)

    def test_empty_customer_is_unclassified(self):
        customer = self.make_customer()

        result = _rule_based_analysis(customer, [])

        self.assertEqual(result["segment"], Customer.Segment.UNCLASSIFIED)
        self.assertEqual(result["score"], 25)

    @override_settings(GEMINI_API_KEY="")
    def test_missing_api_key_uses_rules_fallback(self):
        customer = self.make_customer()

        result = analyze_customer(customer)

        self.assertEqual(result["provider"], "rules")
        self.assertIn("segment", result)
        self.assertIn("recommendation", result)

    @override_settings(GEMINI_API_KEY="")
    def test_public_lead_requires_ai_consent_for_analysis(self):
        customer = self.make_customer()
        LeadRequest.objects.create(
            customer=customer,
            request_text="Muốn tìm hiểu giải pháp CRM.",
            solution_interest=LeadRequest.SolutionInterest.CRM,
            ai_processing_consent=False,
        )

        with self.assertRaises(AIConsentRequired):
            analyze_customer(customer)

    @override_settings(GEMINI_API_KEY="")
    def test_consented_public_analysis_ignores_customer_spending(self):
        customer = self.make_customer(total_spent=Decimal("25000000"))
        lead = LeadRequest.objects.create(
            customer=customer,
            request_text="Đang tìm hiểu phương án quản lý khách hàng.",
            solution_interest=LeadRequest.SolutionInterest.CRM,
            ai_processing_consent=True,
        )

        result = analyze_customer(customer, permitted_requests=[lead])

        self.assertEqual(result["segment"], Customer.Segment.POTENTIAL)

    @override_settings(GEMINI_API_KEY="test-key")
    @patch("crm.services.ai_service._request_gemini")
    def test_gemini_prompt_for_public_lead_excludes_contact_and_unconsented_requests(self, request_gemini):
        customer = self.make_customer(full_name="Tên riêng cần bảo vệ", email="private@example.com")
        allowed = LeadRequest.objects.create(
            customer=customer,
            request_text="Đang tìm hiểu phương án CRM.",
            solution_interest=LeadRequest.SolutionInterest.CRM,
            ai_processing_consent=True,
        )
        LeadRequest.objects.create(
            customer=customer,
            request_text="Nội dung chưa được đồng ý gửi phân tích.",
            solution_interest=LeadRequest.SolutionInterest.ERP,
            ai_processing_consent=False,
        )
        request_gemini.return_value = (
            '{"segment":"POTENTIAL","score":75,"summary":"Đang tìm hiểu CRM.",'
            '"recommendation":"Liên hệ tư vấn."}'
        )

        analyze_customer(customer, permitted_requests=[allowed])

        prompt = request_gemini.call_args.args[0]
        self.assertIn("Đang tìm hiểu phương án CRM.", prompt)
        self.assertNotIn(customer.full_name, prompt)
        self.assertNotIn(customer.email, prompt)
        self.assertNotIn("Nội dung chưa được đồng ý gửi phân tích.", prompt)
