# ⚠️ Database Migration Required

## Issue Identified

The production database is missing the `platform_id` column in the `sessions` table, causing 500 errors on several endpoints.

**Error:** `column sessions.platform_id does not exist`

## Affected Endpoints

The following endpoints are failing with 500 errors:
- `POST /api/v1/detection/sessions` - Create session
- `GET /api/v1/dashboard/sessions` - List sessions  
- `GET /api/v1/reports/summary/{survey_id}` - Get survey summary
- `GET /api/v1/surveys/{survey_id}` - Get survey details
- `GET /api/v1/surveys/{survey_id}/summary` - Get survey summary
- `GET /api/v1/surveys/{survey_id}/platforms` - List platforms

## Solution: Run Database Migration

### Migration SQL Script
Location: `backend/migration_platform_id.sql`

### How to Run the Migration

#### Option 1: Via Cloud Console (Easiest)
1. Go to [Google Cloud Console](https://console.cloud.google.com/sql/instances)
2. Select instance: `bot-db`
3. Click on "Databases" tab
4. Select database: `bot_detection`
5. Click "Open Cloud Shell" or use the Query interface
6. Copy and paste the SQL from `backend/migration_platform_id.sql`
7. Execute the SQL

#### Option 2: Via Cloud SQL Proxy
```powershell
# Start Cloud SQL Proxy (in separate terminal)
cloud_sql_proxy -instances=survey-bot-detection:northamerica-northeast2:bot-db=tcp:5432

# In another terminal, connect and run migration
psql -h localhost -U postgres -d bot_detection -f backend/migration_platform_id.sql
```

#### Option 3: Via gcloud sql connect
```powershell
gcloud sql connect bot-db --user=postgres --project=survey-bot-detection
# Then in psql:
\i backend/migration_platform_id.sql
```

### What the Migration Does

1. ✅ Adds `platform_id VARCHAR(50)` column to `sessions` table
2. ✅ Populates `platform_id` from existing `platform` values
3. ✅ Creates composite indexes for efficient hierarchical queries:
   - `idx_survey_platform_respondent_session`
   - `idx_survey_platform`
   - `idx_survey_platform_respondent`
4. ✅ Creates individual index on `platform_id`

### Verification

After running the migration, test the endpoints:
```powershell
.\test-endpoints-comprehensive.ps1
```

All previously failing endpoints should now work.

## Current Status

- ✅ **11 endpoints working** (65%)
- ❌ **6 endpoints failing** (35%) - All due to missing `platform_id` column

## Next Steps

1. Run the migration using one of the options above
2. Verify endpoints are working
3. Test all API endpoints again

