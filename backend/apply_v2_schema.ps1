# PowerShell script to apply schema to bot_detection_v2 database
# This script uses Cloud SQL Admin API to execute SQL commands

param(
    [string]$ProjectId = "survey-bot-detection",
    [string]$InstanceName = "bot-db",
    [string]$DatabaseName = "bot_detection_v2",
    [string]$SchemaFile = "schema_bot_detection_v2.sql"
)

Write-Host "Applying schema to bot_detection_v2 database..." -ForegroundColor Cyan

# Check if schema file exists
if (-not (Test-Path $SchemaFile)) {
    Write-Host "ERROR: Schema file not found: $SchemaFile" -ForegroundColor Red
    exit 1
}

Write-Host "Reading schema file: $SchemaFile" -ForegroundColor Yellow
$schemaContent = Get-Content $SchemaFile -Raw

# Note: Cloud SQL Admin API doesn't directly support executing SQL
# We need to use gcloud sql connect or create a temporary Cloud Run job
# For now, we'll provide instructions

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Schema Application Instructions" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
Write-Host "Option 1: Use Cloud SQL Proxy (Recommended)" -ForegroundColor Yellow
Write-Host "  1. Install Cloud SQL Proxy: https://cloud.google.com/sql/docs/postgres/connect-admin-proxy"
Write-Host "  2. Start proxy: cloud-sql-proxy survey-bot-detection:northamerica-northeast2:bot-db"
Write-Host "  3. Connect: psql -h 127.0.0.1 -U bot_user -d bot_detection_v2"
Write-Host "  4. Run: \i $SchemaFile"
Write-Host ""
Write-Host "Option 2: Use gcloud sql connect (requires psql)" -ForegroundColor Yellow
Write-Host "  gcloud sql connect bot-db --user=bot_user --database=bot_detection_v2 --project=$ProjectId"
Write-Host "  Then paste the contents of $SchemaFile"
Write-Host ""
Write-Host "Option 3: Use Python script (if backend can connect)" -ForegroundColor Yellow
Write-Host "  The backend's init_db() function will create tables automatically on startup"
Write-Host "  if they don't exist. Check Cloud Run logs for 'Database tables created successfully'"
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan

# Check if we can verify the schema via backend
Write-Host ""
Write-Host "Checking if backend can initialize schema..." -ForegroundColor Yellow
Write-Host "The backend will automatically create tables when it starts if they don't exist."
Write-Host "Check Cloud Run logs for initialization messages."
Write-Host ""

# Provide a way to check schema via Python
Write-Host "To verify schema, run:" -ForegroundColor Green
Write-Host "  cd backend" -ForegroundColor Green
Write-Host "  `$env:DATABASE_URL = 'postgresql+asyncpg://bot_user:NewPassword123!@/bot_detection_v2?host=/cloudsql/survey-bot-detection:northamerica-northeast2:bot-db'" -ForegroundColor Green
Write-Host "  python check_v2_database_schema.py" -ForegroundColor Green
Write-Host ""
