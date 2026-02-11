# PowerShell script to deploy bot_detection_v2 database setup
# This script automates the deployment process for the new database
# IMPORTANT: Runs database preparation (migrations + verification) BEFORE deploying

param(
    [string]$ProjectId = "survey-bot-detection",
    [string]$Region = "northamerica-northeast2",
    [string]$InstanceName = "bot-db",
    [string]$DatabaseName = "bot_detection_v2",
    [string]$ServiceName = "bot-backend",
    [string]$ImageTag = "v2-fresh-db",
    [switch]$SkipDbPrep
)

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "Bot Detection V2 Database Deployment" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

# Step 0: Prepare database (migrations + verification) - REQUIRED before deploy
if (-not $SkipDbPrep) {
    Write-Host "Step 0: Preparing database (migrations + schema verification)..." -ForegroundColor Yellow
    $prepScript = Join-Path $PSScriptRoot "prepare_database_for_deploy.ps1"
    if (Test-Path $prepScript) {
        & $prepScript -ProjectId $ProjectId -InstanceName $InstanceName -DatabaseName $DatabaseName
        if ($LASTEXITCODE -ne 0) {
            Write-Host ""
            Write-Host "ABORT: Database preparation failed. Fix issues above before deploying." -ForegroundColor Red
            Write-Host "Use -SkipDbPrep to deploy without running migrations (not recommended)." -ForegroundColor Gray
            exit 1
        }
        Write-Host "  Database preparation: OK" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: prepare_database_for_deploy.ps1 not found. Proceeding without DB prep." -ForegroundColor Yellow
    }
} else {
    Write-Host "Step 0: Skipping database preparation ( -SkipDbPrep )" -ForegroundColor Yellow
}

# Step 1: Verify database exists
Write-Host "Step 1: Checking if database exists..." -ForegroundColor Yellow
$databases = gcloud sql databases list --instance=$InstanceName --project=$ProjectId --format="value(name)"
if ($databases -contains $DatabaseName) {
    Write-Host "[OK] Database $DatabaseName already exists" -ForegroundColor Green
} else {
    Write-Host "Creating database $DatabaseName..." -ForegroundColor Yellow
    gcloud sql databases create $DatabaseName `
        --instance=$InstanceName `
        --project=$ProjectId
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Database created successfully" -ForegroundColor Green
    } else {
        Write-Host "[X] Failed to create database" -ForegroundColor Red
        exit 1
    }
}

# Step 2: Verify DATABASE_URL secret
Write-Host ""
Write-Host "Step 2: Checking DATABASE_URL secret..." -ForegroundColor Yellow
$currentUrl = gcloud secrets versions access latest --secret=DATABASE_URL --project=$ProjectId 2>$null
if ($currentUrl -match $DatabaseName) {
    Write-Host "[OK] DATABASE_URL already points to $DatabaseName" -ForegroundColor Green
    $urlPreview = if ($currentUrl) { $currentUrl.Substring(0, [Math]::Min(80, $currentUrl.Length)) } else { "..." }
    Write-Host "  Current URL: $urlPreview..." -ForegroundColor Gray
} else {
    Write-Host "[!] DATABASE_URL does not point to $DatabaseName" -ForegroundColor Yellow
    Write-Host "  Update DATABASE_URL secret to point to $DatabaseName" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To update DATABASE_URL, run:" -ForegroundColor Cyan
    Write-Host "  See README or PRODUCTION_DB_MIGRATION.md for DATABASE_URL update steps" -ForegroundColor White
}

# Step 3: Build and push Docker image
Write-Host ""
Write-Host "Step 3: Building Docker image..." -ForegroundColor Yellow
$imageName = "$Region-docker.pkg.dev/$ProjectId/backend/bot-backend`:$ImageTag"
Write-Host "  Image: $imageName" -ForegroundColor Gray

