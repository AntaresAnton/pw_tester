"""
Universal PHP Linter, Security Auditor & WordPress Standards Analyzer.
Works out-of-the-box on ANY WordPress plugin directory.
"""

import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Tuple
from config import PHP_EXECUTABLE, PLUGIN_ROOT, PLUGIN_INFO


class PHPLinter:
    """Performs static syntax, security audits, and WP standards checks on any WordPress plugin."""

    # Subdirectories commonly containing 3rd-party vendor SDKs bundled in plugins
    THIRD_PARTY_DIRS = (
        "google", "windowsazure", "pear", "dropbox2", "dropbox", "onedrive",
        "pcloud", "backblaze", "cloudfiles", "aws", "guzzle", "symfony",
        "psr", "monolog", "composer", "vendor"
    )

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
            "message": "Uso de base64_decode() detectado (verificar si es criptografía/token legítimo).",
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
        (r"defined\s*\(\s*['\"](ABSPATH|WPINC|[A-Z0-9_]+_DIR|[A-Z0-9_]+_PATH)['\"]\s*\)", "Protección contra acceso directo de archivo (ABSPATH)."),
    ]

    def __init__(self, target_dir: Path = PLUGIN_ROOT, php_bin: str = PHP_EXECUTABLE):
        self.target_dir = target_dir
        self.php_bin = php_bin
        self.max_workers = min(32, (os.cpu_count() or 4) * 4)

    def get_php_files(self) -> List[Path]:
        """Collect all PHP files in plugin, excluding vendor/node_modules/pw_tester/tests."""
        files = []
        for p in self.target_dir.rglob("*.php"):
            parts = p.parts
            if any(x in parts for x in ("pw_tester", "node_modules", "vendor", ".git", "tests")):
                continue
            files.append(p)
        return sorted(files)

    def is_bundled_library(self, file_path: Path) -> bool:
        """Determines if a file is part of a bundled 3rd-party library/SDK."""
        rel = file_path.relative_to(self.target_dir)
        parts_lower = [p.lower() for p in rel.parts]
        for idx, part in enumerate(parts_lower[:-1]):
            if any(tp in part for tp in self.THIRD_PARTY_DIRS):
                return True
            if part == "includes" and idx + 1 < len(parts_lower) - 1:
                sub = parts_lower[idx + 1]
                if any(tp in sub for tp in self.THIRD_PARTY_DIRS):
                    return True
        return False

    def is_view_template(self, file_path: Path) -> bool:
        """Checks if the file is a view, template, notice partial, or CLI example."""
        rel = file_path.relative_to(self.target_dir)
        parts_lower = [p.lower() for p in rel.parts]
        if any(p in ("templates", "views", "notices", "partials", "languages", "css", "js") for p in parts_lower):
            return True
        if file_path.name.startswith("example-") or file_path.name.startswith("cli-"):
            return True
        return False

    def is_pure_declaration_file(self, content: str) -> bool:
        """Checks if a PHP file only defines classes, functions, interfaces, traits, or namespaces (no top-level execution)."""
        # Strip comments
        clean = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
        clean = re.sub(r"//.*", "", clean)
        clean = re.sub(r"#.*", "", clean)
        clean = clean.replace("<?php", "").replace("?>", "").strip()

        # If it defines a class/interface/trait/function and contains no immediate top-level side effects
        if re.search(r"\b(class|interface|trait|enum|function)\s+[A-Za-z0-9_]+", clean):
            # Check for top-level risky execution outside functions/classes
            top_level_risky = re.search(r"^(?:add_action|add_filter|header|do_action|wp_redirect)\s*\(", clean, re.MULTILINE)
            if not top_level_risky:
                return True
        return False

    def has_direct_access_protection(self, file_path: Path, content: str) -> bool:
        """Verifies if the file is protected from direct HTTP invocation."""
        if self.is_bundled_library(file_path):
            return True

        if self.is_view_template(file_path):
            return True

        if self.is_pure_declaration_file(content):
            return True

        # Check standard WP guards: ABSPATH, WPINC, WP_UNINSTALL_PLUGIN or plugin-defined constants
        guards = (
            r"defined\s*\(\s*['\"](ABSPATH|WPINC|WP_UNINSTALL_PLUGIN|[A-Z0-9_]+_DIR|[A-Z0-9_]+_PATH|[A-Z0-9_]+_VERSION|[A-Z0-9_]+_FILE)['\"]\s*\)",
            r"if\s*\(\s*!\s*defined\s*\(",
            r"!\s*defined\s*\([^)]+\)\s*(?:and|&&|\|\|)?\s*(?:exit|die)",
            r"die\s*\(\s*['\"](?:Direct access forbidden|No direct script access allowed|Direct script access not allowed|No direct access|Cheatin)[\s\S]*?\)",
        )
        for pattern in guards:
            if re.search(pattern, content, re.IGNORECASE):
                return True

        return False

    def check_syntax(self, file_path: Path) -> Tuple[bool, str]:
        """Run php -l on a specific file safely across Windows and POSIX."""
        try:
            kwargs = {
                "capture_output": True,
                "text": True,
                "timeout": 10,
                "check": False,
                "stdin": subprocess.DEVNULL,
            }
            if os.name == "nt":
                kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW

            res = subprocess.run(
                [self.php_bin, "-l", str(file_path)],
                **kwargs
            )
            if res.returncode == 0:
                return True, "No syntax errors detected."
            return False, res.stderr or res.stdout
        except Exception as e:
            return False, f"Error ejecutando binario de PHP: {e}"


    def check_all_syntax_parallel(self) -> List[Tuple[Path, bool, str]]:
        """Validates all PHP files in parallel using ThreadPoolExecutor."""
        php_files = self.get_php_files()
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {executor.submit(self.check_syntax, f): f for f in php_files}
            for future in as_completed(future_to_file):
                f = future_to_file[future]
                try:
                    ok, msg = future.result()
                    results.append((f, ok, msg))
                except Exception as e:
                    results.append((f, False, str(e)))
        return sorted(results, key=lambda x: str(x[0]))

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

    def _scan_single_file(self, file_path: Path) -> Dict[str, Any]:
        """Scans a single file for syntax and security."""
        passed, syntax_msg = self.check_syntax(file_path)
        sec_audit = self.audit_security(file_path)
        rel_path = file_path.relative_to(self.target_dir)
        return {
            "path": str(rel_path),
            "file_obj": file_path,
            "syntax_ok": passed,
            "syntax_message": syntax_msg.strip(),
            "warnings": sec_audit["warnings"],
            "practices": sec_audit["practices"]
        }

    def run_full_scan(self) -> Dict[str, Any]:
        """Run syntax and security scan on all plugin files in parallel."""
        php_files = self.get_php_files()
        results = {
            "plugin_info": PLUGIN_INFO,
            "total_files": len(php_files),
            "passed_syntax": 0,
            "failed_syntax": 0,
            "total_warnings": 0,
            "files": []
        }

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            file_results = list(executor.map(self._scan_single_file, php_files))

        for item in sorted(file_results, key=lambda x: x["path"]):
            if item["syntax_ok"]:
                results["passed_syntax"] += 1
            else:
                results["failed_syntax"] += 1

            results["total_warnings"] += len(item["warnings"])
            results["files"].append(item)

        return results

