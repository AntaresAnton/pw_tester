"""
Universal WordPress Plugin Discovery & Feature Extraction Engine.
Automatically detects plugin metadata, hooks, AJAX actions, REST routes,
admin menu slugs, and architectural patterns for ANY WordPress plugin.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


class PluginDetector:
    """Introspects the parent directory to dynamically analyze any WordPress plugin."""

    def __init__(self, plugin_dir: Path):
        self.plugin_dir = plugin_dir
        self._info: Optional[Dict[str, Any]] = None

    def get_info(self) -> Dict[str, Any]:
        """Extracts complete metadata and discovered features from the plugin."""
        if self._info is not None:
            return self._info

        main_file = self.find_main_plugin_file()
        metadata = self.parse_plugin_headers(main_file) if main_file else {}
        php_files = self.get_all_php_files()

        ajax_actions = self.discover_ajax_actions(php_files)
        rest_routes = self.discover_rest_routes(php_files)
        admin_pages = self.discover_admin_pages(php_files)
        has_llm = self.detect_ai_capabilities(php_files)
        has_woocommerce = self.detect_woocommerce_features(php_files)

        self._info = {
            "plugin_dir": str(self.plugin_dir),
            "folder_name": self.plugin_dir.name,
            "main_file": str(main_file.relative_to(self.plugin_dir)) if main_file else None,
            "main_file_path": main_file,
            "name": metadata.get("name", self.plugin_dir.name.replace("-", " ").title()),
            "version": metadata.get("version", "1.0.0"),
            "author": metadata.get("author", "Unknown"),
            "text_domain": metadata.get("text_domain", self.plugin_dir.name),
            "requires_php": metadata.get("requires_php", "7.4"),
            "tested_up_to": metadata.get("tested_up_to", "6.7"),
            "php_files_count": len(php_files),
            "ajax_actions": ajax_actions,
            "rest_routes": rest_routes,
            "admin_pages": admin_pages,
            "has_llm": has_llm,
            "has_woocommerce": has_woocommerce,
        }
        return self._info

    def get_all_php_files(self) -> List[Path]:
        """Collects all PHP files excluding testing directories and vendor packages."""
        files = []
        for p in self.plugin_dir.rglob("*.php"):
            parts = p.parts
            if any(x in parts for x in ("pw_tester", "node_modules", "vendor", ".git", "tests")):
                continue
            files.append(p)
        return sorted(files)

    def find_main_plugin_file(self) -> Optional[Path]:
        """Locates the primary PHP file containing the standard 'Plugin Name:' header."""
        # 1. Check direct PHP files in root directory
        for p in sorted(self.plugin_dir.glob("*.php")):
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")[:3000]
                if "Plugin Name:" in content:
                    return p
            except Exception:
                continue

        # 2. Fallback: Check subdirectories if plugin has unconventional structure
        for p in self.plugin_dir.rglob("*.php"):
            if "pw_tester" in p.parts or "vendor" in p.parts:
                continue
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")[:3000]
                if "Plugin Name:" in content:
                    return p
            except Exception:
                continue

        return None

    def parse_plugin_headers(self, main_file: Optional[Path]) -> Dict[str, str]:
        """Parses standard WordPress plugin headers from comment docblock."""
        if not main_file or not main_file.exists():
            return {}

        headers = {
            "name": "",
            "version": "",
            "author": "",
            "text_domain": "",
            "requires_php": "",
            "tested_up_to": "",
            "description": "",
        }

        try:
            content = main_file.read_text(encoding="utf-8", errors="ignore")[:4000]

            name_match = re.search(r"Plugin Name:\s*(.+)", content, re.IGNORECASE)
            if name_match:
                headers["name"] = name_match.group(1).strip()

            ver_match = re.search(r"Version:\s*([0-9\.\-a-zA-Z]+)", content, re.IGNORECASE)
            if ver_match:
                headers["version"] = ver_match.group(1).strip()

            author_match = re.search(r"Author:\s*(.+)", content, re.IGNORECASE)
            if author_match:
                headers["author"] = author_match.group(1).strip()

            domain_match = re.search(r"Text Domain:\s*([a-zA-Z0-9\-_]+)", content, re.IGNORECASE)
            if domain_match:
                headers["text_domain"] = domain_match.group(1).strip()

            req_php_match = re.search(r"Requires PHP:\s*([0-9\.]+)", content, re.IGNORECASE)
            if req_php_match:
                headers["requires_php"] = req_php_match.group(1).strip()

            tested_match = re.search(r"Tested up to:\s*([0-9\.]+)", content, re.IGNORECASE)
            if tested_match:
                headers["tested_up_to"] = tested_match.group(1).strip()

        except Exception:
            pass

        return headers

    def discover_ajax_actions(self, php_files: List[Path]) -> List[Dict[str, Any]]:
        """Finds all add_action('wp_ajax_...') declarations in PHP codebase."""
        actions = []
        for f in php_files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                matches = re.findall(r"add_action\s*\(\s*['\"]wp_ajax_([a-zA-Z0-9_\-]+)['\"]\s*,\s*([^,\)]+)", content)
                for action_name, callback in matches:
                    actions.append({
                        "action": action_name.strip(),
                        "callback": callback.strip(),
                        "file": str(f.relative_to(self.plugin_dir)),
                        "has_nopriv": f"wp_ajax_nopriv_{action_name}" in content
                    })
            except Exception:
                continue
        return actions

    def discover_rest_routes(self, php_files: List[Path]) -> List[Dict[str, Any]]:
        """Finds all register_rest_route(...) declarations in PHP codebase."""
        routes = []
        for f in php_files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                matches = re.finditer(r"register_rest_route\s*\(\s*([^,]+)\s*,\s*['\"]([^'\"]+)['\"]\s*,", content)
                for m in matches:
                    ns_expr = m.group(1).strip().replace("self::NAMESPACE", "").strip("'\"")
                    route_path = m.group(2).strip()
                    routes.append({
                        "namespace_expr": ns_expr,
                        "route": route_path,
                        "file": str(f.relative_to(self.plugin_dir))
                    })
            except Exception:
                continue
        return routes

    def discover_admin_pages(self, php_files: List[Path]) -> List[Dict[str, str]]:
        """Finds admin menu pages created via add_menu_page, add_options_page, etc."""
        pages = []
        for f in php_files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                # Pattern for menu slugs
                patterns = [
                    (r"add_menu_page\s*\([^,]+,[^,]+,[^,]+,\s*['\"]([^'\"]+)['\"]", "menu"),
                    (r"add_submenu_page\s*\([^,]+,[^,]+,[^,]+,[^,]+,\s*['\"]([^'\"]+)['\"]", "submenu"),
                    (r"add_options_page\s*\([^,]+,[^,]+,[^,]+,\s*['\"]([^'\"]+)['\"]", "options"),
                    (r"add_management_page\s*\([^,]+,[^,]+,[^,]+,\s*['\"]([^'\"]+)['\"]", "tools"),
                ]
                for pat, page_type in patterns:
                    for slug in re.findall(pat, content):
                        pages.append({
                            "slug": slug.strip(),
                            "type": page_type,
                            "file": str(f.relative_to(self.plugin_dir))
                        })
            except Exception:
                continue
        return pages

    def detect_ai_capabilities(self, php_files: List[Path]) -> bool:
        """Detects if the plugin interfaces with LLMs or AI providers."""
        ai_patterns = (
            r"\bollama\b",
            r"\bopenai\b",
            r"\bgroq\b",
            r"\btogether\.ai\b",
            r"\bapi\.together\b",
            r"\banthropic\b",
            r"\bgemini\b",
            r"\bllama[-_]?[234]?\b",
            r"\bdeepseek\b",
            r"chat/completions",
            r"api/generate",
            r"models/gemini",
        )
        for f in php_files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore").lower()
                for pat in ai_patterns:
                    if re.search(pat, content):
                        return True
            except Exception:
                continue
        return False

    def detect_woocommerce_features(self, php_files: List[Path]) -> bool:
        """Detects if the plugin integrates with WooCommerce."""
        keywords = ("woocommerce", "wc_get_product", "product_cat", "product_tag", "WC_Product")
        for f in php_files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                if any(kw in content for kw in keywords):
                    return True
            except Exception:
                continue
        return False

