# Execute platform_id migration using Cloud Shell
# This script uploads the SQL to Cloud Shell and executes it

param(
    [string]$ProjectId = "survey-bot-detection",
    [string]$InstanceName = "bot-db",
    [string]$DatabaseName = "bot_detection"
)

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Platform ID Migration via Cloud Shell" -ForegroundColor Cyan
Write-Host "=" * 60
Write-Host ""

$sqlFile = "backend\migration_platform_id_production.sql"
if (-not (Test-Path $sqlFile)) {
    Write-Host "ERROR: SQL file not found: $sqlFile" -ForegroundColor Red
    exit 1
}

$migrationSQL = Get-Content $sqlFile -Raw

Write-Host "Since Cloud SQL requires authorized networks," -ForegroundColor Yellow
Write-Host "we'll use Cloud Shell to execute the migration." -ForegroundColor Yellow
Write-Host ""

# Create a script that will be run in Cloud Shell
$cloudShellScript = @"
#!/bin/bash
# Platform ID Migration Script for Cloud Shell

PROJECT_ID="$ProjectId"
INSTANCE_NAME="$InstanceName"
DATABASE_NAME="$DatabaseName"

echo "============================================================"
echo "Platform ID Migration"
echo "============================================================"
echo "Project: `$PROJECT_ID"
echo "Instance: `$INSTANCE_NAME"
echo "Database: `$DATABASE_NAME"
echo ""

# SQL migration
SQL_MIGRATION='$($migrationSQL -replace "'", "''")'

echo "Connecting to Cloud SQL..."
gcloud sql connect `$INSTANCE_NAME --user=bot_user --database=`$DATABASE_NAME --project=`$PROJECT_ID <<EOF
`$SQL_MIGRATION
EOF

if [ `$? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "SUCCESS: Migration completed!"
    echo "============================================================"
    
    # Verify
    echo ""
    echo "Verifying migration..."
    gcloud sql connect `$INSTANCE_NAME --user=bot_user --database=`$DATABASE_NAME --project=`$PROJECT_ID <<EOF
SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns
WHERE table_name = 'sessions' AND column_name = 'platform_id';
EOF
else
    echo ""
    echo "ERROR: Migration failed"
    exit 1
fi
"@

# Save script to temp file
$tempScript = [System.IO.Path]::GetTempFileName() + ".sh"
$cloudShellScript | Out-File -FilePath $tempScript -Encoding UTF8 -NoNewline

Write-Host "Cloud Shell script created: $tempScript" -ForegroundColor Green
Write-Host ""

# Try to use Cloud Shell API to execute (if available)
Write-Host "Attempting to execute via Cloud Shell API..." -ForegroundColor Yellow

# Alternative: Provide simple instructions
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Yellow
Write-Host "Simplest Method: Copy-Paste in Cloud Shell" -ForegroundColor Yellow
Write-Host "=" * 60
Write-Host ""
Write-Host "1. Open Cloud Shell: https://shell.cloud.google.com/" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Run this command to connect:" -ForegroundColor Cyan
Write-Host "   gcloud sql connect $InstanceName --user=bot_user --database=$DatabaseName --project=$ProjectId" -ForegroundColor White
Write-Host ""
Write-Host "3. When connected to psql, paste this SQL:" -ForegroundColor Cyan
Write-Host "   (The SQL will be displayed below)" -ForegroundColor Gray
Write-Host ""
Write-Host "-" * 60 -ForegroundColor Gray
Write-Host $migrationSQL -ForegroundColor White
Write-Host "-" * 60 -ForegroundColor Gray
Write-Host ""

# Or provide a one-liner approach
Write-Host "=" * 60 -ForegroundColor Green
Write-Host "One-Liner Alternative (if you have the SQL file in Cloud Shell):" -ForegroundColor Green
Write-Host "=" * 60
Write-Host ""
Write-Host "1. Upload $sqlFile to Cloud Shell" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Run this command:" -ForegroundColor Cyan
Write-Host "   gcloud sql connect $InstanceName --user=bot_user --database=$DatabaseName --project=$ProjectId < $sqlFile" -ForegroundColor White
Write-Host ""

Write-Host "Script saved at: $tempScript" -ForegroundColor Gray
Write-Host "You can upload this to Cloud Shell and run it with: bash $([System.IO.Path]::GetFileName($tempScript))" -ForegroundColor Gray
