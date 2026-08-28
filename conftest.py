"""
Pytest global fixtures for pw_tester.
"""

import sys
import subprocess
import time
import pytest
import httpx
from config import BASE_DIR, MOCK_LLM_HOST, MOCK_LLM_PORT, MOCK_LLM_URL, WP_SITE_URL, PLUGIN_API_KEY


@pytest.fixture(scope="session")
def mock_server():
    """Spawns the background Mock LLM Server if not already running."""
    # Check if already running
    try:
        r = httpx.get(f"{MOCK_LLM_URL}/", timeout=1.0)
        if r.status_code == 200:
            yield MOCK_LLM_URL
            return
    except Exception:
        pass

    # Start using subprocess
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "mock_llm_server:app", "--host", MOCK_LLM_HOST, "--port", str(MOCK_LLM_PORT), "--log-level", "warning"],
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(1.2)  # Wait for server startup

    yield MOCK_LLM_URL

    proc.terminate()
    try:
        proc.wait(timeout=2.0)
    except Exception:
        proc.kill()


@pytest.fixture
def http_client():
    """Sync HTTP client for testing endpoints."""
    with httpx.Client(follow_redirects=True, verify=False, timeout=15.0) as client:
        yield client


@pytest.fixture
def auth_headers():
    """Headers with secret API key or WordPress Application Password for REST API tests."""
    from config import get_wp_app_auth_header
    headers = {
        "X-OSA-API-Key": PLUGIN_API_KEY,
        "Content-Type": "application/json"
    }
    app_auth = get_wp_app_auth_header()
    if app_auth:
        headers.update(app_auth)
    return headers
