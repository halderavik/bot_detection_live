# Run platform_id migration on production Cloud SQL using gcloud CLI
# This script uses gcloud sql databases execute-sql to run the migration
# without requiring psql to be installed

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

# Check if gcloud is available
try {
    $gcloudVersion = gcloud --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: gcloud CLI is not installed or not in PATH" -ForegroundColor Red
        Write-Host "Please install gcloud CLI: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "gcloud CLI found" -ForegroundColor Green
} catch {
    Write-Host "ERROR: gcloud CLI is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install gcloud CLI: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

# Check authentication
Write-Host "Checking gcloud authentication..." -ForegroundColor Yellow
try {
    $account = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>&1
    if ($account) {
        Write-Host "Authenticated as: $account" -ForegroundColor Green
    } else {
        Write-Host "WARNING: No active gcloud authentication found" -ForegroundColor Yellow
        Write-Host "Please run: gcloud auth login" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "WARNING: Could not verify authentication" -ForegroundColor Yellow
}

Write-Host ""

# Migration SQL - using DO block for safety
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

# Save SQL to temp file
$tempFile = [System.IO.Path]::GetTempFileName() + ".sql"
$migrationSQL | Out-File -FilePath $tempFile -Encoding UTF8 -NoNewline

Write-Host "Migration SQL saved to: $tempFile" -ForegroundColor Gray
Write-Host ""
Write-Host "Executing migration on Cloud SQL..." -ForegroundColor Yellow
Write-Host ""

# Execute migration using gcloud
try {
    gcloud sql databases execute-sql $DatabaseName `
        --instance=$InstanceName `
        --file=$tempFile `
        --project=$ProjectId `
        --quiet
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "=" * 60 -ForegroundColor Green
        Write-Host "SUCCESS: Migration completed successfully!" -ForegroundColor Green
        Write-Host "=" * 60
        
        # Verify the migration
        Write-Host ""
        Write-Host "Verifying migration..." -ForegroundColor Yellow
        
        $verifySQL = "SELECT column_name FROM information_schema.columns WHERE table_name = 'sessions' AND column_name = 'platform_id';"
        $verifyFile = [System.IO.Path]::GetTempFileName() + ".sql"
        $verifySQL | Out-File -FilePath $verifyFile -Encoding UTF8 -NoNewline
        
        gcloud sql databases execute-sql $DatabaseName `
            --instance=$InstanceName `
            --file=$verifyFile `
            --project=$ProjectId `
            --quiet | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "SUCCESS: Verification - platform_id column exists" -ForegroundColor Green
        }
        
        Remove-Item $verifyFile -Force -ErrorAction SilentlyContinue
        
    } else {
        Write-Host ""
        Write-Host "=" * 60 -ForegroundColor Red
        Write-Host "ERROR: Migration failed!" -ForegroundColor Red
        Write-Host "=" * 60
        Write-Host ""
        Write-Host "You may need to run the SQL manually in Cloud SQL Console:" -ForegroundColor Yellow
        Write-Host "1. Go to: https://console.cloud.google.com/sql/instances/$InstanceName" -ForegroundColor White
        Write-Host "2. Click on 'Databases' tab" -ForegroundColor White
        Write-Host "3. Select database: $DatabaseName" -ForegroundColor White
        Write-Host "4. Click 'Open Cloud Shell' or use Query tab" -ForegroundColor White
        Write-Host "5. Paste and run the SQL from: $tempFile" -ForegroundColor White
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Red
    Write-Host "ERROR: Failed to execute migration" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "=" * 60
    Write-Host ""
    Write-Host "Alternative: Run SQL manually in Cloud SQL Console" -ForegroundColor Yellow
    Write-Host "SQL file location: $tempFile" -ForegroundColor Gray
    exit 1
} finally {
    # Keep temp file for reference
    Write-Host ""
    Write-Host "Note: SQL file saved at: $tempFile" -ForegroundColor Gray
    Write-Host "You can delete it manually after verifying the migration." -ForegroundColor Gray
}

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Verify the migration by checking the database schema" -ForegroundColor White
Write-Host "2. Test the API endpoints to ensure they work correctly" -ForegroundColor White
Write-Host "3. Run: .\test-endpoints-comprehensive.ps1" -ForegroundColor White
