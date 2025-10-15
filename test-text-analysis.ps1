# Test Text Analysis Functionality After Deployment
$baseUrl = "https://bot-backend-i56xopdg6q-pd.a.run.app/api/v1"
$headers = @{'Content-Type'='application/json'}

Write-Host "Testing Text Analysis Functionality..." -ForegroundColor Green
Write-Host "Base URL: $baseUrl" -ForegroundColor Cyan

# Test 1: Capture a survey question
Write-Host "`n1. Testing Question Capture..." -ForegroundColor Yellow
$questionBody = @{
    survey_id = "TEST_SURVEY_001"
    question_text = "What is your favorite color?"
    question_type = "open_ended"
} | ConvertTo-Json

try {
    $questionResponse = Invoke-RestMethod -Uri "$baseUrl/text-analysis/questions" -Method POST -Headers $headers -Body $questionBody
    Write-Host "✅ Question capture: SUCCESS" -ForegroundColor Green
    Write-Host "Question ID: $($questionResponse.question_id)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Question capture: FAILED" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Analyze a response
Write-Host "`n2. Testing Response Analysis..." -ForegroundColor Yellow
$responseBody = @{
    survey_id = "TEST_SURVEY_001"
    question_id = "TEST_QUESTION_001"
    respondent_id = "TEST_RESPONDENT_001"
    response_text = "I like blue because it reminds me of the ocean and sky. It's a calming color that makes me feel peaceful."
    session_id = "TEST_SESSION_001"
} | ConvertTo-Json

try {
    $analysisResponse = Invoke-RestMethod -Uri "$baseUrl/text-analysis/analyze" -Method POST -Headers $headers -Body $responseBody
    Write-Host "✅ Response analysis: SUCCESS" -ForegroundColor Green
    Write-Host "Quality Score: $($analysisResponse.quality_score)" -ForegroundColor Cyan
    Write-Host "Risk Level: $($analysisResponse.risk_level)" -ForegroundColor Cyan
    Write-Host "Analysis Details:" -ForegroundColor Cyan
    $analysisResponse.analysis_details | ConvertTo-Json -Depth 3 | Write-Host
} catch {
    Write-Host "❌ Response analysis: FAILED" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Test with gibberish response
Write-Host "`n3. Testing Gibberish Detection..." -ForegroundColor Yellow
$gibberishBody = @{
    survey_id = "TEST_SURVEY_001"
    question_id = "TEST_QUESTION_001"
    respondent_id = "TEST_RESPONDENT_002"
    response_text = "asdfghjkl qwertyuiop zxcvbnm 123456789"
    session_id = "TEST_SESSION_002"
} | ConvertTo-Json

try {
    $gibberishResponse = Invoke-RestMethod -Uri "$baseUrl/text-analysis/analyze" -Method POST -Headers $headers -Body $gibberishBody
    Write-Host "✅ Gibberish analysis: SUCCESS" -ForegroundColor Green
    Write-Host "Quality Score: $($gibberishResponse.quality_score)" -ForegroundColor Cyan
    Write-Host "Risk Level: $($gibberishResponse.risk_level)" -ForegroundColor Cyan
    Write-Host "Gibberish Detected: $($gibberishResponse.analysis_details.gibberish_detected)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Gibberish analysis: FAILED" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Test with generic response
Write-Host "`n4. Testing Generic Response Detection..." -ForegroundColor Yellow
$genericBody = @{
    survey_id = "TEST_SURVEY_001"
    question_id = "TEST_QUESTION_001"
    respondent_id = "TEST_RESPONDENT_003"
    response_text = "I don't know"
    session_id = "TEST_SESSION_003"
} | ConvertTo-Json

try {
    $genericResponse = Invoke-RestMethod -Uri "$baseUrl/text-analysis/analyze" -Method POST -Headers $headers -Body $genericBody
    Write-Host "✅ Generic response analysis: SUCCESS" -ForegroundColor Green
    Write-Host "Quality Score: $($genericResponse.quality_score)" -ForegroundColor Cyan
    Write-Host "Risk Level: $($genericResponse.risk_level)" -ForegroundColor Cyan
    Write-Host "Generic Answer Detected: $($genericResponse.analysis_details.generic_answer_detected)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Generic response analysis: FAILED" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 5: Get session summary
Write-Host "`n5. Testing Session Summary..." -ForegroundColor Yellow
try {
    $summaryResponse = Invoke-RestMethod -Uri "$baseUrl/text-analysis/sessions/TEST_SESSION_001/summary" -Method GET -Headers $headers
    Write-Host "✅ Session summary: SUCCESS" -ForegroundColor Green
    Write-Host "Total Responses: $($summaryResponse.total_responses)" -ForegroundColor Cyan
    Write-Host "Average Quality Score: $($summaryResponse.average_quality_score)" -ForegroundColor Cyan
    Write-Host "Risk Distribution:" -ForegroundColor Cyan
    $summaryResponse.risk_distribution | ConvertTo-Json -Depth 2 | Write-Host
} catch {
    Write-Host "❌ Session summary: FAILED" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nText Analysis Testing Complete!" -ForegroundColor Green
