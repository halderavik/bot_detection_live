# PowerShell script to run the platform_id migration locally
# This adds the missing platform_id column to the sessions table

Write-Host "Running platform_id migration..." -ForegroundColor Green
Write-Host ""

# Read database connection from .env file
$envContent = Get-Content "backend\.env" | Where-Object { $_ -match "^DATABASE_URL=" }
if (-not $envContent) {
    Write-Host "Error: DATABASE_URL not found in .env file" -ForegroundColor Red
    exit 1
}

# Extract connection details (basic parsing)
$dbUrl = ($envContent -split "=")[1]
Write-Host "Database URL: $($dbUrl -replace ':[^:@]+@', ':****@')" -ForegroundColor Yellow
Write-Host ""

# Parse connection string
if ($dbUrl -match "postgresql\+asyncpg://([^:]+):([^@]+)@([^/]+)/(.+)") {
    $username = $matches[1]
    $password = $matches[2]
    $host = $matches[3]
    $database = $matches[4]
    
    Write-Host "Connecting to database: $database on $host" -ForegroundColor Cyan
    Write-Host ""
    
    # Set PGPASSWORD environment variable
    $env:PGPASSWORD = $password
    
    # Run the migration SQL
    $sqlFile = "backend\add_platform_id_column.sql"
    if (Test-Path $sqlFile) {
        Write-Host "Running migration SQL..." -ForegroundColor Yellow
        psql -h $host -U $username -d $database -f $sqlFile
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "Migration completed successfully!" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "Migration failed. Check the error above." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "Error: Migration SQL file not found: $sqlFile" -ForegroundColor Red
        exit 1
    }
    
    # Clear password
    Remove-Item Env:\PGPASSWORD
} else {
    Write-Host "Error: Could not parse DATABASE_URL" -ForegroundColor Red
    Write-Host "Expected format: postgresql+asyncpg://user:password@host/database" -ForegroundColor Yellow
    exit 1
}
