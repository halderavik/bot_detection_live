# Final attempt to run production database migration
# This script tries multiple methods to execute the SQL migration

param(
    [string]$ProjectId = "survey-bot-detection",
    [string]$InstanceName = "bot-db",
    [string]$DatabaseName = "bot_detection",
    [string]$DbUser = "bot_user"
)

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "Production Database Migration - Automated Execution" -ForegroundColor Cyan
Write-Host "=" * 70
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

# Save SQL to file
$sqlFile = ".\backend\migration_platform_id_production.sql"
$migrationSQL | Out-File -FilePath $sqlFile -Encoding UTF8 -NoNewline
Write-Host "[INFO] SQL migration saved to: $sqlFile" -ForegroundColor Green
Write-Host ""

# Method 1: Try using gcloud sql connect (requires psql)
Write-Host "Method 1: Attempting gcloud sql connect..." -ForegroundColor Yellow
$psqlCheck = Get-Command psql -ErrorAction SilentlyContinue
if ($psqlCheck) {
    Write-Host "[INFO] psql found, attempting connection..." -ForegroundColor Green
    # This would be interactive, so we'll skip for now
    Write-Host "[SKIP] gcloud sql connect requires interactive session" -ForegroundColor Yellow
} else {
    Write-Host "[SKIP] psql not found in PATH" -ForegroundColor Yellow
    Write-Host "      Install PostgreSQL client tools to use this method" -ForegroundColor Gray
}
Write-Host ""

# Method 2: Try using Cloud SQL Proxy (if available)
Write-Host "Method 2: Checking for Cloud SQL Proxy..." -ForegroundColor Yellow
$proxyCheck = Get-Command cloud_sql_proxy -ErrorAction SilentlyContinue
if ($proxyCheck) {
    Write-Host "[INFO] Cloud SQL Proxy found" -ForegroundColor Green
    Write-Host "[INFO] Starting Cloud SQL Proxy in background..." -ForegroundColor Yellow
    # Start proxy in background
    Start-Process -FilePath "cloud_sql_proxy" -ArgumentList "-instances=${ProjectId}:northamerica-northeast2:${InstanceName}=tcp:5432" -WindowStyle Hidden
    Start-Sleep -Seconds 3
    Write-Host "[INFO] Attempting to connect via proxy..." -ForegroundColor Yellow
    
    # Try to get database password from Secret Manager
    try {
        $dbUrl = gcloud secrets versions access latest --secret="DATABASE_URL" --project=$ProjectId 2>&1
        if ($LASTEXITCODE -eq 0) {
            # Extract password from URL
            if ($dbUrl -match "postgresql\+asyncpg://([^:]+):([^@]+)@") {
                $dbPassword = $matches[2]
                $dbUserFromUrl = $matches[1]
                
                # Try to execute SQL via psql through proxy
                if ($psqlCheck) {
                    $env:PGPASSWORD = $dbPassword
                    $sqlContent = Get-Content $sqlFile -Raw
                    echo $sqlContent | psql -h localhost -p 5432 -U $dbUserFromUrl -d $DatabaseName
                    
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host ""
                        Write-Host "[SUCCESS] Migration completed via Cloud SQL Proxy!" -ForegroundColor Green
                        exit 0
                    }
                }
            }
        }
    } catch {
        Write-Host "[SKIP] Could not use Cloud SQL Proxy method: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "[SKIP] Cloud SQL Proxy not found" -ForegroundColor Yellow
}
Write-Host ""

# Method 3: Provide manual instructions
Write-Host "Method 3: Manual Execution Required" -ForegroundColor Yellow
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""
Write-Host "Since automated methods are not available, please run the migration manually:" -ForegroundColor White
Write-Host ""
Write-Host "OPTION A: Via Cloud SQL Console (Easiest)" -ForegroundColor Cyan
Write-Host "  1. Open: https://console.cloud.google.com/sql/instances/$InstanceName/databases/$DatabaseName?project=$ProjectId" -ForegroundColor White
Write-Host "  2. Click 'Open Cloud Shell' button (top right)" -ForegroundColor White
Write-Host "  3. In Cloud Shell, run:" -ForegroundColor White
Write-Host "     gcloud sql connect $InstanceName --user=$DbUser --database=$DatabaseName --project=$ProjectId" -ForegroundColor Gray
Write-Host "  4. In psql, run:" -ForegroundColor White
Write-Host "     \i $sqlFile" -ForegroundColor Gray
Write-Host "     (or paste the SQL below)" -ForegroundColor Gray
Write-Host ""
Write-Host "OPTION B: Install psql and use gcloud sql connect" -ForegroundColor Cyan
Write-Host "  1. Install PostgreSQL client tools" -ForegroundColor White
Write-Host "  2. Run: gcloud sql connect $InstanceName --user=$DbUser --database=$DatabaseName --project=$ProjectId" -ForegroundColor White
Write-Host "  3. In psql, run: \i $sqlFile" -ForegroundColor White
Write-Host ""
Write-Host "SQL Migration Content:" -ForegroundColor Yellow
Write-Host "-" * 70 -ForegroundColor Gray
Write-Host $migrationSQL -ForegroundColor Gray
Write-Host "-" * 70 -ForegroundColor Gray
Write-Host ""
Write-Host "SQL file location: $sqlFile" -ForegroundColor Green
Write-Host ""
