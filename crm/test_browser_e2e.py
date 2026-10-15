import os
import unittest
import re
from datetime import timedelta
from io import StringIO
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core import mail
from django.core.management import call_command
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from django.utils import timezone
from django.test import override_settings

from .models import AIAnalysis, CareTask, Customer, Interaction, LeadRequest, LeadFollowUpResponse, LeadFollowUp


def launch_browser(playwright):
    engine = os.environ.get("CRM_E2E_BROWSER", "chromium")
    if engine not in {"chromium", "firefox", "webkit"}:
        raise ValueError("CRM_E2E_BROWSER must be chromium, firefox or webkit")
    return getattr(playwright, engine).launch()


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
            browser = launch_browser(playwright)
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
                page.locator(".btn-open-lead-modal").first.click()
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
                self.assertIn("crm/css/app.css", page.locator("link[rel='stylesheet']").get_attribute("href"))
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


@unittest.skipUnless(os.environ.get("RUN_BROWSER_E2E") == "1", "Set RUN_BROWSER_E2E=1 to run Chromium.")
@override_settings(GEMINI_API_KEY="", EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class CRMFeatureBrowserTests(StaticLiveServerTestCase):
    """Real browser checks against Django's isolated test database, including mobile."""

    def setUp(self):
        from playwright.sync_api import sync_playwright
        self.staff = get_user_model().objects.create_superuser("feature-e2e", password="test-only-password")
        call_command("seed_consultation_scenarios", "--analyze", "--rules-only", stdout=StringIO())
        self.customer = Customer.objects.get(email="scenario.crm-sales@consultation.test")
        self.lead = self.customer.lead_requests.get()
        self.output = Path("artifacts/e2e") / os.environ.get("CRM_E2E_BROWSER", "chromium")
        self.output.mkdir(parents=True, exist_ok=True)
        self.db_pool = ThreadPoolExecutor(max_workers=1)
        self.playwright = sync_playwright().start()
        self.browser = launch_browser(self.playwright)
        self.context = self.browser.new_context(viewport={"width": 1440, "height": 1000}, accept_downloads=True)
        self.context.tracing.start(screenshots=True, snapshots=True)
        self.page = self.context.new_page()
        self.page.set_default_timeout(10000)
        self.errors = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))

    def tearDown(self):
        self.page.screenshot(path=str(self.output / f"{self._testMethodName}.png"), full_page=True)
        self.context.tracing.stop(path=str(self.output / f"{self._testMethodName}.zip"))
        self.browser.close()
        self.playwright.stop()
        self.db_pool.shutdown()
        self.assertEqual(self.errors, [])

    def database(self, callback):
        return self.db_pool.submit(callback).result(timeout=10)

    def staff_login(self):
        self.database(lambda: self.client.force_login(self.staff))
        self.context.add_cookies([{"name": settings.SESSION_COOKIE_NAME,
            "value": self.client.cookies[settings.SESSION_COOKIE_NAME].value, "url": self.live_server_url}])

    def go(self, name, *args):
        response = self.page.goto(self.live_server_url + reverse(name, args=args), wait_until="networkidle")
        self.assertEqual(response.status, 200)
        return response

    def test_public_chat_context_clear_invalid_form_and_no_ai_consent(self):
        self.go("landing_page")
        self.page.locator('[data-tab="chat"]').first.click()
        self.page.locator("#chatInput").fill("Bên tôi có 3 kho và 2 quầy POS, cần kiểm kê bằng mã vạch")
        self.page.locator("#chatSubmitBtn").click()
        self.page.get_by_text("Nguồn: Tư vấn cục bộ", exact=False).first.wait_for()
        self.page.locator("#chatInput").fill("Chi phí bao nhiêu?")
        self.page.locator("#chatSubmitBtn").click()
        self.page.get_by_text("Hiện chưa có bảng giá được xác nhận", exact=False).wait_for()
        self.page.locator("#tabBtnForm").click()
        self.assertEqual(self.page.locator("#id_solution_interest").input_value(), "ERP")
        self.assertTrue(self.page.locator("#id_chat_history").input_value())
        self.page.locator("#btnClearAiContext").click()
        self.page.locator("#id_full_name").fill("Khách từ chối AI E2E")
        self.page.locator("#id_email").fill("invalid-email")
        self.page.locator("#id_request_text").fill("Muốn nhân viên tư vấn kho, không phân tích AI")
        self.page.get_by_role("button", name="Gửi thông tin cho đội ngũ").click()
        self.page.locator(".field-error").first.wait_for()
        self.page.wait_for_timeout(200)
        self.page.locator("#id_email").fill("no-ai-browser@example.test")
        self.page.locator("#id_consent").check()
        self.page.get_by_role("button", name="Gửi thông tin cho đội ngũ").click()
        self.page.get_by_role("heading", name="Cảm ơn bạn đã liên hệ").wait_for()
        customer = self.database(lambda: Customer.objects.get(email="no-ai-browser@example.test"))
        self.assertFalse(self.database(lambda: customer.lead_requests.get().ai_processing_consent))
        self.assertFalse(self.database(lambda: customer.interactions.filter(subject="Lịch sử trao đổi cùng Trợ lý AI").exists()))
        self.staff_login()
        self.go("crm:customer_detail", customer.pk)
        self.assertEqual(self.page.get_by_role("button", name="Phân tích ngay", exact=False).count(), 0)

    def test_staff_pages_mobile_reports_export_tasks_and_email_draft(self):
        self.staff_login()
        routes = [("crm:dashboard", []), ("crm:customers", []), ("crm:lead_requests", []),
                  ("crm:priority_customers", []), ("crm:care_tasks", []), ("crm:report", []),
                  ("crm:customer_detail", [self.customer.pk])]
        for width in (1440, 390):
            self.page.set_viewport_size({"width": width, "height": 1000 if width > 400 else 844})
            for name, args in routes:
                with self.subTest(width=width, route=name):
                    self.go(name, *args)
                    self.assertTrue(self.page.locator("h1").first.is_visible())
                    self.assertLessEqual(self.page.evaluate("document.documentElement.scrollWidth"), width + 2)
                    if name in ("crm:report", "crm:customer_detail"):
                        self.page.screenshot(path=str(self.output / f"{name.split(':')[1]}-{width}.png"), full_page=True)
        self.page.set_viewport_size({"width":1440,"height":1000})
        self.go("crm:customers")
        self.page.locator('input[name="q"]').fill("An Phúc")
        self.page.get_by_role("button", name="Tìm kiếm").click()
        self.page.wait_for_url(lambda url: "q=" in url)
        self.page.get_by_text("Phụ trách IT Sao Mai", exact=True).wait_for(state="detached")
        self.page.get_by_text("Phụ trách kinh doanh An Phúc", exact=True).wait_for()
        self.assertEqual(self.page.get_by_text("Phụ trách IT Sao Mai", exact=True).count(), 0)
        self.go("crm:customer_email_draft", self.customer.pk)
        before = self.database(lambda: self.customer.interactions.count())
        self.page.get_by_role("button", name="Tạo bản nháp").click()
        self.page.wait_for_function("document.querySelector('#id_draft')?.value.length > 40")
        self.assertGreater(len(self.page.locator("#id_draft").input_value()), 40)
        self.assertEqual(self.database(lambda: self.customer.interactions.count()), before)
        self.assertEqual(len(mail.outbox), 0)
        self.page.get_by_role("button", name="Tôi đã gửi email này", exact=False).click()
        self.page.wait_for_url("**/customers/*/")
        self.assertEqual(self.database(lambda: self.customer.interactions.count()), before + 1)
        self.go("crm:customer_care_task_create", self.customer.pk)
        self.page.locator("#id_title").fill("Gọi xác minh dữ liệu 12 sales")
        self.page.locator("#id_due_at").fill(timezone.localdate().isoformat())
        self.page.get_by_role("button", name="Tạo việc chăm sóc", exact=True).click()
        self.page.get_by_text("Gọi xác minh dữ liệu 12 sales", exact=True).wait_for()
        task = self.database(lambda: CareTask.objects.get(title="Gọi xác minh dữ liệu 12 sales"))
        self.go("crm:care_task_edit", task.pk)
        self.page.locator("#id_status").select_option("DONE")
        self.page.get_by_role("button", name="Lưu thay đổi").click()
        self.page.wait_for_url("**/viec/")
        self.database(task.refresh_from_db)
        self.assertIsNotNone(task.completed_at)
        self.go("crm:dashboard")
        self.assertEqual(self.page.get_by_text(task.title, exact=True).count(), 0)
        self.go("crm:report")
        self.page.get_by_role("button", name="Làm mới dữ liệu phân tích").click()
        self.page.get_by_text("Đã cập nhật phân tích:", exact=False).wait_for()
        self.assertTrue(self.page.evaluate("typeof echarts !== 'undefined'"))
        with self.page.expect_download() as downloaded:
            self.page.get_by_title("Tải ảnh PNG", exact=True).first.click()
        self.assertTrue(downloaded.value.suggested_filename.endswith(".png"))
        self.page.get_by_title("Xem to", exact=True).first.click()
        self.assertTrue(self.page.locator("#lightboxModal").is_visible())
        self.page.locator("#lightboxModal button").last.click()
        with self.page.expect_download() as downloaded:
            self.page.get_by_role("link", name="Xuất CSV", exact=True).click()
        self.assertTrue(downloaded.value.suggested_filename.endswith(".csv"))

    def test_follow_up_send_reply_once_revoke_and_expire(self):
        self.staff_login()
        with override_settings(PUBLIC_SITE_URL=self.live_server_url, DEBUG=True):
            self.go("crm:lead_follow_up", self.lead.pk)
            self.page.locator("#id_question_text").fill("Bạn có thể gửi mẫu cột dữ liệu và quy tắc phân công lead không?")
            self.page.get_by_role("button", name="Gửi email hỏi thêm").click()
            self.page.get_by_text("Đã gửi email đến", exact=False).wait_for()
            self.assertEqual(len(mail.outbox), 1)
            token = re.search(r"/crm/bo-sung-thong-tin/([\w-]{43})/", mail.outbox[0].body).group(1)
            self.go("crm:lead_follow_up_reply", token)
            self.page.locator("#id_current_challenge").fill("12 nhân viên đang dùng bảng tính, cần tập trung lịch sử chăm sóc")
            self.page.locator("#id_desired_outcome").fill("Giảm trùng khách và có lịch gọi rõ ràng")
            self.page.locator("#id_ai_processing_consent").check()
            self.page.get_by_role("button", name="Gửi thông tin bổ sung", exact=False).click()
            self.page.get_by_role("heading", name="Cảm ơn bạn đã bổ sung thông tin").wait_for()
            self.page.reload()
            self.assertEqual(self.page.locator("#id_current_challenge").count(), 0)
            self.assertEqual(self.database(lambda: LeadFollowUpResponse.objects.count()), 1)
            self.go("crm:lead_follow_up", self.lead.pk)
            self.page.locator("#id_question_text").fill("Bạn có thể xác nhận lịch khảo sát không?")
            self.page.get_by_role("button", name="Gửi email hỏi thêm").click()
            self.page.get_by_role("button", name="Thu hồi link").click()
            self.page.get_by_text("Đã thu hồi link", exact=False).wait_for()
            revoked = re.search(r"/crm/bo-sung-thong-tin/([\w-]{43})/", mail.outbox[-1].body).group(1)
            response = self.page.goto(self.live_server_url + reverse("crm:lead_follow_up_reply", args=[revoked]))
            self.assertEqual(response.status, 404)
            self.go("crm:lead_follow_up", self.lead.pk)
            self.page.locator("#id_question_text").fill("Xác nhận lại phạm vi thí điểm CRM")
            self.page.get_by_role("button", name="Gửi email hỏi thêm").click()
            self.page.get_by_role("button", name="Thu hồi link").wait_for()
            latest = self.database(lambda: LeadFollowUp.objects.filter(status="SENT").get())
            latest.expires_at = timezone.now() - timedelta(seconds=1)
            self.database(lambda: latest.save(update_fields=["expires_at"]))
            expired = re.search(r"/crm/bo-sung-thong-tin/([\w-]{43})/", mail.outbox[-1].body).group(1)
            response = self.page.goto(self.live_server_url + reverse("crm:lead_follow_up_reply", args=[expired]))
            self.assertEqual(response.status, 410)
            self.page.get_by_role("heading", name="Biểu mẫu không còn nhận phản hồi").wait_for()

    def test_wagtail_snippets_and_customer_create_edit(self):
        self.staff_login()
        for model in ("customer", "leadrequest", "interaction", "caretask", "aianalysis", "salesrecord"):
            self.go(f"wagtailsnippets_crm_{model}:list")
            self.assertTrue(self.page.locator("h1").first.is_visible())
        self.go("wagtailsnippets_crm_customer:add")
        self.page.locator("#id_full_name").fill("Khách hàng tạo từ Wagtail E2E")
        self.page.locator("#id_email").fill("wagtail-browser@example.test")
        self.page.locator("#id_company").fill("Công ty minh họa Wagtail")
        self.page.get_by_role("button", name="Lưu", exact=True).click()
        self.page.wait_for_url("**/admin/snippets/crm/customer/")
        customer = self.database(lambda: Customer.objects.get(email="wagtail-browser@example.test"))
        self.go("wagtailsnippets_crm_customer:edit", customer.pk)
        self.page.locator("#id_company").fill("Công ty đã cập nhật qua trình duyệt")
        self.page.get_by_role("button", name="Lưu", exact=True).click()
        self.page.wait_for_url("**/admin/snippets/crm/customer/")
        self.database(customer.refresh_from_db)
        self.assertEqual(customer.company, "Công ty đã cập nhật qua trình duyệt")
