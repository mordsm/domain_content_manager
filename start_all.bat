@echo off
echo Starting Domain Content Manager Server and Telegram Bot...
start "Domain Content Manager Server" cmd /k "uv run uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 2 >nul
start "Domain Content Manager Telegram Bot" cmd /k "uv run python -m app.services.telegram_bot"
echo System started! Open http://localhost:8000 in your browser.
pause

