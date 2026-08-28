"""
Universal PHP Linter, Security Auditor & WordPress Standards Analyzer.
Works out-of-the-box on ANY WordPress plugin directory.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple
from config import PHP_EXECUTABLE, PLUGIN_ROOT, PLUGIN_INFO


class PHPLinter:
    """Performs static syntax, security audits, and WP standards checks on any WordPress plugin."""

    SECURITY_RULES = [
        {
            "id": "eval_execution",
            "pattern": r"\beval\s*\(",
            "message": "Uso crítico e inseguro de eval() detectado.",
            "severity": "CRITICAL"
        },
        {
            "id": "base64_decode",
            "pattern": r"\bbase64_decode\s*\(",
            "message": "Posible ofuscación de código con base64_decode().",
            "severity": "WARNING"
        },
        {
            "id": "raw_echo_superglobal",
            "pattern": r"echo\s+\$_(GET|POST|REQUEST)\[",
            "message": "Riesgo de XSS: Impresión directa de superglobal sin escapar (usar esc_html, esc_attr o esc_url).",
            "severity": "HIGH"
        },
        {
            "id": "direct_sqli_query",
            "pattern": r"\$wpdb->(query|get_results|get_row|get_var)\s*\(\s*\"[^\"]*\$_(GET|POST|REQUEST)",
            "message": "Riesgo crítico de SQL Injection: Consulta $wpdb concatenando superglobales sin $wpdb->prepare().",
            "severity": "CRITICAL"
        },
        {
            "id": "insecure_unserialize",
            "pattern": r"\bunserialize\s*\(\s*\$_(GET|POST|REQUEST|COOKIE)",
            "message": "Riesgo de ejecución remota de código con unserialize() sobre datos de usuario.",
            "severity": "CRITICAL"
        },
    ]

    WP_BEST_PRACTICES = [
        (r"check_ajax_referer\(|wp_verify_nonce\(", "Verificación de Nonce implementada."),
        (r"current_user_can\(", "Verificación de permisos/capacidades de usuario implementada."),
        (r"sanitize_text_field\(|esc_url_raw\(|wp_strip_all_tags\(|sanitize_textarea_field\(|absint\(", "Sanitización de entradas utilizada."),
        (r"wp_json_encode\(", "Uso seguro de wp_json_encode."),
        (r"esc_html\(|esc_attr\(|esc_url\(|wp_kses\(", "Escape de salida (Escaping) implementado."),
        (r"defined\s*\(\s*['\"](ABSPATH|WPINC)['\"]\s*\)", "Protección contra acceso directo de archivo (ABSPATH)."),
    ]

    def __init__(self, target_dir: Path = PLUGIN_ROOT, php_bin: str = PHP_EXECUTABLE):
        self.target_dir = target_dir
        self.php_bin = php_bin

    def get_php_files(self) -> List[Path]:
        """Collect all PHP files in plugin, excluding vendor/node_modules/pw_tester/tests."""
        files = []
        for p in self.target_dir.rglob("*.php"):
            parts = p.parts
            if any(x in parts for x in ("pw_tester", "node_modules", "vendor", ".git", "tests")):
                continue
            files.append(p)
        return sorted(files)

    def check_syntax(self, file_path: Path) -> Tuple[bool, str]:
        """Run php -l on a specific file."""
        try:
            res = subprocess.run(
                [self.php_bin, "-l", str(file_path)],
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )
            if res.returncode == 0:
                return True, "No syntax errors detected."
            return False, res.stderr or res.stdout
        except Exception as e:
            return False, f"Error ejecutando binario de PHP: {e}"

    def audit_security(self, file_path: Path) -> Dict[str, List[str]]:
        """Scan file for security vulnerabilities and verify WordPress best practices."""
        findings = {
            "warnings": [],
            "practices": []
        }

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()

            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("//") or stripped.startswith("*") or stripped.startswith("/*"):
                    continue

                for rule in self.SECURITY_RULES:
                    if re.search(rule["pattern"], line):
                        # Filter false positives when properly sanitized in same line
                        if rule["id"] == "raw_echo_superglobal" and any(fn in line for fn in ("esc_html", "esc_attr", "esc_url", "sanitize_")):
                            continue
                        findings["warnings"].append(f"Línea {i} [{rule['severity']}]: {rule['message']}")

            for pattern, label in self.WP_BEST_PRACTICES:
                if re.search(pattern, content) and label not in findings["practices"]:
                    findings["practices"].append(label)

        except Exception as e:
            findings["warnings"].append(f"No se pudo leer el archivo: {e}")

        return findings

    def run_full_scan(self) -> Dict[str, Any]:
        """Run syntax and security scan on all plugin files."""
        php_files = self.get_php_files()
        results = {
            "plugin_info": PLUGIN_INFO,
            "total_files": len(php_files),
            "passed_syntax": 0,
            "failed_syntax": 0,
            "total_warnings": 0,
            "files": []
        }

        for f in php_files:
            passed, syntax_msg = self.check_syntax(f)
            sec_audit = self.audit_security(f)

            if passed:
                results["passed_syntax"] += 1
            else:
                results["failed_syntax"] += 1

            results["total_warnings"] += len(sec_audit["warnings"])

            rel_path = f.relative_to(self.target_dir)
            results["files"].append({
                "path": str(rel_path),
                "syntax_ok": passed,
                "syntax_message": syntax_msg.strip(),
                "warnings": sec_audit["warnings"],
                "practices": sec_audit["practices"]
            })

        return results
