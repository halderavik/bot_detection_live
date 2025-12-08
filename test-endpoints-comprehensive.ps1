# Comprehensive API Endpoint Testing
$BASE_URL = "https://bot-backend-119522247395.northamerica-northeast2.run.app"
$API_BASE = "$BASE_URL/api/v1"
$HEADERS = @{"Content-Type" = "application/json"; "Accept" = "application/json"}

$results = @()
$passed = 0
$failed = 0

function Test-Endpoint {
    param([string]$Method, [string]$Url, [object]$Body = $null, [string]$Description)
    
    Write-Host "`n[$Method] $Url" -ForegroundColor Cyan
    Write-Host "  $Description" -ForegroundColor Gray
    
    try {
        $params = @{Uri = $Url; Method = $Method; Headers = $HEADERS; ErrorAction = "Stop"}
        if ($Body) { $params.Body = ($Body | ConvertTo-Json -Depth 10) }
        
        $response = Invoke-RestMethod @params
        Write-Host "  ✅ PASSED" -ForegroundColor Green
        $script:passed++
        return @{Status = "PASSED"; Response = $response}
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        $errorMsg = $_.Exception.Message
        Write-Host "  ❌ FAILED ($statusCode)" -ForegroundColor Red
        
        # Try to get error details
        if ($_.Exception.Response) {
            try {
                $stream = $_.Exception.Response.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($stream)
                $errorBody = $reader.ReadToEnd()
                if ($errorBody) { Write-Host "  Error: $errorBody" -ForegroundColor Yellow }
            } catch {}
        }
        
        $script:failed++
        return @{Status = "FAILED"; Error = "$statusCode - $errorMsg"}
    }
}

Write-Host "========================================" -ForegroundColor Yellow
Write-Host "Comprehensive API Endpoint Testing" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

# 1. Root & Health
Write-Host "`n=== Health & Monitoring ===" -ForegroundColor Magenta
Test-Endpoint -Method "GET" -Url "$BASE_URL/" -Description "Root endpoint"
Test-Endpoint -Method "GET" -Url "$BASE_URL/health" -Description "Health check"
Test-Endpoint -Method "GET" -Url "$BASE_URL/docs" -Description "API documentation"

# 2. Session Management
Write-Host "`n=== Session Management ===" -ForegroundColor Magenta
$sessionResult = Test-Endpoint -Method "POST" -Url "$API_BASE/detection/sessions" -Body @{} -Description "Create session"
$sessionId = $null
if ($sessionResult.Status -eq "PASSED" -and $sessionResult.Response.session_id) {
    $sessionId = $sessionResult.Response.session_id
    Write-Host "  Created session: $sessionId" -ForegroundColor Green
    Test-Endpoint -Method "GET" -Url "$API_BASE/detection/sessions/$sessionId/status" -Description "Get session status"
}

# 3. Event Collection (if session created)
if ($sessionId) {
    Write-Host "`n=== Event Collection ===" -ForegroundColor Magenta
    $eventBody = @{
        event_type = "keystroke"
        timestamp = (Get-Date).ToUniversalTime().ToString("o")
        data = @{key = "a"; key_code = 65}
    }
    Test-Endpoint -Method "POST" -Url "$API_BASE/detection/sessions/$sessionId/events" -Body $eventBody -Description "Submit event"
}

# 4. Dashboard
Write-Host "`n=== Dashboard ===" -ForegroundColor Magenta
Test-Endpoint -Method "GET" -Url "$API_BASE/dashboard/overview" -Description "Dashboard overview"
Test-Endpoint -Method "GET" -Url "$API_BASE/dashboard/sessions?page=1&limit=10" -Description "List sessions"
Test-Endpoint -Method "GET" -Url "$API_BASE/dashboard/test" -Description "Dashboard test endpoint"

# 5. Text Analysis
Write-Host "`n=== Text Analysis ===" -ForegroundColor Magenta
Test-Endpoint -Method "GET" -Url "$API_BASE/text-analysis/health" -Description "Text analysis health"
Test-Endpoint -Method "GET" -Url "$API_BASE/text-analysis/stats" -Description "Text analysis stats"
Test-Endpoint -Method "GET" -Url "$API_BASE/text-analysis/dashboard/summary?days=7" -Description "Text analysis dashboard summary"

if ($sessionId) {
    Test-Endpoint -Method "GET" -Url "$API_BASE/text-analysis/sessions/$sessionId/summary" -Description "Session text analysis summary"
}

# 6. Reports
Write-Host "`n=== Reports ===" -ForegroundColor Magenta
$surveysResult = Test-Endpoint -Method "GET" -Url "$API_BASE/reports/surveys" -Description "List available surveys"
$testSurveyId = $null
if ($surveysResult.Status -eq "PASSED" -and $surveysResult.Response.surveys -and $surveysResult.Response.surveys.Count -gt 0) {
    $testSurveyId = $surveysResult.Response.surveys[0].survey_id
    Test-Endpoint -Method "GET" -Url "$API_BASE/reports/summary/$testSurveyId" -Description "Get survey summary report"
}

# 7. Hierarchical API
Write-Host "`n=== Hierarchical API (V2) ===" -ForegroundColor Magenta
Test-Endpoint -Method "GET" -Url "$API_BASE/surveys" -Description "List all surveys"
if ($testSurveyId) {
    Test-Endpoint -Method "GET" -Url "$API_BASE/surveys/$testSurveyId" -Description "Get survey details"
    Test-Endpoint -Method "GET" -Url "$API_BASE/surveys/$testSurveyId/summary" -Description "Get survey summary"
    Test-Endpoint -Method "GET" -Url "$API_BASE/surveys/$testSurveyId/platforms" -Description "List platforms"
}

# 8. Integrations
Write-Host "`n=== Integrations ===" -ForegroundColor Magenta
Test-Endpoint -Method "GET" -Url "$API_BASE/integrations/status" -Description "Integration status"

# Summary
Write-Host "`n========================================" -ForegroundColor Yellow
Write-Host "Test Summary" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "Total: $($passed + $failed) | ✅ Passed: $passed | ❌ Failed: $failed" -ForegroundColor White
Write-Host ""

if ($failed -eq 0) {
    Write-Host "🎉 All endpoints working!" -ForegroundColor Green
} else {
    Write-Host "⚠️  $failed endpoint(s) failed" -ForegroundColor Yellow
    Write-Host "`nNote: Some failures may be expected (e.g., 500 errors from database issues)" -ForegroundColor Gray
}

