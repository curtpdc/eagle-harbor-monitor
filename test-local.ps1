# Quick Local Test Script
# This allows you to test the site with a local backend

Write-Host "Starting local backend for testing..." -ForegroundColor Cyan

# Start backend in background
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python -m venv venv; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt; uvicorn app.main:app --host 0.0.0.0 --port 8000"

Write-Host "`n✅ Backend starting on http://localhost:8000" -ForegroundColor Green
Write-Host "`nTo test with production frontend:" -ForegroundColor Yellow
Write-Host "1. Update .github/workflows/azure-static-web-apps-calm-moss-0bea6ad10.yml"
Write-Host "2. Change NEXT_PUBLIC_API_URL to your local IP (find with 'ipconfig')"
Write-Host "3. OR just test locally with 'cd frontend; npm run dev'"

Write-Host "`n⚠️  For PRODUCTION, you MUST deploy the backend to Azure!" -ForegroundColor Red
