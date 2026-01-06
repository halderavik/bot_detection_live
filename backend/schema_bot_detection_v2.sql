-- Complete Schema for bot_detection_v2 Database
-- This schema includes all tables, columns, indexes, and constraints
-- for the hierarchical API V2 with platform_id support

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- SESSIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    
    -- Session metadata
    user_agent TEXT,
    ip_address VARCHAR(45),  -- IPv6 compatible
    referrer TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Session status
    is_active BOOLEAN DEFAULT TRUE,
    is_completed BOOLEAN DEFAULT FALSE,
    
    -- Integration metadata (hierarchical structure)
    survey_id VARCHAR(255),
    respondent_id VARCHAR(255),
    platform VARCHAR(50),  -- Legacy field for backward compatibility
    platform_id VARCHAR(255)  -- Platform identifier for hierarchical structure (V2)
);

-- Indexes for sessions table
CREATE INDEX IF NOT EXISTS idx_sessions_survey_id ON sessions(survey_id);
CREATE INDEX IF NOT EXISTS idx_sessions_respondent_id ON sessions(respondent_id);
CREATE INDEX IF NOT EXISTS idx_sessions_platform_id ON sessions(platform_id);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);

-- Composite indexes for efficient hierarchical queries (V2)
CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent_session 
    ON sessions (survey_id, platform_id, respondent_id, id);
CREATE INDEX IF NOT EXISTS idx_survey_platform 
    ON sessions (survey_id, platform_id);
CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent 
    ON sessions (survey_id, platform_id, respondent_id);

-- ============================================================================
-- BEHAVIOR_DATA TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS behavior_data (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    session_id VARCHAR(36) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    
    -- Event metadata
    event_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Event data (stored as JSONB for flexibility and querying)
    event_data JSONB NOT NULL,
    
    -- Element information
    element_id VARCHAR(255),
    element_type VARCHAR(50),
    element_class VARCHAR(255),
    
    -- Page context
    page_url TEXT,
    page_title TEXT,
    
    -- Device information
    screen_width INTEGER,
    screen_height INTEGER,
    viewport_width INTEGER,
    viewport_height INTEGER,
    
    -- Performance metrics
    load_time DOUBLE PRECISION,
    response_time DOUBLE PRECISION
);

-- Indexes for behavior_data table
CREATE INDEX IF NOT EXISTS idx_behavior_data_session_id ON behavior_data(session_id);
CREATE INDEX IF NOT EXISTS idx_behavior_data_event_type ON behavior_data(event_type);
CREATE INDEX IF NOT EXISTS idx_behavior_data_timestamp ON behavior_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_behavior_data_created_at ON behavior_data(created_at);

-- ============================================================================
-- DETECTION_RESULTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS detection_results (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    session_id VARCHAR(36) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    
    -- Detection results
    is_bot BOOLEAN NOT NULL,
    confidence_score DOUBLE PRECISION NOT NULL,  -- 0.0 to 1.0
    risk_level VARCHAR(20) NOT NULL,  -- 'low', 'medium', 'high', 'critical'
    
    -- Detection methods used
    detection_methods JSONB NOT NULL,  -- List of methods used
    method_scores JSONB NOT NULL,  -- Individual method scores
    
    -- Processing metrics
    processing_time_ms DOUBLE PRECISION NOT NULL,
    event_count INTEGER NOT NULL,
    
    -- Analysis details
    analysis_summary TEXT,
    flagged_patterns JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for detection_results table
CREATE INDEX IF NOT EXISTS idx_detection_results_session_id ON detection_results(session_id);
CREATE INDEX IF NOT EXISTS idx_detection_results_is_bot ON detection_results(is_bot);
CREATE INDEX IF NOT EXISTS idx_detection_results_confidence_score ON detection_results(confidence_score);
CREATE INDEX IF NOT EXISTS idx_detection_results_risk_level ON detection_results(risk_level);
CREATE INDEX IF NOT EXISTS idx_detection_results_created_at ON detection_results(created_at);

-- ============================================================================
-- SURVEY_QUESTIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS survey_questions (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    session_id VARCHAR(36) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    
    -- Question metadata
    question_text TEXT NOT NULL,
    question_type VARCHAR(50),  -- 'open_ended', 'multiple_choice', etc.
    element_id VARCHAR(255),  -- HTML element ID
    element_type VARCHAR(50),  -- 'textarea', 'input', etc.
    page_url TEXT,
    page_title TEXT,
    
    -- Timing
    asked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for survey_questions table
CREATE INDEX IF NOT EXISTS idx_survey_questions_session_id ON survey_questions(session_id);
CREATE INDEX IF NOT EXISTS idx_survey_questions_question_type ON survey_questions(question_type);
CREATE INDEX IF NOT EXISTS idx_survey_questions_created_at ON survey_questions(created_at);

-- ============================================================================
-- SURVEY_RESPONSES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS survey_responses (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    
    -- Foreign keys
    question_id VARCHAR(36) NOT NULL REFERENCES survey_questions(id) ON DELETE CASCADE,
    session_id VARCHAR(36) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    
    -- Response data
    response_text TEXT NOT NULL,
    response_time_ms INTEGER,  -- Time to respond in milliseconds
    
    -- Text analysis results (stored as JSONB)
    text_analysis_result JSONB,
    
    -- Quality metrics
    quality_score DOUBLE PRECISION,  -- 0-100 quality score
    is_flagged BOOLEAN DEFAULT FALSE,
    flag_reasons JSONB,  -- List of flag reasons
    
    -- Analysis details
    gibberish_score DOUBLE PRECISION,  -- 0-1 gibberish probability
    copy_paste_score DOUBLE PRECISION,  -- 0-1 copy-paste probability
    relevance_score DOUBLE PRECISION,  -- 0-1 relevance score
    generic_score DOUBLE PRECISION,  -- 0-1 generic answer probability
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    analyzed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for survey_responses table
CREATE INDEX IF NOT EXISTS idx_survey_responses_question_id ON survey_responses(question_id);
CREATE INDEX IF NOT EXISTS idx_survey_responses_session_id ON survey_responses(session_id);
CREATE INDEX IF NOT EXISTS idx_survey_responses_quality_score ON survey_responses(quality_score);
CREATE INDEX IF NOT EXISTS idx_survey_responses_is_flagged ON survey_responses(is_flagged);
CREATE INDEX IF NOT EXISTS idx_survey_responses_created_at ON survey_responses(created_at);

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE sessions IS 'User sessions for bot detection tracking with hierarchical structure (Survey -> Platform -> Respondent -> Session)';
COMMENT ON COLUMN sessions.platform_id IS 'Platform identifier for hierarchical API V2 (e.g., qualtrics, decipher)';
COMMENT ON TABLE behavior_data IS 'User behavior events captured during sessions';
COMMENT ON TABLE detection_results IS 'Bot detection analysis results with confidence scores and risk levels';
COMMENT ON TABLE survey_questions IS 'Survey question metadata for text quality analysis';
COMMENT ON TABLE survey_responses IS 'Survey responses with OpenAI-powered text quality analysis results';

-- ============================================================================
-- VERIFICATION QUERIES (for manual checking)
-- ============================================================================
-- Run these queries to verify the schema:
-- 
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'sessions' ORDER BY column_name;
-- SELECT indexname FROM pg_indexes WHERE tablename = 'sessions' AND schemaname = 'public' ORDER BY indexname;
