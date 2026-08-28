@echo off
echo =========================================================
echo  Instalando Entorno Virtual y Dependencias de pw_tester
echo =========================================================

cd /d "%~dp0"

if not exist venv (
    echo Creando entorno virtual venv con Python...
    python -m venv venv
)

echo Activando venv e instalando librerias de requirements.txt...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo Instalando navegadores de Playwright para pruebas E2E...
python -m playwright install chromium

echo.
echo =========================================================
echo  Instalacion completada con exito.
echo  Puedes ejecutar los tests con: run_tests.bat
echo =========================================================
pause
