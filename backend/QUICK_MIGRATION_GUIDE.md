# Quick Migration Guide - Stage 3 Deployment

> **Current state (November 2026):** This is a record of a one-off migration for the Stage 3 deployment. It is not part of a normal deploy. New tables (`tracked_surveys`, `survey_quality_rules`, `app_settings`) are created when the backend starts (`Base.metadata.create_all` in `main.py`), so they need no migration. Existing tables were not changed. Only run SQL like this when an existing table changes. For deploy and rollback steps, see `SELECTIVE_DEPLOYMENT_GUIDE.md` and `rollback-procedures.md` in the repository root.

## Fastest Method: Cloud SQL Console Query Tab

1. **Open Query Tab**: https://console.cloud.google.com/sql/instances/bot-db/databases/bot_detection_v2/query?project=survey-bot-detection

2. **Copy SQL**: Open `combined_migration.sql` and copy ALL contents

3. **Paste & Run**: Paste into Query editor and click "Run"

4. **Verify**: Check for success messages (migrations are idempotent)

## What the Migration Does

- ✅ Adds `platform_id` column to `sessions` table
- ✅ Creates composite indexes for hierarchical queries
- ✅ Creates `fraud_indicators` table with all Stage 3 columns
- ✅ Adds `device_fingerprint` to `sessions`
- ✅ Adds `fraud_score` and `fraud_indicators` to `detection_results`
- ✅ Creates all required indexes for fraud detection

## After Migration

Test the deployment:
```powershell
# Test session creation
Invoke-RestMethod -Uri "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/detection/sessions?survey_id=test&platform_id=test-platform&respondent_id=test-123" -Method Post

# Test fraud detection endpoint
Invoke-RestMethod -Uri "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/test/platforms/test-platform/fraud-detection" -Method Get
```

## Alternative: Cloud Shell

If Query tab doesn't work, use Cloud Shell:
```bash
export DATABASE_URL=$(gcloud secrets versions access latest --secret=DATABASE_URL --project=survey-bot-detection)
pip3 install --user psycopg2-binary
python3 run_migration_sync.py
python3 run_fraud_migration_sync.py
python3 verify_v2_schema.py
```
