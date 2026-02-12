# Bot Detection API V2 - Hierarchical Structure Documentation

## Implementation Status ✅ **COMPLETED & READY TO DEPLOY**

**All endpoints documented below are fully implemented and tested:**
- ✅ **Backend Implementation**: All hierarchical endpoints implemented ✅ **COMPLETED**
- ✅ **Database Schema**: Hierarchical indexes and fraud_indicators table designed ✅ **COMPLETED**
- ✅ **Frontend Integration**: All components implemented and functional ✅ **COMPLETED**
- ✅ **Fraud Detection**: Complete fraud detection system with hierarchical endpoints ✅ **COMPLETED**
- ✅ **Unit Tests**: Comprehensive test coverage with 100% passing rate ✅ **COMPLETED**
- ✅ **Migration**: Database migration script created and ready ✅ **COMPLETED**
- ✅ **Production Deployment**: Dashboard redeployed February 2026 with fraud/grid/timing in API Playground and Report Builder

## Overview

The Bot Detection API V2 introduces a hierarchical data structure that organizes data by **Survey → Platform → Respondent → Session**. This structure enables efficient navigation and aggregation of bot detection data at different levels.

### Hierarchy Structure

```
Survey ID
  └── Platform ID
      └── Respondent ID
          └── Session ID
```

### Key Features

- **Hierarchical Navigation**: Navigate through surveys, platforms, respondents, and sessions
- **Aggregated Metrics**: Get aggregated statistics at each level
- **Backward Compatibility**: All V1 endpoints remain unchanged
- **Efficient Queries**: Composite indexes for fast hierarchical queries

---

## Base URL

**Production:**
```
https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1
```

**Frontend Dashboard (Production):**
```
https://storage.googleapis.com/bot-detection-frontend-20251208/index.html
```

**Frontend Deployment Status:** ✅ **VERIFIED** (February 2026)
- ✅ Frontend successfully deployed to Cloud Storage
- ✅ All hierarchical API endpoints verified and returning data from Cloud SQL
- ✅ Data flow verified: Cloud SQL → Backend API → Frontend Dashboard
- ✅ API Playground: Endpoint templates for fraud (flat + hierarchical), grid analysis, and timing analysis
- ✅ Report Builder: Fraud & Duplicate, Grid Analysis, and Timing Analysis in summary and detailed reports (including CSV export); click respondent ID to open full-detail popup; CSV includes every analysis per respondent (text responses of interest, fraud/grid/timing explanations)

**Local Development:**
```
http://localhost:8000/api/v1
```

---

## Survey Level Endpoints

### List All Surveys

```http
GET /surveys
```

**Description:** Get a list of all surveys with basic aggregated statistics.

**Query Parameters:**
- `limit` (integer, optional): Maximum number of surveys to return (default: 100, max: 1000)
- `offset` (integer, optional): Offset for pagination (default: 0)

