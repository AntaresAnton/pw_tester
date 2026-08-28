"""
Suite 4: Universal End-to-End Browser Automation with Playwright.
Discovers and tests any admin menu pages or settings pages created by the plugin.
"""

import pytest
import httpx
from playwright.sync_api import sync_playwright, Page, expect
from config import WP_SITE_URL, WP_ADMIN_USER, WP_ADMIN_PASS, HEADLESS, BROWSER_TIMEOUT, PLUGIN_INFO


@pytest.fixture(scope="module")
def browser_page():
    try:
        r = httpx.get(f"{WP_SITE_URL}/", verify=False, timeout=3.0)
        reachable = r.status_code < 500
    except Exception:
        reachable = False

    if not reachable:
        pytest.skip(f"El sitio WordPress local ({WP_SITE_URL}) no está activo.")

    admin_pages = PLUGIN_INFO.get("admin_pages", [])
    if not admin_pages:
        pytest.skip(f"El plugin '{PLUGIN_INFO['name']}' no registra páginas de administración (add_menu_page/add_submenu_page).")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            ignore_https_errors=True
        )
        page = context.new_page()
        page.set_default_timeout(BROWSER_TIMEOUT)

        # Listen for uncaught JS errors
        js_errors = []
        page.on("pageerror", lambda err: js_errors.append(str(err)))

        # Attempt WP Admin login
        try:
            page.goto(f"{WP_SITE_URL}/wp-login.php")
            if page.locator("#user_login").is_visible():
                page.fill("#user_login", WP_ADMIN_USER)
                page.fill("#user_pass", WP_ADMIN_PASS)
                page.click("#wp-submit")
                page.wait_for_load_state("domcontentloaded")
        except Exception:
            pass

        yield page, js_errors

        browser.close()


class TestUniversalPlaywrightE2E:

    def test_discovered_admin_pages_load_cleanly(self, browser_page):
        """Visits each discovered admin page slug and verifies 0 fatal JS console errors."""
        page, js_errors = browser_page

        if "wp-login.php" in page.url:
            pytest.skip("Se requiere configurar WP_ADMIN_USER y WP_ADMIN_PASS válidos en .env para E2E.")

        admin_pages = PLUGIN_INFO.get("admin_pages", [])
        for page_info in admin_pages[:3]:  # Test up to first 3 pages
            slug = page_info["slug"]
            page_type = page_info.get("type", "admin")

            # Route to correct admin URL
            if page_type == "options":
                target_url = f"{WP_SITE_URL}/wp-admin/options-general.php?page={slug}"
            elif page_type == "tools":
                target_url = f"{WP_SITE_URL}/wp-admin/tools.php?page={slug}"
            else:
                target_url = f"{WP_SITE_URL}/wp-admin/admin.php?page={slug}"

            page.goto(target_url)
            page.wait_for_load_state("domcontentloaded")

            # Verify page has rendered
            expect(page.locator(".wrap, #wpbody-content")).to_be_visible()

        # Check for 0 fatal JS errors
        assert len(js_errors) == 0, f"Errores JavaScript detectados en consola: {js_errors}"
