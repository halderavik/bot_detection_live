# Simple script to run platform_id migration on production Cloud SQL
# Since gcloud doesn't have execute-sql, we'll use Cloud Shell or provide manual instructions

param(
    [string]$ProjectId = "survey-bot-detection",
    [string]$InstanceName = "bot-db",
    [string]$DatabaseName = "bot_detection"
)

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Platform ID Migration for Production Cloud SQL" -ForegroundColor Cyan
Write-Host "=" * 60
Write-Host "Project: $ProjectId" -ForegroundColor Gray
Write-Host "Instance: $InstanceName" -ForegroundColor Gray
Write-Host "Database: $DatabaseName" -ForegroundColor Gray
Write-Host ""

# Migration SQL
$migrationSQL = @"
DO `$
BEGIN
    -- Check if column exists
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'sessions' 
        AND column_name = 'platform_id'
    ) THEN
        -- Add platform_id column (VARCHAR(255) to match model)
        ALTER TABLE sessions 
        ADD COLUMN platform_id VARCHAR(255);
        
        RAISE NOTICE 'platform_id column added successfully';
    ELSE
        RAISE NOTICE 'platform_id column already exists';
    END IF;
END `$;

-- Populate platform_id from existing platform values
UPDATE sessions 
SET platform_id = platform 
WHERE platform IS NOT NULL AND platform_id IS NULL;

-- Create composite indexes
CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent_session 
ON sessions (survey_id, platform_id, respondent_id, id);

CREATE INDEX IF NOT EXISTS idx_survey_platform 
ON sessions (survey_id, platform_id);

CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent 
ON sessions (survey_id, platform_id, respondent_id);

CREATE INDEX IF NOT EXISTS idx_sessions_platform_id 
ON sessions (platform_id);
"@

# Save SQL to file
$sqlFile = "backend\migration_platform_id_production.sql"
$migrationSQL | Out-File -FilePath $sqlFile -Encoding UTF8 -NoNewline

Write-Host "Migration SQL saved to: $sqlFile" -ForegroundColor Green
Write-Host ""

Write-Host "=" * 60 -ForegroundColor Yellow
Write-Host "Since gcloud doesn't support direct SQL execution," -ForegroundColor Yellow
Write-Host "please use one of these methods:" -ForegroundColor Yellow
Write-Host "=" * 60
Write-Host ""

Write-Host "OPTION 1: Cloud SQL Console (Easiest)" -ForegroundColor Cyan
Write-Host "  1. Open: https://console.cloud.google.com/sql/instances/$InstanceName/databases/$DatabaseName?project=$ProjectId" -ForegroundColor White
Write-Host "  2. Click 'Open Cloud Shell' button (top right)" -ForegroundColor White
Write-Host "  3. In Cloud Shell, run:" -ForegroundColor White
Write-Host "     gcloud sql connect $InstanceName --user=bot_user --database=$DatabaseName --project=$ProjectId" -ForegroundColor Gray
Write-Host "  4. In psql, run:" -ForegroundColor White
Write-Host "     \i $sqlFile" -ForegroundColor Gray
Write-Host "     (or copy/paste the SQL from the file)" -ForegroundColor Gray
Write-Host ""

Write-Host "OPTION 2: Cloud SQL Console Query Tab" -ForegroundColor Cyan
Write-Host "  1. Open: https://console.cloud.google.com/sql/instances/$InstanceName?project=$ProjectId" -ForegroundColor White
Write-Host "  2. Click on 'Databases' tab" -ForegroundColor White
Write-Host "  3. Select database: $DatabaseName" -ForegroundColor White
Write-Host "  4. Click 'Query' tab (if available)" -ForegroundColor White
Write-Host "  5. Copy and paste the SQL from: $sqlFile" -ForegroundColor White
Write-Host "  6. Click 'Run' to execute" -ForegroundColor White
Write-Host ""

Write-Host "OPTION 3: Use Python script with Cloud SQL Admin API" -ForegroundColor Cyan
Write-Host "  python backend\run_production_migration_api.py" -ForegroundColor White
Write-Host "  (Note: This will provide the SQL for manual execution)" -ForegroundColor Gray
Write-Host ""

Write-Host "=" * 60 -ForegroundColor Green
Write-Host "SQL File Location: $sqlFile" -ForegroundColor Green
Write-Host "=" * 60
