# Test API Endpoints
$baseUrl = "https://bot-backend-i56xopdg6q-pd.a.run.app"

Write-Host "Testing API Endpoints..." -ForegroundColor Green

# Test 1: Root endpoint
Write-Host "`n1. Testing Root Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/" -Method GET
    Write-Host "✅ Root endpoint: SUCCESS" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 2
} catch {
    Write-Host "❌ Root endpoint: FAILED" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Health endpoint
Write-Host "`n2. Testing Health Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
    Write-Host "✅ Health endpoint: SUCCESS" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 2
} catch {
    Write-Host "❌ Health endpoint: FAILED" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Detection endpoint
Write-Host "`n3. Testing Detection Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/detection/sessions" -Method POST -Headers @{'Content-Type'='application/json'} -Body '{}'
    Write-Host "✅ Detection endpoint: SUCCESS" -ForegroundColor Green
    Write-Host "Session ID: $($response.session_id)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Detection endpoint: FAILED" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Text Analysis endpoint (should fail)
Write-Host "`n4. Testing Text Analysis Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/text-analysis/questions" -Method POST -Headers @{'Content-Type'='application/json'} -Body '{}'
    Write-Host "✅ Text Analysis endpoint: SUCCESS" -ForegroundColor Green
} catch {
    Write-Host "❌ Text Analysis endpoint: FAILED (Expected)" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nEndpoint Testing Complete!" -ForegroundColor Green
