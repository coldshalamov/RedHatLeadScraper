@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python -m app.main
start http://localhost:8000
pause
