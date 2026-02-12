# Run Grid and Timing Analysis Migration on Production Cloud SQL
# This script runs the migration to add grid_responses and timing_analysis tables

param(
    [string]$ProjectId = "survey-bot-detection",
    [string]$InstanceName = "bot-db-v2",
    [string]$DatabaseName = "bot_detection_v2",
    [string]$Region = "northamerica-northeast2"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Grid and Timing Analysis Migration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Project: $ProjectId" -ForegroundColor Gray
Write-Host "Instance: $InstanceName" -ForegroundColor Gray
Write-Host "Database: $DatabaseName" -ForegroundColor Gray
Write-Host ""

$migrationFile = "backend\migrations\add_grid_analysis_tables.sql"

if (-not (Test-Path $migrationFile)) {
    Write-Host "❌ Migration file not found: $migrationFile" -ForegroundColor Red
    exit 1
}

Write-Host "Migration file found: $migrationFile" -ForegroundColor Green
Write-Host ""

# Read migration SQL
$migrationSQL = Get-Content $migrationFile -Raw

Write-Host "========================================" -ForegroundColor Yellow
Write-Host "To run this migration, use one of:" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

Write-Host "OPTION 1: Cloud SQL Proxy (Recommended)" -ForegroundColor Cyan
Write-Host "  1. Start Cloud SQL Proxy:" -ForegroundColor White
Write-Host "     cloud-sql-proxy $ProjectId`:$Region`:$InstanceName" -ForegroundColor Gray
Write-Host "  2. In another terminal, connect:" -ForegroundColor White
Write-Host "     psql -h 127.0.0.1 -U bot_user -d $DatabaseName" -ForegroundColor Gray
Write-Host "  3. Run the migration:" -ForegroundColor White
Write-Host "     \i $migrationFile" -ForegroundColor Gray
Write-Host ""

Write-Host "OPTION 2: Cloud Shell" -ForegroundColor Cyan
Write-Host "  1. Open Cloud Shell: https://shell.cloud.google.com" -ForegroundColor White
Write-Host "  2. Connect to database:" -ForegroundColor White
Write-Host "     gcloud sql connect $InstanceName --user=bot_user --database=$DatabaseName --project=$ProjectId" -ForegroundColor Gray
Write-Host "  3. Copy and paste the SQL from: $migrationFile" -ForegroundColor White
Write-Host ""

Write-Host "OPTION 3: Direct gcloud command (if supported)" -ForegroundColor Cyan
Write-Host "  gcloud sql connect $InstanceName --user=bot_user --database=$DatabaseName --project=$ProjectId" -ForegroundColor Gray
Write-Host "  Then paste the SQL from: $migrationFile" -ForegroundColor Gray
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "Migration SQL File: $migrationFile" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Display first few lines of migration
Write-Host "Preview of migration SQL:" -ForegroundColor Yellow
Get-Content $migrationFile | Select-Object -First 20
Write-Host "..."
Write-Host ""
