from datetime import timedelta

from django.contrib.auth.models import Permission, User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from crm.models import AIAnalysis, CareTask, Customer, LeadRequest


class CRMViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="crm-tester",
            password="test-password-123",
        )
        self.user.user_permissions.add(*Permission.objects.filter(content_type__app_label="crm"))
        self.customer = Customer.objects.create(
            full_name="Công ty kiểm thử",
            email="company@example.com",
            company="Công ty Kiểm thử",
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("crm:dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_wagtail_login_page_uses_vietnamese_labels(self):
        response = self.client.get("/admin/login/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Đăng nhập DigiFlow CRM")
        self.assertContains(response, "Tên đăng nhập")
        self.assertContains(response, "Mật khẩu")
        self.assertContains(response, "Quên mật khẩu?")

    def test_authenticated_user_without_crm_permission_is_denied(self):
        unassigned = User.objects.create_user(username="no-crm-role", password="test-password-123")
        self.client.force_login(unassigned)

        response = self.client.get(reverse("crm:dashboard"))

        self.assertEqual(response.status_code, 403)

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
        self.assertContains(response, "KHÔNG GIAN LÀM VIỆC CRM")
        self.assertContains(response, "Xem ai cần chăm sóc trước")
        self.assertContains(response, "Việc đang mở")
        self.assertContains(response, "Bạn muốn làm gì?")
        self.assertContains(response, "Yêu cầu tư vấn gần đây")
        self.assertContains(response, reverse("crm:customers"))
        self.assertContains(response, reverse("crm:lead_requests"))

    def test_empty_dashboard_guides_first_time_users_through_the_crm_flow(self):
        self.customer.delete()
        self.client.force_login(self.user)

        response = self.client.get(reverse("crm:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["show_first_run_guide"])
        self.assertContains(response, "HƯỚNG DẪN LẦN ĐẦU")
        self.assertContains(response, "Gửi yêu cầu tư vấn thử")
        self.assertContains(response, "Đọc gợi ý AI")
        self.assertContains(response, "python manage.py seed_crm_data")
        self.assertNotContains(response, "Bạn muốn làm gì?")

    def test_customer_detail_explains_ai_data_and_score(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("crm:customer_detail", args=[self.customer.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AI dùng dữ liệu nào? Điểm số có nghĩa gì?")
        self.assertContains(response, "không phải xác suất mua hàng")
        self.assertContains(response, "Gemini có thể nhận tên, công ty")

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

    def test_user_can_create_care_task_and_get_assigned_automatically(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("crm:customer_care_task_create", args=[self.customer.pk]), {
            "title": "Gọi trao đổi về demo",
            "description": "Thống nhất lịch trình diễn.",
            "kind": CareTask.Kind.CALL,
            "due_at": timezone.localdate().isoformat(),
            "priority": CareTask.Priority.HIGH,
            "status": CareTask.Status.TODO,
        })

        task = CareTask.objects.get()
        self.assertRedirects(response, reverse("crm:customer_detail", args=[self.customer.pk]))
        self.assertEqual(task.customer, self.customer)
        self.assertEqual(task.assignee, self.user)
        self.assertEqual(task.priority, CareTask.Priority.HIGH)

    def test_task_can_be_completed_from_edit_form(self):
        self.client.force_login(self.user)
        task = CareTask.objects.create(
            customer=self.customer,
            title="Gửi báo giá",
            due_at=timezone.localdate(),
            assignee=self.user,
        )

        response = self.client.post(reverse("crm:care_task_edit", args=[task.pk]), {
            "customer": self.customer.pk,
            "title": task.title,
            "description": "",
            "kind": CareTask.Kind.QUOTE,
            "due_at": timezone.localdate().isoformat(),
            "priority": CareTask.Priority.MEDIUM,
            "status": CareTask.Status.DONE,
        })

        self.assertRedirects(response, reverse("crm:care_tasks"))
        task.refresh_from_db()
        self.assertEqual(task.status, CareTask.Status.DONE)
        self.assertIsNotNone(task.completed_at)

    def test_ai_recommendation_prefills_task_but_does_not_save_automatically(self):
        self.client.force_login(self.user)
        recommendation = "Gọi lại để hẹn buổi demo giải pháp quản lý kho."
        AIAnalysis.objects.create(
            customer=self.customer,
            segment=Customer.Segment.POTENTIAL,
            score=75,
            summary="Nhu cầu phù hợp.",
            recommendation=recommendation,
            provider="rules",
        )

        response = self.client.get(
            reverse("crm:customer_care_task_create", args=[self.customer.pk]),
            {"suggestion": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"]["description"].value(), recommendation)
        self.assertEqual(CareTask.objects.count(), 0)

    def test_task_list_filters_by_status(self):
        self.client.force_login(self.user)
        CareTask.objects.create(customer=self.customer, title="Cần gọi", due_at=timezone.localdate())
        CareTask.objects.create(
            customer=self.customer,
            title="Đã xong",
            due_at=timezone.localdate(),
            status=CareTask.Status.DONE,
        )

        response = self.client.get(reverse("crm:care_tasks"), {"status": CareTask.Status.TODO})

        self.assertContains(response, "Cần gọi")
        self.assertNotContains(response, "Đã xong")

    def test_priority_queue_explains_why_customer_needs_attention(self):
        self.client.force_login(self.user)
        self.customer.ai_segment = Customer.Segment.CHURN_RISK
        self.customer.ai_score = 88
        self.customer.save(update_fields=["ai_segment", "ai_score"])
        CareTask.objects.create(
            customer=self.customer,
            title="Việc bị trễ",
            due_at=timezone.localdate() - timedelta(days=1),
        )

        response = self.client.get(reverse("crm:priority_customers"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Có nguy cơ rời bỏ")
        self.assertContains(response, "Có việc chăm sóc quá hạn")
        self.assertEqual(response.context["queue"][0]["customer"], self.customer)

    def test_priority_queue_quick_filter_shows_only_matching_customers(self):
        self.client.force_login(self.user)
        self.customer.ai_segment = Customer.Segment.CHURN_RISK
        self.customer.save(update_fields=["ai_segment"])
        ordinary = Customer.objects.create(full_name="Khách thường", email="ordinary@example.com")

        response = self.client.get(reverse("crm:priority_customers"), {"filter": "churn"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["customer"] for row in response.context["queue"]], [self.customer])
        self.assertNotContains(response, ordinary.full_name)

    @override_settings(GEMINI_API_KEY="")
    def test_email_draft_is_generated_without_sending_or_logging(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("crm:customer_email_draft", args=[self.customer.pk]), {
            "goal": "check_in", "tone": "formal", "length": "vừa", "action": "generate",
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "bản nháp")
        self.assertContains(response, "Kính gửi")
        self.assertEqual(self.customer.interactions.count(), 0)
        self.assertTrue(response.context["form"]["draft"].value())

    def test_email_is_logged_only_after_explicit_user_confirmation(self):
        self.client.force_login(self.user)
        draft = "Kính gửi Anh/Chị,\n\nXin cảm ơn anh/chị đã trao đổi.\n\nTrân trọng."

        response = self.client.post(reverse("crm:customer_email_draft", args=[self.customer.pk]), {
            "goal": "thanks", "tone": "formal", "length": "ngắn", "draft": draft,
            "action": "record_sent",
        })

        self.assertRedirects(response, reverse("crm:customer_detail", args=[self.customer.pk]))
        self.assertEqual(self.customer.interactions.count(), 1)
        self.assertEqual(self.customer.interactions.get().content, draft)

    def test_customer_export_returns_csv(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("crm:export_customers_csv"), {"q": "Kiểm thử"})

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])
        self.assertIn(self.customer.email, response.content.decode("utf-8-sig"))

    def test_customer_export_neutralizes_spreadsheet_formulas(self):
        self.client.force_login(self.user)
        Customer.objects.create(full_name="=HYPERLINK(\"https://bad.test\")", email="formula@example.com")

        response = self.client.get(reverse("crm:export_customers_csv"))

        self.assertIn("'=HYPERLINK", response.content.decode("utf-8-sig"))
        self.assertNotIn("\n=HYPERLINK", response.content.decode("utf-8-sig"))

    def test_report_shows_existing_crm_counts(self):
        self.client.force_login(self.user)
        CareTask.objects.create(customer=self.customer, title="Gọi khách", due_at=timezone.localdate())

        response = self.client.get(reverse("crm:report"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["customer_total"], 1)
        self.assertContains(response, "Báo cáo CRM")

    def test_dashboard_groups_overdue_today_and_upcoming_tasks(self):
        self.client.force_login(self.user)
        today = timezone.localdate()
        CareTask.objects.create(customer=self.customer, title="Việc quá hạn", due_at=today - timedelta(days=1))
        CareTask.objects.create(customer=self.customer, title="Việc hôm nay", due_at=today)
        CareTask.objects.create(customer=self.customer, title="Việc sắp tới", due_at=today + timedelta(days=1))
        CareTask.objects.create(
            customer=self.customer,
            title="Việc xong không còn mở",
            due_at=today - timedelta(days=1),
            status=CareTask.Status.DONE,
        )

        response = self.client.get(reverse("crm:dashboard"))

        self.assertContains(response, "Việc quá hạn")
        self.assertContains(response, "Việc hôm nay")
        self.assertContains(response, "Việc sắp tới")
        self.assertNotContains(response, "Việc xong không còn mở")

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
