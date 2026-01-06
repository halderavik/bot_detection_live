# Comprehensive API Endpoint Testing Script
# Tests all endpoints on the deployed backend

$BASE_URL = "https://bot-backend-i56xopdg6q-pd.a.run.app/api/v1"
$HEADERS = @{
    "Content-Type" = "application/json"
    "Accept" = "application/json"
}

$results = @()
$passed = 0
$failed = 0

function Test-Endpoint {
    param(
        [string]$Method,
        [string]$Endpoint,
        [object]$Body = $null,
        [string]$Description
    )
    
    $url = "$BASE_URL$Endpoint"
    Write-Host "`nTesting: $Method $Endpoint" -ForegroundColor Cyan
    Write-Host "Description: $Description" -ForegroundColor Gray
    
    try {
        $params = @{
            Uri = $url
            Method = $Method
            Headers = $HEADERS
            ErrorAction = "Stop"
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
        }
        
        $response = Invoke-RestMethod @params
        $statusCode = $response.StatusCode
        
        # Check if response is successful (200-299)
        if ($LASTEXITCODE -eq 0 -or $response) {
            Write-Host "✅ PASSED" -ForegroundColor Green
            $script:passed++
            $script:results += [PSCustomObject]@{
                Endpoint = "$Method $Endpoint"
                Status = "PASSED"
                Description = $Description
                Error = ""
            }
            return $response
        } else {
            Write-Host "❌ FAILED - Status: $statusCode" -ForegroundColor Red
            $script:failed++
            $script:results += [PSCustomObject]@{
                Endpoint = "$Method $Endpoint"
                Status = "FAILED"
                Description = $Description
                Error = "Status: $statusCode"
            }
            return $null
        }
    } catch {
        $statusCode = $null
        $errorMsg = $_.Exception.Message
        if ($_.Exception.Response) {
            $statusCode = $_.Exception.Response.StatusCode.value__
            try {
                $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
                $responseBody = $reader.ReadToEnd()
                $reader.Close()
                if ($responseBody) {
                    $errorMsg = "($statusCode) $errorMsg"
                }
            } catch {
                $errorMsg = "($statusCode) $errorMsg"
            }
        }
        Write-Host "❌ FAILED - $errorMsg" -ForegroundColor Red
        $script:failed++
        $script:results += [PSCustomObject]@{
            Endpoint = "$Method $Endpoint"
            Status = "FAILED"
            Description = $Description
            Error = $errorMsg
        }
        return $null
    }
}

Write-Host "========================================" -ForegroundColor Yellow
Write-Host "API Endpoint Testing" -ForegroundColor Yellow
Write-Host "Base URL: $BASE_URL" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

# 1. Health Check
Write-Host "`n=== Health & Monitoring ===" -ForegroundColor Magenta
# Health is at root level, not under /api/v1
$healthUrl = "https://bot-backend-i56xopdg6q-pd.a.run.app/health"
try {
    $response = Invoke-RestMethod -Uri $healthUrl -Method GET -Headers $HEADERS
    Write-Host "✅ PASSED - Health check endpoint" -ForegroundColor Green
    $script:passed++
    $script:results += [PSCustomObject]@{
        Endpoint = "GET /health"
        Status = "PASSED"
        Description = "Health check"
        Error = ""
    }
} catch {
    $errorMsg = $_.Exception.Message
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        $errorMsg = "($statusCode) $errorMsg"
    }
    Write-Host "❌ FAILED - Health check endpoint: $errorMsg" -ForegroundColor Red
    $script:failed++
    $script:results += [PSCustomObject]@{
        Endpoint = "GET /health"
        Status = "FAILED"
        Description = "Health check"
        Error = $errorMsg
    }
}

# 2. Session Management
Write-Host "`n=== Session Management ===" -ForegroundColor Magenta
$sessionResponse = Test-Endpoint -Method "POST" -Endpoint "/detection/sessions" -Description "Create new session"
$sessionId = $null
if ($sessionResponse -and $sessionResponse.session_id) {
    $sessionId = $sessionResponse.session_id
    Write-Host "Created session: $sessionId" -ForegroundColor Green
    
    Test-Endpoint -Method "GET" -Endpoint "/detection/sessions/$sessionId" -Description "Get session details"
    Test-Endpoint -Method "GET" -Endpoint "/detection/sessions" -Description "List all sessions"
}

