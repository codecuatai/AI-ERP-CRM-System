import hashlib
import re
import secrets
from datetime import timedelta
from smtplib import SMTPException
from unittest.mock import patch

from django.contrib.auth.models import Permission, User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from crm.models import (
    AIAnalysis,
    Customer,
    Interaction,
    LeadFollowUp,
    LeadFollowUpResponse,
    LeadRequest,
)


class LeadFollowUpFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="follow-up-staff",
            password="test-password-123",
            is_staff=True,
        )
        self.user.user_permissions.add(*Permission.objects.filter(content_type__app_label="crm"))
        self.customer = Customer.objects.create(
            full_name="Công ty kiểm thử",
            email="follow-up@example.com",
            company="Công ty Kiểm thử",
        )
        self.lead_request = LeadRequest.objects.create(
            customer=self.customer,
            solution_interest=LeadRequest.SolutionInterest.CRM,
            request_text="Đang tìm hiểu giải pháp CRM.",
        )
        self.send_url = reverse("crm:lead_follow_up", args=[self.lead_request.pk])
        self.email_settings = override_settings(
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
            DEFAULT_FROM_EMAIL="DigiFlow <no-reply@example.com>",
            PUBLIC_SITE_URL="https://crm.example.test",
            DEBUG=False,
        )
        self.email_settings.enable()
        self.addCleanup(self.email_settings.disable)

    def follow_up_payload(self, token=None, **overrides):
        token = token or secrets.token_urlsafe(32)
        values = {
            "lead_request": self.lead_request,
            "question_text": "Vui lòng chia sẻ thêm về nhu cầu.",
            "token_hash": hashlib.sha256(token.encode("utf-8")).hexdigest(),
            "status": LeadFollowUp.Status.SENT,
            "created_by": self.user,
            "sent_at": timezone.now(),
            "expires_at": timezone.now() + timedelta(days=2),
        }
        values.update(overrides)
        follow_up = LeadFollowUp.objects.create(**values)
        return follow_up, token

    def valid_response_payload(self, **overrides):
        return {
            "current_challenge": "Đang quản lý khách hàng bằng bảng tính.",
            "desired_outcome": "Tập trung lịch sử trao đổi.",
            "implementation_timing": LeadFollowUpResponse.ImplementationTiming.ONE_TO_THREE_MONTHS,
            "preferred_contact_time": "Buổi sáng",
            "ai_processing_consent": "",
            **overrides,
        }

    def test_staff_can_send_follow_up_email_and_create_activity(self):
        self.client.force_login(self.user)

        response = self.client.post(self.send_url, {
            "question_text": "Bạn có thể chia sẻ thêm về quy trình hiện tại không?",
        })

        self.assertRedirects(response, self.send_url)
        follow_up = LeadFollowUp.objects.get()
        self.assertEqual(follow_up.status, LeadFollowUp.Status.SENT)
        self.assertEqual(follow_up.created_by, self.user)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.customer.email])
        email_body = str(mail.outbox[0].body)
        self.assertIn("Bạn có thể chia sẻ thêm", email_body)
        self.assertTrue(mail.outbox[0].message().is_multipart())
        self.assertEqual(Interaction.objects.get().kind, Interaction.Kind.EMAIL)
        self.lead_request.refresh_from_db()
        self.assertEqual(self.lead_request.status, LeadRequest.Status.CONTACTED)

        token_match = re.search(r"/crm/bo-sung-thong-tin/([A-Za-z0-9_-]{43})/", email_body)
        if token_match is None:
            self.fail("Email không chứa link follow-up hợp lệ.")
        self.assertEqual(
            follow_up.token_hash,
            hashlib.sha256(token_match.group(1).encode("utf-8")).hexdigest(),
        )

    def test_follow_up_compose_page_requires_login(self):
        response = self.client.get(self.send_url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/django-admin/login/", response["Location"])

    def test_non_staff_user_cannot_send_follow_up_email(self):
        non_staff = User.objects.create_user(username="crm-customer", password="test-password-123")
        self.client.force_login(non_staff)

        response = self.client.post(self.send_url, {"question_text": "Không được phép gửi."})

        self.assertEqual(response.status_code, 302)
        self.assertIn("/django-admin/login/", response["Location"])
        self.assertFalse(LeadFollowUp.objects.exists())

    def test_email_failure_revokes_link_and_does_not_log_successful_contact(self):
        self.client.force_login(self.user)
        with self.assertLogs("crm.views", level="ERROR"):
            with patch("crm.views.EmailMultiAlternatives.send", side_effect=SMTPException("simulated failure")):
                response = self.client.post(self.send_url, {"question_text": "Cần bổ sung thông tin."})

        self.assertRedirects(response, self.send_url)
        follow_up = LeadFollowUp.objects.get()
        self.assertEqual(follow_up.status, LeadFollowUp.Status.FAILED)
        self.assertEqual(follow_up.token_hash, "")
        self.assertFalse(Interaction.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_customer_can_submit_response_once_and_it_is_saved_to_customer_timeline(self):
        follow_up, token = self.follow_up_payload()
        url = reverse("crm:lead_follow_up_reply", kwargs={"token": token})

        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, follow_up.question_text)
        self.assertEqual(page["Referrer-Policy"], "no-referrer")
        self.assertEqual(page["Cache-Control"], "max-age=0, no-cache, no-store, must-revalidate, private")

        response = self.client.post(url, self.valid_response_payload(ai_processing_consent="on"))

        self.assertRedirects(response, url)
        saved_response = LeadFollowUpResponse.objects.get(follow_up=follow_up)
        self.assertEqual(saved_response.current_challenge, "Đang quản lý khách hàng bằng bảng tính.")
        self.assertTrue(saved_response.ai_processing_consent)
        self.assertIsNotNone(saved_response.ai_processing_consent_at)
        self.assertEqual(saved_response.ai_processing_consent_version, "followup-v1")
        self.assertEqual(Interaction.objects.get().subject, "Khách hàng phản hồi form bổ sung")
        follow_up.refresh_from_db()
        self.assertEqual(follow_up.status, LeadFollowUp.Status.ANSWERED)
        self.assertIsNotNone(follow_up.responded_at)

        duplicate = self.client.post(url, self.valid_response_payload())
        self.assertEqual(duplicate.status_code, 200)
        self.assertContains(duplicate, "Cảm ơn bạn đã bổ sung thông tin")
        self.assertEqual(LeadFollowUpResponse.objects.count(), 1)

    def test_expired_link_is_rejected_and_marked_expired(self):
        follow_up, token = self.follow_up_payload(expires_at=timezone.now() - timedelta(minutes=1))

        response = self.client.get(reverse("crm:lead_follow_up_reply", kwargs={"token": token}))

        self.assertEqual(response.status_code, 410)
        self.assertContains(response, "Biểu mẫu không còn nhận phản hồi", status_code=410)
        follow_up.refresh_from_db()
        self.assertEqual(follow_up.status, LeadFollowUp.Status.EXPIRED)

    def test_invalid_or_revoked_link_does_not_expose_lead_data(self):
        self.assertEqual(
            self.client.get(reverse("crm:lead_follow_up_reply", kwargs={"token": "not-a-token"})).status_code,
            404,
        )
        follow_up, token = self.follow_up_payload(status=LeadFollowUp.Status.REVOKED)

        response = self.client.get(reverse("crm:lead_follow_up_reply", kwargs={"token": token}))

        self.assertEqual(response.status_code, 410)
        self.assertNotContains(response, self.customer.email, status_code=410)

    def test_staff_can_revoke_an_unanswered_response_link(self):
        follow_up, token = self.follow_up_payload()
        self.client.force_login(self.user)

        response = self.client.post(reverse(
            "crm:revoke_lead_follow_up",
            args=[self.lead_request.pk, follow_up.pk],
        ))

        self.assertRedirects(response, self.send_url)
        follow_up.refresh_from_db()
        self.assertEqual(follow_up.status, LeadFollowUp.Status.REVOKED)
        self.assertEqual(follow_up.token_hash, "")
        self.assertEqual(
            self.client.get(reverse("crm:lead_follow_up_reply", kwargs={"token": token})).status_code,
            404,
        )

    def test_sending_a_new_follow_up_invalidates_the_previous_open_link(self):
        old_follow_up, old_token = self.follow_up_payload()
        self.client.force_login(self.user)

        response = self.client.post(self.send_url, {"question_text": "Câu hỏi cập nhật."})

        self.assertRedirects(response, self.send_url)
        old_follow_up.refresh_from_db()
        self.assertEqual(old_follow_up.status, LeadFollowUp.Status.REVOKED)
        self.assertEqual(old_follow_up.token_hash, "")
        self.assertEqual(
            self.client.get(reverse("crm:lead_follow_up_reply", kwargs={"token": old_token})).status_code,
            404,
        )

    @override_settings(GEMINI_API_KEY="")
    def test_staff_can_analyze_consented_follow_up_even_if_initial_lead_was_not_consented(self):
        follow_up, _token = self.follow_up_payload()
        LeadFollowUpResponse.objects.create(
            follow_up=follow_up,
            current_challenge="Cần triển khai CRM trong thời gian tới.",
            ai_processing_consent=True,
            ai_processing_consent_at=timezone.now(),
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse("crm:analyze_customer", args=[self.customer.pk]))

        self.assertRedirects(response, reverse("crm:customer_detail", args=[self.customer.pk]))
        analysis = AIAnalysis.objects.get(customer=self.customer)
        self.assertEqual(analysis.provider, "rules")
        self.assertEqual(analysis.segment, Customer.Segment.POTENTIAL)

    def test_staff_cannot_analyze_when_initial_and_follow_up_consents_are_absent(self):
        follow_up, _token = self.follow_up_payload()
        LeadFollowUpResponse.objects.create(
            follow_up=follow_up,
            current_challenge="Cần triển khai CRM.",
            ai_processing_consent=False,
        )
        self.client.force_login(self.user)

        self.client.post(reverse("crm:analyze_customer", args=[self.customer.pk]))

        self.assertFalse(AIAnalysis.objects.exists())
