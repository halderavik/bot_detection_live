DO $$
BEGIN
    -- Check if column exists
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'sessions' 
        AND column_name = 'platform_id'
    ) THEN
        -- Add platform_id column (VARCHAR(255) to match model)
        ALTER TABLE sessions 
        ADD COLUMN platform_id VARCHAR(255);
        
        RAISE NOTICE 'platform_id column added successfully';
    ELSE
        RAISE NOTICE 'platform_id column already exists';
    END IF;
END $$;

-- Populate platform_id from existing platform values
UPDATE sessions 
SET platform_id = platform 
WHERE platform IS NOT NULL AND platform_id IS NULL;

-- Create composite indexes
CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent_session 
ON sessions (survey_id, platform_id, respondent_id, id);

CREATE INDEX IF NOT EXISTS idx_survey_platform 
ON sessions (survey_id, platform_id);

CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent 
ON sessions (survey_id, platform_id, respondent_id);

CREATE INDEX IF NOT EXISTS idx_sessions_platform_id 
ON sessions (platform_id);