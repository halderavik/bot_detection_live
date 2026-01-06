# Deploy Backend with bot-db-v2 and OPENAI_API_KEY
# This script builds and deploys the backend using bot-db-v2 Cloud SQL instance
# and ensures OPENAI_API_KEY is properly configured

param(
    [string]$ProjectId = "survey-bot-detection",
    [string]$Region = "northamerica-northeast2",
    [string]$ServiceName = "bot-backend",
    [string]$InstanceName = "bot-db-v2",
    [string]$DatabaseName = "bot_detection_v2"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Backend Deployment with bot-db-v2" -ForegroundColor Cyan
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
Write-Host "  Cloud SQL Instance: $InstanceName" -ForegroundColor White
Write-Host "  Database: $DatabaseName" -ForegroundColor White
Write-Host "  Image Tag: $IMAGE_TAG" -ForegroundColor White
Write-Host "  Cloud SQL Connection: $CLOUD_SQL_CONNECTION" -ForegroundColor White
Write-Host ""

# Step 1: Verify Cloud SQL instance exists
Write-Host "Step 1: Verifying Cloud SQL instance..." -ForegroundColor Green
Write-Host ""

$instances = gcloud sql instances list --project=$ProjectId --format='value(name)' 2>$null
if ($instances -contains $InstanceName) {
    Write-Host "✓ Cloud SQL instance '$InstanceName' exists" -ForegroundColor Green
} else {
    Write-Host "❌ Cloud SQL instance '$InstanceName' not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Available instances:" -ForegroundColor Yellow
    gcloud sql instances list --project=$ProjectId --format='table(name,region,databaseVersion)'
    Write-Host ""
    Write-Host "Please create the instance or use an existing one." -ForegroundColor Yellow
    exit 1
}

# Step 2: Verify database exists
Write-Host ""
Write-Host "Step 2: Verifying database exists..." -ForegroundColor Green
Write-Host ""

$databases = gcloud sql databases list --instance=$InstanceName --project=$ProjectId --format='value(name)' 2>$null
if ($databases -contains $DatabaseName) {
    Write-Host "✓ Database '$DatabaseName' exists" -ForegroundColor Green
} else {
    Write-Host "⚠ Database '$DatabaseName' not found. Creating..." -ForegroundColor Yellow
    gcloud sql databases create $DatabaseName `
        --instance=$InstanceName `
        --project=$ProjectId
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Database created successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to create database" -ForegroundColor Red
        exit 1
    }
}

# Step 3: Verify secrets exist
Write-Host ""
Write-Host "Step 3: Verifying secrets..." -ForegroundColor Green
Write-Host ""

$requiredSecrets = @("DATABASE_URL", "SECRET_KEY", "OPENAI_API_KEY")
$missingSecrets = @()

foreach ($secret in $requiredSecrets) {
    $secretExists = gcloud secrets describe $secret --project=$ProjectId 2>$null
    if ($secretExists) {
        Write-Host "✓ Secret '$secret' exists" -ForegroundColor Green
    } else {
        Write-Host "❌ Secret '$secret' not found!" -ForegroundColor Red
        $missingSecrets += $secret
    }
}

if ($missingSecrets.Count -gt 0) {
    Write-Host ""
    Write-Host "Missing secrets detected. Please create them:" -ForegroundColor Yellow
    foreach ($secret in $missingSecrets) {
        if ($secret -eq "DATABASE_URL") {
            Write-Host ""
            Write-Host "Create DATABASE_URL secret:" -ForegroundColor Yellow
            Write-Host "  `$dbUrl = 'postgresql+asyncpg://bot_user:PASSWORD@/$DatabaseName?host=/cloudsql/$CLOUD_SQL_CONNECTION'" -ForegroundColor White
            Write-Host "  echo `$dbUrl | gcloud secrets create DATABASE_URL --data-file=- --project=$ProjectId" -ForegroundColor White
        } elseif ($secret -eq "OPENAI_API_KEY") {
            Write-Host ""
            Write-Host "Create OPENAI_API_KEY secret:" -ForegroundColor Yellow
            Write-Host "  echo 'YOUR_OPENAI_API_KEY' | gcloud secrets create OPENAI_API_KEY --data-file=- --project=$ProjectId" -ForegroundColor White
        } elseif ($secret -eq "SECRET_KEY") {
            Write-Host ""
            Write-Host "Create SECRET_KEY secret:" -ForegroundColor Yellow
            Write-Host "  `$secretKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 64 | ForEach-Object {[char]$_})" -ForegroundColor White
            Write-Host "  echo `$secretKey | gcloud secrets create SECRET_KEY --data-file=- --project=$ProjectId" -ForegroundColor White
        }
    }
    Write-Host ""
    Write-Host "After creating secrets, run this script again." -ForegroundColor Yellow
    exit 1
}

# Step 4: Verify DATABASE_URL points to correct database
Write-Host ""
Write-Host "Step 4: Verifying DATABASE_URL configuration..." -ForegroundColor Green
Write-Host ""

