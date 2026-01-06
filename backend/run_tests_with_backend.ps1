# PowerShell script to start backend and run text analysis tests
# This script starts the backend server and then runs the comprehensive test suite

Write-Host "Starting Backend Server..." -ForegroundColor Green
Write-Host ""

# Start backend in background
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    cd backend
    python main.py
}

# Wait for backend to start
Write-Host "Waiting for backend to start (10 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check if backend is running
try {
    $healthCheck = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
    if ($healthCheck.StatusCode -eq 200) {
        Write-Host "Backend is running!" -ForegroundColor Green
        Write-Host ""
    }
} catch {
    Write-Host "Backend may not be ready yet. Continuing anyway..." -ForegroundColor Yellow
    Write-Host ""
}

# Run the test script
Write-Host "Running Text Analysis Tests..." -ForegroundColor Green
Write-Host ""
cd backend
python test_all_text_analysis_checks.py

# Cleanup
Write-Host ""
Write-Host "Stopping backend server..." -ForegroundColor Yellow
Stop-Job $backendJob
Remove-Job $backendJob

Write-Host ""
Write-Host "Tests completed!" -ForegroundColor Green
