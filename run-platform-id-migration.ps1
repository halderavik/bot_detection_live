# Run platform_id migration for both local and production databases
# This script fixes the database schema differences

param(
    [string]$Environment = "production",  # "local" or "production"
    [switch]$DryRun = $false
)

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Platform ID Migration Script" -ForegroundColor Cyan
Write-Host "=" * 60
Write-Host ""

if ($DryRun) {
    Write-Host "🔍 DRY RUN MODE - No changes will be made" -ForegroundColor Yellow
    Write-Host ""
}

if ($Environment -eq "production") {
    Write-Host "🌐 Production Mode" -ForegroundColor Yellow
    Write-Host "Fetching DATABASE_URL from Secret Manager..." -ForegroundColor Gray
    
    try {
        $dbUrl = gcloud secrets versions access latest --secret="DATABASE_URL" --project="survey-bot-detection" 2>&1
        if ($LASTEXITCODE -eq 0) {
            $env:DATABASE_URL = $dbUrl.Trim()
            Write-Host "✅ Database URL retrieved from Secret Manager" -ForegroundColor Green
        } else {
            Write-Host "❌ Failed to retrieve DATABASE_URL from Secret Manager" -ForegroundColor Red
            Write-Host "Error: $dbUrl" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "❌ Error retrieving DATABASE_URL: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "💻 Local Mode" -ForegroundColor Yellow
    Write-Host "Using DATABASE_URL from .env file" -ForegroundColor Gray
    
    if (-not $env:DATABASE_URL) {
        Write-Host "⚠️  DATABASE_URL not set. Loading from backend/.env..." -ForegroundColor Yellow
        # Try to load from .env file
        if (Test-Path "backend\.env") {
            Get-Content "backend\.env" | ForEach-Object {
                if ($_ -match '^DATABASE_URL=(.+)$') {
                    $env:DATABASE_URL = $matches[1]
                }
            }
        }
    }
    
    if (-not $env:DATABASE_URL) {
        Write-Host "❌ DATABASE_URL not found. Please set it in backend/.env or as environment variable" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Running migration..." -ForegroundColor Yellow
Write-Host ""

# Change to backend directory
Push-Location backend

try {
    if ($DryRun) {
        Write-Host "DRY RUN: Would execute: python fix_platform_id_migration.py" -ForegroundColor Yellow
    } else {
        python fix_platform_id_migration.py
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "=" * 60 -ForegroundColor Green
            Write-Host "✅ Migration completed successfully!" -ForegroundColor Green
            Write-Host "=" * 60
        } else {
            Write-Host ""
            Write-Host "=" * 60 -ForegroundColor Red
            Write-Host "❌ Migration failed. Check error messages above." -ForegroundColor Red
            Write-Host "=" * 60
            exit 1
        }
    }
} catch {
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Red
    Write-Host "❌ Error running migration: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "=" * 60
    exit 1
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Verify the migration by checking the database schema" -ForegroundColor White
Write-Host "2. Test the API endpoints to ensure they work correctly" -ForegroundColor White
if ($Environment -eq "production") {
    Write-Host "3. Run: .\test-endpoints-comprehensive.ps1" -ForegroundColor White
}
