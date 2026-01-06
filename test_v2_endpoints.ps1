# PowerShell script to test V2 hierarchical API endpoints
param(
    [string]$BaseUrl = "https://bot-backend-i56xopdg6q-pd.a.run.app/api/v1"
)

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
    
    $url = "$BaseUrl$Endpoint"
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
        
        Write-Host "✅ PASSED" -ForegroundColor Green
        $script:passed++
        $script:results += [PSCustomObject]@{
            Endpoint = "$Method $Endpoint"
            Status = "PASSED"
            Description = $Description
            Error = ""
        }
        return $response
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
Write-Host "V2 Hierarchical API Endpoint Testing" -ForegroundColor Yellow
Write-Host "Base URL: $BaseUrl" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

# 1. Survey Level Endpoints
Write-Host "`n=== Survey Level Endpoints ===" -ForegroundColor Magenta
$surveys = Test-Endpoint -Method "GET" -Endpoint "/surveys" -Description "List all surveys"

# Get a survey ID for further testing
$testSurveyId = $null
if ($surveys -and $surveys.surveys -and $surveys.surveys.Count -gt 0) {
    $testSurveyId = $surveys.surveys[0].survey_id
    Write-Host "Using survey ID for testing: $testSurveyId" -ForegroundColor Green
    
    Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId" -Description "Get survey details"
    Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/summary" -Description "Get survey summary"
} else {
    Write-Host "⚠️  No surveys found. Testing with placeholder survey ID..." -ForegroundColor Yellow
    $testSurveyId = "SV_TEST_123456"
    Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId" -Description "Get survey details (expected to fail if no data)"
    Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/summary" -Description "Get survey summary (expected to fail if no data)"
}

# 2. Platform Level Endpoints
Write-Host "`n=== Platform Level Endpoints ===" -ForegroundColor Magenta
if ($testSurveyId) {
    $platforms = Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/platforms" -Description "List platforms for survey"
    
    $testPlatformId = $null
    if ($platforms -and $platforms.platforms -and $platforms.platforms.Count -gt 0) {
        $testPlatformId = $platforms.platforms[0].platform_id
        Write-Host "Using platform ID for testing: $testPlatformId" -ForegroundColor Green
        
        Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/platforms/$testPlatformId" -Description "Get platform details"
        Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/platforms/$testPlatformId/summary" -Description "Get platform summary"
    } else {
        Write-Host "⚠️  No platforms found. Testing with placeholder platform ID..." -ForegroundColor Yellow
        $testPlatformId = "qualtrics"
        Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/platforms/$testPlatformId" -Description "Get platform details (expected to fail if no data)"
        Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/platforms/$testPlatformId/summary" -Description "Get platform summary (expected to fail if no data)"
    }
    
    # 3. Respondent Level Endpoints
    Write-Host "`n=== Respondent Level Endpoints ===" -ForegroundColor Magenta
    if ($testPlatformId) {
        $respondents = Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/platforms/$testPlatformId/respondents?limit=10" -Description "List respondents for platform"
        
        $testRespondentId = $null
        if ($respondents -and $respondents.respondents -and $respondents.respondents.Count -gt 0) {
            $testRespondentId = $respondents.respondents[0].respondent_id
            Write-Host "Using respondent ID for testing: $testRespondentId" -ForegroundColor Green
            
            Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/platforms/$testPlatformId/respondents/$testRespondentId" -Description "Get respondent details"
            Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/platforms/$testPlatformId/respondents/$testRespondentId/summary" -Description "Get respondent summary"
            
            # 4. Session Level Endpoints
            Write-Host "`n=== Session Level Endpoints ===" -ForegroundColor Magenta
            $sessions = Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/platforms/$testPlatformId/respondents/$testRespondentId/sessions?limit=10" -Description "List sessions for respondent"
            
            $testSessionId = $null
            if ($sessions -and $sessions.sessions -and $sessions.sessions.Count -gt 0) {
                $testSessionId = $sessions.sessions[0].session_id
                Write-Host "Using session ID for testing: $testSessionId" -ForegroundColor Green
                
                Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/platforms/$testPlatformId/respondents/$testRespondentId/sessions/$testSessionId" -Description "Get session by hierarchy"
            } else {
                Write-Host "⚠️  No sessions found for respondent." -ForegroundColor Yellow
            }
        } else {
            Write-Host "⚠️  No respondents found. Testing with placeholder respondent ID..." -ForegroundColor Yellow
            $testRespondentId = "RSP_TEST_123456"
            Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/platforms/$testPlatformId/respondents/$testRespondentId" -Description "Get respondent details (expected to fail if no data)"
            Test-Endpoint -Method "GET" -Endpoint "/surveys/$testSurveyId/platforms/$testPlatformId/respondents/$testRespondentId/summary" -Description "Get respondent summary (expected to fail if no data)"
        }
    }
}

# Summary
Write-Host "`n========================================" -ForegroundColor Yellow
Write-Host "Test Summary" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "Total Tests: $($passed + $failed)" -ForegroundColor White
Write-Host "✅ Passed: $passed" -ForegroundColor Green
Write-Host "❌ Failed: $failed" -ForegroundColor Red
Write-Host ""

if ($failed -eq 0) {
    Write-Host "🎉 All V2 hierarchical endpoints are working correctly!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Some endpoints failed. See details above." -ForegroundColor Yellow
    Write-Host "`nFailed Endpoints:" -ForegroundColor Red
    $results | Where-Object { $_.Status -eq "FAILED" } | Format-Table -AutoSize
}

# Export results
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$resultsFile = "v2-endpoints-test-results-$timestamp.csv"
$results | Export-Csv -Path $resultsFile -NoTypeInformation
Write-Host "`nResults exported to: $resultsFile" -ForegroundColor Cyan
