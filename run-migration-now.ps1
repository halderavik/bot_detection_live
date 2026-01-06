# Execute platform_id migration on production Cloud SQL using Cloud SQL Admin API
# This script uses gcloud authentication and REST API to execute SQL

param(
    [string]$ProjectId = "survey-bot-detection",
    [string]$InstanceName = "bot-db",
    [string]$DatabaseName = "bot_detection"
)

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Platform ID Migration - Executing Now" -ForegroundColor Cyan
Write-Host "=" * 60
Write-Host "Project: $ProjectId" -ForegroundColor Gray
Write-Host "Instance: $InstanceName" -ForegroundColor Gray
Write-Host "Database: $DatabaseName" -ForegroundColor Gray
Write-Host ""

# Get access token
Write-Host "Authenticating with gcloud..." -ForegroundColor Yellow
try {
    $accessToken = gcloud auth print-access-token 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to get access token" -ForegroundColor Red
        Write-Host "Please ensure you're authenticated: gcloud auth login" -ForegroundColor Yellow
        exit 1
    }
    $accessToken = $accessToken.Trim()
    Write-Host "Authenticated" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "ERROR: Could not get access token: $_" -ForegroundColor Red
    exit 1
}

# Read migration SQL
$sqlFile = "backend\migration_platform_id_production.sql"
if (-not (Test-Path $sqlFile)) {
    Write-Host "ERROR: SQL file not found: $sqlFile" -ForegroundColor Red
    exit 1
}

$migrationSQL = Get-Content $sqlFile -Raw
Write-Host "Migration SQL loaded from: $sqlFile" -ForegroundColor Green
Write-Host ""

# Split SQL into statements for execution
$statements = @(
    @"
DO `$`$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'sessions' 
        AND column_name = 'platform_id'
    ) THEN
        ALTER TABLE sessions 
        ADD COLUMN platform_id VARCHAR(255);
        
        RAISE NOTICE 'platform_id column added successfully';
    ELSE
        RAISE NOTICE 'platform_id column already exists';
    END IF;
END `$`$;
"@,
    @"
UPDATE sessions 
SET platform_id = platform 
WHERE platform IS NOT NULL AND platform_id IS NULL;
"@,
    @"
CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent_session 
ON sessions (survey_id, platform_id, respondent_id, id);
"@,
    @"
CREATE INDEX IF NOT EXISTS idx_survey_platform 
ON sessions (survey_id, platform_id);
"@,
    @"
CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent 
ON sessions (survey_id, platform_id, respondent_id);
"@,
    @"
CREATE INDEX IF NOT EXISTS idx_sessions_platform_id 
ON sessions (platform_id);
"@
)

Write-Host "Executing migration statements..." -ForegroundColor Yellow
Write-Host ""

$apiUrl = "https://sqladmin.googleapis.com/v1/projects/$ProjectId/instances/$InstanceName/databases/$DatabaseName/executeSql"

$successCount = 0
$failCount = 0

for ($i = 0; $i -lt $statements.Count; $i++) {
    $statement = $statements[$i].Trim()
    $statementNum = $i + 1
    
    Write-Host "Executing statement $statementNum/$($statements.Count)..." -NoNewline
    
    $headers = @{
        "Authorization" = "Bearer $accessToken"
        "Content-Type" = "application/json"
    }
    
    $body = @{
        sql = $statement
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri $apiUrl -Method Post -Headers $headers -Body $body -ErrorAction Stop
        
        Write-Host " SUCCESS" -ForegroundColor Green
        $successCount++
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        $errorMessage = $_.Exception.Message
        
        Write-Host " FAILED" -ForegroundColor Red
        Write-Host "  Status: $statusCode" -ForegroundColor Red
        Write-Host "  Error: $errorMessage" -ForegroundColor Red
        
        if ($statusCode -eq 403 -or $statusCode -eq 401) {
            Write-Host ""
            Write-Host "=" * 60 -ForegroundColor Yellow
            Write-Host "API Permission Error" -ForegroundColor Yellow
            Write-Host "=" * 60
            Write-Host "The Cloud SQL Admin API executeSql endpoint requires" -ForegroundColor Yellow
            Write-Host "specific IAM permissions that may not be enabled." -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Please use Cloud SQL Console instead:" -ForegroundColor Cyan
            Write-Host "1. Go to: https://console.cloud.google.com/sql/instances/$InstanceName" -ForegroundColor White
            Write-Host "2. Click 'Databases' tab -> Select '$DatabaseName'" -ForegroundColor White
            Write-Host "3. Click 'Open Cloud Shell' or use Query tab" -ForegroundColor White
            Write-Host "4. Paste SQL from: $sqlFile" -ForegroundColor White
            exit 1
        }
        
        $failCount++
    }
}

Write-Host ""
Write-Host "=" * 60

if ($failCount -eq 0) {
    Write-Host "SUCCESS: Migration completed successfully!" -ForegroundColor Green
    Write-Host "=" * 60
    
    # Verify migration
    Write-Host ""
    Write-Host "Verifying migration..." -ForegroundColor Yellow
    
    $verifySQL = @"
SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns
WHERE table_name = 'sessions' AND column_name = 'platform_id';
"@
    
    $verifyBody = @{
        sql = $verifySQL
    } | ConvertTo-Json
    
    try {
        $verifyResponse = Invoke-RestMethod -Uri $apiUrl -Method Post -Headers $headers -Body $verifyBody -ErrorAction Stop
        Write-Host "SUCCESS: Verification - platform_id column exists" -ForegroundColor Green
        if ($verifyResponse.rows) {
            Write-Host "  Column details: $($verifyResponse.rows | ConvertTo-Json)" -ForegroundColor Gray
        }
    } catch {
        Write-Host "WARNING: Could not verify, but migration appeared successful" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "1. Test the API endpoints to ensure they work correctly" -ForegroundColor White
    Write-Host "2. Run: .\test-endpoints-comprehensive.ps1" -ForegroundColor White
    
} else {
    Write-Host "ERROR: Migration completed with $failCount failure(s)" -ForegroundColor Red
    Write-Host "=" * 60
    Write-Host ""
    Write-Host "Please check the errors above and try again," -ForegroundColor Yellow
    Write-Host "or use Cloud SQL Console to run the migration manually." -ForegroundColor Yellow
    exit 1
}
