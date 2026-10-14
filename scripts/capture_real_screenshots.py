"""Automated script to capture high-definition real screenshots of DigiFlow CRM & Superset."""

import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

DOCS_IMG_DIR = Path(__file__).resolve().parent.parent / "docs" / "images"
DOCS_IMG_DIR.mkdir(parents=True, exist_ok=True)

def run():
    print(f"==> Lưu ảnh chụp vào: {DOCS_IMG_DIR}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1.5)
        page = context.new_page()

        # 1. ĐĂNG NHẬP DJANGO CRM
        print("1. Đang đăng nhập CRM...")
        try:
            page.goto("http://127.0.0.1:8000/admin/login/?next=/crm/", timeout=15000)
            page.fill('input[name="username"]', "admin")
            page.fill('input[name="password"]', "admin")
            page.click('button[type="submit"]')
            page.wait_for_url("**/crm/", timeout=15000)
            time.sleep(1.5)

            # Chụp Dashboard
            print("2. Chụp Dashboard CRM Cockpit...")
            page.screenshot(path=str(DOCS_IMG_DIR / "01-dashboard-cockpit.png"), full_page=True)
            print("   ✔ Đã lưu: 01-dashboard-cockpit.png")

            # Chụp Báo cáo CRM
            print("3. Chụp Trang Báo cáo Trực quan hóa CRM & Superset...")
            page.goto("http://127.0.0.1:8000/crm/bao-cao/", timeout=15000)
            time.sleep(2.5) # Chờ ECharts vẽ xong
            page.screenshot(path=str(DOCS_IMG_DIR / "02-crm-report-studio.png"), full_page=True)
            print("   ✔ Đã lưu: 02-crm-report-studio.png")

            # Chụp từng card biểu đồ ECharts
            charts = [
                ("chartLeadTier", "chart-01-lead-winrate-tier.png"),
                ("chartSolutions", "chart-02-expected-won-solutions.png"),
                ("chartForecast", "chart-03-prophet-revenue-forecast.png"),
                ("chartSentimentChurn", "chart-04-sentiment-churn-risk.png"),
                ("chartRfm", "chart-05-kmeans-rfm-clusters.png"),
                ("chartXai", "chart-06-explainable-ai-features.png"),
            ]
            for element_id, filename in charts:
                try:
                    el = page.query_selector(f"#{element_id}")
                    if el:
                        parent_card = el.evaluate_handle('el => el.closest("article")')
                        if parent_card:
                            parent_card.screenshot(path=str(DOCS_IMG_DIR / filename))
                            print(f"   ✔ Đã lưu biểu đồ: {filename}")
                except Exception as e:
                    print(f"   ⚠ Lỗi chụp {element_id}: {e}")

        except Exception as e:
            print(f"   ⚠ Lỗi CRM: {e}")

        # 2. ĐĂNG NHẬP VÀO APACHE SUPERSET
        print("4. Đang đăng nhập Apache Superset (cổng 18088)...")
        try:
            page.goto("http://127.0.0.1:18088/login/", timeout=20000)
            page.wait_for_selector('input[type="password"]', timeout=15000)
            
            # Find inputs
            inputs = page.query_selector_all('input')
            for inp in inputs:
                inp_type = inp.get_attribute('type')
                inp_name = inp.get_attribute('name') or ''
                if inp_type in ('text', None) or 'user' in inp_name:
                    inp.fill('admin')
                elif inp_type == 'password' or 'pass' in inp_name:
                    inp.fill('admin')
            
            submit_btn = page.query_selector('button[type="submit"], input[type="submit"], .btn-primary')
            if submit_btn:
                submit_btn.click()
            time.sleep(3)

            # Chụp Dashboard AI Intelligence
            print("5. Chụp Dashboard Superset AI Intelligence...")
            page.goto("http://127.0.0.1:18088/superset/dashboard/crm-ai-intelligence-dashboard/", timeout=30000)
            time.sleep(6) # Chờ Superset render các slice
            page.screenshot(path=str(DOCS_IMG_DIR / "03-superset-ai-intelligence-dashboard.png"), full_page=True)
            print("   ✔ Đã lưu: 03-superset-ai-intelligence-dashboard.png")

            # Chụp Dashboard Tổng hợp Kinh doanh
            print("6. Chụp Dashboard Superset CRM Analytics...")
            page.goto("http://127.0.0.1:18088/superset/dashboard/crm-analytics-dashboard/", timeout=30000)
            time.sleep(5)
            page.screenshot(path=str(DOCS_IMG_DIR / "04-superset-crm-analytics-dashboard.png"), full_page=True)
            print("   ✔ Đã lưu: 04-superset-crm-analytics-dashboard.png")

        except Exception as e:
            print(f"   ⚠ Lỗi Superset: {e}")

        browser.close()
        print("==> HOÀN THÀNH CHỤP ẢNH MINH CHỨNG TOÀN DIỆN!")

if __name__ == "__main__":
    run()
