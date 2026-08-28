@echo off
cd /d "%~dp0"

if exist venv (
    call venv\Scripts\activate.bat
)

python cli_runner.py all
pause
