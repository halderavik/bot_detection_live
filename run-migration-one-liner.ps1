# One-liner to run migration with password
# This pipes the SQL directly to the database connection

param(
    [string]$ProjectId = "survey-bot-detection",
    [string]$InstanceName = "bot-db",
    [string]$DatabaseName = "bot_detection",
    [string]$DbUser = "bot_user",
    [string]$DbPassword = "B3Int2019!"
)

Write-Host "Running platform_id migration..." -ForegroundColor Yellow
Write-Host ""

# Set password
$env:PGPASSWORD = $DbPassword

# SQL to execute
$sql = @"
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS platform_id VARCHAR(255);
UPDATE sessions SET platform_id = platform WHERE platform IS NOT NULL AND platform_id IS NULL;
CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent_session ON sessions (survey_id, platform_id, respondent_id, id);
CREATE INDEX IF NOT EXISTS idx_survey_platform ON sessions (survey_id, platform_id);
CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent ON sessions (survey_id, platform_id, respondent_id);
CREATE INDEX IF NOT EXISTS idx_sessions_platform_id ON sessions (platform_id);
"@

# Save to temp file
$tempFile = [System.IO.Path]::GetTempFileName() + ".sql"
$sql | Out-File -FilePath $tempFile -Encoding UTF8 -NoNewline

Write-Host "SQL file: $tempFile" -ForegroundColor Gray
Write-Host ""
Write-Host "To run the migration, execute this in Cloud Shell:" -ForegroundColor Cyan
Write-Host ""
Write-Host "export PGPASSWORD='$DbPassword'" -ForegroundColor White
Write-Host "gcloud sql connect $InstanceName --user=$DbUser --database=$DatabaseName --project=$ProjectId < $tempFile" -ForegroundColor White
Write-Host ""
Write-Host "Or connect interactively and paste this SQL:" -ForegroundColor Cyan
Write-Host ""
Write-Host $sql -ForegroundColor Gray
Write-Host ""

# For Windows/PowerShell, we need to use a different approach
Write-Host "For Windows PowerShell, use this command:" -ForegroundColor Yellow
Write-Host ""
Write-Host "`$env:PGPASSWORD = '$DbPassword'" -ForegroundColor White
Write-Host "gcloud sql connect $InstanceName --user=$DbUser --database=$DatabaseName --project=$ProjectId" -ForegroundColor White
Write-Host ""
Write-Host "Then when in psql, paste the SQL above or run:" -ForegroundColor White
Write-Host "  \i $tempFile" -ForegroundColor White
Write-Host ""
