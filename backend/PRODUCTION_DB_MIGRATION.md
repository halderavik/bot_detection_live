# Production Database Migration Guide

## Issue
Production database is missing the `platform_id` column in the `sessions` table, causing session creation to fail with HTTP 500 errors.

## Solution
Run the following SQL in the production Cloud SQL database to add the missing column.

## Method 1: Cloud SQL Console (Easiest)

1. Go to [Google Cloud Console - Cloud SQL](https://console.cloud.google.com/sql/instances)
2. Select instance: `bot-db`
3. Click on "Databases" tab
4. Select database: `bot_detection`
5. Click "Open Cloud Shell" or use the Query interface
6. Copy and paste the SQL below:

```sql
-- Add platform_id column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'sessions' 
        AND column_name = 'platform_id'
    ) THEN
        ALTER TABLE sessions ADD COLUMN platform_id VARCHAR(50);
        
        -- Populate from existing platform values
        UPDATE sessions 
        SET platform_id = platform 
        WHERE platform IS NOT NULL AND platform_id IS NULL;
        
        RAISE NOTICE 'platform_id column added successfully';
    ELSE
        RAISE NOTICE 'platform_id column already exists';
    END IF;
END $$;
```

7. Execute the SQL
8. Verify success message

## Method 2: Using gcloud CLI

If you have Cloud SQL Proxy running locally:

```powershell
# Connect to database
gcloud sql connect bot-db --user=postgres --database=bot_detection --project=survey-bot-detection

# Then in psql, run the SQL above
```

## Method 3: Using Cloud SQL Proxy + psql

1. Start Cloud SQL Proxy:
```powershell
cloud_sql_proxy -instances=survey-bot-detection:northamerica-northeast2:bot-db=tcp:5432
```

2. In another terminal, connect with psql:
```powershell
psql -h localhost -U postgres -d bot_detection
```

3. Run the SQL migration

## Verification

After running the migration, test the production API:

```powershell
cd backend
python test_production_text_analysis.py
```

The tests should now pass with proper text analysis results.

## Current Status

- ✅ Local database: Has `platform_id` column
- ⚠️ Production database: Needs `platform_id` column (run migration above)
