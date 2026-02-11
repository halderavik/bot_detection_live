# PowerShell script to prepare database for Stage 3 (Fraud & Duplicate) deployment
# Run this BEFORE deploy_v2_database.ps1 to ensure migrations are applied and schema is verified

param(
    [string]$ProjectId = "survey-bot-detection",
    [string]$InstanceName = "bot-db",
    [string]$DatabaseName = "bot_detection_v2",
    [switch]$SkipMigrations
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "Database Preparation for Stage 3 Deployment" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

# Step 1: Get DATABASE_URL from Secret Manager
Write-Host "Step 1: Getting DATABASE_URL from Secret Manager..." -ForegroundColor Yellow
try {
    $env:DATABASE_URL = gcloud secrets versions access latest --secret=DATABASE_URL --project=$ProjectId 2>$null
    if (-not $env:DATABASE_URL) {
        Write-Host "ERROR: Could not retrieve DATABASE_URL" -ForegroundColor Red
        Write-Host "Ensure you have access to Secret Manager and the secret exists." -ForegroundColor Gray
        exit 1
    }
    Write-Host "  DATABASE_URL retrieved (points to database in URL)" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to get DATABASE_URL: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Get Cloud SQL public IP (needed for TCP connection from local machine)
Write-Host ""
Write-Host "Step 2: Getting Cloud SQL instance IP..." -ForegroundColor Yellow
try {
    $publicIp = gcloud sql instances describe $InstanceName --project=$ProjectId --format="value(ipAddresses[0].ipAddress)" 2>$null
    if ($publicIp) {
        $env:CLOUD_SQL_IP = $publicIp
        Write-Host "  CLOUD_SQL_IP: $publicIp" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: Could not get public IP. Using default or env CLOUD_SQL_IP." -ForegroundColor Yellow
    }
} catch {
    Write-Host "  WARNING: Could not fetch IP: $_" -ForegroundColor Yellow
}

# Step 3: Run migrations (unless skipped)
if (-not $SkipMigrations) {
    Write-Host ""
    Write-Host "Step 3: Running database migrations..." -ForegroundColor Yellow
    Push-Location $PSScriptRoot

    # 3a: Platform ID migration
    Write-Host ""
    Write-Host "  3a. Platform ID migration (sessions.platform_id, indexes)..." -ForegroundColor Gray
    python run_migration_sync.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNING: Platform ID migration failed (connection timeout)" -ForegroundColor Yellow
        Write-Host "  Cloud SQL may not be accessible from this machine." -ForegroundColor Gray
        Write-Host "  Options:" -ForegroundColor Gray
        Write-Host "    1. Run migrations from Cloud Shell: gcloud cloud-shell ssh" -ForegroundColor Gray
        Write-Host "    2. Use Cloud SQL Proxy: https://cloud.google.com/sql/docs/postgres/sql-proxy" -ForegroundColor Gray
        Write-Host "    3. If migrations already applied, continue with -SkipMigrations" -ForegroundColor Gray
        Write-Host "  Attempting schema verification to check if migrations are already applied..." -ForegroundColor Yellow
    } else {
        Write-Host "  Platform ID migration: OK" -ForegroundColor Green
    }

    # 3b: Fraud detection migration
    Write-Host ""
    Write-Host "  3b. Fraud detection migration (fraud_indicators, device_fingerprint, etc.)..." -ForegroundColor Gray
    python run_fraud_migration_sync.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNING: Fraud detection migration failed (connection timeout)" -ForegroundColor Yellow
        Write-Host "  See options above for running migrations." -ForegroundColor Gray
        Write-Host "  Attempting schema verification to check if migrations are already applied..." -ForegroundColor Yellow
    } else {
        Write-Host "  Fraud detection migration: OK" -ForegroundColor Green
    }

    Pop-Location
} else {
    Write-Host ""
    Write-Host "Step 3: Skipping migrations ( -SkipMigrations )" -ForegroundColor Yellow
}

# Step 4: Verify schema
Write-Host ""
Write-Host "Step 4: Verifying database schema..." -ForegroundColor Yellow
Push-Location $PSScriptRoot
python verify_v2_schema.py
$verifyExit = $LASTEXITCODE
Pop-Location

if ($verifyExit -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Schema verification FAILED. Database is not ready for deployment." -ForegroundColor Red
    Write-Host "Fix the schema issues above before deploying." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "Database is READY for deployment" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""
Write-Host "Next: Run deploy_v2_database.ps1 to deploy the application." -ForegroundColor Cyan
Write-Host ""