Push-Location $PSScriptRoot
docker build -t $imageName .
if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] Docker build failed" -ForegroundColor Red
    Pop-Location
    exit 1
}
Write-Host "[OK] Docker image built successfully" -ForegroundColor Green

Write-Host ""
Write-Host "Pushing image to Artifact Registry..." -ForegroundColor Yellow
docker push $imageName
if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] Docker push failed" -ForegroundColor Red
    Pop-Location
    exit 1
}
Write-Host "[OK] Image pushed successfully" -ForegroundColor Green
Pop-Location

# Step 4: Deploy to Cloud Run
Write-Host ""
Write-Host "Step 4: Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $ServiceName `
    --image $imageName `
    --region $Region `
    --platform managed `
    --add-cloudsql-instances "$ProjectId`:$Region`:$InstanceName" `
    --set-secrets DATABASE_URL=DATABASE_URL:latest `
    --set-secrets SECRET_KEY=SECRET_KEY:latest `
    --set-secrets OPENAI_API_KEY=OPENAI_API_KEY:latest `
    --allow-unauthenticated `
    --project=$ProjectId `
    --memory 512Mi `
    --cpu 1 `
    --timeout 300 `
    --max-instances 10

if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] Deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Deployment successful" -ForegroundColor Green

# Step 5: Get service URL
Write-Host ""
Write-Host "Step 5: Getting service URL..." -ForegroundColor Yellow
$serviceUrl = gcloud run services describe $ServiceName --region=$Region --project=$ProjectId --format="value(status.url)"
Write-Host "[OK] Service URL: $serviceUrl" -ForegroundColor Green

# Step 6: Test health endpoint
Write-Host ""
Write-Host "Step 6: Testing health endpoint..." -ForegroundColor Yellow
Start-Sleep -Seconds 5  # Wait for service to be ready
try {
    $healthResponse = Invoke-RestMethod -Uri "$serviceUrl/health" -Method Get -ErrorAction Stop
    Write-Host "[OK] Health check passed: $($healthResponse | ConvertTo-Json -Compress)" -ForegroundColor Green
} catch {
    Write-Host "[!] Health check failed: $_" -ForegroundColor Yellow
    Write-Host "  This might be normal if the service is still starting up." -ForegroundColor Gray
}

# Step 7: Check logs for schema initialization
Write-Host ""
Write-Host "Step 7: Checking logs for schema initialization..." -ForegroundColor Yellow
Write-Host "  Checking for Database tables created successfully message..." -ForegroundColor Gray
Start-Sleep -Seconds 10  # Wait for logs to appear
$logsFilter = "resource.type=cloud_run_revision AND resource.labels.service_name=$ServiceName AND textPayload=~Database tables created"
$logs = gcloud logging read $logsFilter --limit=1 --format="value(textPayload)" --project=$ProjectId 2>$null
if ($logs) {
    Write-Host "[OK] Schema initialized successfully" -ForegroundColor Green
} else {
    Write-Host "[!] Schema initialization message not found in logs" -ForegroundColor Yellow
    Write-Host "  This might mean:" -ForegroundColor Gray
    Write-Host "    - Tables already exist" -ForegroundColor Gray
    Write-Host "    - Connection issue preventing initialization" -ForegroundColor Gray
    Write-Host "    - Logs have not appeared yet (check manually)" -ForegroundColor Gray
}

# Summary
Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "Deployment Summary" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "Database: $DatabaseName" -ForegroundColor White
Write-Host "Service: $ServiceName" -ForegroundColor White
Write-Host "URL: $serviceUrl" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Test session creation: POST $serviceUrl/api/v1/detection/sessions?platform_id=test" -ForegroundColor Cyan
Write-Host "  2. Verify schema: cd backend; python verify_v2_schema.py" -ForegroundColor Cyan
Write-Host "  3. Test V2 hierarchical endpoints: GET $serviceUrl/api/v1/surveys" -ForegroundColor Cyan
Write-Host "  4. Check logs via: gcloud logging read --project=$ProjectId" -ForegroundColor Cyan
Write-Host ""