**Response:**
```json
{
  "surveys": [
    {
      "survey_id": "SV_1234567890abcdef",
      "respondent_count": 1250,
      "session_count": 2500,
      "bot_count": 300,
      "human_count": 2200,
      "bot_rate": 12.0,
      "first_session": "2025-01-01T00:00:00Z",
      "last_session": "2025-01-15T23:59:59Z"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

**Example:**
```bash
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys?limit=50"
```

### Get Survey Details

```http
GET /surveys/{survey_id}
```

**Description:** Get detailed aggregated metrics for a specific survey.

**Path Parameters:**
- `survey_id` (string, required): Survey identifier

**Query Parameters:**
- `date_from` (string, optional): Start date filter (ISO format)
- `date_to` (string, optional): End date filter (ISO format)

**Response:**
```json
{
  "survey_id": "SV_1234567890abcdef",
  "total_sessions": 2500,
  "total_respondents": 1250,
  "total_platforms": 2,
  "platform_distribution": {
    "qualtrics": 1500,
    "decipher": 1000
  },
  "bot_detection": {
    "total_detections": 2500,
    "bot_count": 300,
    "human_count": 2200,
    "bot_rate": 12.0,
    "avg_confidence": 0.785
  },
  "risk_distribution": {
    "LOW": 2200,
    "MEDIUM": 200,
    "HIGH": 100
  },
  "events": {
    "total_events": 125000,
    "avg_events_per_session": 50.0
  },
  "text_quality": {
    "total_responses": 5000,
    "avg_quality_score": 72.5,
    "flagged_count": 250,
    "flagged_percentage": 5.0
  },
  "date_range": {
    "first_session": "2025-01-01T00:00:00Z",
    "last_session": "2025-01-15T23:59:59Z"
  }
}
```

**Example:**
```bash
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/SV_1234567890abcdef"
```

### Get Survey Summary

```http
GET /surveys/{survey_id}/summary
```

**Description:** Get a concise summary of key metrics for a survey.

**Response:**
```json
{
  "survey_id": "SV_1234567890abcdef",
  "summary": {
    "total_respondents": 1250,
    "total_sessions": 2500,
    "total_platforms": 2,
    "bot_rate": 12.0,
    "avg_confidence": 0.785,
    "avg_quality_score": 72.5,
    "flagged_percentage": 5.0
  },
  "platform_distribution": {
    "qualtrics": 1500,
    "decipher": 1000
  },
  "risk_distribution": {
    "LOW": 2200,
    "MEDIUM": 200,
    "HIGH": 100
  }
}
```

---

## Platform Level Endpoints

### List Platforms for a Survey

```http
GET /surveys/{survey_id}/platforms
```

**Description:** Get a list of all platforms used in a survey.

**Response:**
```json
{
  "survey_id": "SV_1234567890abcdef",
  "platforms": [
    {
      "platform_id": "qualtrics",
      "respondent_count": 750,
      "session_count": 1500
    },
    {
      "platform_id": "decipher",
      "respondent_count": 500,
      "session_count": 1000
    }
  ],
  "total": 2
}
```

### Get Platform Details

```http
GET /surveys/{survey_id}/platforms/{platform_id}
```

**Description:** Get detailed aggregated metrics for a platform within a survey.

**Path Parameters:**
- `survey_id` (string, required): Survey identifier
- `platform_id` (string, required): Platform identifier

**Query Parameters:**
- `date_from` (string, optional): Start date filter (ISO format)
- `date_to` (string, optional): End date filter (ISO format)

**Response:**
```json
{
  "survey_id": "SV_1234567890abcdef",
  "platform_id": "qualtrics",
  "total_sessions": 1500,
  "total_respondents": 750,
  "bot_detection": {
    "total_detections": 1500,
    "bot_count": 180,
    "human_count": 1320,
    "bot_rate": 12.0,
    "avg_confidence": 0.790
  },
  "events": {
    "total_events": 75000,
    "avg_events_per_session": 50.0
  },
  "text_quality": {
    "total_responses": 3000,
    "avg_quality_score": 73.2,
    "flagged_count": 150,
    "flagged_percentage": 5.0
  }
}
```

### Get Platform Summary

```http
GET /surveys/{survey_id}/platforms/{platform_id}/summary
```

**Description:** Get a concise summary of key metrics for a platform.

**Response:**
```json
{
  "survey_id": "SV_1234567890abcdef",
  "platform_id": "qualtrics",
  "summary": {
    "total_respondents": 750,
    "total_sessions": 1500,
    "bot_rate": 12.0,
    "avg_confidence": 0.790,
    "avg_quality_score": 73.2,
    "flagged_percentage": 5.0
  }
}
```

---

## Respondent Level Endpoints

### List Respondents for a Platform

```http
GET /surveys/{survey_id}/platforms/{platform_id}/respondents
```

**Description:** Get a list of all respondents for a platform.

**Query Parameters:**
- `limit` (integer, optional): Maximum number of respondents to return (default: 100, max: 1000)
- `offset` (integer, optional): Offset for pagination (default: 0)

**Response:**
```json
{
  "survey_id": "SV_1234567890abcdef",
  "platform_id": "qualtrics",
  "respondents": [
    {
      "respondent_id": "RSP_1234567890abcdef",
      "session_count": 2,
      "bot_count": 0,
      "human_count": 2,
      "first_session": "2025-01-01T00:00:00Z",
      "last_session": "2025-01-01T01:00:00Z"
    }
  ],
  "total": 750,
  "limit": 100,
  "offset": 0
}
```

### Get Respondent Details

```http
GET /surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}
```

**Description:** Get detailed aggregated metrics for a respondent across all their sessions.

**Path Parameters:**
- `survey_id` (string, required): Survey identifier
- `platform_id` (string, required): Platform identifier
- `respondent_id` (string, required): Respondent identifier

**Query Parameters:**
- `date_from` (string, optional): Start date filter (ISO format)
- `date_to` (string, optional): End date filter (ISO format)

**Response:**
```json
{
  "survey_id": "SV_1234567890abcdef",
  "platform_id": "qualtrics",
  "respondent_id": "RSP_1234567890abcdef",
  "total_sessions": 2,
  "sessions": [
    {
      "session_id": "e41c423d-cdfb-4228-bd25-3fee8459e591",
      "created_at": "2025-01-01T00:00:00Z",
      "event_count": 150,
      "latest_detection": {
        "is_bot": false,
        "confidence_score": 0.85,
        "risk_level": "LOW"
      }
    }
  ],
  "bot_detection": {
    "total_detections": 2,
    "bot_count": 0,
    "human_count": 2,
    "bot_rate": 0.0,
    "avg_confidence": 0.85,
    "max_confidence": 0.90,
    "min_confidence": 0.80,
    "overall_risk": "LOW"
  },
  "text_quality": {
    "total_responses": 5,
    "avg_quality_score": 75.5,
    "flagged_count": 0,
    "flagged_percentage": 0.0
  },
  "session_timeline": [
    {
      "session_id": "e41c423d-cdfb-4228-bd25-3fee8459e591",
      "created_at": "2025-01-01T00:00:00Z",
      "is_active": false,
      "is_completed": true
    }
  ]
}
```

### Get Respondent Summary

```http
GET /surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/summary
```

**Description:** Get a concise summary of key metrics for a respondent.

**Response:**
```json
{
  "survey_id": "SV_1234567890abcdef",
  "platform_id": "qualtrics",
  "respondent_id": "RSP_1234567890abcdef",
  "summary": {
    "total_sessions": 2,
    "bot_rate": 0.0,
    "avg_confidence": 0.85,
    "overall_risk": "LOW",
    "avg_quality_score": 75.5,
    "flagged_percentage": 0.0
  },
  "session_timeline": [
    {
      "session_id": "e41c423d-cdfb-4228-bd25-3fee8459e591",
      "created_at": "2025-01-01T00:00:00Z",
      "is_active": false,
      "is_completed": true
    }
  ]
}
```

### List Sessions for a Respondent

```http
GET /surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions
```

**Description:** Get all sessions for a specific respondent.

**Query Parameters:**
- `limit` (integer, optional): Maximum number of sessions to return (default: 100, max: 1000)
- `offset` (integer, optional): Offset for pagination (default: 0)

**Response:**
```json
{
  "survey_id": "SV_1234567890abcdef",
  "platform_id": "qualtrics",
  "respondent_id": "RSP_1234567890abcdef",
  "sessions": [
    {
      "session_id": "e41c423d-cdfb-4228-bd25-3fee8459e591",
      "created_at": "2025-01-01T00:00:00Z",
      "event_count": 150,
      "latest_detection": {
        "is_bot": false,
        "confidence_score": 0.85,
        "risk_level": "LOW"
      }
    }
  ],
  "total": 2,
  "limit": 100,
  "offset": 0
}
```

---

## Session Level Endpoints (Hierarchical Path)

### Get Session by Hierarchy

```http
GET /surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}
```

**Description:** Get session details via hierarchical path. This endpoint verifies that the session belongs to the specified hierarchy.

**Path Parameters:**
- `survey_id` (string, required): Survey identifier
- `platform_id` (string, required): Platform identifier
- `respondent_id` (string, required): Respondent identifier
- `session_id` (string, required): Session identifier

**Response:**
```json
{
  "survey_id": "SV_1234567890abcdef",
  "platform_id": "qualtrics",
  "respondent_id": "RSP_1234567890abcdef",
  "session_id": "e41c423d-cdfb-4228-bd25-3fee8459e591",
  "session": {
    "id": "e41c423d-cdfb-4228-bd25-3fee8459e591",
    "created_at": "2025-01-01T00:00:00Z",
    "is_active": false,
    "is_completed": true,
    "user_agent": "Mozilla/5.0...",
    "ip_address": "192.168.1.100",
    "event_count": 150
  },
  "latest_detection": {
    "is_bot": false,
    "confidence_score": 0.85,
    "risk_level": "LOW",
    "created_at": "2025-01-01T00:15:30Z"
  }
}
```

**Error Response (404):**
```json
{
  "detail": "Session not found in the specified hierarchy"
}
```

---

## Text Analysis (Hierarchical V2) ✅ **COMPLETED**

These endpoints provide **aggregated text-quality metrics** at each hierarchy level.

**Status**: ✅ **FULLY DEPLOYED** - All endpoints operational (deployed before fraud detection)

### Survey Text Analysis Summary

```http
GET /surveys/{survey_id}/text-analysis/summary
```

### Platform Text Analysis Summary

```http
GET /surveys/{survey_id}/platforms/{platform_id}/text-analysis/summary
```

### Respondent Text Analysis Summary

```http
GET /surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/text-analysis/summary
```

### Session Text Analysis (Hierarchical)

```http
GET /surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}/text-analysis
```

**Notes:**
- These hierarchical endpoints are ideal for dashboards and reporting (survey/platform/respondent rollups).
- You must have the correct hierarchy identifiers (`survey_id`, `platform_id`, `respondent_id`) for the session.

---

## Grid Analysis (Hierarchical V2) ✅ **DEPLOYED**

These endpoints provide **aggregated grid/matrix question analysis** at each hierarchy level, detecting straight-lining patterns, response patterns (diagonal, zigzag), variance scores, and satisficing behavior.

**Status**: ✅ **FULLY DEPLOYED** - All endpoints operational (February 2026)

### Survey Grid Analysis Summary

```http
GET /surveys/{survey_id}/grid-analysis/summary
```

**Query Parameters:**
- `date_from` (string, optional): Start date filter (ISO format)
- `date_to` (string, optional): End date filter (ISO format)

**Response:**
```json
{
  "survey_id": "SV_1234567890abcdef",
  "total_responses": 1000,
  "straight_lined_count": 150,
  "straight_lined_percentage": 15.0,
  "pattern_distribution": {
    "diagonal": 20,
    "reverse_diagonal": 10,
    "zigzag": 15,
    "straight_line": 150,
    "random": 805
  },
  "avg_variance_score": 0.65,
  "avg_satisficing_score": 0.45,
  "unique_questions": 25
}
```

### Platform Grid Analysis Summary

```http
GET /surveys/{survey_id}/platforms/{platform_id}/grid-analysis/summary
```

**Response:** Same structure as survey-level, but filtered by platform.

### Respondent Grid Analysis Summary

```http
GET /surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/grid-analysis/summary
```

**Response:** Same structure as survey-level, but aggregated for a single respondent.

### Session Grid Analysis (Hierarchical)

```http
GET /surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}/grid-analysis
```

**Response:** Detailed grid analysis for a specific session, including per-question breakdowns.

**Notes:**
- Grid analysis detects satisficing behavior in matrix/grid questions
- Straight-lining detection identifies identical responses across rows (>80% threshold)
- Pattern detection identifies systematic response patterns (diagonal, zigzag, etc.)
- Variance and satisficing scores help identify low-effort responses

---

## Timing Analysis (Hierarchical V2) ✅ **DEPLOYED**

These endpoints provide **aggregated timing analysis** at each hierarchy level, detecting speeders (too fast), flatliners (too slow), timing anomalies, and adaptive threshold violations.

**Status**: ✅ **FULLY DEPLOYED** - All endpoints operational (February 2026)

### Survey Timing Analysis Summary

```http
GET /surveys/{survey_id}/timing-analysis/summary
```

**Query Parameters:**
- `date_from` (string, optional): Start date filter (ISO format)
- `date_to` (string, optional): End date filter (ISO format)

**Response:**
```json
{
  "survey_id": "SV_1234567890abcdef",
  "total_analyses": 500,
  "speeders_count": 50,
  "speeders_percentage": 10.0,
  "flatliners_count": 15,
  "flatliners_percentage": 3.0,
  "anomalies_count": 25,
  "anomalies_percentage": 5.0,
  "avg_response_time_ms": 5000.0,
  "median_response_time_ms": 4500.0,
  "unique_questions": 20
}
```

### Platform Timing Analysis Summary

```http
GET /surveys/{survey_id}/platforms/{platform_id}/timing-analysis/summary
```

**Response:** Same structure as survey-level, but filtered by platform.

### Respondent Timing Analysis Summary

```http
GET /surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/timing-analysis/summary
```

**Response:** Same structure as survey-level, but aggregated for a single respondent.

### Session Timing Analysis (Hierarchical)

```http
GET /surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}/timing-analysis
```

**Response:** Detailed timing analysis for a specific session, including per-question timing breakdowns.

**Notes:**
- Speeder detection: Responses faster than threshold (< 2000ms default)
- Flatliner detection: Responses slower than threshold (> 300000ms default)
- Anomaly detection: Statistical outliers using z-score analysis (|z-score| > 2.0)
- Adaptive thresholds: Context-aware thresholds based on question complexity

---

## Fraud Detection (Hierarchical V2) ✅ **COMPLETED & READY TO DEPLOY**

These endpoints provide **aggregated fraud detection metrics** at each hierarchy level, including IP tracking, device fingerprinting, duplicate response detection, geolocation checks, and velocity analysis.

**Status**: ✅ **IMPLEMENTATION COMPLETE** - All endpoints implemented, tested, and ready for production deployment

### Survey Fraud Detection Summary

```http
GET /surveys/{survey_id}/fraud/summary
```

**Query Parameters:**
- `date_from` (string, optional): Start date filter (ISO format)
- `date_to` (string, optional): End date filter (ISO format)

**Response:**
```json
{
  "survey_id": "SV_1234567890abcdef",
  "total_sessions_analyzed": 2500,
  "total_sessions": 2500,
  "duplicate_sessions": 150,
  "high_risk_sessions": 200,
  "average_fraud_score": 0.425,
  "duplicate_rate": 6.0,
  "high_risk_rate": 8.0,
  "risk_distribution": {
    "LOW": 2100,
    "MEDIUM": 200,
    "HIGH": 150,
    "CRITICAL": 50
  },
  "fraud_methods": {
    "ip_high_risk": 120,
    "fingerprint_high_risk": 80,
    "duplicate_responses": 150,
    "geolocation_inconsistent": 30,
    "high_velocity": 45
  }
}
```

### Platform Fraud Detection Summary

```http
GET /surveys/{survey_id}/platforms/{platform_id}/fraud/summary
```

**Response:** Same structure as survey-level, but filtered by platform.

### Respondent Fraud Detection Summary

```http
GET /surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/fraud/summary
```

**Response:** Same structure as survey-level, but aggregated for a single respondent across all their sessions.

### Session Fraud Detection (Hierarchical)

```http
GET /surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}/fraud
```

**Response:**
```json
{
  "survey_id": "SV_1234567890abcdef",
  "platform_id": "qualtrics",
  "respondent_id": "RSP_1234567890abcdef",
  "session_id": "e41c423d-cdfb-4228-bd25-3fee8459e591",
  "fraud_analysis_available": true,
  "overall_fraud_score": 0.75,
  "is_duplicate": true,
  "fraud_confidence": 0.75,
  "risk_level": "HIGH",
  "ip_analysis": {
    "ip_address": "192.168.1.100",
    "usage_count": 12,
    "sessions_today": 5,
    "risk_score": 0.8
  },
  "device_fingerprint": {
    "fingerprint": "abc123...",
    "usage_count": 6,
    "risk_score": 0.9
  },
  "duplicate_responses": {
    "similarity_score": 0.95,
    "duplicate_count": 3
  },
  "geolocation": {
    "consistent": true,
    "risk_score": 0.0
  },
  "velocity": {
    "responses_per_hour": 15.0,
    "risk_score": 0.8
  },
  "flag_reasons": {
    "ip_reuse": {"count": 12, "severity": "high"},
    "device_reuse": {"count": 6, "severity": "high"},
    "duplicate_responses": {"count": 3, "severity": "high"},
    "high_velocity": {"responses_per_hour": 15.0, "severity": "high"}
  },
  "created_at": "2025-01-01T00:15:30Z"
}
```

**Notes:**
- These hierarchical endpoints enable fraud analysis at different aggregation levels.
- Fraud scores are integrated into the composite bot detection algorithm (40% behavioral, 30% text quality, 30% fraud).
- Use these endpoints for reporting and dashboards that need fraud metrics per survey, platform, or respondent.

---

## Text Analysis (Flat / Session-Based Endpoints — Still Supported)

While the V2 hierarchy introduces new aggregated endpoints, the **flat text-analysis endpoints remain available** under `/api/v1/text-analysis` for integrations that only have a `session_id` (or that submit questions/responses in real time):

- **Submit question**: `POST /text-analysis/questions`
- **Submit response**: `POST /text-analysis/responses`
- **Session text summary (flat)**: `GET /text-analysis/sessions/{session_id}/summary`
- **Health**: `GET /text-analysis/health`
- **Stats**: `GET /text-analysis/stats`

## Fraud Detection (Flat / Session-Based Endpoints — Still Supported)

The **flat fraud detection endpoints remain available** under `/api/v1/fraud` for integrations that only have a `session_id`:

- **Get fraud indicators**: `GET /fraud/sessions/{session_id}`
- **Get sessions by IP**: `GET /fraud/ip/{ip_address}`
- **Get sessions by fingerprint**: `GET /fraud/fingerprint/{fingerprint}`
- **Fraud dashboard summary**: `GET /fraud/dashboard/summary`
- **Get duplicate sessions**: `GET /fraud/dashboard/duplicates`
- **Analyze session fraud**: `POST /fraud/analyze/{session_id}`

**Note:** For hierarchical navigation, prefer the hierarchical endpoints listed above.

---

## Migration from V1 to V2

### Key Changes

1. **Platform Field**: The `platform` field is now complemented by `platform_id` for hierarchical structure
2. **New Endpoints**: All hierarchical endpoints are new and don't replace existing V1 endpoints
3. **Backward Compatibility**: All V1 endpoints (`/detection/sessions/*`, `/dashboard/*`) remain unchanged

### Migration Steps

1. **Update Session Creation**: When creating sessions, include `platform_id` parameter:
   ```bash
   POST /detection/sessions?survey_id=SV_123&platform_id=qualtrics&respondent_id=RSP_123
   ```

2. **Use Hierarchical Endpoints**: For aggregated views, use the new hierarchical endpoints:
   - Survey-level: `/surveys/{survey_id}`
   - Platform-level: `/surveys/{survey_id}/platforms/{platform_id}`
   - Respondent-level: `/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}`

3. **Update Frontend**: Use the new hierarchical service methods in `apiService.js`

---

## Code Examples

### JavaScript/TypeScript

```javascript
import { hierarchicalService } from './services/apiService';

// Get all surveys
const surveys = await hierarchicalService.getSurveys({ limit: 50 });

// Get survey details
const surveyDetails = await hierarchicalService.getSurveyDetails('SV_123');

// Get platform details
const platformDetails = await hierarchicalService.getPlatformDetails(
  'SV_123', 
  'qualtrics'
);

// Get respondent details
const respondentDetails = await hierarchicalService.getRespondentDetails(
  'SV_123',
  'qualtrics',
  'RSP_123'
);

// Get all sessions for a respondent
const sessions = await hierarchicalService.getRespondentSessions(
  'SV_123',
  'qualtrics',
  'RSP_123'
);

// Get fraud detection summaries at different levels
const surveyFraud = await hierarchicalService.getSurveyFraudSummary('SV_123');
const platformFraud = await hierarchicalService.getPlatformFraudSummary('SV_123', 'qualtrics');
const respondentFraud = await hierarchicalService.getRespondentFraudSummary('SV_123', 'qualtrics', 'RSP_123');
const sessionFraud = await hierarchicalService.getSessionFraudByHierarchy('SV_123', 'qualtrics', 'RSP_123', 'session-id');

// Get grid analysis summaries at different levels
const surveyGrid = await hierarchicalService.getGridAnalysisSummary('SV_123');
const platformGrid = await hierarchicalService.getGridAnalysisSummary('SV_123', 'qualtrics');
const respondentGrid = await hierarchicalService.getGridAnalysisSummary('SV_123', 'qualtrics', 'RSP_123');
const sessionGrid = await hierarchicalService.getGridAnalysisSummary('SV_123', 'qualtrics', 'RSP_123', 'session-id');

// Get timing analysis summaries at different levels
const surveyTiming = await hierarchicalService.getTimingAnalysisSummary('SV_123');
const platformTiming = await hierarchicalService.getTimingAnalysisSummary('SV_123', 'qualtrics');
const respondentTiming = await hierarchicalService.getTimingAnalysisSummary('SV_123', 'qualtrics', 'RSP_123');
const sessionTiming = await hierarchicalService.getTimingAnalysisSummary('SV_123', 'qualtrics', 'RSP_123', 'session-id');
```

### Python

```python
import requests

base_url = "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1"

# Get all surveys
response = requests.get(f"{base_url}/surveys?limit=50")
surveys = response.json()

# Get survey details
response = requests.get(f"{base_url}/surveys/SV_123")
survey_details = response.json()

# Get platform details
response = requests.get(f"{base_url}/surveys/SV_123/platforms/qualtrics")
platform_details = response.json()

# Get respondent details
response = requests.get(
    f"{base_url}/surveys/SV_123/platforms/qualtrics/respondents/RSP_123"
)
respondent_details = response.json()

# Get fraud detection summaries at different levels
response = requests.get(f"{base_url}/surveys/SV_123/fraud/summary")
survey_fraud = response.json()

response = requests.get(f"{base_url}/surveys/SV_123/platforms/qualtrics/fraud/summary")
platform_fraud = response.json()

response = requests.get(
    f"{base_url}/surveys/SV_123/platforms/qualtrics/respondents/RSP_123/fraud/summary"
)
respondent_fraud = response.json()

# Get grid analysis summaries at different levels
response = requests.get(f"{base_url}/surveys/SV_123/grid-analysis/summary")
survey_grid = response.json()

response = requests.get(f"{base_url}/surveys/SV_123/platforms/qualtrics/grid-analysis/summary")
platform_grid = response.json()

# Get timing analysis summaries at different levels
response = requests.get(f"{base_url}/surveys/SV_123/timing-analysis/summary")
survey_timing = response.json()

response = requests.get(f"{base_url}/surveys/SV_123/platforms/qualtrics/timing-analysis/summary")
platform_timing = response.json()
```

---

## Error Handling

### HTTP Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found in hierarchy
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Best Practices

1. **Use Hierarchical Paths**: Always use the full hierarchical path when accessing sessions via hierarchy
2. **Cache Aggregations**: Survey and platform aggregations can be cached for better performance
3. **Pagination**: Use `limit` and `offset` for large result sets
4. **Date Filtering**: Use `date_from` and `date_to` for time-based analysis
5. **Error Handling**: Always handle 404 errors when navigating hierarchy

---

## Frontend Deployment & Data Flow Verification

**Status:** ✅ **VERIFIED** (February 2026)

### Deployment Status
- ✅ Frontend successfully deployed to Cloud Storage
- ✅ All hierarchical API endpoints verified returning data from Cloud SQL
- ✅ Data flow verified: Cloud SQL → Backend API → Frontend Dashboard
- ✅ Hierarchical fraud detection widgets integrated and operational

### Verified Hierarchical Endpoints
- **Surveys List** (`/api/v1/surveys`) - ✅ Verified (3 surveys found)
- **Survey Details** (`/api/v1/surveys/{survey_id}`) - ✅ Verified
- **Platform Fraud Summary** (`/api/v1/surveys/{survey_id}/platforms/{platform_id}/fraud/summary`) - ✅ Verified
- **Respondent Fraud Summary** (`/api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/fraud/summary`) - ✅ Verified
- **Session Fraud Details** (`/api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}/fraud`) - ✅ Verified

### Frontend Configuration
- **API Base URL**: `https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1`
- **Frontend URL**: `https://storage.googleapis.com/bot-detection-frontend-20251208`
- **Configuration File**: `frontend/src/config/config.ts` (centralized config system)

---

## Support

For questions or issues with the hierarchical API:

- **Documentation**: See `API.md` for V1 endpoints
- **Frontend Integration**: Check `frontend/src/services/apiService.js` for service methods
- **Backend Implementation**: See `backend/app/controllers/hierarchical_controller.py`
- **Text Analysis (flat endpoints)**: See `backend/app/controllers/text_analysis_controller.py`

---

*Last updated: February 2026*

---

## Changelog

### February 2026
- ✅ Frontend deployment verified - All hierarchical endpoints pulling data correctly from Cloud SQL
- ✅ Data flow verification completed - Cloud SQL → Backend API → Frontend Dashboard
- ✅ Updated production URLs in documentation
- ✅ Hierarchical fraud detection widgets integrated into frontend dashboard
- ✅ Stage 2 (Grid & Timing Analysis) fully implemented and deployed
- ✅ Grid analysis endpoints: 4 hierarchical endpoints operational
- ✅ Timing analysis endpoints: 4 hierarchical endpoints operational
- ✅ Frontend widgets: GridAnalysisWidget, TimingAnalysisWidget, PerQuestionTimingTable integrated
- ✅ Comprehensive test suite: 40 tests covering grid and timing analysis (100% passing)
- ✅ Database migration: grid_responses and timing_analysis tables created
- ✅ Dashboard redeployed: API Playground fraud/grid/timing endpoint templates; Report Builder fraud, grid, and timing in summary and detailed reports/CSV; respondent detail popup and full CSV per respondent

