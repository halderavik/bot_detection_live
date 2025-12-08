# Run database migration on production
# This script runs the platform_id migration on the production database

Write-Host "🚀 Running Database Migration on Production" -ForegroundColor Green
Write-Host ""

# Set environment to use production database
$env:DATABASE_URL = (gcloud secrets versions access latest --secret="DATABASE_URL" --project="survey-bot-detection")

Write-Host "Running migration script..." -ForegroundColor Yellow
cd backend
python -m app.migrations.add_platform_id_migration

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Migration completed successfully!" -ForegroundColor Green
} else {
    Write-Host "`n❌ Migration failed. Check logs above." -ForegroundColor Red
}

cd ..

