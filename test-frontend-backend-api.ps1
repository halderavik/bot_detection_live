# Frontend-Backend API Compatibility Test
# Tests if frontend components are correctly calling backend APIs

$BaseUrl = "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1"
$Results = @()

Write-Host "`n🔍 Frontend-Backend API Compatibility Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Base URL: $BaseUrl`n" -ForegroundColor Yellow

# Test 1: List Surveys
Write-Host "Test 1: GET /surveys" -ForegroundColor White
try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/surveys?limit=10" -Method Get -ErrorAction Stop
    if ($response.surveys -ne $null) {
        Write-Host "  ✅ PASS - Response structure correct (has 'surveys' array)" -ForegroundColor Green
        $Results += @{Test="List Surveys"; Status="PASS"; Details="Response has 'surveys' array"}
    } else {
        Write-Host "  ❌ FAIL - Response missing 'surveys' array" -ForegroundColor Red
        $Results += @{Test="List Surveys"; Status="FAIL"; Details="Missing 'surveys' array"}
    }
} catch {
    Write-Host "  ❌ FAIL - Error: $($_.Exception.Message)" -ForegroundColor Red
    $Results += @{Test="List Surveys"; Status="FAIL"; Details=$_.Exception.Message}
}

# Test 2: Get Survey Details (if surveys exist)
Write-Host "`nTest 2: GET /surveys/{survey_id}" -ForegroundColor White
try {
    $listResponse = Invoke-RestMethod -Uri "$BaseUrl/surveys?limit=1" -Method Get -ErrorAction Stop
    if ($listResponse.surveys -and $listResponse.surveys.Count -gt 0) {
        $surveyId = $listResponse.surveys[0].survey_id
        $response = Invoke-RestMethod -Uri "$BaseUrl/surveys/$surveyId" -Method Get -ErrorAction Stop
        if ($response.total_respondents -ne $null -and $response.total_sessions -ne $null) {
            Write-Host "  ✅ PASS - Response structure correct" -ForegroundColor Green
            $Results += @{Test="Get Survey Details"; Status="PASS"; Details="Response has required fields"}
        } else {
            Write-Host "  ❌ FAIL - Response missing required fields" -ForegroundColor Red
            $Results += @{Test="Get Survey Details"; Status="FAIL"; Details="Missing required fields"}
        }
    } else {
        Write-Host "  ⚠️  SKIP - No surveys found to test" -ForegroundColor Yellow
        $Results += @{Test="Get Survey Details"; Status="SKIP"; Details="No surveys available"}
    }
} catch {
    Write-Host "  ❌ FAIL - Error: $($_.Exception.Message)" -ForegroundColor Red
    $Results += @{Test="Get Survey Details"; Status="FAIL"; Details=$_.Exception.Message}
}

# Test 3: List Platforms
Write-Host "`nTest 3: GET /surveys/{survey_id}/platforms" -ForegroundColor White
try {
    $listResponse = Invoke-RestMethod -Uri "$BaseUrl/surveys?limit=1" -Method Get -ErrorAction Stop
    if ($listResponse.surveys -and $listResponse.surveys.Count -gt 0) {
        $surveyId = $listResponse.surveys[0].survey_id
        $response = Invoke-RestMethod -Uri "$BaseUrl/surveys/$surveyId/platforms" -Method Get -ErrorAction Stop
        if ($response.platforms -ne $null) {
            Write-Host "  ✅ PASS - Response structure correct (has 'platforms' array)" -ForegroundColor Green
            $Results += @{Test="List Platforms"; Status="PASS"; Details="Response has 'platforms' array"}
        } else {
            Write-Host "  ❌ FAIL - Response missing 'platforms' array" -ForegroundColor Red
            $Results += @{Test="List Platforms"; Status="FAIL"; Details="Missing 'platforms' array"}
        }
    } else {
        Write-Host "  ⚠️  SKIP - No surveys found to test" -ForegroundColor Yellow
        $Results += @{Test="List Platforms"; Status="SKIP"; Details="No surveys available"}
    }
} catch {
    Write-Host "  ❌ FAIL - Error: $($_.Exception.Message)" -ForegroundColor Red
    $Results += @{Test="List Platforms"; Status="FAIL"; Details=$_.Exception.Message}
}

