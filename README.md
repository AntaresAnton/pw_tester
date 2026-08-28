# 🧪 pw_tester: Suite Universal de CI/CD, Seguridad y Testing para Plugins de WordPress

> **100% Portable y Plug-and-Play**: Solo copia la carpeta `pw_tester/` dentro de **cualquier plugin de WordPress**, ejecuta `run_tests.bat` (o `python cli_runner.py all`), y el motor introspeccionará dinámicamente el plugin, detectará sus hooks, rutas REST, páginas de administración y ejecutará una auditoría de seguridad y compatibilidad completa.

---

## ⚡ ¿Cómo usarlo en cualquier Plugin?

1. **Copia la carpeta `pw_tester/`** dentro de la raíz de cualquier plugin de WordPress (ejemplo: `wp-content/plugins/mi-nuevo-plugin/pw_tester/`).
2. **Ejecuta `run_tests.bat`** (en Windows) o `python cli_runner.py all`.
3. **¡Listo!** El motor detectará automáticamente:
   - 📌 Nombre del plugin, versión, autor y archivo principal.
   - 🛡️ Vulnerabilidades de seguridad (SQL Injection, XSS, Nonces, Capabilities, `ABSPATH`).
   - 🔍 Todas las acciones AJAX (`wp_ajax_`) y sus validaciones.
   - 🤖 Rutas REST (`register_rest_route`) y callbacks de permisos.
   - 🖥️ Páginas de administración (`add_menu_page`) y pruebas E2E con Playwright.
   - 🧠 Integraciones con IA / LLMs con servidor Mock determinista a costo $0.

---

## 📁 Estructura del Entorno `pw_tester`

```text
pw_tester/
├── cli_runner.py                # Orquestador CLI principal con reportes Rich
├── php_linter.py                # Linter estático y auditor de seguridad de PHP
├── mock_llm_server.py           # Servidor Mock de Ollama y OpenAI (FastAPI)
├── config.py                    # Variables de entorno y configuración
├── conftest.py                  # Fixtures globales de Pytest
├── requirements.txt             # Dependencias de Python
├── setup_env.bat                # Instalador automático en 1 clic para Windows
├── run_tests.bat                # Ejecutor de pipeline en 1 clic
└── tests/
    ├── test_01_php_syntax_and_security.py  # Suite 1: Sintaxis PHP 8.2 y Nonces/Caps
    ├── test_02_mock_llm_integration.py     # Suite 2: Validación de esquemas LLM
    ├── test_03_rest_api.py                 # Suite 3: Seguridad y Auth de la API REST
    └── test_04_e2e_playwright.py           # Suite 4: Automatización de Navegador
```

---

## 🚀 Instalación y Puesta en Marcha

### Opción Rápida (Windows)
Haz doble clic en `setup_env.bat`. El script:
1. Creará un entorno virtual aislado (`venv`).
2. Instalará todas las librerías (`pytest`, `playwright`, `httpx`, `fastapi`, `rich`).
3. Descargará los binarios del navegador Chromium de Playwright.

### Opción Manual (Terminal)
```bash
cd pw_tester
python -m venv venv
venv\Scripts\activate          # En Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

---

## 🎯 Comandos Disponibles

Ejecuta el runner desde la carpeta `pw_tester`:

### 1. Ejecutar el Pipeline Completo de CI/CD
```bash
python cli_runner.py all
```
* Ejecuta el análisis de sintaxis de todos los archivos PHP.
* Inicia el servidor Mock LLM en segundo plano.
* Ejecuta todas las pruebas unitarias y de integración de Pytest.
* Muestra un resumen visual con tiempos y resultados.

### 2. Ejecutar Solo el Linter Estático de PHP
```bash
python cli_runner.py lint
```
* Escanea todos los archivos de `includes/` y `ollama-seo-ai.php` usando el binario de PHP configurado (`PHP 8.2`).
* Valida buenas prácticas (uso de `check_ajax_referer`, `current_user_can`, `sanitize_text_field`).
* Detecta patrones de riesgo (`eval`, superglobales desprotegidas).

### 3. Ejecutar las Pruebas con Pytest
```bash
python cli_runner.py test
```
O directamente con `pytest`:
```bash
pytest -v
pytest -v tests/test_01_php_syntax_and_security.py
pytest -v tests/test_03_rest_api.py
```

### 4. Iniciar el Servidor Mock de LLM Independiente
```bash
python cli_runner.py mock
```
Inicia un servidor local en `http://127.0.0.1:11434` que simula Ollama y OpenAI sin necesidad de tener modelos descargados ni consumir créditos.

---

## ⚙️ Configuración (`config.py` o `.env`)

Puedes crear un archivo `.env` dentro de `pw_tester/` para sobreescribir las opciones por defecto:

```ini
WP_SITE_URL=http://pquintanilla.local
WP_ADMIN_USER=admin
WP_ADMIN_PASS=password
PLUGIN_API_KEY=mi_clave_secreta_rest
MOCK_LLM_PORT=11434
HEADLESS=true
```

---

## 🌐 Integración con GitHub Actions

Para ejecutar este mismo runner en la nube en cada *Pull Request*, añade el siguiente archivo en `.github/workflows/local-ci.yml`:

```yaml
name: Plugin Quality & CI/CD
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Setup PHP
        uses: shivammathur/setup-php@v2
        with:
          php-version: '8.2'
      - name: Install dependencies
        run: |
          cd pw_tester
          pip install -r requirements.txt
          playwright install chromium
      - name: Run CI/CD Pipeline
        run: |
          cd pw_tester
          python cli_runner.py all
```
