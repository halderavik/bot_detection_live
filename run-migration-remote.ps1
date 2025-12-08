# Run migration remotely via Cloud Run job or direct database connection
# This script helps run the migration on production database

param(
    [switch]$DryRun = $false
)

Write-Host "🚀 Database Migration Runner" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""

if ($DryRun) {
    Write-Host "🔍 DRY RUN MODE - No changes will be made" -ForegroundColor Yellow
    Write-Host ""
}

# Option 1: Run via Cloud SQL Proxy (if available)
Write-Host "Migration Options:" -ForegroundColor Cyan
Write-Host "1. Run locally with Cloud SQL Proxy" -ForegroundColor White
Write-Host "2. Run via Cloud Run Job (recommended)" -ForegroundColor White
Write-Host "3. Run directly with production credentials" -ForegroundColor White
Write-Host ""

# Get production DATABASE_URL from Secret Manager
Write-Host "Fetching production database URL from Secret Manager..." -ForegroundColor Yellow
try {
    $dbUrl = gcloud secrets versions access latest --secret="DATABASE_URL" --project="survey-bot-detection" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database URL retrieved" -ForegroundColor Green
        $env:DATABASE_URL = $dbUrl
        
        Write-Host "`nRunning migration..." -ForegroundColor Yellow
        cd backend
        
        if ($DryRun) {
            Write-Host "DRY RUN: Would execute migration script" -ForegroundColor Yellow
        } else {
            python -m app.migrations.add_platform_id_migration
            if ($LASTEXITCODE -eq 0) {
                Write-Host "`n✅ Migration completed successfully!" -ForegroundColor Green
            } else {
                Write-Host "`n❌ Migration failed. Check error messages above." -ForegroundColor Red
            }
        }
        
        cd ..
    } else {
        Write-Host "❌ Failed to retrieve database URL" -ForegroundColor Red
        Write-Host "Error: $dbUrl" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`nAlternative: Run migration manually:" -ForegroundColor Yellow
    Write-Host "1. Connect to Cloud SQL instance" -ForegroundColor White
    Write-Host "2. Run SQL commands from migration script" -ForegroundColor White
}

