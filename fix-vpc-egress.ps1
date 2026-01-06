# Quick Fix: Remove vpc-access-egress annotation to enable OpenAI API access
# This enables Cloud Run's split routing:
# - Private IPs (Cloud SQL) → VPC connector
# - Public IPs (OpenAI API) → Default internet gateway

param(
    [string]$ProjectId = "survey-bot-detection",
    [string]$Region = "northamerica-northeast2",
    [string]$ServiceName = "bot-backend"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fix VPC Egress for OpenAI API Access" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check current annotation
Write-Host "Step 1: Checking current VPC egress configuration..." -ForegroundColor Green
$currentEgress = gcloud run services describe $ServiceName `
    --region=$Region `
    --project=$ProjectId `
    --format="value(spec.template.metadata.annotations['run.googleapis.com/vpc-access-egress'])" 2>$null

if ($currentEgress -eq "private-ranges-only") {
    Write-Host "  Current setting: private-ranges-only (blocks OpenAI API)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Step 2: Removing annotation to enable split routing..." -ForegroundColor Green
    
    # Remove the annotation by updating the service
    gcloud run services update $ServiceName `
        --region=$Region `
        --project=$ProjectId `
        --update-annotations="run.googleapis.com/vpc-access-egress="
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to update service!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✓ Annotation removed successfully" -ForegroundColor Green
} elseif ([string]::IsNullOrEmpty($currentEgress)) {
    Write-Host "  Current setting: Not set (split routing enabled)" -ForegroundColor Green
    Write-Host "  No changes needed - split routing is already enabled!" -ForegroundColor Green
} else {
    Write-Host "  Current setting: $currentEgress" -ForegroundColor Yellow
    Write-Host "  Removing annotation..." -ForegroundColor Yellow
    
    gcloud run services update $ServiceName `
        --region=$Region `
        --project=$ProjectId `
        --update-annotations="run.googleapis.com/vpc-access-egress="
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to update service!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✓ Annotation removed successfully" -ForegroundColor Green
}

Write-Host ""
Write-Host "Step 3: Verifying configuration..." -ForegroundColor Green
$newEgress = gcloud run services describe $ServiceName `
    --region=$Region `
    --project=$ProjectId `
    --format="value(spec.template.metadata.annotations['run.googleapis.com/vpc-access-egress'])" 2>$null

if ([string]::IsNullOrEmpty($newEgress)) {
    Write-Host "✓ Split routing is now enabled!" -ForegroundColor Green
    Write-Host "  - Private IPs (Cloud SQL) → VPC connector" -ForegroundColor Gray
    Write-Host "  - Public IPs (OpenAI API) → Default internet gateway" -ForegroundColor Gray
} else {
    Write-Host "⚠ Warning: Annotation still present: $newEgress" -ForegroundColor Yellow
    Write-Host "  You may need to wait a moment and check again." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fix Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Wait 1-2 minutes for changes to propagate" -ForegroundColor White
Write-Host "2. Test OpenAI API calls:" -ForegroundColor White
Write-Host "   cd backend" -ForegroundColor Gray
Write-Host "   python test_production_text_analysis.py" -ForegroundColor Gray
Write-Host ""