# Test 4: List Respondents
Write-Host "`nTest 4: GET /surveys/{survey_id}/platforms/{platform_id}/respondents" -ForegroundColor White
try {
    $listResponse = Invoke-RestMethod -Uri "$BaseUrl/surveys?limit=1" -Method Get -ErrorAction Stop
    if ($listResponse.surveys -and $listResponse.surveys.Count -gt 0) {
        $surveyId = $listResponse.surveys[0].survey_id
        $platformsResponse = Invoke-RestMethod -Uri "$BaseUrl/surveys/$surveyId/platforms" -Method Get -ErrorAction Stop
        if ($platformsResponse.platforms -and $platformsResponse.platforms.Count -gt 0) {
            $platformId = $platformsResponse.platforms[0].platform_id
            $response = Invoke-RestMethod -Uri "$BaseUrl/surveys/$surveyId/platforms/$platformId/respondents?limit=10" -Method Get -ErrorAction Stop
            if ($response.respondents -ne $null) {
                Write-Host "  ✅ PASS - Response structure correct (has 'respondents' array)" -ForegroundColor Green
                $Results += @{Test="List Respondents"; Status="PASS"; Details="Response has 'respondents' array"}
            } else {
                Write-Host "  ❌ FAIL - Response missing 'respondents' array" -ForegroundColor Red
                $Results += @{Test="List Respondents"; Status="FAIL"; Details="Missing 'respondents' array"}
            }
        } else {
            Write-Host "  ⚠️  SKIP - No platforms found to test" -ForegroundColor Yellow
            $Results += @{Test="List Respondents"; Status="SKIP"; Details="No platforms available"}
        }
    } else {
        Write-Host "  ⚠️  SKIP - No surveys found to test" -ForegroundColor Yellow
        $Results += @{Test="List Respondents"; Status="SKIP"; Details="No surveys available"}
    }
} catch {
    Write-Host "  ❌ FAIL - Error: $($_.Exception.Message)" -ForegroundColor Red
    $Results += @{Test="List Respondents"; Status="FAIL"; Details=$_.Exception.Message}
}

# Test 5: Get Respondent Details
Write-Host "`nTest 5: GET /surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}" -ForegroundColor White
try {
    $listResponse = Invoke-RestMethod -Uri "$BaseUrl/surveys?limit=1" -Method Get -ErrorAction Stop
    if ($listResponse.surveys -and $listResponse.surveys.Count -gt 0) {
        $surveyId = $listResponse.surveys[0].survey_id
        $platformsResponse = Invoke-RestMethod -Uri "$BaseUrl/surveys/$surveyId/platforms" -Method Get -ErrorAction Stop
        if ($platformsResponse.platforms -and $platformsResponse.platforms.Count -gt 0) {
            $platformId = $platformsResponse.platforms[0].platform_id
            $respondentsResponse = Invoke-RestMethod -Uri "$BaseUrl/surveys/$surveyId/platforms/$platformId/respondents?limit=1" -Method Get -ErrorAction Stop
            if ($respondentsResponse.respondents -and $respondentsResponse.respondents.Count -gt 0) {
                $respondentId = $respondentsResponse.respondents[0].respondent_id
                $response = Invoke-RestMethod -Uri "$BaseUrl/surveys/$surveyId/platforms/$platformId/respondents/$respondentId" -Method Get -ErrorAction Stop
                if ($response.sessions -ne $null -and $response.total_sessions -ne $null) {
                    Write-Host "  ✅ PASS - Response structure correct (has 'sessions' array and 'total_sessions')" -ForegroundColor Green
                    $Results += @{Test="Get Respondent Details"; Status="PASS"; Details="Response has 'sessions' array"}
                } else {
                    Write-Host "  ❌ FAIL - Response missing 'sessions' array or 'total_sessions'" -ForegroundColor Red
                    $Results += @{Test="Get Respondent Details"; Status="FAIL"; Details="Missing 'sessions' or 'total_sessions'"}
                }
            } else {
                Write-Host "  ⚠️  SKIP - No respondents found to test" -ForegroundColor Yellow
                $Results += @{Test="Get Respondent Details"; Status="SKIP"; Details="No respondents available"}
            }
        } else {
            Write-Host "  ⚠️  SKIP - No platforms found to test" -ForegroundColor Yellow
            $Results += @{Test="Get Respondent Details"; Status="SKIP"; Details="No platforms available"}
        }
    } else {
        Write-Host "  ⚠️  SKIP - No surveys found to test" -ForegroundColor Yellow
        $Results += @{Test="Get Respondent Details"; Status="SKIP"; Details="No surveys available"}
    }
} catch {
    Write-Host "  ❌ FAIL - Error: $($_.Exception.Message)" -ForegroundColor Red
    $Results += @{Test="Get Respondent Details"; Status="FAIL"; Details=$_.Exception.Message}
}

