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
                errors, chart_statuses = [], []
                phase = {"name": "initial"}
                page.on("pageerror", lambda error: errors.append({"message": str(error), "stack": error.stack, "phase": phase["name"]}))
                page.on("response", lambda response: chart_statuses.append(response.status) if "/api/v1/chart/" in response.url and "/data" in response.url else None)
                page.goto(f"http://{host}:8000/crm/bao-cao/", wait_until="domcontentloaded")
                guest = context.request.get(f"http://{host}:8000/crm/bao-cao/superset-session/").json()
                assert len(guest["widgets"]) == 8
                denied = context.request.get(guest["domain"] + f"/api/v1/dashboard/{other_id}", headers={"X-GuestToken": guest["token"]})
                assert denied.status in (403, 404), "Guest token must not grant another dashboard"
                denied_origin = context.request.get(guest["domain"] + "/embedded/" + guest["widgets"][0]["id"], headers={"Referer": "http://untrusted.example/"})
                assert denied_origin.status == 403
                assert page.locator("#tab-btn-charts").count() == 0
                page.locator("#tab-btn-superset-live").click()
                cards = page.locator(".live-chart-card")
                assert cards.count() == 8
                for i in range(8):
                    card = cards.nth(i)
                    card.scroll_into_view_if_needed()
                    card.locator('[data-chart-source]').filter(has_text="Superset trực tiếp").wait_for(timeout=60000)
                    frame = card.frame_locator("iframe")
                    frame.locator(".dashboard-component-chart-holder").first.wait_for(timeout=30000)
                    analysis = card.locator(".chart-analysis")
                    assert analysis.count() == 1
                    assert analysis.bounding_box()["y"] >= card.locator(".superset-chart-mount").bounding_box()["y"] + 420
                    assert analysis.locator("p").inner_text().strip()
                    assert not frame.locator('.ant-alert-error:visible, .alert-danger:visible').all_text_contents()
                assert len(chart_statuses) >= 8 and all(status == 200 for status in chart_statuses), chart_statuses
                cards.first.scroll_into_view_if_needed()
                cards.first.frame_locator('iframe').locator('canvas').first.wait_for()
                page.wait_for_timeout(1100)
                page.screenshot(path=str(output / f"{host}-unified.png"))
                phase["name"] = "reload"
                page.reload(wait_until="domcontentloaded")
                assert page.locator("#tab-content-superset-live").is_visible()
                cards.first.scroll_into_view_if_needed()
                cards.first.locator('[data-chart-source]').filter(has_text="Superset trực tiếp").wait_for(timeout=60000)
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "Mobile page overflows"
                cards.first.scroll_into_view_if_needed()
                page.screenshot(path=str(output / f"{host}-unified-mobile.png"))
                phase["name"] = "outage"
                page.route("**/crm/bao-cao/superset-session/", lambda route: route.fulfill(status=503, content_type="application/json", body='{"error":"unavailable"}'))
                page.locator("#supersetEmbedRetry").click()
                page.wait_for_load_state("domcontentloaded")
                for i in range(8):
                    card = cards.nth(i)
                    card.scroll_into_view_if_needed()
                    card.locator('[data-chart-source]').filter(has_text="Superset gián đoạn").wait_for(timeout=15000)
                    assert card.locator(".local-chart-fallback canvas").count() == 1
                    assert card.locator(".chart-analysis").is_visible()
                assert not errors, errors
                results.append({"origin": host, "chart_queries": len(chart_statuses), "all_queries_ok": True, "live_cards":8, "analysis_below_each_chart":True, "legacy_chart_tab_removed":True, "independent_superset_login": False, "remembered_tab": True, "outage_fallback": True, "mobile_overflow": False, "unrelated_dashboard_denied": True, "untrusted_origin_denied": True})
                context.close()
            browser.close()
    finally:
        docker_python("from django.contrib.sessions.models import Session; Session.objects.filter(session_key=" + repr(session_id) + ").delete(); print('session removed')")
    (output / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    main()
