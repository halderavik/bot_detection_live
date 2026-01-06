# Run Production Database Schema Fix
# This script applies the platform_id migration to production database

param(
    [string]$ProjectId = "survey-bot-detection",
    [string]$Region = "northamerica-northeast2",
    [string]$InstanceName = "bot-db",
    [string]$DatabaseName = "bot_detection"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Production Database Schema Fix" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Target Database:" -ForegroundColor Yellow
Write-Host "  Project: $ProjectId" -ForegroundColor White
Write-Host "  Instance: $InstanceName" -ForegroundColor White
Write-Host "  Database: $DatabaseName" -ForegroundColor White
Write-Host ""

# Step 1: Check current schema
Write-Host "Step 1: Checking if platform_id column exists..." -ForegroundColor Green

$CHECK_QUERY = "SELECT column_name FROM information_schema.columns WHERE table_name = 'sessions' AND column_name = 'platform_id';"

Write-Host "Executing query: $CHECK_QUERY" -ForegroundColor Gray

try {
    $result = gcloud sql query $InstanceName `
        --database=$DatabaseName `
        --project=$ProjectId `
        --sql="$CHECK_QUERY" `
        2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Query executed successfully" -ForegroundColor Green
        if ($result -match "platform_id") {
            Write-Host "✓ platform_id column already exists!" -ForegroundColor Green
            Write-Host ""
            Write-Host "Schema is up to date. No migration needed." -ForegroundColor Green
            exit 0
        } else {
            Write-Host "⚠ platform_id column is missing!" -ForegroundColor Yellow
            Write-Host ""
        }
    }
} catch {
    Write-Host "⚠ Could not check schema: $_" -ForegroundColor Yellow
    Write-Host "Proceeding with migration anyway..." -ForegroundColor Yellow
}

# Step 2: Apply migration
Write-Host "Step 2: Applying migration..." -ForegroundColor Green
Write-Host ""

$MIGRATION_SQL = @"
-- Add platform_id column if it doesn't exist
DO `$`$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'sessions' AND column_name = 'platform_id'
    ) THEN
        ALTER TABLE sessions ADD COLUMN platform_id VARCHAR(255);
        CREATE INDEX IF NOT EXISTS idx_sessions_platform_id ON sessions(platform_id);
        RAISE NOTICE 'Added platform_id column and index';
    ELSE
        RAISE NOTICE 'platform_id column already exists';
    END IF;
END
`$`$;

-- Add composite indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_survey_platform ON sessions(survey_id, platform_id);
CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent ON sessions(survey_id, platform_id, respondent_id);
CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent_session ON sessions(survey_id, platform_id, respondent_id, id);

-- Verify the changes
SELECT 
    column_name, 
    data_type, 
    is_nullable 
FROM information_schema.columns 
WHERE table_name = 'sessions' 
  AND column_name IN ('platform', 'platform_id')
ORDER BY column_name;
"@

Write-Host "Migration SQL:" -ForegroundColor Gray
Write-Host $MIGRATION_SQL -ForegroundColor DarkGray
Write-Host ""

# Save migration to temp file
$MIGRATION_SQL | Out-File -FilePath "temp_migration.sql" -Encoding UTF8

Write-Host "Applying migration to production database..." -ForegroundColor Yellow

try {
    # Note: gcloud sql query doesn't support file input directly with DO blocks
    # We'll need to execute the migration using Cloud SQL Auth Proxy or direct connection
    
    Write-Host ""
    Write-Host "⚠ IMPORTANT: gcloud sql query has limitations with complex SQL." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please use ONE of these methods:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "METHOD 1: Cloud Shell (Recommended)" -ForegroundColor Cyan
    Write-Host "-----------------------------------------" -ForegroundColor Gray
    Write-Host "1. Upload migration file to Cloud Shell:" -ForegroundColor White
    Write-Host "   gcloud compute scp backend\migration_platform_id_production.sql cloudshell:~/" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. In Cloud Shell, run:" -ForegroundColor White
    Write-Host "   gcloud sql connect $InstanceName --user=bot_user --database=$DatabaseName --project=$ProjectId" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3. At the postgres prompt, run:" -ForegroundColor White
    Write-Host "   \i migration_platform_id_production.sql" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "METHOD 2: Using Cloud SQL Proxy (Local)" -ForegroundColor Cyan
    Write-Host "-----------------------------------------" -ForegroundColor Gray
    Write-Host "1. Download and start Cloud SQL Proxy:" -ForegroundColor White
    Write-Host "   cloud-sql-proxy $ProjectId`:$Region`:$InstanceName" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. In another terminal, run:" -ForegroundColor White
    Write-Host "   psql -h localhost -U bot_user -d $DatabaseName -f backend\migration_platform_id_production.sql" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "METHOD 3: Try Simple ALTER (Limited)" -ForegroundColor Cyan
    Write-Host "-----------------------------------------" -ForegroundColor Gray
    Write-Host "Attempting simple column add..." -ForegroundColor White
    
    $SIMPLE_ALTER = "ALTER TABLE sessions ADD COLUMN IF NOT EXISTS platform_id VARCHAR(255);"
    
    $alterResult = gcloud sql query $InstanceName `
        --database=$DatabaseName `
        --project=$ProjectId `
        --sql="$SIMPLE_ALTER" `
        2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Column added successfully!" -ForegroundColor Green
        
        # Try to add index
        $INDEX_SQL = "CREATE INDEX IF NOT EXISTS idx_sessions_platform_id ON sessions(platform_id);"
        gcloud sql query $InstanceName `
            --database=$DatabaseName `
            --project=$ProjectId `
            --sql="$INDEX_SQL" `
            2>&1 | Out-Null
        
        Write-Host "✓ Basic migration completed!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Note: Composite indexes may need to be added manually." -ForegroundColor Yellow
    } else {
        Write-Host "⚠ Simple ALTER failed: $alterResult" -ForegroundColor Yellow
        Write-Host "Please use METHOD 1 or METHOD 2 above." -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "❌ Error applying migration: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please use METHOD 1 or METHOD 2 above to apply the migration." -ForegroundColor Yellow
} finally {
    # Clean up
    Remove-Item "temp_migration.sql" -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "After migration is complete:" -ForegroundColor Yellow
Write-Host "1. Verify schema with diagnostic script" -ForegroundColor White
Write-Host "2. Redeploy backend to Cloud Run" -ForegroundColor White
Write-Host "3. Run production tests" -ForegroundColor White
Write-Host ""