# Test 6: List Respondent Sessions
Write-Host "`nTest 6: GET /surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions" -ForegroundColor White
try {
    $listResponse = Invoke-RestMethod -Uri "$BaseUrl/surveys?limit=1" -Method Get -ErrorAction Stop
    if ($listResponse.surveys -and $listResponse.surveys.Count -gt 0) {
        $surveyId = $listResponse.surveys[0].survey_id
        $platformsResponse = Invoke-RestMethod -Uri "$BaseUrl/surveys/$surveyId/platforms" -Method Get -ErrorAction Stop
        if ($platformsResponse.platforms -and $platformsResponse.platforms.Count -gt 0) {
            $platformId = $platformsResponse.platforms[0].platform_id
            $respondentsResponse = Invoke-RestMethod -Uri "$BaseUrl/surveys/$surveyId/platforms/$platformId/respondents?limit=1" -Method Get -ErrorAction Stop
            if ($respondentsResponse.respondents -and $respondentsResponse.respondents.Count -gt 0) {
                $respondentId = $respondentsResponse.respondents[0].respondent_id
                $response = Invoke-RestMethod -Uri "$BaseUrl/surveys/$surveyId/platforms/$platformId/respondents/$respondentId/sessions?limit=10" -Method Get -ErrorAction Stop
                if ($response.sessions -ne $null) {
                    Write-Host "  ✅ PASS - Response structure correct (has 'sessions' array)" -ForegroundColor Green
                    $Results += @{Test="List Respondent Sessions"; Status="PASS"; Details="Response has 'sessions' array"}
                } else {
                    Write-Host "  ❌ FAIL - Response missing 'sessions' array" -ForegroundColor Red
                    $Results += @{Test="List Respondent Sessions"; Status="FAIL"; Details="Missing 'sessions' array"}
                }
            } else {
                Write-Host "  ⚠️  SKIP - No respondents found to test" -ForegroundColor Yellow
                $Results += @{Test="List Respondent Sessions"; Status="SKIP"; Details="No respondents available"}
            }
        } else {
            Write-Host "  ⚠️  SKIP - No platforms found to test" -ForegroundColor Yellow
            $Results += @{Test="List Respondent Sessions"; Status="SKIP"; Details="No platforms available"}
        }
    } else {
        Write-Host "  ⚠️  SKIP - No surveys found to test" -ForegroundColor Yellow
        $Results += @{Test="List Respondent Sessions"; Status="SKIP"; Details="No surveys available"}
    }
} catch {
    Write-Host "  ❌ FAIL - Error: $($_.Exception.Message)" -ForegroundColor Red
    $Results += @{Test="List Respondent Sessions"; Status="FAIL"; Details=$_.Exception.Message}
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$passCount = ($Results | Where-Object { $_.Status -eq "PASS" }).Count
$failCount = ($Results | Where-Object { $_.Status -eq "FAIL" }).Count
$skipCount = ($Results | Where-Object { $_.Status -eq "SKIP" }).Count

Write-Host "`nTotal Tests: $($Results.Count)" -ForegroundColor White
Write-Host "✅ Passed: $passCount" -ForegroundColor Green
Write-Host "❌ Failed: $failCount" -ForegroundColor Red
Write-Host "⚠️  Skipped: $skipCount" -ForegroundColor Yellow

if ($failCount -eq 0) {
    Write-Host "`n✨ All tests passed! Frontend-Backend API compatibility verified." -ForegroundColor Green
} else {
    Write-Host "`n⚠️  Some tests failed. Please review the errors above." -ForegroundColor Yellow
}

Write-Host "`nDetailed Results:" -ForegroundColor Cyan
foreach ($result in $Results) {
    $statusIcon = switch ($result.Status) {
        "PASS" { "[OK]" }
        "FAIL" { "[FAIL]" }
        "SKIP" { "[SKIP]" }
    }
    $color = if ($result.Status -eq "PASS") { "Green" } elseif ($result.Status -eq "FAIL") { "Red" } else { "Yellow" }
    $testName = $result.Test
    $status = $result.Status
    $details = $result.Details -replace [char]34, [char]39
    Write-Host ('  ' + $statusIcon + ' ' + $testName + ' : ' + $status + ' - ' + $details) -ForegroundColor $color
}

