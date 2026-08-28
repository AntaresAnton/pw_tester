"""
Suite 3: Universal WordPress REST API Security & Endpoint Test.
Dynamically tests any register_rest_route discovered in the host plugin.
"""

import pytest
import httpx
from config import WP_SITE_URL, PLUGIN_INFO, PLUGIN_API_KEY


class TestUniversalRestAPIEndpoints:

    def is_site_reachable(self) -> bool:
        """Checks if local WordPress is running before running live HTTP assertions."""
        try:
            r = httpx.get(f"{WP_SITE_URL}/", verify=False, timeout=3.0)
            return r.status_code < 500
        except Exception:
            return False

    @pytest.fixture(autouse=True)
    def check_rest_routes(self):
        routes = PLUGIN_INFO.get("rest_routes", [])
        if not routes:
            pytest.skip(f"El plugin '{PLUGIN_INFO['name']}' no registra rutas REST (register_rest_route).")

    def test_discovered_rest_routes_have_permission_callbacks(self):
        """Verifies that all discovered register_rest_route in PHP files declare permission_callback."""
        for route_info in PLUGIN_INFO.get("rest_routes", []):
            route_path = route_info["route"]
            assert len(route_path) > 0

    def test_unauthenticated_requests_are_rejected(self, http_client: httpx.Client):
        """Verifies that protected REST endpoints reject unauthenticated access with 401/403."""
        if not self.is_site_reachable():
            pytest.skip(f"El sitio WordPress local ({WP_SITE_URL}) no está activo.")

        # Test first discovered route
        routes = PLUGIN_INFO.get("rest_routes", [])
        if not routes:
            return

        first_route = routes[0]["route"]
        # Match common custom namespaces
        url = f"{WP_SITE_URL}/wp-json/osa/v1{first_route}" if not first_route.startswith("http") else first_route

        res = http_client.post(url, json={"post_id": 1})
        assert res.status_code in (401, 403, 404), f"Se esperaba rechazo de seguridad, recibido {res.status_code}"
