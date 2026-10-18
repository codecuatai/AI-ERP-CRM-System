"""Read-only browser checks of live Docker CRM/Superset; only temporary sessions are created."""

import json
from pathlib import Path
import subprocess

from playwright.sync_api import sync_playwright


def docker_python(code):
    return subprocess.run(
        ["docker", "compose", "exec", "-T", "crm-web", "python", "manage.py", "shell", "-c", code],
        check=True, capture_output=True, text=True, encoding="utf-8",
    ).stdout.strip().splitlines()[-1]


def main():
    output = Path("artifacts/report-embedding")
    output.mkdir(parents=True, exist_ok=True)
    session_id = docker_python(
        "from django.test import Client; from django.contrib.auth import get_user_model; "
        "u=get_user_model().objects.filter(is_superuser=True,is_active=True).first(); "
        "assert u is not None; c=Client(); c.force_login(u); print(c.cookies['sessionid'].value)"
    )
    results = []
    try:
        other_id = int(docker_python(
            "from crm.services.superset_embed import superset_api; "
            "print(superset_api()._request('/api/v1/dashboard/crm-analytics-dashboard')['result']['id'])"
        ))
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            for host in ("localhost", "127.0.0.1"):
                context = browser.new_context(viewport={"width": 1440, "height": 1000})
                context.add_cookies([{"name": "sessionid", "value": session_id, "url": f"http://{host}:8000", "httpOnly": True, "sameSite": "Lax"}])
                page = context.new_page()
                # Accelerate only the first five-minute renewal timer in the
                # host page. Backend JWT expiry/authorization remain unchanged.
                page.add_init_script("""(() => {
                  if (window !== window.top) return;
                  const schedule = window.setTimeout.bind(window);
                  let accelerated = false;
                  window.setTimeout = (callback, delay, ...args) => {
                    if (!accelerated && delay > 200000 && delay < 310000) {
                      accelerated = true; delay = 100;
                    }
                    return schedule(callback, delay, ...args);
                  };
                })();""")
                errors, chart_statuses, session_statuses = [], [], []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("response", lambda response: chart_statuses.append(response.status) if "/api/v1/chart/" in response.url and "/data" in response.url else None)
                page.on("response", lambda response: session_statuses.append(response.status) if "/crm/bao-cao/superset-session/" in response.url else None)
                page.goto(f"http://{host}:8000/crm/bao-cao/", wait_until="networkidle")
                guest = context.request.get(f"http://{host}:8000/crm/bao-cao/superset-session/").json()
                denied = context.request.get(guest["domain"] + f"/api/v1/dashboard/{other_id}", headers={"X-GuestToken": guest["token"]})
                assert denied.status in (403, 404), "Guest token must not grant another dashboard"
                denied_origin = context.request.get(guest["domain"] + "/embedded/" + guest["id"], headers={"Referer": "http://untrusted.example/"})
                assert denied_origin.status == 403, "Untrusted embedding origin must be refused"
                page.locator("#tab-btn-superset-live").click()
                page.wait_for_function("document.getElementById('supersetEmbedStatus').textContent.startsWith('Đã kết nối')", timeout=80000)
                page.locator("#supersetEmbedMount").scroll_into_view_if_needed()
                frame = page.frame_locator("#supersetEmbedMount iframe")
                frame.locator(".dashboard-component-chart-holder").first.wait_for(timeout=30000)
                # Wait for actual chart queries, rather than only a loaded iframe.
                for _ in range(60):
                    if len(chart_statuses) >= 8:
                        break
                    page.wait_for_timeout(1000)
                assert len(chart_statuses) >= 8 and all(status == 200 for status in chart_statuses), chart_statuses
                assert len(session_statuses) >= 2 and all(status == 200 for status in session_statuses), "Automatic token renewal failed"
                frame_errors = frame.locator('.ant-alert-error:visible, .alert-danger:visible').all_text_contents()
                assert not [error for error in frame_errors if error.strip()], frame_errors
                assert not errors, errors
                assert page.locator("#tab-content-superset-live").get_by_role("heading", name="Phân tích biểu đồ và gợi ý chăm sóc").is_visible()
                page.locator("#supersetEmbedMount").scroll_into_view_if_needed()
                page.screenshot(path=str(output / f"{host}-dashboard.png"))
                page.locator("#tab-content-superset-live").get_by_role("heading", name="Phân tích biểu đồ và gợi ý chăm sóc").scroll_into_view_if_needed()
                page.screenshot(path=str(output / f"{host}-analysis.png"))
                page.reload(wait_until="networkidle")
                assert page.locator("#tab-content-superset-live").is_visible(), "Selected tab was not remembered"
                page.wait_for_function("document.getElementById('supersetEmbedStatus').textContent.startsWith('Đã kết nối')", timeout=80000)
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "Mobile page overflows"
                page.screenshot(path=str(output / f"{host}-mobile.png"))
                # Simulate a token-service outage without stopping any live service.
                page.route("**/crm/bao-cao/superset-session/", lambda route: route.fulfill(status=503, content_type="application/json", body='{"error":"unavailable"}'))
                page.locator("#supersetEmbedRetry").click()
                page.wait_for_function("document.getElementById('supersetEmbedStatus').textContent.startsWith('Chưa tải được')")
                assert page.locator("#supersetEmbedMount iframe").count() == 0
                assert page.locator("#supersetLocalFallback").is_visible()
                assert page.locator("#supersetLocalFallback canvas").count() == 6
                results.append({"origin": host, "chart_queries": len(chart_statuses), "all_queries_ok": True, "independent_superset_login": False, "remembered_tab": True, "outage_fallback": True, "mobile_overflow": False, "unrelated_dashboard_denied": True, "untrusted_origin_denied": True, "automatic_renewal_accelerated_timer": True})
                context.close()
            browser.close()
    finally:
        # The session ID is captured in memory only and is never logged or saved.
        docker_python("from django.contrib.sessions.models import Session; Session.objects.filter(session_key=" + repr(session_id) + ").delete(); print('session removed')")
    (output / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    main()
