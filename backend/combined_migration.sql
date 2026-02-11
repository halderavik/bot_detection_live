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



-- ==========================================
-- Fraud Detection Migration
-- ==========================================

-- Migration: Add Fraud Detection Tables
-- Date: 2026-01-06
-- Description: Creates fraud_indicators table and updates existing tables for fraud detection

-- Create fraud_indicators table
CREATE TABLE IF NOT EXISTS fraud_indicators (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    
    -- IP Analysis
    ip_address VARCHAR(45),
    ip_usage_count INTEGER DEFAULT 0,
    ip_sessions_today INTEGER DEFAULT 0,
    ip_risk_score DECIMAL(3,2),
    ip_country_code VARCHAR(2),
    ip_city VARCHAR(100),
    
    -- Device Fingerprint
    device_fingerprint TEXT,
    fingerprint_usage_count INTEGER DEFAULT 0,
    fingerprint_risk_score DECIMAL(3,2),
    
    -- Response Pattern
    response_similarity_score DECIMAL(3,2),
    duplicate_response_count INTEGER DEFAULT 0,
    
    -- Geolocation
    geolocation_consistent BOOLEAN DEFAULT TRUE,
    geolocation_risk_score DECIMAL(3,2),
    
    -- Velocity
    responses_per_hour DECIMAL(5,2),
    velocity_risk_score DECIMAL(3,2),
    
    -- Overall
    overall_fraud_score DECIMAL(3,2),
    is_duplicate BOOLEAN DEFAULT FALSE,
    fraud_confidence DECIMAL(3,2),
    
    -- Metadata
    flag_reasons JSONB,
    analysis_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Update sessions table: add device_fingerprint column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'sessions' AND column_name = 'device_fingerprint'
    ) THEN
        ALTER TABLE sessions ADD COLUMN device_fingerprint TEXT;
    END IF;
END $$;

-- Create index for device_fingerprint on sessions
CREATE INDEX IF NOT EXISTS idx_session_fingerprint ON sessions(device_fingerprint);

-- Add hierarchical fields to fraud_indicators if they don't exist (for existing tables)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'fraud_indicators' AND column_name = 'survey_id'
    ) THEN
        ALTER TABLE fraud_indicators ADD COLUMN survey_id VARCHAR(255);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'fraud_indicators' AND column_name = 'platform_id'
    ) THEN
        ALTER TABLE fraud_indicators ADD COLUMN platform_id VARCHAR(255);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'fraud_indicators' AND column_name = 'respondent_id'
    ) THEN
        ALTER TABLE fraud_indicators ADD COLUMN respondent_id VARCHAR(255);
    END IF;
END $$;

-- Create indexes for fraud_indicators (after columns are ensured to exist)
CREATE INDEX IF NOT EXISTS idx_fraud_ip ON fraud_indicators(ip_address);
CREATE INDEX IF NOT EXISTS idx_fraud_fingerprint ON fraud_indicators(device_fingerprint);
CREATE INDEX IF NOT EXISTS idx_fraud_session ON fraud_indicators(session_id);
CREATE INDEX IF NOT EXISTS idx_fraud_created_at ON fraud_indicators(created_at);

-- Hierarchical indexes for efficient aggregation queries
CREATE INDEX IF NOT EXISTS idx_fraud_survey ON fraud_indicators(survey_id);
CREATE INDEX IF NOT EXISTS idx_fraud_survey_platform ON fraud_indicators(survey_id, platform_id);
CREATE INDEX IF NOT EXISTS idx_fraud_survey_platform_respondent ON fraud_indicators(survey_id, platform_id, respondent_id);
CREATE INDEX IF NOT EXISTS idx_fraud_survey_platform_respondent_session ON fraud_indicators(survey_id, platform_id, respondent_id, session_id);

-- Composite index for date-filtered hierarchical queries
CREATE INDEX IF NOT EXISTS idx_fraud_survey_created ON fraud_indicators(survey_id, created_at);
CREATE INDEX IF NOT EXISTS idx_fraud_survey_platform_created ON fraud_indicators(survey_id, platform_id, created_at);
CREATE INDEX IF NOT EXISTS idx_fraud_survey_platform_respondent_created ON fraud_indicators(survey_id, platform_id, respondent_id, created_at);

-- Indexes for fraud analysis queries
CREATE INDEX IF NOT EXISTS idx_fraud_duplicate ON fraud_indicators(is_duplicate) WHERE is_duplicate = TRUE;
CREATE INDEX IF NOT EXISTS idx_fraud_high_risk ON fraud_indicators(survey_id, overall_fraud_score) WHERE overall_fraud_score >= 0.7;

-- Update detection_results table: add fraud_score and fraud_indicators columns
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'detection_results' AND column_name = 'fraud_score'
    ) THEN
        ALTER TABLE detection_results ADD COLUMN fraud_score DECIMAL(3,2);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'detection_results' AND column_name = 'fraud_indicators'
    ) THEN
        ALTER TABLE detection_results ADD COLUMN fraud_indicators JSONB;
    END IF;
END $$;

-- Note: Hierarchical fields (survey_id, platform_id, respondent_id) will be populated
-- automatically by the application layer when creating new fraud_indicators records.
-- If you need to backfill existing records, run a separate backfill script.

-- Comments for documentation
COMMENT ON TABLE fraud_indicators IS 'Stores fraud detection analysis results for sessions with hierarchical fields for efficient aggregation';
COMMENT ON COLUMN fraud_indicators.survey_id IS 'Survey identifier (denormalized from sessions for efficient hierarchical queries)';
COMMENT ON COLUMN fraud_indicators.platform_id IS 'Platform identifier (denormalized from sessions for efficient hierarchical queries)';
COMMENT ON COLUMN fraud_indicators.respondent_id IS 'Respondent identifier (denormalized from sessions for efficient hierarchical queries)';
COMMENT ON COLUMN fraud_indicators.overall_fraud_score IS 'Overall fraud score (0.0-1.0) combining all fraud detection methods';
COMMENT ON COLUMN sessions.device_fingerprint IS 'SHA256 hash of device characteristics for fingerprinting';
COMMENT ON COLUMN detection_results.fraud_score IS 'Fraud detection score integrated into composite bot detection';

