# Production Restore Point — February 6, 2026

## 🎯 Status at Snapshot

**Git Tag**: `v1.1-db-fix-2026-02-06`
**Commit**: `4160aca` (main)
**Created**: February 6, 2026 ~22:50 UTC
**Status**: ✅ All systems operational, 142 articles + 106 events live in production

## 🐛 What Broke (and Why)

### Problem 1: `/api/health` returning 503

**Root cause**: SQLAlchemy 2.0 requires raw SQL strings to be wrapped in `text()`.

```python
# BROKEN (SQLAlchemy 2.0 rejects plain strings)
db.execute("SELECT 1")

# FIXED
from sqlalchemy import text
db.execute(text("SELECT 1"))
```

**File changed**: `backend/app/api/routes.py` — added `text` to imports, wrapped the health-check query.
**Commit**: `ac4ebec`

### Problem 2: Production database empty (0 articles despite 142 scraped locally)

This had **three** sub-causes:

#### 2a. Relative SQLite path wiped on every deploy

The original `DATABASE_URL` was `sqlite:///./eagle_harbor.db` (relative path). On Azure App Service, the app runs inside an ephemeral container directory — each deployment creates a fresh empty `eagle_harbor.db` in the working directory, losing all data.

**Fix**: Changed `DATABASE_URL` to `sqlite:////home/data/eagle_harbor.db` in Azure App Settings. The `/home/` directory on Azure App Service (Linux) is **persistent** across restarts and deployments.

```powershell
az webapp config appsettings set --name eagleharbor-api --resource-group eagleharbor `
  --settings DATABASE_URL="sqlite:////home/data/eagle_harbor.db"
```

#### 2b. `Base.metadata.create_all()` overwrites existing data

`backend/app/main.py` unconditionally ran `Base.metadata.create_all(bind=engine)` on every startup. Even when the database file existed with data, this would replace it with empty tables.

**Fix**: Made it conditional — only creates tables when the database has no existing tables:

```python
from sqlalchemy import inspect

inspector = inspect(engine)
existing_tables = inspector.get_table_names()
if not existing_tables:
    Base.metadata.create_all(bind=engine)
```

**File changed**: `backend/app/main.py`
**Commit**: `4160aca`

#### 2c. Kudu VFS API path mapping was wrong

When uploading the database file via Kudu's VFS API, the VFS root is already `/home/`. So:

- ❌ `api/vfs/home/data/eagle_harbor.db` → writes to `/home/home/data/` (wrong!)
- ✅ `api/vfs/data/eagle_harbor.db` → writes to `/home/data/` (correct!)

The upload reported success in both cases but the app was reading from the wrong location. This was discovered after multiple upload attempts appeared to succeed but the file size at `/home/data/` never changed.

**Correct upload command**:
```powershell
$token = az account get-access-token --query accessToken -o tsv
$dbBytes = [System.IO.File]::ReadAllBytes("path\to\eagle_harbor.db")
Invoke-RestMethod -Uri "https://eagleharbor-api.scm.azurewebsites.net/api/vfs/data/eagle_harbor.db" `
  -Method PUT -Headers @{Authorization="Bearer $token"; "If-Match"="*"} `
  -ContentType "application/octet-stream" -Body $dbBytes
```

## 📦 Backup Contents

| File | Description |
|------|-------------|
| `eagle_harbor.db` | SQLite database (479,232 bytes) — 142 articles, 106 events |
| `azure-app-settings.json` | Full Azure App Service configuration export |
| `RESTORE.md` | This file |

## ✅ Verified Production Endpoints

| Endpoint | Status | Response |
|----------|--------|----------|
| `GET /health` | 200 | `{"status": "healthy"}` |
| `GET /api/health` | 200 | `{"status": "healthy", "database": "healthy", "last_scrape": "2026-02-06T14:58:18"}` |
| `GET /api/articles` | 200 | 142 total articles returned |
| `POST /api/ask` | 200 | AI answers grounded in real article data |

## 🔄 How to Restore

### Option A: Restore code from git tag

```powershell
git fetch --tags
git checkout v1.1-db-fix-2026-02-06
```

### Option B: Re-upload database to production

If the production database is lost or corrupted:

```powershell
# 1. Stop the app (prevents create_all from overwriting)
az webapp stop --name eagleharbor-api --resource-group eagleharbor

# 2. Upload the backup database
$token = az account get-access-token --query accessToken -o tsv
$dbBytes = [System.IO.File]::ReadAllBytes("backup-2026-02-06-db-fix\eagle_harbor.db")
Invoke-RestMethod `
  -Uri "https://eagleharbor-api.scm.azurewebsites.net/api/vfs/data/eagle_harbor.db" `
  -Method PUT -Headers @{Authorization="Bearer $token"; "If-Match"="*"} `
  -ContentType "application/octet-stream" -Body $dbBytes

# 3. Verify file size (should be 479232)
$body = '{"command":"ls -l /home/data/eagle_harbor.db","dir":"/home"}'
Invoke-RestMethod `
  -Uri "https://eagleharbor-api.scm.azurewebsites.net/api/command" `
  -Method POST -Headers @{Authorization="Bearer $token"; "Content-Type"="application/json"} `
  -Body $body

# 4. Restart the app
az webapp start --name eagleharbor-api --resource-group eagleharbor
```

### Option C: Restore Azure app settings

```powershell
# Review and selectively restore settings from the backup
Get-Content "backup-2026-02-06-db-fix\azure-app-settings.json" | ConvertFrom-Json |
  Format-Table name, value
```

## 🌐 Live URLs

- **Frontend**: https://calm-moss-0bea6ad10.4.azurestaticapps.net
- **Backend API**: https://eagleharbor-api.azurewebsites.net
- **Kudu SCM**: https://eagleharbor-api.scm.azurewebsites.net

## 📝 Key Lesson Learned

> **Never use relative SQLite paths on Azure App Service.** The container working directory is ephemeral. Always use `/home/data/` for persistent storage. And always make `create_all()` conditional so it doesn't nuke an existing database on restart.
