-- Migration: Add Grid Analysis and Timing Analysis Tables
-- Date: 2026-02-11
-- Description: Creates grid_responses and timing_analysis tables for survey-specific detection

-- ============================================================================
-- GRID_RESPONSES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS grid_responses (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    
    -- Hierarchical fields (denormalized for efficient querying)
    survey_id VARCHAR(255),
    platform_id VARCHAR(255),
    respondent_id VARCHAR(255),
    session_id VARCHAR(36) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    
    -- Foreign keys
    question_id VARCHAR(36) NOT NULL REFERENCES survey_questions(id) ON DELETE CASCADE,
    
    -- Grid-specific fields
    row_id VARCHAR(255),  -- Row identifier within the grid question
    column_id VARCHAR(255),  -- Column identifier within the grid question
    response_value TEXT,  -- The actual response value
    response_time_ms INTEGER,  -- Time to respond in milliseconds
    
    -- Analysis fields
    is_straight_lined BOOLEAN DEFAULT FALSE,  -- Whether this response is part of a straight-lining pattern
    pattern_type VARCHAR(50),  -- Pattern detected: 'diagonal', 'reverse_diagonal', 'zigzag', 'straight_line', etc.
    variance_score DOUBLE PRECISION,  -- Variance score (0-1 scale)
    satisficing_score DOUBLE PRECISION,  -- Satisficing behavior score (0-1 scale)
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    analyzed_at TIMESTAMP WITH TIME ZONE
);

-- ============================================================================
-- TIMING_ANALYSIS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS timing_analysis (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    
    -- Hierarchical fields (denormalized for efficient querying)
    survey_id VARCHAR(255),
    platform_id VARCHAR(255),
    respondent_id VARCHAR(255),
    session_id VARCHAR(36) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    
    -- Foreign keys
    question_id VARCHAR(36) NOT NULL REFERENCES survey_questions(id) ON DELETE CASCADE,
    
    -- Timing fields
    question_time_ms INTEGER NOT NULL,  -- Time taken to answer this question
    is_speeder BOOLEAN DEFAULT FALSE,  -- Response time < threshold (too fast)
    is_flatliner BOOLEAN DEFAULT FALSE,  -- Response time > threshold (too slow)
    threshold_used DOUBLE PRECISION,  -- Threshold used for detection (in ms)
    
    -- Anomaly fields
    anomaly_score DOUBLE PRECISION,  -- Statistical anomaly score (z-score)
    anomaly_type VARCHAR(50),  -- Type of anomaly: 'speeder', 'flatliner', 'outlier', etc.
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    analyzed_at TIMESTAMP WITH TIME ZONE
);

-- ============================================================================
-- COMPOSITE INDEXES FOR GRID_RESPONSES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_grid_survey ON grid_responses(survey_id);
CREATE INDEX IF NOT EXISTS idx_grid_survey_platform ON grid_responses(survey_id, platform_id);
CREATE INDEX IF NOT EXISTS idx_grid_survey_platform_respondent ON grid_responses(survey_id, platform_id, respondent_id);
CREATE INDEX IF NOT EXISTS idx_grid_survey_platform_respondent_session ON grid_responses(survey_id, platform_id, respondent_id, session_id);

-- Additional indexes for grid_responses
CREATE INDEX IF NOT EXISTS idx_grid_question_id ON grid_responses(question_id);
CREATE INDEX IF NOT EXISTS idx_grid_session_id ON grid_responses(session_id);
CREATE INDEX IF NOT EXISTS idx_grid_straight_lined ON grid_responses(is_straight_lined) WHERE is_straight_lined = TRUE;
CREATE INDEX IF NOT EXISTS idx_grid_pattern_type ON grid_responses(pattern_type);

-- ============================================================================
-- COMPOSITE INDEXES FOR TIMING_ANALYSIS
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_timing_survey ON timing_analysis(survey_id);
CREATE INDEX IF NOT EXISTS idx_timing_survey_platform ON timing_analysis(survey_id, platform_id);
CREATE INDEX IF NOT EXISTS idx_timing_survey_platform_respondent ON timing_analysis(survey_id, platform_id, respondent_id);
CREATE INDEX IF NOT EXISTS idx_timing_survey_platform_respondent_session ON timing_analysis(survey_id, platform_id, respondent_id, session_id);

