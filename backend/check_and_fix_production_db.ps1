# PowerShell script to check and fix production database schema
# This ensures the production database has the platform_id column

param(
    [string]$ProjectId = "survey-bot-detection",
    [string]$InstanceName = "bot-db",
    [string]$DatabaseName = "bot_detection",
    [string]$Region = "northamerica-northeast2"
)

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Checking Production Database Schema" -ForegroundColor Cyan
Write-Host "=" * 60
Write-Host ""

# SQL to check and add platform_id column
$sqlScript = @"
-- Add platform_id column if it doesn't exist
DO `$`$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'sessions' 
        AND column_name = 'platform_id'
    ) THEN
        ALTER TABLE sessions ADD COLUMN platform_id VARCHAR(50);
        
        -- Populate from existing platform values
        UPDATE sessions 
        SET platform_id = platform 
        WHERE platform IS NOT NULL AND platform_id IS NULL;
        
        RAISE NOTICE 'platform_id column added successfully';
    ELSE
        RAISE NOTICE 'platform_id column already exists';
    END IF;
END `$`$;
"@

# Save SQL to temporary file
$tempFile = [System.IO.Path]::GetTempFileName() + ".sql"
$sqlScript | Out-File -FilePath $tempFile -Encoding UTF8

Write-Host "Connecting to production database..." -ForegroundColor Yellow
Write-Host "Project: $ProjectId" -ForegroundColor Gray
Write-Host "Instance: $InstanceName" -ForegroundColor Gray
Write-Host "Database: $DatabaseName" -ForegroundColor Gray
Write-Host ""

try {
    # Connect and run the migration
    Write-Host "Running migration SQL..." -ForegroundColor Yellow
    
    # Use gcloud sql connect to run the SQL
    $sqlCommand = "gcloud sql connect $InstanceName --database=$DatabaseName --project=$ProjectId --quiet"
    
    # Alternative: Use psql via Cloud SQL Proxy or direct connection
    # For now, let's use gcloud sql execute-sql
    Write-Host "Executing SQL migration..." -ForegroundColor Yellow
    
    # Read the SQL file content
    $sqlContent = Get-Content $tempFile -Raw
    
    # Execute via gcloud
    gcloud sql databases execute-sql $DatabaseName `
        --instance=$InstanceName `
        --project=$ProjectId `
        --sql="$sqlContent"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[SUCCESS] Database schema check and migration completed!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "[WARNING] Migration may have failed. Check the output above." -ForegroundColor Yellow
        Write-Host "You may need to run this SQL manually in Cloud SQL Console." -ForegroundColor Yellow
    }
    
} catch {
    Write-Host ""
    Write-Host "[ERROR] Failed to execute migration: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Alternative: Run this SQL manually in Cloud SQL Console:" -ForegroundColor Yellow
    Write-Host $sqlScript -ForegroundColor Gray
} finally {
    # Clean up temp file
    if (Test-Path $tempFile) {
        Remove-Item $tempFile -Force
    }
}

Write-Host ""
Write-Host "=" * 60
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Verify the migration completed successfully" -ForegroundColor White
Write-Host "2. Test production API again" -ForegroundColor White
Write-Host "3. Run: python backend/test_production_text_analysis.py" -ForegroundColor White
Write-Host "=" * 60
