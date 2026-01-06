# Run production database migration using gcloud sql connect
# This script connects to Cloud SQL and runs the migration SQL

param(
    [string]$ProjectId = "survey-bot-detection",
    [string]$InstanceName = "bot-db",
    [string]$DatabaseName = "bot_detection",
    [string]$DbUser = "bot_user"
)

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Running Production Database Migration" -ForegroundColor Cyan
Write-Host "=" * 60
Write-Host ""

# SQL migration script
$migrationSQL = @"
DO `$`$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'sessions' 
        AND column_name = 'platform_id'
    ) THEN
        ALTER TABLE sessions ADD COLUMN platform_id VARCHAR(50);
        
        UPDATE sessions 
        SET platform_id = platform 
        WHERE platform IS NOT NULL AND platform_id IS NULL;
        
        RAISE NOTICE 'platform_id column added successfully';
    ELSE
        RAISE NOTICE 'platform_id column already exists';
    END IF;
END `$`$;
"@

# Save to temp file
$tempFile = [System.IO.Path]::GetTempFileName() + ".sql"
$migrationSQL | Out-File -FilePath $tempFile -Encoding UTF8 -NoNewline

Write-Host "Connecting to Cloud SQL and running migration..." -ForegroundColor Yellow
Write-Host "Instance: $InstanceName" -ForegroundColor Gray
Write-Host "Database: $DatabaseName" -ForegroundColor Gray
Write-Host ""

# Use gcloud sql connect with psql
# Note: This requires psql to be installed and gcloud to handle the connection
Write-Host "Attempting to connect via gcloud sql connect..." -ForegroundColor Yellow

# Try to execute SQL via psql through gcloud
$psqlCommand = "`\i $tempFile"
$fullCommand = "echo '$migrationSQL' | gcloud sql connect $InstanceName --user=$DbUser --database=$DatabaseName --project=$ProjectId"

Write-Host "Note: gcloud sql connect is interactive." -ForegroundColor Yellow
Write-Host "Please run this command manually:" -ForegroundColor Cyan
Write-Host ""
Write-Host "gcloud sql connect $InstanceName --user=$DbUser --database=$DatabaseName --project=$ProjectId" -ForegroundColor White
Write-Host ""
Write-Host "Then in psql, run:" -ForegroundColor Yellow
Write-Host "`\i $tempFile" -ForegroundColor White
Write-Host ""
Write-Host "Or paste this SQL directly:" -ForegroundColor Yellow
Write-Host $migrationSQL -ForegroundColor Gray
Write-Host ""

# Alternative: Try to use Cloud SQL Admin API to execute SQL
Write-Host "Alternative: Using Cloud SQL Console" -ForegroundColor Cyan
Write-Host "1. Go to: https://console.cloud.google.com/sql/instances/$InstanceName/databases/$DatabaseName" -ForegroundColor White
Write-Host "2. Click 'Open Cloud Shell' or use Query tab" -ForegroundColor White
Write-Host "3. Run the SQL from: $tempFile" -ForegroundColor White
Write-Host ""

Write-Host "SQL file saved to: $tempFile" -ForegroundColor Green
