param([switch]$SkipDbPrep)
Write-Host "Step 0..."
if (-not $SkipDbPrep) {
    Write-Host "Running prep"
} else {
    Write-Host "Skipping"
}
Write-Host "Step 1..."
$x = "postgresql://user@/bot_detection_v2?host=/x"
$y = $x -replace '.*@/([^?]+).*', '$1'
Write-Host $y
if ($x) {
    Write-Host "OK"
} else {
    Write-Host "No"
}
Write-Host "Done"
