"""
Universal configuration module for pw_tester local CI/CD environment.
Dynamically introspects the host WordPress plugin.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from plugin_detector import PluginDetector

# Base paths
BASE_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = BASE_DIR.parent
TESTS_DIR = BASE_DIR / "tests"

# Load .env if present
load_dotenv(BASE_DIR / ".env")

# Introspect host plugin
DETECTOR = PluginDetector(PLUGIN_ROOT)
PLUGIN_INFO = DETECTOR.get_info()

# WordPress Site Configuration (e.g. Local by Flywheel or Docker instance)
WP_SITE_URL = os.getenv("WP_SITE_URL", "https://pquintanilla.local").rstrip("/")
WP_ADMIN_USER = os.getenv("WP_ADMIN_USER", "admin")
WP_ADMIN_PASS = os.getenv("WP_ADMIN_PASS", "password")

# WordPress Application Passwords (Usuarios > Perfil > Claves de Aplicación)
WP_APP_USERNAME = os.getenv("WP_APP_USERNAME", "")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "").strip()

# REST API & Plugin Secrets
PLUGIN_API_KEY = os.getenv("PLUGIN_API_KEY", "test_osa_secret_key_12345")
WP_REST_BASE = f"{WP_SITE_URL}/wp-json/osa/v1"


def get_wp_app_auth_header() -> dict:
    """Generates standard HTTP Basic Auth header for WordPress Application Passwords."""
    import base64
    if WP_APP_USERNAME and WP_APP_PASSWORD:
        token = base64.b64encode(f"{WP_APP_USERNAME}:{WP_APP_PASSWORD}".encode("utf-8")).decode("utf-8")
        return {"Authorization": f"Basic {token}"}
    return {}


# Mock LLM Server Configuration
MOCK_LLM_HOST = os.getenv("MOCK_LLM_HOST", "127.0.0.1")
MOCK_LLM_PORT = int(os.getenv("MOCK_LLM_PORT", "11435"))  # Dedicated mock port
MOCK_LLM_URL = f"http://{MOCK_LLM_HOST}:{MOCK_LLM_PORT}"

# PHP Binary auto-detection
DEFAULT_LOCAL_PHP = r"C:\Users\patri\AppData\Roaming\Local\lightning-services\php-8.2.29+0\bin\win64\php.exe"
PHP_EXECUTABLE = os.getenv("PHP_EXECUTABLE", DEFAULT_LOCAL_PHP if os.path.exists(DEFAULT_LOCAL_PHP) else "php")

# Playwright Browser Configuration
HEADLESS = os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes")
BROWSER_TIMEOUT = int(os.getenv("BROWSER_TIMEOUT", "15000"))