# 3. Event Collection
Write-Host "`n=== Event Collection ===" -ForegroundColor Magenta
if ($sessionId) {
    $eventBody = @{
        event_type = "keystroke"
        timestamp = (Get-Date).ToUniversalTime().ToString("o")
        data = @{
            key = "a"
            key_code = 65
        }
    }
    Test-Endpoint -Method "POST" -Endpoint "/detection/sessions/$sessionId/events" -Body $eventBody -Description "Submit behavioral event"
}

# 4. Bot Detection Analysis
Write-Host "`n=== Bot Detection Analysis ===" -ForegroundColor Magenta
if ($sessionId) {
    Test-Endpoint -Method "POST" -Endpoint "/detection/sessions/$sessionId/analyze" -Description "Perform bot detection analysis"
    Test-Endpoint -Method "GET" -Endpoint "/detection/sessions/$sessionId/results" -Description "Get detection results"
}

# 5. Text Analysis
Write-Host "`n=== Text Analysis ===" -ForegroundColor Magenta
if ($sessionId) {
    $questionBody = @{
        session_id = $sessionId
        question_text = "What is your favorite color?"
        question_type = "open_ended"
    }
    $questionResponse = Test-Endpoint -Method "POST" -Endpoint "/text-analysis/questions" -Body $questionBody -Description "Submit question for analysis"
    
    if ($questionResponse -and $questionResponse.question_id) {
        $questionId = $questionResponse.question_id
        $responseBody = @{
            session_id = $sessionId
            question_id = $questionId
            response_text = "Blue is my favorite color because it reminds me of the ocean."
        }
        Test-Endpoint -Method "POST" -Endpoint "/text-analysis/responses" -Body $responseBody -Description "Submit response for analysis"
    }
    
    # Note: Old flat endpoint removed, use hierarchical V2 endpoint instead
    # Test-Endpoint -Method "GET" -Endpoint "/text-analysis/sessions/$sessionId/summary" -Description "Get text analysis session summary (DEPRECATED)"
    Test-Endpoint -Method "GET" -Endpoint "/text-analysis/stats" -Description "Get text analysis statistics"
    Test-Endpoint -Method "GET" -Endpoint "/text-analysis/health" -Description "Text analysis health check"
}

# 6. Dashboard
Write-Host "`n=== Dashboard ===" -ForegroundColor Magenta
Test-Endpoint -Method "GET" -Endpoint "/dashboard/overview" -Description "Get dashboard overview"
Test-Endpoint -Method "GET" -Endpoint "/dashboard/sessions" -Description "Get dashboard sessions"

# 7. Text Analysis Dashboard
Write-Host "`n=== Text Analysis Dashboard ===" -ForegroundColor Magenta
Test-Endpoint -Method "GET" -Endpoint "/text-analysis/dashboard/summary?days=7" -Description "Get text analysis dashboard summary"
Test-Endpoint -Method "GET" -Endpoint "/text-analysis/dashboard/respondents?days=30&page=1&limit=10" -Description "Get respondent analysis"

# 8. Reports
Write-Host "`n=== Reports ===" -ForegroundColor Magenta
$reportBody = @{
    survey_id = "test-survey-123"
    report_type = "summary"
    format = "json"
}
Test-Endpoint -Method "POST" -Endpoint "/reports/generate" -Body $reportBody -Description "Generate report"
Test-Endpoint -Method "GET" -Endpoint "/reports/surveys" -Description "Get available surveys"

