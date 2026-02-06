# PostgreSQL Setup Script - Eagle Harbor Monitor
# Run this after Microsoft.DBforPostgreSQL provider is registered

Write-Host "🗄️ PostgreSQL Database Setup" -ForegroundColor Cyan
Write-Host ""

# Check registration status
$regStatus = az provider show -n Microsoft.DBforPostgreSQL --query "registrationState" -o tsv
Write-Host "PostgreSQL Provider Status: $regStatus"

if ($regStatus -ne "Registered") {
    Write-Host "❌ PostgreSQL provider not ready yet. Current status: $regStatus" -ForegroundColor Red
    Write-Host "Please wait a few more minutes and run this script again." -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ PostgreSQL provider is registered!" -ForegroundColor Green
Write-Host ""

# Step 1: Create PostgreSQL Server
Write-Host "Step 1: Creating PostgreSQL Flexible Server..." -ForegroundColor Yellow
Write-Host "This will take 5-10 minutes..." -ForegroundColor Gray

$dbPassword = "EagleHarbor2026!"

az postgres flexible-server create `
    --name eagle-harbor-db `
    --resource-group eagleharbor `
    --location eastus `
    --admin-user adminuser `
    --admin-password $dbPassword `
    --sku-name Standard_B1ms `
    --tier Burstable `
    --storage-size 32 `
    --version 15 `
    --public-access 0.0.0.0

Write-Host "✓ PostgreSQL server created" -ForegroundColor Green

# Step 2: Create database
Write-Host ""
Write-Host "Step 2: Creating database..." -ForegroundColor Yellow

az postgres flexible-server db create `
    --resource-group eagleharbor `
    --server-name eagle-harbor-db `
    --database-name eagle_harbor_monitor

Write-Host "✓ Database created" -ForegroundColor Green

# Step 3: Configure firewall
Write-Host ""
Write-Host "Step 3: Configuring firewall rules..." -ForegroundColor Yellow

# Allow Azure services
az postgres flexible-server firewall-rule create `
    --resource-group eagleharbor `
    --name eagle-harbor-db `
    --rule-name AllowAzureServices `
    --start-ip-address 0.0.0.0 `
    --end-ip-address 0.0.0.0

# Allow your current IP
$myIp = (Invoke-WebRequest -Uri "https://api.ipify.org" -UseBasicParsing).Content
az postgres flexible-server firewall-rule create `
    --resource-group eagleharbor `
    --name eagle-harbor-db `
    --rule-name AllowMyIP `
    --start-ip-address $myIp `
    --end-ip-address $myIp

Write-Host "✓ Firewall configured" -ForegroundColor Green

# Step 4: Run database schema
Write-Host ""
Write-Host "Step 4: Creating database schema..." -ForegroundColor Yellow

$connString = "postgresql://adminuser:$dbPassword@eagle-harbor-db.postgres.database.azure.com:5432/eagle_harbor_monitor?sslmode=require"

# Check if psql is available
$psqlExists = Get-Command psql -ErrorAction SilentlyContinue

if ($psqlExists) {
    Set-Location database
    $env:PGPASSWORD = $dbPassword
    psql "host=eagle-harbor-db.postgres.database.azure.com port=5432 dbname=eagle_harbor_monitor user=adminuser sslmode=require" -f schema.sql
    Remove-Item env:PGPASSWORD
    Set-Location ..
    Write-Host "✓ Schema created" -ForegroundColor Green
} else {
    Write-Host "⚠️  psql not found. You'll need to run the schema manually:" -ForegroundColor Yellow
    Write-Host "1. Install PostgreSQL client tools, or"
    Write-Host "2. Use Azure Portal Query Editor to run database/schema.sql"
    Write-Host ""
    Write-Host "Connection string:" -ForegroundColor Cyan
    Write-Host $connString
}

# Step 5: Update application settings
Write-Host ""
Write-Host "Step 5: Updating application settings..." -ForegroundColor Yellow

# Update backend
az webapp config appsettings set `
    --resource-group eagleharbor `
    --name eagleharbor-api `
    --settings DATABASE_URL=$connString

# Update functions
az functionapp config appsettings set `
    --resource-group eagleharbor `
    --name eagleharbor-scrapers `
    --settings DATABASE_URL=$connString

Write-Host "✓ Applications updated" -ForegroundColor Green

# Summary
Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "✅ PostgreSQL Setup Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Database Details:" -ForegroundColor Yellow
Write-Host "  Server: eagle-harbor-db.postgres.database.azure.com"
Write-Host "  Database: eagle_harbor_monitor"
Write-Host "  Username: adminuser"
Write-Host "  Password: $dbPassword"
Write-Host ""
Write-Host "Connection String:" -ForegroundColor Cyan
Write-Host $connString
Write-Host ""
Write-Host "✓ Backend and Functions have been updated to use PostgreSQL" -ForegroundColor Green
Write-Host "✓ Restart your apps for changes to take effect:" -ForegroundColor Yellow
Write-Host "  az webapp restart --resource-group eagleharbor --name eagleharbor-api"
Write-Host "  az functionapp restart --resource-group eagleharbor --name eagleharbor-scrapers"
