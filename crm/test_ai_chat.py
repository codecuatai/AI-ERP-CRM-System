import json
from django.test import TestCase, override_settings
from django.urls import reverse

from crm.models import Customer, Interaction, LeadRequest
from crm.services.ai_chat_service import answer_customer_question


@override_settings(GEMINI_API_KEY="")
class AIChatConsultantTests(TestCase):
    def test_answer_customer_question_rules_fallback(self):
        # Kiểm tra fallback tư vấn chi phí
        res_pricing = answer_customer_question("Chi phí triển khai giải pháp kho là bao nhiêu?")
        self.assertEqual(res_pricing["provider"], "rules")
        self.assertEqual(res_pricing["suggested_solution"], "ERP")
        self.assertIn("chi phí", res_pricing["reply"].lower())

        # Kiểm tra fallback tư vấn thời gian
        res_time = answer_customer_question("Thời gian triển khai mất bao lâu?")
        self.assertIn("khảo sát", res_time["reply"])

        # Kiểm tra fallback tư vấn POS
        res_pos = answer_customer_question("Bên tôi muốn dùng POS bán hàng quét mã vạch")
        self.assertEqual(res_pos["suggested_solution"], "ERP")
        self.assertIn("pos", res_pos["reply"].lower())

        # Kiểm tra câu hỏi rỗng
        res_empty = answer_customer_question("")
        self.assertEqual(res_empty["suggested_solution"], "OTHER")

    def test_ai_chat_consultant_view_post_success(self):
        url = reverse("crm:ai_chat_consultant")
        payload = {
            "message": "Tôi muốn tìm hiểu về AI CRM cho doanh nghiệp 20 người",
            "history": [],
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("reply", data)
        self.assertEqual(data["suggested_solution"], "CRM")

    def test_ai_chat_consultant_view_invalid_requests(self):
        url = reverse("crm:ai_chat_consultant")

        # GET method should be disallowed (require_POST)
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 405)

        # Empty message
        response_empty = self.client.post(
            url,
            data=json.dumps({"message": ""}),
            content_type="application/json",
        )
        self.assertEqual(response_empty.status_code, 400)

        # Non-JSON payload
        response_bad_json = self.client.post(
            url,
            data="not a json",
            content_type="text/plain",
        )
        self.assertEqual(response_bad_json.status_code, 400)

    def test_lead_request_with_chat_history_creates_interaction(self):
        history = [
            {"role": "user", "content": "Tư vấn cho tôi giải pháp quản lý kho"},
            {"role": "assistant", "content": "DigiFlow có giải pháp kho đa điểm đồng bộ realtime..."},
            {"role": "user", "content": "Chi phí khoảng bao nhiêu?"},
        ]
        post_data = {
            "full_name": "Lê Văn Chat",
            "email": "levanchat@example.com",
            "phone": "0988776655",
            "company": "Công ty TNHH Chat Demo",
            "solution_interest": "ERP",
            "request_text": "Cần demo quản lý 3 kho hàng",
            "consent": "on",
            "ai_processing_consent": "on",
            "chat_history": json.dumps(history),
        }
        response = self.client.post(reverse("crm:lead_request"), data=post_data)
        self.assertRedirects(response, reverse("crm:lead_request_success"))

        customer = Customer.objects.get(email="levanchat@example.com")
        self.assertEqual(customer.full_name, "Lê Văn Chat")

        # Kiểm tra interaction lưu đoạn chat
        interactions = customer.interactions.filter(subject="Lịch sử trao đổi cùng Trợ lý AI")
        self.assertTrue(interactions.exists())
        chat_interaction = interactions.first()
        self.assertIn("Tư vấn cho tôi giải pháp quản lý kho", chat_interaction.content)
        self.assertIn("Chi phí khoảng bao nhiêu?", chat_interaction.content)
