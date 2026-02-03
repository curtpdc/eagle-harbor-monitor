@echo off
cd /d C:\Users\cprin\eagle-harbor-monitor\backend
call venv\Scripts\activate.bat
python -m uvicorn app.main:app --reload --port 8001
pause
