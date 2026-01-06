# Platform ID Migration Guide

## Issue
The production Cloud SQL database is missing the `platform_id` column in the `sessions` table, causing differences between local and production database structures. The local database is correct.

## Solution
Run the migration SQL on the production database to add the `platform_id` column and create necessary indexes.

## Migration SQL File
Location: `backend/migration_platform_id_production.sql`

This SQL file:
1. ✅ Checks if `platform_id` column exists (safe to run multiple times)
2. ✅ Adds `platform_id VARCHAR(255)` column if missing (matches model definition)
3. ✅ Populates `platform_id` from existing `platform` values
4. ✅ Creates composite indexes for efficient hierarchical queries

## How to Run the Migration

Since `psql` is not installed and `gcloud sql databases execute-sql` doesn't exist, use one of these methods:

### Option 1: Cloud SQL Console (Recommended - Easiest)

1. Open Cloud SQL Console:
   - Go to: https://console.cloud.google.com/sql/instances/bot-db?project=survey-bot-detection
   
2. Access the database:
   - Click on the "Databases" tab
   - Select database: `bot_detection`
   
3. Execute SQL:
   - Click "Open Cloud Shell" button (top right) OR
   - Use the "Query" tab if available
   
4. In Cloud Shell (if using):
   ```bash
   gcloud sql connect bot-db --user=bot_user --database=bot_detection --project=survey-bot-detection
   ```
   Then in psql:
   ```sql
   \i backend/migration_platform_id_production.sql
   ```
   Or copy/paste the SQL content directly.

5. If using Query tab:
   - Copy the entire content from `backend/migration_platform_id_production.sql`
   - Paste into the query editor
   - Click "Run" to execute

### Option 2: Cloud Shell (Alternative)

1. Open Cloud Shell: https://shell.cloud.google.com/

2. Upload the SQL file:
   ```bash
   # Upload backend/migration_platform_id_production.sql to Cloud Shell
   ```

3. Connect to database:
   ```bash
   gcloud sql connect bot-db --user=bot_user --database=bot_detection --project=survey-bot-detection
   ```

4. Execute SQL:
   ```sql
   \i migration_platform_id_production.sql
   ```

### Option 3: Use PowerShell Script (Provides Instructions)

Run the helper script:
```powershell
.\run-production-migration-simple.ps1
```

This will:
- Generate the migration SQL file
- Provide step-by-step instructions
- Show you exactly where to run the SQL

## Verification

After running the migration, verify it worked:

1. **Check column exists:**
   ```sql
   SELECT column_name, data_type, character_maximum_length
   FROM information_schema.columns
   WHERE table_name = 'sessions' AND column_name = 'platform_id';
   ```
   Should return: `platform_id | character varying | 255`

2. **Check indexes:**
   ```sql
   SELECT indexname FROM pg_indexes 
   WHERE tablename = 'sessions' AND indexname LIKE '%platform%';
   ```
   Should return indexes:
   - `idx_survey_platform_respondent_session`
   - `idx_survey_platform`
   - `idx_survey_platform_respondent`
   - `idx_sessions_platform_id`

3. **Test API endpoints:**
   ```powershell
   .\test-endpoints-comprehensive.ps1
   ```
   
   Previously failing endpoints should now work:
   - `POST /api/v1/detection/sessions` - Create session
   - `GET /api/v1/dashboard/sessions` - List sessions
   - `GET /api/v1/reports/summary/{survey_id}` - Get survey summary
   - `GET /api/v1/surveys/{survey_id}` - Get survey details

## What Was Fixed

1. ✅ **Column Type Consistency**: Updated all migration SQL files to use `VARCHAR(255)` to match the model definition (was `VARCHAR(50)` in some files)

2. ✅ **Migration Scripts**: Created multiple migration scripts:
   - `backend/fix_platform_id_migration.py` - Python async migration (for local)
   - `backend/run_production_migration_api.py` - Cloud SQL Admin API approach
   - `backend/execute_migration_via_api.py` - REST API approach
   - `run-production-migration-simple.ps1` - PowerShell helper script

3. ✅ **SQL File**: Created `backend/migration_platform_id_production.sql` with correct syntax

## Notes

- The migration is **safe to run multiple times** - it checks if the column exists first
- The migration will **not delete or modify existing data** - it only adds the column and populates it
- All indexes use `IF NOT EXISTS` so they won't fail if already present
- The local database structure is correct and doesn't need changes

## Next Steps

1. Run the migration using one of the options above
2. Verify the migration completed successfully
3. Test the API endpoints to ensure they work
4. Update `DATABASE_MIGRATION_REQUIRED.md` to mark as completed
