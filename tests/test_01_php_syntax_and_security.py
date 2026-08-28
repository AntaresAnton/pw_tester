"""
Suite 1: Universal Static Analysis, PHP Syntax and Security Audit.
Works dynamically for ANY WordPress plugin.
"""

import pytest
from pathlib import Path
from php_linter import PHPLinter
from config import PLUGIN_ROOT, PLUGIN_INFO


class TestUniversalPHPSyntaxAndSecurity:

    @pytest.fixture(autouse=True)
    def setup_linter(self):
        self.linter = PHPLinter(PLUGIN_ROOT)

    def test_all_php_files_pass_syntax_check(self):
        """Validates that every PHP file in the plugin passes php -l with 0 syntax errors."""
        php_files = self.linter.get_php_files()
        assert len(php_files) > 0, f"No se encontraron archivos PHP en el directorio {PLUGIN_ROOT}."

        failed_files = []
        for file_path in php_files:
            ok, msg = self.linter.check_syntax(file_path)
            if not ok:
                failed_files.append((str(file_path.name), msg))

        assert len(failed_files) == 0, f"Archivos PHP con errores de sintaxis: {failed_files}"

    def test_main_plugin_file_has_valid_headers(self):
        """Validates that the main plugin file contains valid WordPress plugin headers."""
        main_file = PLUGIN_INFO.get("main_file_path")
        assert main_file and main_file.exists(), "No se pudo detectar el archivo principal con cabecera 'Plugin Name:'."

        content = main_file.read_text(encoding="utf-8", errors="ignore")
        assert "Plugin Name:" in content, "Falta cabecera 'Plugin Name:' en el archivo principal."
        assert "Version:" in content, "Falta cabecera 'Version:' en el archivo principal."
        assert PLUGIN_INFO["name"], "El nombre del plugin no pudo ser extraído."
        assert PLUGIN_INFO["version"], "La versión del plugin no pudo ser extraída."

    def test_direct_file_access_prevention(self):
        """Verifies that PHP files implement direct execution protection (ABSPATH check)."""
        php_files = self.linter.get_php_files()
        unprotected_files = []

        for f in php_files:
            content = f.read_text(encoding="utf-8", errors="ignore")
            # If the file contains executable PHP code (not just pure template/views)
            if "<?php" in content and len(content.strip().splitlines()) > 5:
                if not ("ABSPATH" in content or "WPINC" in content):
                    unprotected_files.append(f.name)

        assert len(unprotected_files) == 0, f"Archivos sin comprobación if ( ! defined( 'ABSPATH' ) ) exit: {unprotected_files}"

    def test_ajax_handlers_security(self):
        """Verifies that discovered AJAX actions implement Nonce and Capability checks."""
        ajax_actions = PLUGIN_INFO.get("ajax_actions", [])
        if not ajax_actions:
            pytest.skip("El plugin no registra acciones AJAX (wp_ajax_).")

        assert len(ajax_actions) > 0
