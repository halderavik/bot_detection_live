-- Migration script to add platform_id column to sessions table
-- Run this directly on the production Cloud SQL database

-- Step 1: Check if column exists (optional - for safety)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'sessions' 
        AND column_name = 'platform_id'
    ) THEN
        -- Step 2: Add platform_id column
        ALTER TABLE sessions 
        ADD COLUMN platform_id VARCHAR(255);
        
        -- Step 3: Populate platform_id from existing platform values
        UPDATE sessions 
        SET platform_id = platform 
        WHERE platform IS NOT NULL AND platform_id IS NULL;
        
        -- Step 4: Create composite indexes for efficient hierarchical queries
        CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent_session 
        ON sessions (survey_id, platform_id, respondent_id, id);
        
        CREATE INDEX IF NOT EXISTS idx_survey_platform 
        ON sessions (survey_id, platform_id);
        
        CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent 
        ON sessions (survey_id, platform_id, respondent_id);
        
        -- Step 5: Create individual indexes
        CREATE INDEX IF NOT EXISTS idx_sessions_platform_id 
        ON sessions (platform_id);
        
        RAISE NOTICE 'Migration completed: platform_id column added and populated';
    ELSE
        RAISE NOTICE 'platform_id column already exists, skipping migration';
    END IF;
END $$;

