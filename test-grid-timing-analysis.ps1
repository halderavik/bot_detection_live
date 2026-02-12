# Test Grid and Timing Analysis Endpoints (Production)
# Tests the deployed Stage 2 features on production GCP backend

param(
    [string]$BaseUrl = "https://bot-backend-i56xopdg6q-pd.a.run.app/api/v1",
    [string]$SurveyId = "test-survey-grid-timing"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Grid & Timing Analysis Endpoint Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Base URL: $BaseUrl" -ForegroundColor Yellow
Write-Host "Survey ID: $SurveyId" -ForegroundColor Yellow
Write-Host ""

$testResults = @()
$passedTests = 0
$failedTests = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Url,
        [hashtable]$Headers = @{},
        [object]$Body = $null,
        [scriptblock]$Validator = $null
    )
    
    Write-Host "Testing: $Name" -ForegroundColor Cyan
    Write-Host "  $Method $Url" -ForegroundColor Gray
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            Headers = $Headers
            ContentType = "application/json"
            UseBasicParsing = $true
            ErrorAction = "Stop"
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
        }
        
        $startTime = Get-Date
        $response = Invoke-RestMethod @params
        $duration = ((Get-Date) - $startTime).TotalMilliseconds
        
        $statusCode = 200  # Invoke-RestMethod doesn't expose status code directly
        $success = $true
        
        if ($Validator) {
            $validationResult = & $Validator $response
            if (-not $validationResult) {
                $success = $false
                Write-Host "  ❌ Validation failed" -ForegroundColor Red
            }
        }
        
        if ($success) {
            Write-Host "  ✅ PASSED (${duration}ms)" -ForegroundColor Green
            $script:passedTests++
            $testResults += @{
                Test = $Name
                Status = "PASSED"
                Duration = $duration
                Response = $response
            }
        } else {
            Write-Host "  ❌ FAILED (${duration}ms)" -ForegroundColor Red
            $script:failedTests++
            $testResults += @{
                Test = $Name
                Status = "FAILED"
                Duration = $duration
                Response = $response
            }
        }
        
        Write-Host ""
        return $response
        
    } catch {
        $errorMessage = $_.Exception.Message
        Write-Host "  ❌ FAILED: $errorMessage" -ForegroundColor Red
        $script:failedTests++
        $testResults += @{
            Test = $Name
            Status = "FAILED"
            Error = $errorMessage
        }
        Write-Host ""
        return $null
    }
}

# Test 1: Health Check
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "1. Health Check" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

# Health check uses different base URL
$healthBaseUrl = $BaseUrl -replace "/api/v1", ""
Test-Endpoint `
    -Name "Health Check" `
    -Method "GET" `
    -Url "$healthBaseUrl/health" `
    -Validator {
        param($response)
        return $response -ne $null
    }

# Test 2: Survey Grid Analysis Summary
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "2. Grid Analysis Endpoints" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

$gridSummary = Test-Endpoint `
    -Name "Survey Grid Analysis Summary" `
    -Method "GET" `
    -Url "$BaseUrl/surveys/$SurveyId/grid-analysis/summary" `
    -Validator {
        param($response)
        $hasRequiredFields = $response.survey_id -ne $null -and
                            $response.total_responses -ne $null -and
                            $response.straight_lined_percentage -ne $null
        return $hasRequiredFields
    }

if ($gridSummary) {
    Write-Host "Grid Analysis Summary:" -ForegroundColor Cyan
    Write-Host "  Survey ID: $($gridSummary.survey_id)" -ForegroundColor White
    Write-Host "  Total Responses: $($gridSummary.total_responses)" -ForegroundColor White
    Write-Host "  Straight-Lined %: $($gridSummary.straight_lined_percentage)" -ForegroundColor White
    Write-Host "  Avg Variance Score: $($gridSummary.avg_variance_score)" -ForegroundColor White
    Write-Host "  Avg Satisficing Score: $($gridSummary.avg_satisficing_score)" -ForegroundColor White
    Write-Host ""
}

# Test 3: Survey Grid Analysis with Date Filters
$dateFrom = (Get-Date).AddDays(-30).ToString("yyyy-MM-ddTHH:mm:ssZ")
$dateTo = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")

Test-Endpoint `
    -Name "Survey Grid Analysis with Date Filters" `
    -Method "GET" `
    -Url "$BaseUrl/surveys/$SurveyId/grid-analysis/summary?date_from=$dateFrom&date_to=$dateTo" `
    -Validator {
        param($response)
        return $response.survey_id -ne $null
    }

# Test 4: Platform Grid Analysis Summary (if platform exists)
Write-Host "Testing Platform Grid Analysis..." -ForegroundColor Cyan
$platformId = "test-platform"
Test-Endpoint `
    -Name "Platform Grid Analysis Summary" `
    -Method "GET" `
    -Url "$BaseUrl/surveys/$SurveyId/platforms/$platformId/grid-analysis/summary" `
    -Validator {
        param($response)
        # May return empty data if platform doesn't exist, which is OK
        return $response -ne $null
    }

# Test 5: Survey Timing Analysis Summary
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "3. Timing Analysis Endpoints" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