-- Additional indexes for timing_analysis
CREATE INDEX IF NOT EXISTS idx_timing_question_id ON timing_analysis(question_id);
CREATE INDEX IF NOT EXISTS idx_timing_session_id ON timing_analysis(session_id);
CREATE INDEX IF NOT EXISTS idx_timing_speeder ON timing_analysis(is_speeder) WHERE is_speeder = TRUE;
CREATE INDEX IF NOT EXISTS idx_timing_flatliner ON timing_analysis(is_flatliner) WHERE is_flatliner = TRUE;
CREATE INDEX IF NOT EXISTS idx_timing_question_time ON timing_analysis(question_time_ms);

-- ============================================================================
-- DATE-FILTERED INDEXES (for recent data queries)
-- ============================================================================
-- Note: PostgreSQL partial indexes with date conditions
CREATE INDEX IF NOT EXISTS idx_grid_created_at ON grid_responses(created_at) 
    WHERE created_at >= NOW() - INTERVAL '30 days';
CREATE INDEX IF NOT EXISTS idx_timing_created_at ON timing_analysis(created_at) 
    WHERE created_at >= NOW() - INTERVAL '30 days';

-- Composite date-filtered indexes for hierarchical queries
CREATE INDEX IF NOT EXISTS idx_grid_survey_created ON grid_responses(survey_id, created_at) 
    WHERE created_at >= NOW() - INTERVAL '30 days';
CREATE INDEX IF NOT EXISTS idx_grid_survey_platform_created ON grid_responses(survey_id, platform_id, created_at) 
    WHERE created_at >= NOW() - INTERVAL '30 days';
CREATE INDEX IF NOT EXISTS idx_timing_survey_created ON timing_analysis(survey_id, created_at) 
    WHERE created_at >= NOW() - INTERVAL '30 days';
CREATE INDEX IF NOT EXISTS idx_timing_survey_platform_created ON timing_analysis(survey_id, platform_id, created_at) 
    WHERE created_at >= NOW() - INTERVAL '30 days';

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================
COMMENT ON TABLE grid_responses IS 'Stores grid/matrix question responses with analysis results (straight-lining, patterns, variance, satisficing)';
COMMENT ON TABLE timing_analysis IS 'Stores per-question timing analysis with speeder/flatliner detection and anomaly scoring';
COMMENT ON COLUMN grid_responses.survey_id IS 'Survey identifier (denormalized from sessions for efficient hierarchical queries)';
COMMENT ON COLUMN grid_responses.platform_id IS 'Platform identifier (denormalized from sessions for efficient hierarchical queries)';
COMMENT ON COLUMN grid_responses.respondent_id IS 'Respondent identifier (denormalized from sessions for efficient hierarchical queries)';
COMMENT ON COLUMN grid_responses.is_straight_lined IS 'True if this response is part of a straight-lining pattern (>80% identical values)';
COMMENT ON COLUMN grid_responses.pattern_type IS 'Detected pattern: diagonal, reverse_diagonal, zigzag, straight_line, or null';
COMMENT ON COLUMN grid_responses.variance_score IS 'Response variance score normalized to 0-1 scale (0 = no variance, 1 = high variance)';
COMMENT ON COLUMN grid_responses.satisficing_score IS 'Satisficing behavior score (0-1 scale, higher = more satisficing behavior)';
COMMENT ON COLUMN timing_analysis.survey_id IS 'Survey identifier (denormalized from sessions for efficient hierarchical queries)';
COMMENT ON COLUMN timing_analysis.platform_id IS 'Platform identifier (denormalized from sessions for efficient hierarchical queries)';
COMMENT ON COLUMN timing_analysis.respondent_id IS 'Respondent identifier (denormalized from sessions for efficient hierarchical queries)';
COMMENT ON COLUMN timing_analysis.is_speeder IS 'True if response time < 2000ms (too fast, potential bot behavior)';
COMMENT ON COLUMN timing_analysis.is_flatliner IS 'True if response time > 300000ms (5 minutes, too slow, potential disengagement)';
COMMENT ON COLUMN timing_analysis.anomaly_score IS 'Statistical z-score for timing anomaly detection (>2.5 = outlier)';
