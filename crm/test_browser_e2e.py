import os
import unittest

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from django.utils import timezone
from django.test import override_settings

from .models import AIAnalysis, CareTask, Customer


@unittest.skipUnless(
    os.environ.get("RUN_BROWSER_E2E") == "1",
    "Set RUN_BROWSER_E2E=1 and install Chromium to run browser E2E tests.",
)
@override_settings(
    GEMINI_API_KEY="",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    PUBLIC_CONTACT_EMAIL="demo-contact@digiflow.test",
    PUBLIC_PRIVACY_EMAIL="privacy@digiflow.test",
)
class CRMBrowserEndToEndTests(StaticLiveServerTestCase):
    """Exercise the public-to-staff CRM journey in a real isolated browser."""

    def test_public_lead_can_be_analyzed_and_turned_into_a_care_task(self):
        from playwright.sync_api import sync_playwright

        staff = get_user_model().objects.create_superuser(
            username="browser-e2e-staff",
            email="browser-e2e@example.test",
            password="browser-e2e-password-only",
        )
        self.assertTrue(staff.is_superuser)

        browser_errors = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda error: browser_errors.append(str(error)))
            try:
                page.goto(f"{self.live_server_url}/", wait_until="networkidle")
                page.get_by_text("Email minh họa — không nhận thư").wait_for()
                page.goto(f"{self.live_server_url}{reverse('privacy_notice')}")
                page.get_by_role("navigation", name="Mục lục thông báo quyền riêng tư").wait_for()
                page.get_by_role("link", name="AI và Google").click()
                self.assertTrue(page.url.endswith("#ai"))

                page.goto(f"{self.live_server_url}/")
                page.locator("#id_full_name").fill("Nguyễn Minh Anh E2E")
                page.locator("#id_email").fill("minhanh-browser-e2e@example.test")
                page.locator("#id_company").fill("Doanh nghiệp E2E")
                page.locator("#id_solution_interest").select_option("CRM")
                page.locator("#id_request_text").fill(
                    "Đội ngũ muốn quản lý cơ hội CRM và cần tư vấn demo."
                )
                page.locator("#id_consent").check()
                page.locator("#id_ai_processing_consent").check()
                page.get_by_role("button", name="Gửi thông tin cho đội ngũ").click()
                page.get_by_role("heading", name="Cảm ơn bạn đã liên hệ").wait_for()

                page.goto(f"{self.live_server_url}/crm/")
                page.get_by_label("Tên đăng nhập").fill("browser-e2e-staff")
                page.get_by_label("Mật khẩu").fill("browser-e2e-password-only")
                page.get_by_role("button", name="Đăng nhập").click()
                page.get_by_role("heading", name="Chào browser-e2e-staff.").wait_for()
                # The dashboard heading can appear before the stylesheet finishes loading
                # on slower CI runners; wait before asserting computed layout styles.
                page.wait_for_load_state("networkidle")
                page.set_viewport_size({"width": 1920, "height": 937})
                self.assertIn("v=20260928", page.locator("link[rel='stylesheet']").get_attribute("href"))
                self.assertEqual(
                    page.locator(".sidebar").evaluate("element => getComputedStyle(element).backgroundColor"),
                    "rgb(2, 6, 23)",
                )
                self.assertLessEqual(
                    page.locator(".dashboard-hero").evaluate("element => element.getBoundingClientRect().top"),
                    100,
                )

                page.set_viewport_size({"width": 390, "height": 844})
                page.get_by_role("button", name="Mở menu").click()
                self.assertTrue(page.locator("#mobileMenu").is_visible())
                self.assertTrue(page.locator("#mobileOverlay").is_visible())
                self.assertEqual(page.locator("#openMobileMenu").get_attribute("aria-expanded"), "true")
                page.get_by_role("button", name="Đóng menu").last.click()
                self.assertFalse(page.locator("#mobileMenu").is_visible())
                self.assertEqual(page.locator("#openMobileMenu").get_attribute("aria-expanded"), "false")

                page.goto(f"{self.live_server_url}{reverse('crm:lead_requests')}")
                page.get_by_text("Nguyễn Minh Anh E2E", exact=True).wait_for()
                page.get_by_role("link", name="Mở hồ sơ").click()
                page.get_by_role("button", name="Phân tích ngay").click()
                page.get_by_text("Nguồn: Phân tích cục bộ").wait_for()
                page.get_by_role("link", name="Tạo việc từ đề xuất này").click()

                task_title = "Gọi tư vấn CRM từ E2E"
                page.locator("#id_title").fill(task_title)
                page.locator("#id_due_at").fill(timezone.localdate().isoformat())
                page.get_by_role("button", name="Tạo việc chăm sóc").click()
                page.get_by_text(task_title, exact=True).wait_for()

            finally:
                browser.close()

        customer = Customer.objects.get(email="minhanh-browser-e2e@example.test")
        self.assertTrue(AIAnalysis.objects.filter(customer=customer, provider="rules").exists())
        self.assertTrue(CareTask.objects.filter(customer=customer, title=task_title).exists())
        self.assertEqual(browser_errors, [])
