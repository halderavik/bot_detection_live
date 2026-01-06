
# Step 10: Test OpenAI integration
Write-Host "Step 10: Testing OpenAI integration..." -ForegroundColor Green

try {
    $openaiHealthResponse = Invoke-RestMethod -Uri "$SERVICE_URL/api/v1/text-analysis/health" -Method Get -TimeoutSec 10
    if ($openaiHealthResponse.openai_available) {
        Write-Host "âœ“ OpenAI integration is working!" -ForegroundColor Green
        Write-Host "  OpenAI Available: $($openaiHealthResponse.openai_available)" -ForegroundColor Gray
        Write-Host "  Model: $($openaiHealthResponse.model)" -ForegroundColor Gray
    } else {
        Write-Host "âš  OpenAI integration not available" -ForegroundColor Yellow
        Write-Host "  Check that OPENAI_API_KEY secret is set correctly" -ForegroundColor Yellow
    }
    Write-Host ""
} catch {
    Write-Host "âš  OpenAI health check failed: $_" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. âœ“ Backend deployed with bot-db-v2" -ForegroundColor Green
Write-Host "2. âœ“ OPENAI_API_KEY included in deployment" -ForegroundColor Green
Write-Host "3. âš  Verify database connection in logs" -ForegroundColor Yellow
Write-Host "4. âš  Test text analysis endpoints" -ForegroundColor Yellow
Write-Host ""
Write-Host "To check logs:" -ForegroundColor Yellow
Write-Host "gcloud logging read `"resource.type=cloud_run_revision AND resource.labels.service_name=$ServiceName`" --limit=50 --project=$ProjectId" -ForegroundColor White
Write-Host ""