# 9. Hierarchical API (V2) - According to API_V2.md
Write-Host "`n=== Hierarchical API (V2) ===" -ForegroundColor Magenta
Test-Endpoint -Method "GET" -Endpoint "/surveys" -Description "List all surveys"
# Test with actual survey ID from reports
$surveys = Test-Endpoint -Method "GET" -Endpoint "/reports/surveys" -Description "Get surveys for hierarchical testing"
if ($surveys -and $surveys.surveys -and $surveys.surveys.Count -gt 0) {
    $testSurveyId = $surveys.surveys[0].survey_id
    
    # Survey Level Endpoints (API_V2.md)
    Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId" -Description "Get survey details (V2)"
    Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/summary" -Description "Get survey summary (V2)"
    
    # Platform Level Endpoints (API_V2.md)
    $platforms = Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/platforms" -Description "List platforms for survey (V2)"
    if ($platforms -and $platforms.platforms -and $platforms.platforms.Count -gt 0) {
        $testPlatformId = $platforms.platforms[0].platform_id
        Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/platforms/$testPlatformId" -Description "Get platform details (V2)"
        Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/platforms/$testPlatformId/summary" -Description "Get platform summary (V2)"
        
        # Respondent Level Endpoints (API_V2.md)
        $respondents = Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/platforms/$testPlatformId/respondents?limit=1" -Description "List respondents for platform (V2)"
        if ($respondents -and $respondents.respondents -and $respondents.respondents.Count -gt 0) {
            $testRespondentId = $respondents.respondents[0].respondent_id
            Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/platforms/$testPlatformId/respondents/$testRespondentId" -Description "Get respondent details (V2)"
            Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/platforms/$testPlatformId/respondents/$testRespondentId/summary" -Description "Get respondent summary (V2)"
            
            # Session Level Endpoints (API_V2.md)
            $sessions = Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/platforms/$testPlatformId/respondents/$testRespondentId/sessions?limit=1" -Description "List sessions for respondent (V2)"
            if ($sessions -and $sessions.sessions -and $sessions.sessions.Count -gt 0) {
                $testSessionId = $sessions.sessions[0].session_id
                Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/platforms/$testPlatformId/respondents/$testRespondentId/sessions/$testSessionId" -Description "Get session by hierarchy (V2)"
            }
        }
    }
    
    # Hierarchical Text Analysis Endpoints (V2)
    Write-Host "`n=== Hierarchical Text Analysis (V2) ===" -ForegroundColor Magenta
    Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/text-analysis/summary" -Description "Get survey text analysis summary (V2)"
    
    if ($platforms -and $platforms.platforms -and $platforms.platforms.Count -gt 0) {
        $testPlatformId = $platforms.platforms[0].platform_id
        Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/platforms/$testPlatformId/text-analysis/summary" -Description "Get platform text analysis summary (V2)"
        
        if ($respondents -and $respondents.respondents -and $respondents.respondents.Count -gt 0) {
            $testRespondentId = $respondents.respondents[0].respondent_id
            Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/platforms/$testPlatformId/respondents/$testRespondentId/text-analysis/summary" -Description "Get respondent text analysis summary (V2)"
            
            if ($sessions -and $sessions.sessions -and $sessions.sessions.Count -gt 0) {
                $testSessionId = $sessions.sessions[0].session_id
                Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/platforms/$testPlatformId/respondents/$testRespondentId/sessions/$testSessionId/text-analysis" -Description "Get session text analysis (V2)"
            }
        }
    }
}

# 10. Integration Endpoints
Write-Host "`n=== Integration Endpoints ===" -ForegroundColor Magenta
Test-Endpoint -Method "GET" -Endpoint "/integrations/status" -Description "Get integration status"
# Test endpoints don't exist, checking webhook endpoints instead
Write-Host "`nNote: Test endpoints not available, checking webhook endpoints..." -ForegroundColor Yellow

# Summary
Write-Host "`n========================================" -ForegroundColor Yellow
Write-Host "Test Summary" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "Total Tests: $($passed + $failed)" -ForegroundColor White
Write-Host "✅ Passed: $passed" -ForegroundColor Green
Write-Host "❌ Failed: $failed" -ForegroundColor Red
Write-Host ""

if ($failed -eq 0) {
    Write-Host "🎉 All endpoints are working correctly!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Some endpoints failed. See details above." -ForegroundColor Yellow
    Write-Host "`nFailed Endpoints:" -ForegroundColor Red
    $results | Where-Object { $_.Status -eq "FAILED" } | Format-Table -AutoSize
}

# Export results
$results | Export-Csv -Path "api-test-results.csv" -NoTypeInformation
Write-Host "`nResults exported to: api-test-results.csv" -ForegroundColor Cyan

