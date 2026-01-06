-- Add platform_id column to sessions table if it doesn't exist
-- This is a safe migration that checks if the column exists first

DO $$
BEGIN
    -- Check if platform_id column exists
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'sessions' 
        AND column_name = 'platform_id'
    ) THEN
        -- Add the column
        ALTER TABLE sessions ADD COLUMN platform_id VARCHAR(255);
        
        -- Populate platform_id from existing platform values
        UPDATE sessions 
        SET platform_id = platform 
        WHERE platform IS NOT NULL AND platform_id IS NULL;
        
        RAISE NOTICE 'platform_id column added and populated successfully';
    ELSE
        RAISE NOTICE 'platform_id column already exists';
    END IF;
END $$;
