cd C:\Users\cprin\eagle-harbor-monitor\backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8000
