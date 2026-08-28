"""
Universal CLI Runner and Test Orchestrator for ANY WordPress Plugin (pw_tester).
"""

import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.progress import Progress, SpinnerColumn, TextColumn
from php_linter import PHPLinter
from config import BASE_DIR, PLUGIN_ROOT, PHP_EXECUTABLE, WP_SITE_URL, MOCK_LLM_URL, PLUGIN_INFO

# Console with recording enabled for log.txt export
console = Console(record=True, force_terminal=True, legacy_windows=False)


def print_banner():
    name = PLUGIN_INFO.get("name", "WordPress Plugin")
    ver = PLUGIN_INFO.get("version", "1.0.0")
    author = PLUGIN_INFO.get("author", "N/A")
    main_file = PLUGIN_INFO.get("main_file", "Auto-detected")
    num_files = PLUGIN_INFO.get("php_files_count", 0)
    num_ajax = len(PLUGIN_INFO.get("ajax_actions", []))
    num_rest = len(PLUGIN_INFO.get("rest_routes", []))
    num_pages = len(PLUGIN_INFO.get("admin_pages", []))
    has_ai = "Sí 🤖" if PLUGIN_INFO.get("has_llm") else "No"
    has_wc = "Sí 🛍️" if PLUGIN_INFO.get("has_woocommerce") else "No"

    banner_text = (
        f"[bold cyan]🚀 Universal WordPress Plugin CI/CD & Security Tester (pw_tester)[/bold cyan]\n"
        f"[bold white]Plugin Detectado:[/bold white] [green]{name}[/green] (v{ver}) | [dim]Autor: {author}[/dim]\n"
        f"[bold white]Archivo Principal:[/bold white] {main_file} | [bold white]Archivos PHP:[/bold white] {num_files}\n"
        f"[bold white]Capacidades Detectadas:[/bold white] {num_ajax} AJAX | {num_rest} Rutas REST | {num_pages} Páginas Admin | IA: {has_ai} | WooCommerce: {has_wc}\n"
        f"[dim]PHP Binary: {PHP_EXECUTABLE} | WP Target: {WP_SITE_URL}[/dim]"
    )
    console.print(Panel(banner_text, border_style="cyan"))


def run_lint_command():
    """Runs universal PHP syntax linting and security scans across all plugin files."""
    console.print("\n[bold yellow]🔍 Ejecutando Análisis Estático y Auditoría de Seguridad PHP...[/bold yellow]\n")

    linter = PHPLinter(PLUGIN_ROOT)
    results = linter.run_full_scan()

    table = Table(title="Resultados del Análisis Estático y Seguridad", border_style="blue")
    table.add_column("Archivo", style="cyan", no_wrap=True)
    table.add_column("Sintaxis", justify="center")
    table.add_column("Buenas Prácticas", style="green")
    table.add_column("Alertas / Vulnerabilidades", style="yellow")

    for f in results["files"]:
        status = "[bold green]✅ PASS[/bold green]" if f["syntax_ok"] else "[bold red]❌ FAIL[/bold red]"
        practices = ", ".join(f["practices"][:2]) if f["practices"] else "[dim]N/A[/dim]"
        warnings = "\n".join(f["warnings"]) if f["warnings"] else "[dim]0 alertas[/dim]"

        table.add_row(f["path"], status, practices, warnings)

    console.print(table)

    summary_color = "green" if results["failed_syntax"] == 0 and results["total_warnings"] == 0 else ("yellow" if results["failed_syntax"] == 0 else "red")
    console.print(
        f"\n[{summary_color}]Resumen: {results['passed_syntax']}/{results['total_files']} archivos pasaron sintaxis con éxito. "
        f"Fallos de Sintaxis: {results['failed_syntax']} | Alertas de Seguridad: {results['total_warnings']}[/{summary_color}]\n"
    )

    return results["failed_syntax"] == 0


def run_pytest_suite(suite_name: str = ""):
    """Runs pytest with live streamed output so all results are recorded in log.txt."""
    console.print(f"\n[bold yellow]🧪 Ejecutando Suite Universal de Pruebas Pytest {suite_name}...[/bold yellow]\n")

    cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short"]
    if suite_name:
        cmd.append(f"tests/{suite_name}")
    else:
        cmd.append("tests")

    proc = subprocess.Popen(
        cmd,
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if proc.stdout:
        for line in iter(proc.stdout.readline, ""):
            console.print(line, end="")

    proc.wait()
    return proc.returncode == 0


def run_mock_server_command():
    """Launches the mock LLM server directly in the terminal."""
    console.print(f"\n[bold green]🤖 Iniciando Servidor Mock Universal en {MOCK_LLM_URL}...[/bold green]")
    console.print("[dim]Presiona Ctrl+C para detener.[/dim]\n")
    from mock_llm_server import start_server
    start_server()


def save_log_file():
    """Exports recorded console output to log.txt without ANSI escape codes."""
    try:
        log_path = BASE_DIR / "log.txt"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        plain_text = console.export_text()
        divider = "=" * 80
        header = (
            f"{divider}\n"
            f"  pw_tester - REGISTRO DE CI/CD Y AUDITORÍA DE SEGURIDAD\n"
            f"  Fecha de Ejecución: {now_str}\n"
            f"  Plugin: {PLUGIN_INFO.get('name', 'WordPress Plugin')} (v{PLUGIN_INFO.get('version', '1.0.0')})\n"
            f"{divider}\n\n"
        )
        
        log_path.write_text(header + plain_text, encoding="utf-8")
        console.print(f"\n[bold green]📄 Registro completo guardado exitosamente en:[/bold green] [cyan]{log_path}[/cyan]\n")
    except Exception as e:
        console.print(f"[red]Error al guardar log.txt: {e}[/red]")



def run_full_pipeline():
    """Runs the complete universal CI/CD pipeline and saves log.txt."""
    print_banner()

    start_time = time.time()
    lint_ok = run_lint_command()

    console.print("\n" + "=" * 70 + "\n")

    pytest_ok = run_pytest_suite()

    elapsed = round(time.time() - start_time, 2)

    console.print("\n" + "=" * 70 + "\n")
    if lint_ok and pytest_ok:
        console.print(Panel(f"[bold green]🎉 ¡TODOS LOS TESTS DE '{PLUGIN_INFO.get('name')}' PASARON EXITOSAMENTE EN {elapsed}s! 🎉[/bold green]", border_style="green"))
    else:
        console.print(Panel(f"[bold red]❌ HUBO FALLOS EN EL PIPELINE DE CI/CD ({elapsed}s). Revisa el registro superior.[/bold red]", border_style="red"))

    save_log_file()


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("all", "ci"):
        run_full_pipeline()
    elif sys.argv[1] == "lint":
        print_banner()
        run_lint_command()
        save_log_file()
    elif sys.argv[1] == "mock":
        print_banner()
        run_mock_server_command()
    elif sys.argv[1] == "test":
        print_banner()
        suite = sys.argv[2] if len(sys.argv) > 2 else ""
        run_pytest_suite(suite)
        save_log_file()
    else:
        console.print("[yellow]Comandos disponibles:[/yellow]")
        console.print("  python cli_runner.py all      -> Ejecuta CI/CD universal completo (Linter + Pytest + Log)")
        console.print("  python cli_runner.py lint     -> Ejecuta únicamente el linter de PHP y seguridad")
        console.print("  python cli_runner.py test     -> Ejecuta todas las suites de Pytest")
        console.print("  python cli_runner.py mock     -> Inicia el servidor Mock LLM independiente")


if __name__ == "__main__":
    main()

