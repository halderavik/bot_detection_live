# Execute platform_id migration by connecting directly to Cloud SQL
# This script gets the DATABASE_URL and public IP, then connects and executes SQL

param(
    [string]$ProjectId = "survey-bot-detection",
    [string]$InstanceName = "bot-db",
    [string]$DatabaseName = "bot_detection"
)

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Platform ID Migration - Direct Connection" -ForegroundColor Cyan
Write-Host "=" * 60
Write-Host "Project: $ProjectId" -ForegroundColor Gray
Write-Host "Instance: $InstanceName" -ForegroundColor Gray
Write-Host "Database: $DatabaseName" -ForegroundColor Gray
Write-Host ""

# Get DATABASE_URL from Secret Manager
Write-Host "Getting DATABASE_URL from Secret Manager..." -ForegroundColor Yellow
try {
    $databaseUrl = gcloud secrets versions access latest --secret="DATABASE_URL" --project=$ProjectId 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to get DATABASE_URL" -ForegroundColor Red
        exit 1
    }
    $databaseUrl = $databaseUrl.Trim()
    Write-Host "DATABASE_URL retrieved" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Could not get DATABASE_URL: $_" -ForegroundColor Red
    exit 1
}

# Parse DATABASE_URL to extract connection details
Write-Host "Parsing connection details..." -ForegroundColor Yellow
# Format: postgresql+asyncpg://user:password@/database?host=/cloudsql/...
$databaseUrl = $databaseUrl -replace 'postgresql\+asyncpg://', 'postgresql://'

if ($databaseUrl -match 'postgresql://([^:]+):([^@]+)@/([^?]+)') {
    $dbUser = $matches[1]
    $dbPassword = $matches[2]
    $dbName = $matches[3]
    Write-Host "User: $dbUser" -ForegroundColor Gray
    Write-Host "Database: $dbName" -ForegroundColor Gray
} else {
    Write-Host "ERROR: Could not parse DATABASE_URL" -ForegroundColor Red
    exit 1
}

# Get Cloud SQL public IP
Write-Host "Getting Cloud SQL public IP..." -ForegroundColor Yellow
try {
    $publicIp = gcloud sql instances describe $InstanceName --project=$ProjectId --format="value(ipAddresses[0].ipAddress)" 2>&1
    if ($LASTEXITCODE -ne 0 -or -not $publicIp) {
        Write-Host "ERROR: Could not get public IP" -ForegroundColor Red
        Write-Host "The instance may not have a public IP or may require authorized networks" -ForegroundColor Yellow
        exit 1
    }
    $publicIp = $publicIp.Trim()
    Write-Host "Public IP: $publicIp" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Could not get public IP: $_" -ForegroundColor Red
    exit 1
}

# Read migration SQL
$sqlFile = "backend\migration_platform_id_production.sql"
if (-not (Test-Path $sqlFile)) {
    Write-Host "ERROR: SQL file not found: $sqlFile" -ForegroundColor Red
    exit 1
}

$migrationSQL = Get-Content $sqlFile -Raw
Write-Host "Migration SQL loaded" -ForegroundColor Green
Write-Host ""

# Check if psql is available (for direct connection)
$psqlAvailable = $false
try {
    $null = Get-Command psql -ErrorAction Stop
    $psqlAvailable = $true
} catch {
    Write-Host "psql not found. Will use Python with psycopg2..." -ForegroundColor Yellow
}

if ($psqlAvailable) {
    Write-Host "Using psql to connect..." -ForegroundColor Yellow
    
    # Set PGPASSWORD environment variable
    $env:PGPASSWORD = $dbPassword
    
    # Save SQL to temp file
    $tempFile = [System.IO.Path]::GetTempFileName() + ".sql"
    $migrationSQL | Out-File -FilePath $tempFile -Encoding UTF8 -NoNewline
    
    # Connect and execute
    $psqlCommand = "psql -h $publicIp -p 5432 -U $dbUser -d $dbName -f $tempFile"
    
    Write-Host "Executing migration..." -ForegroundColor Yellow
    Invoke-Expression $psqlCommand
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "=" * 60 -ForegroundColor Green
        Write-Host "SUCCESS: Migration completed!" -ForegroundColor Green
        Write-Host "=" * 60
        Remove-Item $tempFile -Force
    } else {
        Write-Host ""
        Write-Host "ERROR: Migration failed" -ForegroundColor Red
        Write-Host "SQL file saved at: $tempFile" -ForegroundColor Yellow
        exit 1
    }
} else {
    # Use Python with psycopg2
    Write-Host "Using Python with psycopg2..." -ForegroundColor Yellow
    
    # Create a Python script to execute
    $pythonScript = @"
import psycopg2
import sys

try:
    conn = psycopg2.connect(
        host='$publicIp',
        port=5432,
        database='$dbName',
        user='$dbUser',
        password='$dbPassword',
        connect_timeout=10
    )
    
    cursor = conn.cursor()
    
    # Read and execute SQL
    with open(r'$sqlFile', 'r', encoding='utf-8') as f:
        sql = f.read()
    
    cursor.execute(sql)
    conn.commit()
    
    # Verify
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'sessions' AND column_name = 'platform_id'
    """)
    result = cursor.fetchone()
    
    if result:
        print(f"SUCCESS: platform_id column exists (Type: {result[1]}({result[2]}))")
    else:
        print("WARNING: Could not verify column exists")
    
    cursor.close()
    conn.close()
    
    print("Migration completed successfully!")
    sys.exit(0)
    
except psycopg2.OperationalError as e:
    if "timeout" in str(e).lower() or "connection" in str(e).lower():
        print("ERROR: Could not connect to Cloud SQL")
        print("The instance may require authorized networks")
        print("Please use Cloud SQL Console instead")
    else:
        print(f"ERROR: {e}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"@
    
    $tempPythonFile = [System.IO.Path]::GetTempFileName() + ".py"
    $pythonScript | Out-File -FilePath $tempPythonFile -Encoding UTF8
    
    Write-Host "Executing migration..." -ForegroundColor Yellow
    python $tempPythonFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "=" * 60 -ForegroundColor Green
        Write-Host "SUCCESS: Migration completed!" -ForegroundColor Green
        Write-Host "=" * 60
        Remove-Item $tempPythonFile -Force
    } else {
        Write-Host ""
        Write-Host "ERROR: Migration failed" -ForegroundColor Red
        Write-Host "Python script saved at: $tempPythonFile" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Alternative: Use Cloud SQL Console" -ForegroundColor Yellow
        Write-Host "1. Go to: https://console.cloud.google.com/sql/instances/$InstanceName" -ForegroundColor White
        Write-Host "2. Click 'Databases' tab -> Select '$DatabaseName'" -ForegroundColor White
        Write-Host "3. Click 'Open Cloud Shell' or use Query tab" -ForegroundColor White
        Write-Host "4. Paste SQL from: $sqlFile" -ForegroundColor White
        exit 1
    }
}

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Test the API endpoints to ensure they work correctly" -ForegroundColor White
Write-Host "2. Run: .\test-endpoints-comprehensive.ps1" -ForegroundColor White
