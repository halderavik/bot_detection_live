# Connect to Cloud SQL with password pre-set
# This makes it easier to run SQL commands

param(
    [string]$ProjectId = "survey-bot-detection",
    [string]$InstanceName = "bot-db",
    [string]$DatabaseName = "bot_detection",
    [string]$DbUser = "bot_user",
    [string]$DbPassword = "B3Int2019!"
)

Write-Host "Connecting to Cloud SQL..." -ForegroundColor Yellow
Write-Host "Instance: $InstanceName" -ForegroundColor Gray
Write-Host "Database: $DatabaseName" -ForegroundColor Gray
Write-Host "User: $DbUser" -ForegroundColor Gray
Write-Host ""

# Set PGPASSWORD environment variable
$env:PGPASSWORD = $DbPassword

Write-Host "Password set. Connecting..." -ForegroundColor Green
Write-Host ""

# Connect to Cloud SQL
# Note: gcloud sql connect may still prompt, but PGPASSWORD should work
gcloud sql connect $InstanceName --user=$DbUser --database=$DatabaseName --project=$ProjectId

# After connection closes, clear the password from environment
$env:PGPASSWORD = $null
