# Redeploy Backend with Fixes
# This script rebuilds and redeploys the backend with improved error logging
# and ensures proper Cloud SQL connection

param(
    [string]$ProjectId = "survey-bot-detection",
    [string]$Region = "northamerica-northeast2",
    [string]$ServiceName = "bot-backend",
    [string]$InstanceName = "bot-db"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Backend Redeployment with Fixes" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$REPO_NAME = "backend"
$IMAGE_NAME = "bot-backend"
$COMMIT_SHA = (git rev-parse --short HEAD)
$IMAGE_TAG = "$Region-docker.pkg.dev/$ProjectId/$REPO_NAME/$IMAGE_NAME`:$COMMIT_SHA"
$CLOUD_SQL_CONNECTION = "$ProjectId`:$Region`:$InstanceName"

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Project: $ProjectId" -ForegroundColor White
Write-Host "  Region: $Region" -ForegroundColor White
Write-Host "  Service: $ServiceName" -ForegroundColor White
Write-Host "  Image Tag: $IMAGE_TAG" -ForegroundColor White
Write-Host "  Cloud SQL: $CLOUD_SQL_CONNECTION" -ForegroundColor White
Write-Host ""

# Step 1: Build new image with fixes
Write-Host "Step 1: Building Docker image with fixes..." -ForegroundColor Green
Write-Host ""

Set-Location backend

try {
    Write-Host "Building image: $IMAGE_TAG" -ForegroundColor Yellow
    
    docker build -t $IMAGE_TAG .
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Docker build failed!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✓ Image built successfully" -ForegroundColor Green
    Write-Host ""
    
    # Step 2: Push image
    Write-Host "Step 2: Pushing image to Artifact Registry..." -ForegroundColor Green
    
    docker push $IMAGE_TAG
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Docker push failed!" -ForegroundColor Red
        Write-Host ""
        Write-Host "You may need to configure Docker auth:" -ForegroundColor Yellow
        Write-Host "gcloud auth configure-docker $Region-docker.pkg.dev" -ForegroundColor White
        exit 1
    }
    
    Write-Host "✓ Image pushed successfully" -ForegroundColor Green
    Write-Host ""
    
} catch {
    Write-Host "❌ Error during build/push: $_" -ForegroundColor Red
    exit 1
} finally {
    Set-Location ..
}

# Step 3: Deploy to Cloud Run
Write-Host "Step 3: Deploying to Cloud Run..." -ForegroundColor Green
Write-Host ""

try {
    Write-Host "Deploying service: $ServiceName" -ForegroundColor Yellow
    
    # Remove vpc-access-egress annotation to enable split routing:
    # - Private IPs (Cloud SQL) → VPC connector
    # - Public IPs (OpenAI API) → Default internet gateway
    gcloud run deploy $ServiceName `
        --image=$IMAGE_TAG `
        --region=$Region `
        --project=$ProjectId `
        --platform=managed `
        --allow-unauthenticated `
        --vpc-connector=serverless-connector `
        --update-annotations="run.googleapis.com/vpc-access-egress=" `
        --add-cloudsql-instances=$CLOUD_SQL_CONNECTION `
        --set-secrets="DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=SECRET_KEY:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest" `
        --set-env-vars="DEBUG=false,LOG_LEVEL=INFO,ALLOWED_ORIGINS=[`"*`"]" `
        --memory=1Gi `
        --cpu=1 `
        --concurrency=80 `
        --min-instances=1 `
        --max-instances=10 `
        --timeout=60s
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Deployment failed!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "✓ Deployment successful!" -ForegroundColor Green
    Write-Host ""
    
} catch {
    Write-Host "❌ Error during deployment: $_" -ForegroundColor Red
    exit 1
}

# Step 4: Get service URL
Write-Host "Step 4: Getting service URL..." -ForegroundColor Green

$SERVICE_URL = (gcloud run services describe $ServiceName `
    --region=$Region `
    --project=$ProjectId `
    --format="value(status.url)")

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Service URL: $SERVICE_URL" -ForegroundColor Green
Write-Host ""
Write-Host "Test endpoints:" -ForegroundColor Yellow
Write-Host "  Health: $SERVICE_URL/health" -ForegroundColor White
Write-Host "  API: $SERVICE_URL/api/v1" -ForegroundColor White
Write-Host "  Docs: $SERVICE_URL/docs" -ForegroundColor White
Write-Host ""

# Step 5: Test health endpoint
Write-Host "Step 5: Testing health endpoint..." -ForegroundColor Green

try {
    $healthResponse = Invoke-RestMethod -Uri "$SERVICE_URL/health" -Method Get -TimeoutSec 10
    Write-Host "✓ Health check passed!" -ForegroundColor Green
    Write-Host "  Response: $($healthResponse | ConvertTo-Json -Compress)" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "⚠ Health check failed: $_" -ForegroundColor Yellow
    Write-Host ""
}

# Step 6: Test session creation
Write-Host "Step 6: Testing session creation..." -ForegroundColor Green

try {
    $sessionResponse = Invoke-RestMethod `
        -Uri "$SERVICE_URL/api/v1/detection/sessions?platform=web" `
        -Method Post `
        -Headers @{"User-Agent"="Test Script"} `
        -TimeoutSec 30
    
    Write-Host "✓ Session creation successful!" -ForegroundColor Green
    Write-Host "  Session ID: $($sessionResponse.session_id)" -ForegroundColor Gray
    Write-Host ""
} catch {
    $errorDetails = $_.ErrorDetails.Message
    if ($errorDetails) {
        $errorObj = $errorDetails | ConvertFrom-Json
        Write-Host "❌ Session creation failed: $($errorObj.detail)" -ForegroundColor Red
    } else {
        Write-Host "❌ Session creation failed: $_" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Check logs with:" -ForegroundColor Yellow
    Write-Host "gcloud logging read `"resource.type=cloud_run_revision AND resource.labels.service_name=$ServiceName`" --limit=20 --project=$ProjectId" -ForegroundColor White
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. ✓ Backend redeployed with improved error logging" -ForegroundColor Green
Write-Host "2. ⚠ Check logs if session creation still fails" -ForegroundColor Yellow
Write-Host "3. ⚠ Run full production test suite" -ForegroundColor Yellow
Write-Host ""
Write-Host "To run production tests:" -ForegroundColor Yellow
Write-Host "cd backend" -ForegroundColor White
Write-Host "python test_production_text_analysis.py" -ForegroundColor White
Write-Host ""