$timingSummary = Test-Endpoint `
    -Name "Survey Timing Analysis Summary" `
    -Method "GET" `
    -Url "$BaseUrl/surveys/$SurveyId/timing-analysis/summary" `
    -Validator {
        param($response)
        $hasRequiredFields = $response.survey_id -ne $null -and
                            $response.total_analyses -ne $null -and
                            $response.speeders_percentage -ne $null -and
                            $response.flatliners_percentage -ne $null
        return $hasRequiredFields
    }

if ($timingSummary) {
    Write-Host "Timing Analysis Summary:" -ForegroundColor Cyan
    Write-Host "  Survey ID: $($timingSummary.survey_id)" -ForegroundColor White
    Write-Host "  Total Analyses: $($timingSummary.total_analyses)" -ForegroundColor White
    Write-Host "  Speeders %: $($timingSummary.speeders_percentage)" -ForegroundColor White
    Write-Host "  Flatliners %: $($timingSummary.flatliners_percentage)" -ForegroundColor White
    Write-Host "  Avg Response Time: $($timingSummary.avg_response_time_ms)ms" -ForegroundColor White
    Write-Host "  Median Response Time: $($timingSummary.median_response_time_ms)ms" -ForegroundColor White
    Write-Host ""
}

# Test 6: Survey Timing Analysis with Date Filters
Test-Endpoint `
    -Name "Survey Timing Analysis with Date Filters" `
    -Method "GET" `
    -Url "$BaseUrl/surveys/$SurveyId/timing-analysis/summary?date_from=$dateFrom&date_to=$dateTo" `
    -Validator {
        param($response)
        return $response.survey_id -ne $null
    }

# Test 7: Platform Timing Analysis Summary
Test-Endpoint `
    -Name "Platform Timing Analysis Summary" `
    -Method "GET" `
    -Url "$BaseUrl/surveys/$SurveyId/platforms/$platformId/timing-analysis/summary" `
    -Validator {
        param($response)
        return $response -ne $null
    }

# Test 8: Test with Real Survey ID (if available)
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "4. Testing with Real Survey Data" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

# Try to get a real survey ID from the surveys list
try {
    $surveysResponse = Invoke-RestMethod `
        -Uri "$BaseUrl/surveys?limit=1" `
        -Method "GET" `
        -ContentType "application/json" `
        -UseBasicParsing `
        -ErrorAction "Stop"
    
    if ($surveysResponse.surveys -and $surveysResponse.surveys.Count -gt 0) {
        $realSurveyId = $surveysResponse.surveys[0].survey_id
        Write-Host "Found real survey: $realSurveyId" -ForegroundColor Green
        
        # Test grid analysis with real survey
        Test-Endpoint `
            -Name "Real Survey Grid Analysis" `
            -Method "GET" `
            -Url "$BaseUrl/surveys/$realSurveyId/grid-analysis/summary" `
            -Validator {
                param($response)
                return $response.survey_id -eq $realSurveyId
            }
        
        # Test timing analysis with real survey
        Test-Endpoint `
            -Name "Real Survey Timing Analysis" `
            -Method "GET" `
            -Url "$BaseUrl/surveys/$realSurveyId/timing-analysis/summary" `
            -Validator {
                param($response)
                return $response.survey_id -eq $realSurveyId
            }
    } else {
        Write-Host "No surveys found in database" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Could not fetch real survey data: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Test 9: Test Error Handling (404 for non-existent survey)
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "5. Error Handling Tests" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

try {
    $errorResponse = Invoke-RestMethod `
        -Uri "$BaseUrl/surveys/non-existent-survey-12345/grid-analysis/summary" `
        -Method "GET" `
        -ContentType "application/json" `
        -UseBasicParsing `
        -ErrorAction "Stop"
    
    Write-Host "  ⚠️  Non-existent survey returned data (unexpected)" -ForegroundColor Yellow
} catch {
    if ($_.Exception.Response.StatusCode -eq 404 -or $_.Exception.Message -like "*404*") {
        Write-Host "  ✅ Error handling: 404 returned for non-existent survey" -ForegroundColor Green
        $script:passedTests++
    } else {
        Write-Host "  ⚠️  Unexpected error: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Total Tests: $($passedTests + $failedTests)" -ForegroundColor White
Write-Host "Passed: $passedTests" -ForegroundColor Green
Write-Host "Failed: $failedTests" -ForegroundColor $(if ($failedTests -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($failedTests -eq 0) {
    Write-Host "✅ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "❌ Some tests failed. Review the output above." -ForegroundColor Red
}

Write-Host ""
Write-Host "Test Results Details:" -ForegroundColor Cyan
$testResults | ForEach-Object {
    $statusColor = if ($_.Status -eq "PASSED") { "Green" } else { "Red" }
    Write-Host "  [$($_.Status)] $($_.Test)" -ForegroundColor $statusColor
    if ($_.Duration) {
        Write-Host "      Duration: $($_.Duration)ms" -ForegroundColor Gray
    }
    if ($_.Error) {
        Write-Host "      Error: $($_.Error)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Grid & Timing Analysis Tests Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