$currentDbUrl = gcloud secrets versions access latest --secret=DATABASE_URL --project=$ProjectId 2>$null
if ($currentDbUrl -match $DatabaseName -and $currentDbUrl -match $InstanceName) {
    Write-Host "✓ DATABASE_URL points to correct database and instance" -ForegroundColor Green
} else {
    Write-Host "⚠ DATABASE_URL may not point to $DatabaseName on $InstanceName" -ForegroundColor Yellow
    Write-Host "  Current URL (first 80 chars): $($currentDbUrl.Substring(0, [Math]::Min(80, $currentDbUrl.Length)))..." -ForegroundColor Gray
    Write-Host ""
    Write-Host "To update DATABASE_URL:" -ForegroundColor Yellow
    Write-Host "  `$dbUrl = 'postgresql+asyncpg://bot_user:PASSWORD@/$DatabaseName?host=/cloudsql/$CLOUD_SQL_CONNECTION'" -ForegroundColor White
    Write-Host "  echo `$dbUrl | gcloud secrets versions add DATABASE_URL --data-file=- --project=$ProjectId" -ForegroundColor White
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        exit 1
    }
}

# Step 5: Build Docker image
Write-Host ""
Write-Host "Step 5: Building Docker image..." -ForegroundColor Green
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
    
    # Step 6: Push image
    Write-Host "Step 6: Pushing image to Artifact Registry..." -ForegroundColor Green
    Write-Host ""
    
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

# Step 7: Deploy to Cloud Run
Write-Host ""
Write-Host "Step 7: Deploying to Cloud Run..." -ForegroundColor Green
Write-Host ""

try {
    Write-Host "Deploying service: $ServiceName" -ForegroundColor Yellow
    Write-Host "  Using Cloud SQL instance: $InstanceName" -ForegroundColor Gray
    Write-Host "  Using database: $DatabaseName" -ForegroundColor Gray
    Write-Host "  Including OPENAI_API_KEY secret" -ForegroundColor Gray
    Write-Host ""
    
    # Deploy without vpc-egress flag to enable split routing:
    # - Private IPs (Cloud SQL) → VPC connector
    # - Public IPs (OpenAI API) → Default internet gateway
    # Note: Not specifying --vpc-egress enables split routing automatically
    gcloud run deploy $ServiceName `
        --image=$IMAGE_TAG `
        --region=$Region `
        --project=$ProjectId `
        --platform=managed `
        --allow-unauthenticated `
        --vpc-connector=serverless-connector `
        --vpc-egress=private-ranges-only `
        --add-cloudsql-instances=$CLOUD_SQL_CONNECTION `
        --set-secrets="DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=SECRET_KEY:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest" `
        --set-env-vars='DEBUG=false,LOG_LEVEL=INFO,ALLOWED_ORIGINS=["*"]' `
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

# Step 8: Get service URL
Write-Host ""
Write-Host "Step 8: Getting service URL..." -ForegroundColor Green

$SERVICE_URL = (gcloud run services describe $ServiceName `
    --region=$Region `
    --project=$ProjectId `
    --format='value(status.url)')

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
Write-Host "  Text Analysis Health: $SERVICE_URL/api/v1/text-analysis/health" -ForegroundColor White
Write-Host ""

# Step 9: Test health endpoint
Write-Host "Step 9: Testing health endpoint..." -ForegroundColor Green

try {
    $healthResponse = Invoke-RestMethod -Uri "$SERVICE_URL/health" -Method Get -TimeoutSec 10
    Write-Host "✓ Health check passed!" -ForegroundColor Green
    Write-Host "  Response: $($healthResponse | ConvertTo-Json -Compress)" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "⚠ Health check failed: $_" -ForegroundColor Yellow
    Write-Host ""
}

# Step 10: Test OpenAI integration
Write-Host "Step 10: Testing OpenAI integration..." -ForegroundColor Green

try {
    $openaiHealthResponse = Invoke-RestMethod -Uri "$SERVICE_URL/api/v1/text-analysis/health" -Method Get -TimeoutSec 10
    if ($openaiHealthResponse.openai_available) {
        Write-Host "✓ OpenAI integration is working!" -ForegroundColor Green
        Write-Host "  OpenAI Available: $($openaiHealthResponse.openai_available)" -ForegroundColor Gray
        Write-Host "  Model: $($openaiHealthResponse.model)" -ForegroundColor Gray
    }
    else {
        Write-Host "⚠ OpenAI integration not available" -ForegroundColor Yellow
        Write-Host "  Check that OPENAI_API_KEY secret is set correctly" -ForegroundColor Yellow
    }
    Write-Host ""
}
catch {
    Write-Host "⚠ OpenAI health check failed: $_" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. ✓ Backend deployed with bot-db-v2" -ForegroundColor Green
Write-Host "2. ✓ OPENAI_API_KEY included in deployment" -ForegroundColor Green
Write-Host "3. ⚠ Verify database connection in logs" -ForegroundColor Yellow
Write-Host "4. ⚠ Test text analysis endpoints" -ForegroundColor Yellow
Write-Host ""
Write-Host "To check logs:" -ForegroundColor Yellow
Write-Host "gcloud logging read `"resource.type=cloud_run_revision AND resource.labels.service_name=$ServiceName`" --limit=50 --project=$ProjectId" -ForegroundColor White
Write-Host ""
