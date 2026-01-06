# Setup Cloud NAT for Cloud Run Internet Access
# This script creates a Cloud Router and Cloud NAT to allow Cloud Run instances
# to access the internet (e.g., OpenAI API) while using a VPC connector

param(
    [string]$ProjectId = "survey-bot-detection",
    [string]$Region = "northamerica-northeast2",
    [string]$RouterName = "serverless-connector-router",
    [string]$NatName = "serverless-connector-nat",
    [string]$NetworkName = "default"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Cloud NAT Setup for Internet Access" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will enable internet access for Cloud Run instances" -ForegroundColor Yellow
Write-Host "using the VPC connector (required for OpenAI API calls)" -ForegroundColor Yellow
Write-Host ""

# Check if router already exists
Write-Host "Step 1: Checking for existing Cloud Router..." -ForegroundColor Green
$existingRouter = gcloud compute routers describe $RouterName `
    --region=$Region `
    --project=$ProjectId `
    --format='value(name)' 2>$null

if ($existingRouter) {
    Write-Host "✓ Cloud Router '$RouterName' already exists" -ForegroundColor Green
} else {
    Write-Host "Creating Cloud Router..." -ForegroundColor Yellow
    gcloud compute routers create $RouterName `
        --network=$NetworkName `
        --region=$Region `
        --project=$ProjectId
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create Cloud Router!" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Cloud Router created successfully" -ForegroundColor Green
}

Write-Host ""

# Check if NAT already exists
Write-Host "Step 2: Checking for existing Cloud NAT..." -ForegroundColor Green
$existingNat = gcloud compute routers nats describe $NatName `
    --router=$RouterName `
    --region=$Region `
    --project=$ProjectId `
    --format='value(name)' 2>$null

if ($existingNat) {
    Write-Host "✓ Cloud NAT '$NatName' already exists" -ForegroundColor Green
    Write-Host ""
    Write-Host "Cloud NAT is already configured. No changes needed." -ForegroundColor Yellow
} else {
    Write-Host "Creating Cloud NAT..." -ForegroundColor Yellow
    gcloud compute routers nats create $NatName `
        --router=$RouterName `
        --region=$Region `
        --nat-all-subnet-ip-ranges `
        --auto-allocate-nat-external-ips `
        --project=$ProjectId
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create Cloud NAT!" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Cloud NAT created successfully" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Cloud NAT Setup Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Cloud Run instances can now access the internet." -ForegroundColor Green
Write-Host "OpenAI API calls should work after this configuration." -ForegroundColor Green
Write-Host ""
Write-Host "Note: It may take a few minutes for the changes to propagate." -ForegroundColor Yellow
Write-Host ""

# Verify configuration
Write-Host "Verifying configuration..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Router:" -ForegroundColor Cyan
gcloud compute routers describe $RouterName `
    --region=$Region `
    --project=$ProjectId `
    --format='table(name,region,network)'

Write-Host ""
Write-Host "NAT:" -ForegroundColor Cyan
gcloud compute routers nats describe $NatName `
    --router=$RouterName `
    --region=$Region `
    --project=$ProjectId `
    --format='table(name,router,region,natIpAllocateOption,natIps)'

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Wait 2-3 minutes for changes to propagate" -ForegroundColor White
Write-Host "2. Test OpenAI API calls by running:" -ForegroundColor White
Write-Host "   cd backend" -ForegroundColor Gray
Write-Host "   python test_production_text_analysis.py" -ForegroundColor Gray
Write-Host ""
