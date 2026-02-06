#!/bin/bash
# Azure App Service startup script for FastAPI
set -e

echo "Starting Eagle Harbor Backend API..."
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

cd /home/site/wwwroot

echo "Installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "Starting Gunicorn..."
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind=0.0.0.0:8000 --timeout 120 --access-logfile - --error-logfile -
