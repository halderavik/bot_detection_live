# Direct SQL migration execution
# This will execute the migration SQL directly on Cloud SQL

$sql = @"
-- Migration: Add platform_id column to sessions table
DO `$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'sessions' 
        AND column_name = 'platform_id'
    ) THEN
        -- Add platform_id column
        ALTER TABLE sessions ADD COLUMN platform_id VARCHAR(50);
        
        -- Populate platform_id from existing platform values
        UPDATE sessions SET platform_id = platform WHERE platform IS NOT NULL AND platform_id IS NULL;
        
        -- Create composite indexes
        CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent_session ON sessions (survey_id, platform_id, respondent_id, id);
        CREATE INDEX IF NOT EXISTS idx_survey_platform ON sessions (survey_id, platform_id);
        CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent ON sessions (survey_id, platform_id, respondent_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_platform_id ON sessions (platform_id);
        
        RAISE NOTICE 'Migration completed successfully';
    ELSE
        RAISE NOTICE 'platform_id column already exists';
    END IF;
END `$;
"@

Write-Host "Executing migration on Cloud SQL..." -ForegroundColor Yellow
Write-Host "Instance: bot-db" -ForegroundColor Cyan
Write-Host "Database: bot_detection" -ForegroundColor Cyan
Write-Host ""

# Save SQL to temp file
$tempFile = [System.IO.Path]::GetTempFileName() + ".sql"
$sql | Out-File -FilePath $tempFile -Encoding UTF8

Write-Host "SQL saved to: $tempFile" -ForegroundColor Gray
Write-Host "`nTo execute, run:" -ForegroundColor Yellow
Write-Host "gcloud sql connect bot-db --user=postgres --project=survey-bot-detection" -ForegroundColor White
Write-Host "Then in psql, run: \i $tempFile" -ForegroundColor White
Write-Host "`nOr copy the SQL from backend/migration_platform_id.sql and run in Cloud Console" -ForegroundColor White

