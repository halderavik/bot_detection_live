# Run SQL migration directly on Cloud SQL
# This script executes the SQL migration on the production database

param(
    [string]$InstanceName = "bot-db",
    [string]$DatabaseName = "bot_detection",
    [string]$ProjectId = "survey-bot-detection",
    [string]$Region = "northamerica-northeast2"
)

Write-Host "🚀 Running SQL Migration on Cloud SQL" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Instance: $InstanceName" -ForegroundColor Cyan
Write-Host "Database: $DatabaseName" -ForegroundColor Cyan
Write-Host "Project: $ProjectId" -ForegroundColor Cyan
Write-Host ""

# Check if Cloud SQL Proxy is needed
Write-Host "⚠️  To run this migration, you need to:" -ForegroundColor Yellow
Write-Host "1. Connect to Cloud SQL instance" -ForegroundColor White
Write-Host "2. Run the SQL script: backend/migration_platform_id.sql" -ForegroundColor White
Write-Host ""

Write-Host "Option 1: Via Cloud SQL Proxy (local)" -ForegroundColor Cyan
Write-Host "  gcloud sql connect $InstanceName --user=postgres --project=$ProjectId" -ForegroundColor White
Write-Host "  Then run: \i backend/migration_platform_id.sql" -ForegroundColor White
Write-Host ""

Write-Host "Option 2: Via gcloud sql execute" -ForegroundColor Cyan
Write-Host "  gcloud sql databases execute-sql $DatabaseName --instance=$InstanceName --sql-file=backend/migration_platform_id.sql --project=$ProjectId" -ForegroundColor White
Write-Host ""

Write-Host "Option 3: Via Cloud Console" -ForegroundColor Cyan
Write-Host "  1. Go to Cloud SQL > $InstanceName" -ForegroundColor White
Write-Host "  2. Open Query tab" -ForegroundColor White
Write-Host "  3. Paste and run the SQL from backend/migration_platform_id.sql" -ForegroundColor White
Write-Host ""

Write-Host "SQL Migration File: backend/migration_platform_id.sql" -ForegroundColor Green

