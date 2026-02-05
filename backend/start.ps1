$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath
& .\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
