# Run platform_id migration with password automatically set
# This script sets the password and connects to Cloud SQL

param(
    [string]$ProjectId = "survey-bot-detection",
    [string]$InstanceName = "bot-db",
    [string]$DatabaseName = "bot_detection",
    [string]$DbUser = "bot_user",
    [string]$DbPassword = "B3Int2019!"
)

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Platform ID Migration with Auto-Password" -ForegroundColor Cyan
Write-Host "=" * 60
Write-Host ""

# SQL migration (simple version without DO blocks)
$migrationSQL = @"
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS platform_id VARCHAR(255);
UPDATE sessions SET platform_id = platform WHERE platform IS NOT NULL AND platform_id IS NULL;
CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent_session ON sessions (survey_id, platform_id, respondent_id, id);
CREATE INDEX IF NOT EXISTS idx_survey_platform ON sessions (survey_id, platform_id);
CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent ON sessions (survey_id, platform_id, respondent_id);
CREATE INDEX IF NOT EXISTS idx_sessions_platform_id ON sessions (platform_id);
"@

# Save SQL to temp file
$tempFile = [System.IO.Path]::GetTempFileName() + ".sql"
$migrationSQL | Out-File -FilePath $tempFile -Encoding UTF8 -NoNewline

Write-Host "Migration SQL prepared" -ForegroundColor Green
Write-Host "SQL file: $tempFile" -ForegroundColor Gray
Write-Host ""

Write-Host "Connecting to Cloud SQL and executing migration..." -ForegroundColor Yellow
Write-Host ""

# Set PGPASSWORD environment variable and run the migration
# We'll use a here-string to pipe the SQL to psql via gcloud sql connect
$env:PGPASSWORD = $DbPassword

# Create a command that pipes the SQL to the connection
$command = @"
`$env:PGPASSWORD = '$DbPassword'
gcloud sql connect $InstanceName --user=$DbUser --database=$DatabaseName --project=$ProjectId << 'SQL_EOF'
$migrationSQL
SQL_EOF
"@

Write-Host "Running migration..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Note: You may still see a password prompt, but the password is set." -ForegroundColor Gray
Write-Host "If prompted, enter: $DbPassword" -ForegroundColor Gray
Write-Host ""

# Execute the command
Invoke-Expression $command

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Green
    Write-Host "SUCCESS: Migration completed!" -ForegroundColor Green
    Write-Host "=" * 60
} else {
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Yellow
    Write-Host "Migration may have completed. Check the output above." -ForegroundColor Yellow
    Write-Host "=" * 60
    Write-Host ""
    Write-Host "If you see errors, you can also run the SQL manually:" -ForegroundColor Cyan
    Write-Host "1. Connect: gcloud sql connect $InstanceName --user=$DbUser --database=$DatabaseName --project=$ProjectId" -ForegroundColor White
    Write-Host "2. When prompted for password, enter: $DbPassword" -ForegroundColor White
    Write-Host "3. Paste the SQL from: $tempFile" -ForegroundColor White
}

Write-Host ""
Write-Host "SQL file saved at: $tempFile" -ForegroundColor Gray
Write-Host "You can delete it after verifying the migration." -ForegroundColor Gray
