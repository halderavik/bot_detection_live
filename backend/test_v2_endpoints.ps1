# PowerShell script to test V2 hierarchical API endpoints

param(
    [string]$BaseUrl = "https://bot-backend-i56xopdg6q-pd.a.run.app"
)

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "Testing V2 Hierarchical API Endpoints" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "Base URL: $BaseUrl" -ForegroundColor Gray
Write-Host ""

$testResults = @()

# Test 1: Health Check
Write-Host "Test 1: Health Check" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get -ErrorAction Stop
    Write-Host "  ✓ Health check passed: $($response | ConvertTo-Json -Compress)" -ForegroundColor Green
    $testResults += @{Test="Health Check"; Status="PASS"; Details=$response}
} catch {
    Write-Host "  ✗ Health check failed: $($_.Exception.Message)" -ForegroundColor Red
    $testResults += @{Test="Health Check"; Status="FAIL"; Details=$_.Exception.Message}
}
Write-Host ""

# Test 2: List Surveys
Write-Host "Test 2: GET /api/v1/surveys" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v1/surveys" -Method Get -ErrorAction Stop
    Write-Host "  ✓ Success: Found $($response.total) surveys" -ForegroundColor Green
    if ($response.surveys) {
        Write-Host "    Surveys: $($response.surveys.Count)" -ForegroundColor Gray
    }
    $testResults += @{Test="List Surveys"; Status="PASS"; Details="Found $($response.total) surveys"}
} catch {
    Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    $testResults += @{Test="List Surveys"; Status="FAIL"; Details=$_.Exception.Message}
}
Write-Host ""

# Test 3: Create Session with platform_id
Write-Host "Test 3: Create Session with platform_id" -ForegroundColor Yellow
try {
    $sessionUrl = "$BaseUrl/api/v1/detection/sessions?survey_id=TEST_SV_001&platform_id=qualtrics&respondent_id=TEST_RSP_001"
    $response = Invoke-RestMethod -Uri $sessionUrl -Method Post -ErrorAction Stop
    Write-Host "  ✓ Session created: $($response.id)" -ForegroundColor Green
    Write-Host "    Platform ID: $($response.platform_id)" -ForegroundColor Gray
    $sessionId = $response.id
    $testResults += @{Test="Create Session"; Status="PASS"; Details="Session ID: $sessionId"}
} catch {
    Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "    Response: $responseBody" -ForegroundColor Gray
    }
    $testResults += @{Test="Create Session"; Status="FAIL"; Details=$_.Exception.Message}
    $sessionId = $null
}
Write-Host ""

# Test 4: Get Survey Details (if we have a survey)
if ($sessionId) {
    Write-Host "Test 4: GET /api/v1/surveys/TEST_SV_001" -ForegroundColor Yellow
    try {
        $response = Invoke-RestMethod -Uri "$BaseUrl/api/v1/surveys/TEST_SV_001" -Method Get -ErrorAction Stop
        Write-Host "  ✓ Survey details retrieved" -ForegroundColor Green
        Write-Host "    Total Sessions: $($response.total_sessions)" -ForegroundColor Gray
        $testResults += @{Test="Get Survey Details"; Status="PASS"; Details="Sessions: $($response.total_sessions)"}
    } catch {
        Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
        $testResults += @{Test="Get Survey Details"; Status="FAIL"; Details=$_.Exception.Message}
    }
    Write-Host ""
}

# Test 5: Get Platforms for Survey
Write-Host "Test 5: GET /api/v1/surveys/TEST_SV_001/platforms" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/api/v1/surveys/TEST_SV_001/platforms" -Method Get -ErrorAction Stop
    Write-Host "  ✓ Platforms retrieved: $($response.total)" -ForegroundColor Green
    if ($response.platforms) {
        foreach ($platform in $response.platforms) {
            Write-Host "    - $($platform.platform_id): $($platform.session_count) sessions" -ForegroundColor Gray
        }
    }
    $testResults += @{Test="Get Platforms"; Status="PASS"; Details="Found $($response.total) platforms"}
} catch {
    Write-Host "  ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    $testResults += @{Test="Get Platforms"; Status="FAIL"; Details=$_.Exception.Message}
}
Write-Host ""

# Summary
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
$passed = ($testResults | Where-Object { $_.Status -eq "PASS" }).Count
$failed = ($testResults | Where-Object { $_.Status -eq "FAIL" }).Count
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })
Write-Host ""

foreach ($result in $testResults) {
    $color = if ($result.Status -eq "PASS") { "Green" } else { "Red" }
    Write-Host "$($result.Status): $($result.Test)" -ForegroundColor $color
    Write-Host "  $($result.Details)" -ForegroundColor Gray
}

Write-Host ""
