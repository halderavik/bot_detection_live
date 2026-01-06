-- Simple platform_id migration without DO blocks
-- This version can be executed statement by statement if needed

-- Step 1: Check if column exists and add it if missing
-- (Run this first - it will fail if column already exists, which is fine)
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS platform_id VARCHAR(255);

-- Step 2: Populate platform_id from existing platform values
UPDATE sessions 
SET platform_id = platform 
WHERE platform IS NOT NULL AND platform_id IS NULL;

-- Step 3: Create composite indexes
CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent_session 
ON sessions (survey_id, platform_id, respondent_id, id);

CREATE INDEX IF NOT EXISTS idx_survey_platform 
ON sessions (survey_id, platform_id);

CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent 
ON sessions (survey_id, platform_id, respondent_id);

CREATE INDEX IF NOT EXISTS idx_sessions_platform_id 
ON sessions (platform_id);
