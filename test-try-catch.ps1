try {
    $response = Invoke-RestMethod -Uri "https://httpbin.org/get" -Method Get -TimeoutSec 10
    if ($response) {
        Write-Host "Success"
    } else {
        Write-Host "Failed"
    }
} catch {
    Write-Host "Error: $_"
}
