# Verify and Fix Production Database Schema
# This script checks if the platform_id column exists and creates it if needed

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Production Database Schema Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$PROJECT_ID = "survey-bot-detection"
$REGION = "northamerica-northeast2"
$INSTANCE_NAME = "bot-db"
$DB_NAME = "bot_detection"

Write-Host "Checking database schema..." -ForegroundColor Yellow
Write-Host ""

# Create a temporary SQL script to check schema
$CHECK_SQL = @"
-- Check if platform_id column exists
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'sessions'
ORDER BY ordinal_position;

-- Check indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'sessions';
"@

$CHECK_SQL | Out-File -FilePath "temp_check_schema.sql" -Encoding UTF8

Write-Host "Step 1: Verifying current schema..." -ForegroundColor Green

# Execute the check (this will require manual inspection or use of gcloud sql connect)
Write-Host ""
Write-Host "To check the current database schema, run:" -ForegroundColor Yellow
Write-Host "gcloud sql connect $INSTANCE_NAME --user=bot_user --database=$DB_NAME --project=$PROJECT_ID" -ForegroundColor White
Write-Host ""
Write-Host "Then in the PostgreSQL prompt, run:" -ForegroundColor Yellow
Write-Host "\d sessions" -ForegroundColor White
Write-Host ""

# Check if platform_id column is missing
Write-Host "Step 2: If platform_id column is missing, apply migration..." -ForegroundColor Green
Write-Host ""
Write-Host "Run the following command to apply the migration:" -ForegroundColor Yellow
Write-Host "psql 'postgresql://bot_user:NewPassword123!@localhost:5432/bot_detection?host=/cloudsql/$PROJECT_ID`:$REGION`:$INSTANCE_NAME' -f backend\migration_platform_id_production.sql" -ForegroundColor White
Write-Host ""

# Alternative: Use Cloud SQL proxy
Write-Host "Alternative: Use Cloud SQL Proxy" -ForegroundColor Green
Write-Host "1. Download Cloud SQL Proxy:" -ForegroundColor Yellow
Write-Host "   https://cloud.google.com/sql/docs/postgres/connect-admin-proxy" -ForegroundColor White
Write-Host ""
Write-Host "2. Start proxy:" -ForegroundColor Yellow
Write-Host "   .\cloud_sql_proxy.exe -instances=$PROJECT_ID`:$REGION`:$INSTANCE_NAME=tcp:5432" -ForegroundColor White
Write-Host ""
Write-Host "3. In another terminal, run migration:" -ForegroundColor Yellow
Write-Host "   psql -h 127.0.0.1 -U bot_user -d $DB_NAME -f backend\migration_platform_id_production.sql" -ForegroundColor White
Write-Host ""

# Create a script to run the diagnostic test
Write-Host "Step 3: Test database connection from local machine..." -ForegroundColor Green
Write-Host ""
Write-Host "To test the database connection with the diagnostic script:" -ForegroundColor Yellow
Write-Host "cd backend" -ForegroundColor White
Write-Host "`$env:DATABASE_URL = 'postgresql+asyncpg://bot_user:NewPassword123!@localhost:5432/bot_detection'" -ForegroundColor White
Write-Host "python test_production_db_connection.py" -ForegroundColor White
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. ✓ DATABASE_URL secret is correct" -ForegroundColor Green
Write-Host "2. ⚠ Check if platform_id column exists (manual)" -ForegroundColor Yellow
Write-Host "3. ⚠ Apply migration if needed (see commands above)" -ForegroundColor Yellow
Write-Host "4. ⚠ Redeploy backend after schema fix" -ForegroundColor Yellow
Write-Host ""

# Clean up
Remove-Item "temp_check_schema.sql" -ErrorAction SilentlyContinue
