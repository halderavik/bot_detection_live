# Bot Detection API Documentation

## Table of Contents
1. [Overview](#overview)
2. [Base URL & Authentication](#base-url--authentication)
3. [Core API Endpoints](#core-api-endpoints)
4. [Text Quality Analysis APIs](#text-quality-analysis-apis)
5. [Integration APIs](#integration-apis)
6. [Dashboard APIs](#dashboard-apis)
7. [Survey Tracking APIs (Decipher)](#survey-tracking-apis-decipher)
8. [Live Quality APIs](#live-quality-apis)
9. [Settings APIs](#settings-apis)
10. [Health & Monitoring](#health--monitoring)
11. [Error Handling](#error-handling)
12. [Integration Guides](#integration-guides)
13. [Client SDKs](#client-sdks)
14. [Rate Limits & Best Practices](#rate-limits--best-practices)
15. [Frontend Integration](#frontend-integration)
16. [Hierarchical API (V2)](#hierarchical-api-v2)

---

## Overview

The Bot Detection API provides comprehensive bot detection capabilities through behavioral analysis, OpenAI-powered text quality analysis, survey platform integration, and real-time monitoring. The API is built with FastAPI and supports both synchronous and asynchronous operations.

> **NEW: Hierarchical API (V2)** - The system now supports hierarchical data access through Survey → Platform → Respondent → Session structure. See [API_V2.md](API_V2.md) for hierarchical endpoints. All existing endpoints remain unchanged for backward compatibility.

### Key Features
- **Session Management**: Create and manage bot detection sessions
- **Event Collection**: Ingest behavioral events (keystrokes, mouse movements, etc.)
- **Text Quality Analysis**: OpenAI GPT-4o-mini powered analysis of survey responses
- **Composite Analysis**: Unified bot detection combining behavioral + text quality
- **Real-time Analysis**: Perform bot detection analysis with confidence scoring
- **Survey Integration**: Seamless integration with Qualtrics and Decipher
- **Dashboard Analytics**: Comprehensive monitoring and reporting
- **Decipher Tracking**: Add live tracking to a Decipher survey XML and upload it to Decipher
- **Live Quality**: Per-survey quality rules, live results, CSV export, and `LQ_` variables added to a data file
- **Settings**: Integration keys, tracking and the bot threshold, saved from the dashboard
- **Client SDKs**: Python and JavaScript libraries for easy integration
- **Frontend Dashboard**: Complete React-based monitoring interface
- **Integration Management**: Webhook testing and status monitoring

---

## Base URL & Authentication

### Base URL
Local (development)
```
http://localhost:8000/api/v1
```

Production (GCP)
```
https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1
```

**Note**: All fraud detection endpoints use `/api/v1/fraud/` prefix (not `/api/v1/fraud-detection/`).

Frontend Dashboard (Production)
```
https://storage.googleapis.com/bot-detection-frontend-20251208/index.html
```

**Frontend Deployment Status:** ✅ **VERIFIED** (February 2026)
- ✅ Frontend successfully deployed to Cloud Storage
- ✅ All API endpoints verified and returning data from Cloud SQL
- ✅ Data flow verified: Cloud SQL → Backend API → Frontend Dashboard
- ✅ Fraud detection widget integrated and operational

Note: Interactive API docs are available at `/docs` in both development and production. Use the curl examples below for production testing.

### Authentication
Most endpoints do not require authentication. Changing settings (`POST /settings/check`, `PUT /settings`) needs the `X-Admin-Token` header to match the `ADMIN_TOKEN` environment variable; see [Settings APIs](#settings-apis).

### Headers
```http
Content-Type: application/json
Accept: application/json
```

---

## Core API Endpoints

### 1. Session Management

#### Create Session
```http
POST /detection/sessions
```

**Description:** Creates a new bot detection session.

**Query Parameters (Optional):**
- `survey_id` (string): Survey identifier from the survey platform
- `respondent_id` (string): Respondent identifier from the survey platform
- `platform` (string): Survey platform name (e.g., "qualtrics", "decipher") - **Deprecated, use `platform_id` instead**
- `platform_id` (string): Platform identifier for hierarchical structure (e.g., "qualtrics", "decipher")

**Request Body:** Empty or `{}`

**Response:**
```json
{
  "session_id": "e41c423d-cdfb-4228-bd25-3fee8459e591",
  "created_at": "2025-06-29T00:10:01.707621+00:00",
  "status": "active"
}
```

**Examples:**
```bash
# Basic session creation (local)
curl -X POST "http://localhost:8000/api/v1/detection/sessions" \
  -H "Content-Type: application/json"

# Session with survey metadata (production)
curl -X POST "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/detection/sessions?survey_id=SV_1234567890abcdef&respondent_id=RSP_1234567890abcdef&platform_id=qualtrics" \
  -H "Content-Type: application/json"

# Session with survey metadata (local)
curl -X POST "http://localhost:8000/api/v1/detection/sessions?survey_id=decipher_survey_123&respondent_id=resp_789abcdef&platform_id=decipher" \
  -H "Content-Type: application/json"
```

#### Get Session Status
```http
GET /detection/sessions/{session_id}/status
```

**Description:** Retrieves the current status and metadata of a session.

**Response:**
```json
{
  "session_id": "e41c423d-cdfb-4228-bd25-3fee8459e591",
  "created_at": "2025-06-29T00:10:01.707621+00:00",
  "status": "active",
  "event_count": 150,
  "last_event_at": "2025-06-29T00:15:30.000Z",
  "latest_detection": {
    "is_bot": false,
    "confidence_score": 0.85,
    "risk_level": "LOW",
    "created_at": "2025-06-29T00:15:30.000Z"
  }
}
```

### 2. Event Collection

#### Ingest Events
```http
POST /detection/sessions/{session_id}/events
```

**Description:** Ingests behavioral events for bot detection analysis.

**Request Body:**
```json
[
  {
    "event_type": "keystroke",
    "timestamp": "2025-06-29T00:15:30.000Z",
    "key": "a",
    "element_id": "input-1",
    "key_code": 65
  },
  {
    "event_type": "mouse_move",
    "timestamp": "2025-06-29T00:15:31.000Z",
    "x": 100,
    "y": 200,
    "delta_x": 5,
    "delta_y": 3
  },
  {
    "event_type": "focus",
    "timestamp": "2025-06-29T00:15:32.000Z",
    "element_id": "input-1"
  },
  {
    "event_type": "scroll",
    "timestamp": "2025-06-29T00:15:33.000Z",
    "delta_x": 0,
    "delta_y": 100
  }
]
```

**Supported Event Types:**
- `keystroke`: Keyboard input events
- `mouse_move`: Mouse movement events
- `mouse_click`: Mouse click events
- `focus`: Element focus events
- `blur`: Element blur events
- `scroll`: Scroll events
- `device_info`: Device fingerprinting data

**Response:**
```json
{
  "session_id": "e41c423d-cdfb-4228-bd25-3fee8459e591",
  "events_processed": 4,
  "processing_time_ms": 45,
  "message": "Events processed successfully"
}
```

### 3. Bot Detection Analysis

#### Check Session Readiness
```http
GET /detection/sessions/{session_id}/ready-for-analysis
```

**Description:** Checks if a session has enough data for analysis.

**Response:**
```json
{
  "session_id": "e41c423d-cdfb-4228-bd25-3fee8459e591",
  "ready": true,
  "event_count": 150,
  "min_events_required": 50,
  "message": "Session is ready for analysis"
}
```

#### Analyze Session
```http
POST /detection/sessions/{session_id}/analyze
```

**Description:** Performs comprehensive bot detection analysis.

**Response:**
```json
{
  "session_id": "e41c423d-cdfb-4228-bd25-3fee8459e591",
  "is_bot": false,
  "confidence_score": 0.85,
  "risk_level": "LOW",
  "processing_time_ms": 125,
  "analysis_summary": "Human-like behavior detected across all metrics",
  "method_scores": {
    "keystroke_analysis": 0.9,
    "mouse_analysis": 0.8,
    "timing_analysis": 0.85,
    "device_analysis": 0.9,
    "behavioral_analysis": 0.8
  },
  "created_at": "2025-06-29T00:15:30.000Z"
}
```

**Risk Levels:**
- `LOW`: Very likely human (confidence > 0.7)
- `MEDIUM`: Uncertain (confidence 0.3-0.7)
- `HIGH`: Very likely bot (confidence < 0.3)

#### Composite Analysis (Behavioral + Text Quality)
```http
POST /detection/sessions/{session_id}/composite-analyze
```

**Description:** Performs unified bot detection analysis combining behavioral patterns and text quality analysis.

**Response:**
```json
{
  "session_id": "e41c423d-cdfb-4228-bd25-3fee8459e591",
  "composite_score": 0.75,
  "behavioral_score": 0.85,
  "text_quality_score": 65.5,
  "text_quality_normalized": 0.345,
  "risk_level": "LOW",
  "is_bot": false,
  "behavioral_details": {
    "confidence_score": 0.85,
    "method_scores": {
      "keystroke_analysis": 0.9,
      "mouse_analysis": 0.8,
      "timing_analysis": 0.85,
      "device_analysis": 0.9
    }
  },
  "text_quality_details": {
    "total_responses": 3,
    "avg_quality_score": 65.5,
    "flagged_count": 1,
    "flagged_percentage": 33.33,
    "flag_types": {
      "generic": 1
    }
  }
}
```

---

## Text Quality Analysis APIs

### 1. Question Capture

#### Capture Survey Question
```http
POST /text-analysis/questions
```

**Description:** Captures a survey question for text quality analysis.

**Request Body:**
```json
{
  "session_id": "e41c423d-cdfb-4228-bd25-3fee8459e591",
  "question_text": "What is your favorite color?",
  "question_type": "open_ended",
  "element_id": "color-input",
  "page_url": "https://example.com/survey",
  "page_title": "Color Preference Survey"
}
```

**Response:**
```json
{
  "question_id": "q_12345678-1234-1234-1234-123456789abc",
  "session_id": "e41c423d-cdfb-4228-bd25-3fee8459e591",
  "message": "Question captured successfully"
}
```

### 2. Response Analysis

#### Analyze Response
```http
POST /text-analysis/responses
```

**Description:** Analyzes a survey response using OpenAI GPT-4o-mini for quality assessment.

**Request Body:**
```json
{
  "session_id": "e41c423d-cdfb-4228-bd25-3fee8459e591",
  "question_id": "q_12345678-1234-1234-1234-123456789abc",
  "response_text": "My favorite color is blue because it reminds me of the ocean and sky.",
  "response_time_ms": 2500
}
```

**Response:**
```json
{
  "response_id": "r_87654321-4321-4321-4321-cba987654321",
  "session_id": "e41c423d-cdfb-4228-bd25-3fee8459e591",
  "question_id": "q_12345678-1234-1234-1234-123456789abc",
  "quality_score": 85.5,
  "is_flagged": false,
  "flag_reasons": {},
  "message": "Response analyzed successfully"
}
```

**Flag Reasons:**
- `gibberish`: Random characters or nonsensical text
- `copy_paste`: Generic or copied content
- `irrelevant`: Off-topic responses
- `generic`: Low-effort, uninformative answers
- `low_quality`: Very poor quality score (< 30)

### 3. Session Summary

#### Get Text Quality Summary
```http
GET /text-analysis/sessions/{session_id}/summary
```

**Description:** Retrieves a summary of text quality analysis for a session.

**Response:**
```json
{
  "session_id": "e41c423d-cdfb-4228-bd25-3fee8459e591",
  "total_responses": 3,
  "avg_quality_score": 72.3,
  "flagged_count": 1,
  "flag_type_counts": {
    "generic": 1
  },
  "responses": [
    {
      "response_id": "r_87654321-4321-4321-4321-cba987654321",
      "question_id": "q_12345678-1234-1234-1234-123456789abc",
      "response_text": "My favorite color is blue because it reminds me of the ocean and sky.",
      "quality_score": 85.5,
      "is_flagged": false,
      "flag_reasons": {}
    }
  ]
}
```

### 4. Usage Statistics

#### Get OpenAI Usage Stats
```http
GET /text-analysis/stats
```

**Description:** Returns OpenAI API usage statistics and cost tracking.

**Response:**
```json
{
  "total_tokens": 15420,
  "total_cost": 0.0231
}
```

### 5. Health Monitoring

#### Get Text Analysis Health Status
```http
GET /text-analysis/health
```

**Description:** Returns OpenAI service availability and configuration status without exposing secrets.

**Status:** ✅ **OPERATIONAL** - Production endpoint active with OpenAI fully configured

**Response:**
```json
{
  "status": "healthy",
  "openai_available": true,
  "model": "gpt-4o-mini",
  "max_tokens": 500,
  "temperature": 0.3,
  "rate_limiter_enabled": true,
  "cache_enabled": true,
  "service_initialized": true
}
```

**Example Usage:**
```bash
# Production
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/text-analysis/health"
```

**Note:** The `platform` parameter is still supported for backward compatibility, but `platform_id` is recommended for the hierarchical API structure.

---

## Integration APIs

### 1. Qualtrics Integration

#### Webhook Endpoint
```http
POST /integrations/webhooks/qualtrics
```

**Description:** Receives webhook notifications from Qualtrics survey completions.

**Headers:**
```http
Content-Type: application/json
X-Qualtrics-Signature: {signature} (optional)
```

**Request Body:**
```json
{
  "surveyId": "SV_1234567890abcdef",
  "responseId": "R_1234567890abcdef",
  "respondentId": "RSP_1234567890abcdef",
  "completedDate": "2025-06-29T00:15:30.000Z",
  "values": {
    "QID1": "John Doe",
    "QID2": "john.doe@example.com",
    "QID3": "25-34",
    "QID4": "Male",
    "QID5": "Very satisfied"
  },
  "embeddedData": {
    "sessionId": "e41c423d-cdfb-4228-bd25-3fee8459e591",
    "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "ipAddress": "192.168.1.100"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Webhook processed successfully"
}
```

#### Get Survey Information
```http
GET /integrations/qualtrics/surveys/{survey_id}
```

**Description:** Retrieves information about a Qualtrics survey.

**Response:**
```json
{
  "platform": "qualtrics",
  "survey_id": "SV_1234567890abcdef",
  "name": "Customer Satisfaction Survey",
  "status": "active",
  "response_count": 1250
}
```

### 2. Decipher Integration

#### Webhook Endpoint
```http
POST /integrations/webhooks/decipher
```

**Description:** Receives webhook notifications from Decipher survey completions.

**Headers:**
```http
Content-Type: application/json
X-Decipher-Signature: {signature} (optional)
```

**Request Body:**
```json
{
  "surveyId": "decipher_survey_123",
  "responseId": "resp_789abcdef",
  "respondentId": "resp_789abcdef",
  "completedAt": "2025-06-29T00:15:30.000Z",
  "answers": {
    "q1": {"value": "Jane Smith", "type": "text"},
    "q2": {"value": "jane.smith@example.com", "type": "email"},
    "q3": {"value": "35-44", "type": "choice"},
    "q4": {"value": "Female", "type": "choice"},
    "q5": {"value": "Somewhat satisfied", "type": "rating"}
  },
  "metadata": {
    "sessionId": "e41c423d-cdfb-4228-bd25-3fee8459e591",
    "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "ipAddress": "203.0.113.45"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Webhook processed successfully"
}
```

#### Get Survey Information
```http
GET /integrations/decipher/surveys/{survey_id}
```

**Description:** Retrieves information about a Decipher survey.

**Response:**
```json
{
  "platform": "decipher",
  "survey_id": "decipher_survey_123",
  "name": "Market Research Survey",
  "status": "active",
  "response_count": 850
}
```

### 3. Integration Status
```http
GET /integrations/status
```

**Description:** Returns the status of all integrations.

**Response:**
```json
{
  "qualtrics": {
    "status": "connected",
    "api_token_configured": true,
  "webhook_url": "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/integrations/webhooks/qualtrics"
  },
  "decipher": {
    "status": "connected",
    "api_key_configured": true,
  "webhook_url": "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/integrations/webhooks/decipher"
  }
}
```

---

## Dashboard APIs

### How Bot Numbers Are Counted
Every dashboard number counts sessions, not detection rows. A session analysed more than once counts once.
- **Checked**: sessions with at least one detection result (analysed).
- **Bots**: checked sessions with a detection that judged them a bot.
- **Bot rate**: bots / checked x 100. It is 0 when nothing has been checked. Sessions that were never analysed are not part of the rate.

The survey, platform and respondent aggregations in [API_V2.md](API_V2.md) use the same rule.

### 1. Dashboard Overview
```http
GET /dashboard/overview
```

**Description:** Returns statistics for sessions created in the last `days` days.

**Query Parameters:**
- `days`: Number of days to cover (default: 7)

**Response:**
```json
{
  "period": {
    "start_date": "2026-11-19T10:00:00",
    "end_date": "2026-11-26T10:00:00",
    "days": 7
  },
  "sessions": {
    "total": 1250,
    "active": 45,
    "completed": 1100,
    "completion_rate": 88.0
  },
  "detections": {
    "total": 1000,
    "checked": 1000,
    "bots_detected": 120,
    "high_confidence": 300,
    "bot_rate": 12.0
  },
  "events": {
    "total": 125000,
    "by_type": { "keystroke": 40000, "mouse_move": 70000 }
  },
  "platforms": {
    "qualtrics": 850,
    "decipher": 400
  }
}
```

`detections` covers sessions created in the period:
- `checked`: sessions that were analysed. `total` has the same value and is kept for older clients.
- `bots_detected`: checked sessions judged bots.
- `high_confidence`: checked sessions with a detection whose confidence score is 0.8 or higher.
- `bot_rate`: `bots_detected / checked x 100` (a percentage, 0 when nothing was checked).

`events` counts events received in the period; `platforms` counts sessions per `platform` value.

### 2. Session List
```http
GET /dashboard/sessions
```

**Description:** Returns a paginated list of sessions, newest first, each with its latest detection result.

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 50, max: 100)
- `platform`: Sessions whose `platform` or `platform_id` equals this value
- `risk_level`: Latest risk level (for example `low`, `medium`, `high`; case does not matter). `unknown` returns sessions that have not been analysed.
- `is_bot`: `true` or `false`, the latest bot verdict. Sessions that have not been analysed match neither.
- `survey_id`: Sessions of this survey
- `search`: Sessions whose session id, respondent id or survey id contains this text

Filters can be combined. `pagination.total` counts the sessions that match the filters.

**Response:**
```json
{
  "sessions": [
    {
      "id": "e41c423d-cdfb-4228-bd25-3fee8459e591",
      "created_at": "2026-11-26T00:10:01.707621",
      "last_activity": "2026-11-26T00:15:30.000000",
      "is_active": true,
      "platform": "decipher",
      "survey_id": "coffee_demo",
      "respondent_id": "a1b2c3d4",
      "event_count": 150,
      "analyzed": true,
      "is_bot": false,
      "risk_level": "low",
      "confidence_score": 0.15,
      "analyzed_at": "2026-11-26T00:15:31.000000"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 1250,
    "pages": 25
  }
}
```

- `platform` falls back to `platform_id` when `platform` is empty.
- `risk_level` is lowercase, and `unknown` when the session has not been analysed. `is_bot`, `confidence_score` and `analyzed_at` are `null` then, and `analyzed` is `false`.

### 3. Session Details
```http
GET /dashboard/sessions/{session_id}/details
```

**Description:** Returns a session with all its events and detection results.

**Response (shortened):**
```json
{
  "session": {
    "id": "e41c423d-cdfb-4228-bd25-3fee8459e591",
    "created_at": "2026-11-26T00:10:01.707621",
    "last_activity": "2026-11-26T00:15:30.000000",
    "is_active": true,
    "is_completed": false,
    "user_agent": "Mozilla/5.0 ...",
    "ip_address": "203.0.113.10",
    "referrer": null,
    "platform": "decipher",
    "survey_id": "coffee_demo",
    "respondent_id": "a1b2c3d4"
  },
  "behavior_data": [
    {
      "id": "...",
      "event_type": "keystroke",
      "timestamp": "2026-11-26T00:10:05.000000",
      "element_id": "q1",
      "element_type": "input",
      "page_url": "https://example.com/survey",
      "screen_width": 1920,
      "screen_height": 1080,
      "event_data": {}
    }
  ],
  "detection_results": [
    {
      "id": "...",
      "is_bot": false,
      "confidence_score": 0.15,
      "risk_level": "low",
      "processing_time_ms": 42.0,
      "event_count": 150,
      "analysis_summary": "...",
      "method_scores": {},
      "flagged_patterns": {},
      "analyzed_at": "2026-11-26T00:15:31.000000"
    }
  ],
  "statistics": {
    "total_events": 150,
    "total_detections": 1,
    "session_duration_minutes": 5.5
  }
}
```

`session.platform` falls back to `platform_id` when `platform` is empty.

**Errors:** `404` when the session does not exist.

### 4. Analytics Trends
```http
GET /dashboard/analytics/trends
```

**Description:** Sessions started per day, with how many of them were checked and judged bots.

**Query Parameters:**
- `days`: Number of days to cover (default: 30)
- `interval`: Accepted for compatibility; buckets are always one day

**Response:**
```json
{
  "period": {
    "start_date": "2026-10-27T10:00:00",
    "end_date": "2026-11-26T10:00:00",
    "interval": "day"
  },
  "trends": [
    { "date": "2026-11-25", "sessions": 40, "checked": 35, "bots": 4, "detections": 35 },
    { "date": "2026-11-26", "sessions": 12, "checked": 9, "bots": 1, "detections": 9 }
  ]
}
```

- Each bucket runs from midnight UTC to the next midnight UTC, from the start day through today, empty days included.
- Sessions are counted by the day they started. `checked` and `bots` are those sessions that were analysed and judged bots, each session counted once.
- `detections` equals `checked` and is kept for older clients.

---

## Survey Tracking APIs (Decipher)

Add live tracking to a Decipher survey XML, and optionally send the tracked file to Decipher. Removing the tracking gives back the original file byte for byte.

### Checking an XML and Fix with AI (Add tracking page)

```http
POST /tracking/decipher/check      (multipart: file)
```

Checks the file before tracking is added. Each issue has `code`, `severity` (`error` stops tracking, `warning` does not), `title`, `detail` (why), `fix` (how), `line`, `ai_can_fix` and `items` (for example the quota sheets or `.dat` files involved). Checks: not UTF-8, empty, DOCTYPE, broken XML (line, column, the line's text and the usual cause), only part of a survey (no `<survey>` tag), compat missing, invalid or below 143, compat 151+ without `delphi="1"`, styles that only run up to a compat (`atm1d.9` up to 149, `autosum.5` and `ranksort.7` up to 154), labels starting with `QOS_`, duplicate labels, no questions; warnings for quota sheets and `Database()`/`File()` data files that live in the Decipher survey, not the XML. The report also has `recommended_compat`, question and page counts, and `ai_available`.

```http
POST /tracking/decipher/fix        (multipart: file, instructions?)
```

Fix with AI. Exact repairs are done in code: a survey body without `<survey>` is wrapped in a standard header (the one Decipher accepted in testing) with the recommended compat and the file name as title, and later copies of a duplicate label are renamed `LABEL_2`, `LABEL_3` (the first keeps its label). The model (`OPENAI_FIX_MODEL`, default `gpt-4o`) then fixes the remaining errors and follows `instructions` (up to 2000 characters, for example a survey title, a compat, or "remove the quotas"); without instructions it fixes errors only and leaves quota sheets and data files alone. It returns exact edits that are applied only where the text matches one place; large files are sent as excerpts around each problem. The result is checked again (up to two rounds) and never kept if it made the XML unreadable. Response: `xml` (without tracking), `filename` (`…_fixed.xml`), `changed`, `applied`, `changes`, `assumptions` (choices to check), `cannot_fix`, `skipped`, `rounds`, `model`, `report`. 503 without an OpenAI key, 502/504 when the AI service fails or is slow; at most 20 calls per address per hour.

### When Decipher refuses an upload

`POST /tracking/decipher/upload` errors now carry `explained` (one entry per Decipher message: `message`, `kind`, `explanation`, `fix`, `page`, `ai_can_fix`, `needs_instruction`) and `file_problem` (true when Decipher refused the file itself, false for a wrong key, path or Decipher being unreachable). Kinds: `style_compat` (a style only runs up to a compat), `compat`, `delphi`, `missing_file` (a `.dat` the Decipher survey lacks), `missing_quota` (no `quota.xls`, or a missing sheet), `missing_label`, `duplicate`, `script` (Python in an `<exec>`, condition or validation fails on a page), `xml`, `other`. Missing files and quotas need the user's instruction before Fix with AI touches them.

`POST /tracking/decipher/fix` also takes `decipher_errors` (a JSON list of those messages). A compat limit Decipher reports is applied in code; the other messages go to the model with the parts of the file they point at (quoted names, the page). The fix never raises compat unless asked or the checker reports it too low, applies each edit only if the XML stays readable, and works on plain line breaks.

On the Add tracking page, **Fix with AI and upload again** is offered only when the file being uploaded came from Fix with AI: it fixes the file with Decipher's errors (and optional instructions), checks it, adds tracking again with the same settings and survey id, and uploads to the same Decipher survey (the one created before a refusal, if any). A file the user fixed by hand gets Decipher's errors explained, without the AI option.

### Manual installation (Integrations page)

```http
GET /tracking/decipher/snippet?survey_id=Coffee%20study%20W1
```

Returns the two blocks to paste into a Decipher survey by hand. Pasting `style` right after `</samplesources>` (or right after the opening `<survey ...>` tag) and `results_page` right before `</survey>` gives exactly the XML that `POST /tracking/decipher` produces with no privacy notice and no in-survey check (covered by `tests/test_tracking_snippets.py`).

```json
{
  "survey_id": "Coffee study W1",
  "api_base": "https://…/api/v1",
  "signed": false,
  "style": "<!-- Bot detection live tracking: survey id Coffee study W1 -->
  <style mode=\"after\" name=\"respview.client.js\">…",
  "results_page": "  <html label=\"QOS_finish\">…</html>
  <text label=\"QOS_RESPONDENT\" …",
  "fields": ["QOS_RESPONDENT", "QOS_SESSION", "…"]
}
```

```http
GET /tracking/script.js?survey_id=Coffee%20study%20W1&platform=web
```

The same tracker as a JavaScript file (`application/javascript`) for Qualtrics (`platform=qualtrics`) or any other website (`platform=web`). Load it with a `<script src>` tag on every page. A page may set `window.QOS_RESPONDENT_ID` before it to use its own respondent id. `QOSTracker.finish()` runs the final check and resolves with `{flag, score, risk, variables, session_id, respondent_id}`; the page also gets `qos:session` and `qos:result` events. With `platform=qualtrics` the tracker writes `QOS_SESSION` and `QOS_RESPONDENT` into embedded data through `Qualtrics.SurveyEngine.setEmbeddedData` (declare both fields in the survey flow). Unsafe survey ids or other platforms give 422.

On any platform the tracker also fills inputs whose `name` is a result variable (`QOS_FLAG`, `QOS_SESSION`, `QOS_STATUS`, …), such as hidden inputs in your own form, and inputs next to a `<span class="qos-bot-field" data-field="…">` marker, which it hides. Outside Decipher it sets values with the element's own value setter and fires `input` and `change` events so form frameworks register them. A page with any of these fields is treated as the last page: the final check runs when it opens and the submit waits at most 3 seconds for it.

### 1. Tracking Options
```http
GET /tracking/decipher/options
```

**Description:** Defaults the Add tracking page shows.

**Response:**
```json
{
  "signals": [
    { "code": "automation", "label": "Automated or headless browser" },
    { "code": "scripted_input", "label": "Clicks and key presses generated by script" },
    { "code": "no_input", "label": "Pages answered with no mouse or keyboard use" },
    { "code": "honeypot", "label": "Hidden honeypot field filled in" },
    { "code": "untyped_answers", "label": "Open ends that appeared without typing" }
  ],
  "default_privacy_text": "...",
  "default_after_page": 2,
  "signed": false,
  "decipher_upload": true,
  "max_upload_mb": 5
}
```

- `signed`: whether `TRACKING_TOKEN_SECRET` is set, so trackers carry a signed survey token. Signing is optional.
- `decipher_upload`: whether a Decipher API key is configured, so `POST /tracking/decipher/upload` can be used.

### 2. Add Tracking to a Decipher Survey
```http
POST /tracking/decipher
Content-Type: multipart/form-data
```

**Description:** Returns the uploaded survey with live tracking added once. If the file is already tracked (including by Quant OS), the old tracking is replaced, not added twice.

**Form Fields:**
- `file` (required): The Decipher survey XML (`.xml`, or `.txt` holding the XML), up to 5 MB. It must be a complete survey with a `<survey>` root element.
- `survey_id` (optional): Tracking survey id. Default: taken from the survey title.
- `terminate` (optional, default `false`): End the survey early on a clear bot signal.
- `after_page` (optional, default `2`): Page whose submit runs the in-survey check when `terminate` is on.
- `signals` (optional): Comma-separated bot signal codes that end the survey (see options). Default: all five.
- `privacy_notice` (optional, default `true`): Show a short privacy notice at the top of the first page (`QOS_privacy`).
- `privacy_text` (optional): Notice text. Default: `default_privacy_text`.

**Query Parameters:**
- `format`: `json` (default) or `xml`. `xml` returns the tracked file itself as an attachment named `<name>_tracked.xml`.

**What is added:**
- The tracker script as a `respview.client.js` style with `mode="after"`, so it runs on every page alongside the survey's own scripts.
- Decipher's `${uuid}` as the respondent id, so results match the `uuid` column in Decipher's data exports.
- A hidden results page with 21 variables: `QOS_RESPONDENT`, `QOS_SESSION`, `QOS_FLAG`, `QOS_SCORE`, `QOS_RISK`, `QOS_STATUS`, `QOS_BEHAV`, `QOS_OES`, `QOS_FRAUD`, `QOS_DUP`, `QOS_DUP_SCORE`, `QOS_IP_RISK`, `QOS_DEVICE_RISK`, `QOS_GEO_RISK`, `QOS_VELOCITY`, `QOS_DATACENTER`, `QOS_SPEEDER`, `QOS_STRAIGHTLINE`, `QOS_FLAGCOUNT`, `QOS_REASON`, `QOS_REASONS`.
- When `privacy_notice` is on: the notice (`QOS_privacy`).
- When `terminate` is on: an early check (`QOS_EARLY` and `QOS_bot_term`). It acts only on the chosen decisive signals and only on a page break every respondent reaches.

The tracker calls `TRACKER_API_BASE`, or else the address the upload came in on. It must be https, except for localhost.

**Response (JSON):**
```json
{
  "survey_id": "coffee_demo",
  "filename": "coffee_demo_tracked.xml",
  "xml": "<survey ...>...</survey>",
  "replaced_existing_tracking": false,
  "new_survey_record": true,
  "existing_sessions": 0,
  "signed": false,
  "api_base": "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1",
  "added": ["Tracker script, as a respview.client.js style with mode=\"after\" ..."],
  "survey": { "questions": 6, "pages": 4, "loops": 0, "blocks": 1 },
  "options": { "terminate": false, "after_page": null, "signals": [], "privacy_notice": true },
  "early_check": { "requested": false, "page": null, "note": null },
  "hidden_fields": ["QOS_RESPONDENT", "QOS_SESSION", "..."],
  "warnings": [],
  "dashboard_path": "/surveys/coffee_demo",
  "decipher_upload": { "configured": true, "last_path": null }
}
```

`warnings` includes survey settings Decipher will refuse, starting "Decipher will refuse this file: ...": no `compat` attribute (read as 0), `compat` below 143 (retired), or `compat` 151 or higher without `delphi="1"`. The tracked file is still returned. Surveys that use quota sheets, data files (`File("x.dat")`) or `${res.X}` resources need those files in the target Decipher survey.

**Errors:**
- `400`: Wrong file type, unknown bot signal, or another invalid option
- `413`: File larger than 5 MB
- `422`: Not a Decipher survey (for example a survey-body fragment without a `<survey>` tag, which is refused as not well-formed)
- `500`: The tracker address is not usable; set `TRACKER_API_BASE` to the service's public https URL ending in `/api/v1`

### 3. Upload a Tracked Survey to Decipher
```http
POST /tracking/decipher/upload
Content-Type: application/json
```

**Description:** Sends tracked survey XML to Decipher. The target is, in order: a new survey when `create_new` is true; `survey_path` when given; the path this survey id was last uploaded to; otherwise a new survey (created in Research Hub under `DECIPHER_COMPANY`). Decipher validates the file before saving it (`validate=true`) and never overwrites a live survey (`overwriteLive=false`). If the target survey has saved data layouts (`layouts.json`), the `QOS_` variables are added to them.

**Request Body:**
```json
{
  "xml": "<survey ...>...</survey>",
  "survey_id": "coffee_demo",
  "survey_path": "selfserve/123/456789",
  "create_new": false
}
```

- `xml` (required): The tracked XML returned by `POST /tracking/decipher` (up to 5 MB).
- `survey_id` (required): Must match the survey id the XML is tracked as.
- `survey_path` (optional): An existing Decipher survey path (`selfserve/123/456789`) or survey link.
- `create_new` (optional, default `false`): Create a new survey even if one was used before.

**Response:**
```json
{
  "survey_id": "coffee_demo",
  "survey_path": "selfserve/123/456789",
  "survey_url": "https://selfserve.decipherinc.com/survey/selfserve/123/456789",
  "created": true,
  "message": "...",
  "layouts_updated": 0,
  "warnings": []
}
```

**Errors:**
- `400`: `survey_path` is not a Decipher survey path, or Decipher refused the file or path. Decipher's own messages, including script errors such as `Exec (page N): ...`, are returned in full.
- `422`: Not a Decipher survey; the XML has no tracking yet; the XML is tracked under a different survey id; or survey settings Decipher would refuse (the message says "nothing was sent to Decipher", and no empty survey is created)
- `502`: Any other Decipher error (for example a rejected API key)
- `503`: Decipher upload is not configured (no Decipher API key)

Errors from Decipher and from the settings check return `detail` as an object:
```json
{
  "detail": {
    "message": "Decipher would refuse this file, so nothing was sent to Decipher. ...",
    "errors": ["..."],
    "survey_path": null,
    "survey_url": null
  }
}
```
If Decipher created a new survey and then refused the XML, that `survey_path` is remembered, so a retry updates the same survey.

---

## Live Quality APIs

Per-survey quality rules, live bot and fraud results, a CSV export, and adding the results to a survey data file. The survey id is always a query parameter (`?survey_id=`), because survey ids are often titles with spaces and punctuation. It must be 1 to 255 characters; otherwise the endpoints return `422`.

Rules apply every time results are read (dashboard, CSV, `LQ_` variables). They do not change stored detection results or the `QOS_` values written into Decipher.

### 1. List Surveys
```http
GET /quality/surveys
```

**Description:** Every survey with sessions, plus tracked surveys nobody has started yet. Tracked surveys come first, then by latest activity.

**Response:**
```json
{
  "surveys": [
    {
      "survey_id": "coffee_demo",
      "title": "coffee_demo",
      "sessions": 25,
      "bots": 2,
      "last_session": "2026-11-26T09:12:00",
      "tracked": true,
      "custom_rules": false
    }
  ]
}
```

`tracked` means the survey was tracked with `POST /tracking/decipher`; `custom_rules` means it has saved rules.

**Errors:** `500` the list could not be loaded.

### 2. Results
```http
GET /quality/results?survey_id={survey_id}
```

**Description:** The Live Quality dashboard payload under the survey's rules.

**Response (shortened):**
```json
{
  "survey_id": "coffee_demo",
  "updated_at": "2026-11-26T10:00:00+00:00",
  "rules": { "bot_threshold": 0.7, "...": "..." },
  "totals": {
    "sessions": 25, "in_progress": 2, "checked": 22, "dropped": 1, "bots": 2,
    "flagged": 5, "duplicates": 0, "speeders": 1, "straight_liners": 1, "low_quality_text": 2
  },
  "text": { "responses": 50, "avg_quality": 71.5, "flagged": 4, "flagged_pct": 8.0 },
  "fraud": { "analyzed": 22, "avg_score": 0.21, "high_risk": 1, "duplicates": 0, "methods": {} },
  "grid": { "responses": 22, "straight_lined_pct": 4.5 },
  "timing": { "analyses": 22, "speeders_pct": 4.5, "flatliners_pct": 0 },
  "flag_counts": [
    { "flag": "Bot-like behaviour", "count": 2 },
    { "flag": "Low-quality open ends", "count": 2 }
  ],
  "quality_distribution": {},
  "trend": {
    "unit": "hour",
    "buckets": [{ "start": "2026-11-26T09:00:00+00:00", "started": 6, "flagged": 1 }]
  },
  "respondents": [
    {
      "session_id": "e41c423d-...",
      "respondent_id": "a1b2c3d4",
      "started": "2026-11-26T09:05:00",
      "status": "completed",
      "verdict": "human",
      "risk": "low",
      "confidence": 0.15,
      "seconds": 312.4,
      "pages": 4,
      "fraud_score": 0.1,
      "duplicate": false,
      "straight_lining": false,
      "speeder": false,
      "flatliner": false,
      "flags": []
    }
  ]
}
```

- `flag_counts` always lists all nine flags in this order, zeros included: Bot-like behaviour, Low-quality open ends, Pasted answers, Straight-lining, Speeder, Flatliner, Duplicate, High fraud risk, Data-centre IP.
- `trend` uses hour buckets when all starts fall within 48 hours, otherwise day buckets; at most 120 buckets, ending at the latest start.
- `respondents` has one row per session. `verdict` is `bot`, `human` or `pending` (not checked yet); `risk` is `unknown` when not checked. Rows also carry bot signals, open-end details, fraud reasons and grid and timing explanations.

**Errors:** `422` invalid survey id; `500` the results could not be built.

### 3. CSV Export
```http
GET /quality/export?survey_id={survey_id}
```

**Description:** The same results as CSV, one row per respondent, as an attachment named `quality-<survey_id>.csv`. Columns: `respondent_id`, `session_id`, `started`, `status`, `verdict`, `risk`, `confidence`, `seconds`, `pages`, `text_responses`, `text_quality`, `text_flagged`, `fraud_score`, `fraud_risk`, `duplicate`, `straight_lining`, `speeder`, `flags` (separated by `; `), `flagged_answers` (separated by ` | `).

**Errors:** As for results.

### 3b. Report
```http
GET /quality/report?survey_id={survey_id}&date_from={iso}&date_to={iso}
```

**Description:** What the Reports page builds a report from. The same payload as `/quality/results`, limited to respondents who started between `date_from` and `date_to` (both optional, ISO 8601; times without a zone are UTC). Totals, `flag_counts`, `trend`, `text`, `fraud`, `grid`, `timing` and `quality_distribution` are recounted from the remaining rows, so every number matches the respondent list. Three fields are added:

- `period`: `{"from": iso | null, "to": iso | null}`, the bounds used.
- `survey`: `survey_id`, `title`, `tracked`, and for surveys tracked on this platform `platform`, `decipher_path`, `source_filename`, `terminates_bots`, `privacy_notice`, `signed`, `tracked_since`.
- `rules_state`: the same shape as `GET /quality/rules` (rules in force, defaults, what changed, labels).

**Errors:** `422` invalid survey id, or `date_from` after `date_to`; `500` the results could not be built.

### 4. Quality Rules
```http
GET    /quality/rules?survey_id={survey_id}
PUT    /quality/rules?survey_id={survey_id}
DELETE /quality/rules?survey_id={survey_id}
```

**Description:** `GET` returns the rules in force (the defaults until rules are saved). `PUT` saves the survey's complete rules. `DELETE` goes back to the defaults. All three return the same shape.

**PUT Request Body** (these are the defaults; omitted fields take the default value):
```json
{
  "bot_threshold": 0.7,
  "bot_signals": ["automation", "scripted_input", "no_input", "honeypot", "untyped_answers"],
  "speeder_page_seconds": 3.5,
  "speeder_median_share": 0.5,
  "straightline_min_rows": 3,
  "text_reasons": ["gibberish", "generic", "irrelevant", "copy_paste", "low_quality"],
  "flag_pasted": true,
  "fraud_threshold": 0.7,
  "flag_duplicates": true,
  "flag_datacenter": true
}
```

| Field | Allowed values | Meaning |
|-------|----------------|---------|
| `bot_threshold` | 0.3 to 0.99 | Bot score at or above which a session counts as a bot |
| `bot_signals` | codes from `bot_signals` | Signals that make a session a bot |
| `speeder_page_seconds` | 0.5 to 60 | Seconds per page below which a respondent is a speeder |
| `speeder_median_share` | 0 to 0.9 | Also a speeder when faster than this share of the median time; needs 5 checked respondents; 0 turns it off |
| `straightline_min_rows` | 2 to 30 | Grid rows needed before straight-lining counts |
| `text_reasons` | codes from `text_reasons` | Reasons that make an open end low quality |
| `flag_pasted` | true / false | Flag pasted answers |
| `fraud_threshold` | 0.3 to 0.99 | Fraud score at or above which a respondent is high fraud risk |
| `flag_duplicates` | true / false | Flag duplicates |
| `flag_datacenter` | true / false | Flag data-centre IP addresses |

**Response:**
```json
{
  "rules": { "bot_threshold": 0.8, "...": "..." },
  "defaults": { "bot_threshold": 0.7, "...": "..." },
  "changed": ["bot_threshold"],
  "bot_signals": { "automation": "Automated or headless browser", "...": "..." },
  "text_reasons": { "gibberish": "Gibberish", "generic": "Generic (\"good\", \"nothing\")", "irrelevant": "Off-topic", "copy_paste": "Copied or repeated text", "low_quality": "Low effort" }
}
```

**Errors:** `422` invalid survey id, a value out of range, or an unknown signal or reason code.

### 5. Add Results to a Data File
```http
POST /quality/merge?survey_id={survey_id}
Content-Type: multipart/form-data
```

**Description:** Upload a survey data file (field `file`: SPSS `.sav`, `.csv` or `.xlsx`, up to 50 MB) and get the same file back with `LQ_` variables added under the survey's rules. Records match on `QOS_SESSION`, then `QOS_RESPONDENT`, then Decipher's `uuid`. SPSS files keep their labels, and the `LQ_` variables get labels and value labels. Uploading a file that already has `LQ_` columns replaces them.

`LQ_` variables: `LQ_MATCHED`, `LQ_STATUS`, `LQ_VERDICT`, `LQ_BOT_SCORE`, `LQ_BOT_RISK`, `LQ_BOT_SIGNALS`, `LQ_SECONDS`, `LQ_PAGES`, `LQ_SEC_PER_PAGE`, `LQ_TEXT_QUALITY`, `LQ_FRAUD_SCORE`, `LQ_FRAUD_RISK`, one 0/1 per flag (`LQ_F_BOT`, `LQ_F_TEXT`, `LQ_F_PASTED`, `LQ_F_STRAIGHT`, `LQ_F_SPEEDER`, `LQ_F_FLATLINE`, `LQ_F_DUPLICATE`, `LQ_F_FRAUD`, `LQ_F_DATACENTRE`), `LQ_NFLAGS`, `LQ_FLAGS`.

**Response:** The merged file as an attachment. The merge report is JSON in the `X-Quality-Report` response header (exposed to browsers through CORS):
```json
{
  "survey_id": "coffee_demo",
  "records": 25,
  "tracked": 25,
  "matched": 24,
  "unmatched": 1,
  "flagged": 5,
  "bots": 2,
  "match_columns": ["QOS_SESSION", "QOS_RESPONDENT", "uuid"],
  "variables": ["LQ_MATCHED", "LQ_STATUS", "..."],
  "merged_at": "2026-11-26T10:00:00+00:00",
  "message": "Added live quality flags for 24 of 25 tracked records (5 flagged, 2 bots) as LQ_ variables. ..."
}
```

**Errors:**
- `413`: File over 50 MB
- `422`: Invalid survey id, unsupported file type, empty file, no live quality results for the survey yet, or a file with no `QOS_SESSION`, `QOS_RESPONDENT` or `uuid` values to match on
- `500`: The results could not be built

---

## Settings APIs

A setting saved here overrides the environment variable of the same name. A change applies at once on the instance that saved it; every instance re-reads saved settings every 30 seconds. Removing a saved value goes back to the environment value. Secret values are encrypted at rest and never returned.

Editable keys: `DECIPHER_API_KEY`, `DECIPHER_API_BASE`, `DECIPHER_COMPANY`, `QUALTRICS_API_TOKEN`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `TRACKER_API_BASE`, `TRACKING_TOKEN_SECRET`, `DETECTION_THRESHOLD` (0.3 to 0.99, default 0.7; the threshold the detection engine uses for the stored verdict of new analyses).

**Admin token:** `POST /settings/check` and `PUT /settings` need the header `X-Admin-Token` to match the `ADMIN_TOKEN` environment variable. `ADMIN_TOKEN` can only be set in the environment.
- `ADMIN_TOKEN` not set: settings are read-only and these endpoints return `403`.
- Header missing or wrong: `401`.

### 1. Get Settings
```http
GET /settings
```

**Description:** Every editable setting with its source. No token needed. Secrets only say whether they are set and where the value comes from.

**Response (shortened):**
```json
{
  "settings": [
    {
      "key": "DECIPHER_API_KEY",
      "label": "Decipher API key",
      "group": "Decipher",
      "kind": "secret",
      "help": "REST API key used for Upload to Decipher. Sent only to Decipher.",
      "placeholder": null,
      "minimum": null,
      "maximum": null,
      "is_set": true,
      "source": "saved",
      "value": null,
      "environment_value": null
    },
    {
      "key": "DETECTION_THRESHOLD",
      "label": "Bot threshold",
      "group": "Detection",
      "kind": "number",
      "help": "...",
      "placeholder": "0.7",
      "minimum": 0.3,
      "maximum": 0.99,
      "is_set": true,
      "source": "environment",
      "value": 0.7,
      "environment_value": 0.7
    }
  ],
  "editable": true,
  "refresh_seconds": 30
}
```

- `kind`: `secret`, `url`, `text` or `number`. For secrets, `value` and `environment_value` are always `null`.
- `source`: `saved`, `environment` or `not set`.
- `editable`: whether `ADMIN_TOKEN` is set.

### 2. Check Admin Token
```http
POST /settings/check
X-Admin-Token: <token>
```

**Description:** Checks the admin token without changing anything.

**Response:** `{"ok": true}`

**Errors:** `401` wrong or missing token; `403` `ADMIN_TOKEN` not set.

### 3. Save Settings
```http
PUT /settings
X-Admin-Token: <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "changes": {
    "DECIPHER_API_KEY": "new-key-value",
    "TRACKER_API_BASE": null
  }
}
```

A value saves an override; `null` removes the saved value and goes back to the environment. If any value is refused, nothing is saved.

**Response:** The same shape as `GET /settings`, after the change.

**Errors:**
- `401`: Wrong or missing token
- `403`: `ADMIN_TOKEN` not set (read-only)
- `422`: Unknown key, or a value that is not allowed (for example a number out of range, an address that is not https except for localhost, or a secret shorter than 8 characters)

---

## Health & Monitoring

### 1. Health Check
```http
GET /health
```

**Description:** Basic health check endpoint.

**Status:** ✅ **OPERATIONAL** - Production endpoint active

**Response:**
```json
{
  "status": "healthy",
  "service": "bot-detection-api"
}
```

**Example Usage:**
```bash
# Production
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/health"
```

### 2. Metrics
```http
GET /metrics
```

**Description:** Prometheus-compatible metrics endpoint.

**Status:** ✅ **OPERATIONAL** - Production endpoint active

**Response:**
```
# HELP python_gc_objects_collected_total Objects collected during gc
# TYPE python_gc_objects_collected_total counter
python_gc_objects_collected_total{generation="0"} 5802.0
python_gc_objects_collected_total{generation="1"} 10668.0
python_gc_objects_collected_total{generation="2"} 1600.0

# HELP python_info Python platform information
# TYPE python_info gauge
python_info{implementation="CPython",major="3",minor="11",patchlevel="13",version="3.11.13"} 1.0

# HELP process_virtual_memory_bytes Virtual memory size in bytes.
# TYPE process_virtual_memory_bytes gauge
process_virtual_memory_bytes 2.08560128e+08

# HELP process_resident_memory_bytes Resident memory size in bytes.
# TYPE process_resident_memory_bytes gauge
process_resident_memory_bytes 9.762816e+07

# HELP process_cpu_seconds_total Total user and system CPU time spent in seconds.
# TYPE process_cpu_seconds_total counter
process_cpu_seconds_total 2.95
```

**Example Usage:**
```bash
# Production
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/metrics"
```

---

## Error Handling

### HTTP Status Codes
- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Admin token missing or wrong (settings)
- `403 Forbidden`: Settings are read-only because `ADMIN_TOKEN` is not set
- `404 Not Found`: Resource not found
- `413 Payload Too Large`: Uploaded file over the limit (5 MB survey XML, 50 MB data file)
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error
- `502 Bad Gateway`: Decipher returned an error
- `503 Service Unavailable`: Decipher upload is not configured

### Error Response Format
Errors use FastAPI's standard format, with a plain-English message in `detail`:
```json
{
  "detail": "Session not found"
}
```

Request validation errors (`422`) return `detail` as a list of field errors. Decipher upload errors return `detail` as an object with `message`, `errors`, `survey_path` and `survey_url` (see [Upload a Tracked Survey to Decipher](#3-upload-a-tracked-survey-to-decipher)).

---

## Integration Guides

### Qualtrics Integration

#### 1. Setup Webhook in Qualtrics
1. Log into your Qualtrics account
2. Navigate to your survey
3. Go to Survey Flow
4. Add a Web Service element
5. Configure the webhook URL: `http://your-domain.com/api/v1/integrations/webhooks/qualtrics`
6. Set the method to POST
7. Configure the payload to include bot detection session ID

#### 2. Embed Bot Detection in Survey
Add this JavaScript to your Qualtrics survey:

```javascript
// Initialize bot detection
const surveyId = '{{e://Field/surveyId}}'; // Qualtrics survey ID
const respondentId = '{{e://Field/respondentId}}'; // Qualtrics respondent ID
const sessionId = '{{e://Field/sessionId}}'; // Qualtrics embedded data
const apiBaseUrl = 'https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1';

// Create session with survey metadata
async function createSession() {
  const response = await fetch(`${apiBaseUrl}/detection/sessions?survey_id=${surveyId}&respondent_id=${respondentId}&platform=qualtrics`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  });
  const data = await response.json();
  return data.session_id;
}

// Send events to bot detection API
function sendEvent(eventData) {
  fetch(`${apiBaseUrl}/detection/sessions/${sessionId}/events`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify([eventData])
  });
}

// Track keystrokes
document.addEventListener('keydown', (e) => {
  sendEvent({
    event_type: 'keystroke',
    timestamp: new Date().toISOString(),
    key: e.key,
    element_id: e.target.id,
    key_code: e.keyCode
  });
});

// Track mouse movements
document.addEventListener('mousemove', (e) => {
  sendEvent({
    event_type: 'mouse_move',
    timestamp: new Date().toISOString(),
    x: e.clientX,
    y: e.clientY
  });
});
```

#### 3. Environment Configuration
```env
QUALTRICS_API_TOKEN=your_qualtrics_api_token
BASE_URL=http://your-domain.com
```

### Decipher Integration

#### 1. Setup Webhook in Decipher
1. Log into your Decipher account
2. Navigate to your survey
3. Go to Survey Settings > Webhooks
4. Add a new webhook
5. Set the URL: `http://your-domain.com/api/v1/integrations/webhooks/decipher`
6. Select events: `response.completed`
7. Configure the payload format

#### 2. Embed Bot Detection in Survey
Add this JavaScript to your Decipher survey:

```javascript
// Initialize bot detection
const surveyId = getIdentifierValue('survey_id'); // Decipher survey ID
const respondentId = getIdentifierValue('respondent_id'); // Decipher respondent ID
const apiBaseUrl = 'https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1';

// Create session with survey metadata
async function createSession() {
  const response = await fetch(`${apiBaseUrl}/detection/sessions?survey_id=${surveyId}&respondent_id=${respondentId}&platform=decipher`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  });
  const data = await response.json();
  return data.session_id;
}

// Send events to bot detection API
function sendEvent(eventData) {
  const sessionId = document.getElementById('bot_session_id')?.value;
  if (!sessionId) return;
  
  fetch(`${apiBaseUrl}/detection/sessions/${sessionId}/events`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify([eventData])
  });
}

// Track user interactions
document.addEventListener('keydown', (e) => {
  sendEvent({
    event_type: 'keystroke',
    timestamp: new Date().toISOString(),
    key: e.key,
    element_id: e.target.id
  });
});

document.addEventListener('mousemove', (e) => {
  sendEvent({
    event_type: 'mouse_move',
    timestamp: new Date().toISOString(),
    x: e.clientX,
    y: e.clientY
  });
});
```

#### 3. Environment Configuration
```env
DECIPHER_API_KEY=your_decipher_api_key
BASE_URL=http://your-domain.com
```

---

## Client SDKs

### Python SDK

#### Installation
```bash
pip install bot-detection-client
```

#### Usage
```python
from bot_detection_client import BotDetectionClient

# Initialize client
client = BotDetectionClient(base_url="https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1")

# Create session (basic)
session = await client.create_session()
session_id = session['session_id']

# Create session with survey metadata
session = await client.create_session(
    survey_id="SV_1234567890abcdef",
    respondent_id="RSP_1234567890abcdef",
    platform="qualtrics"
)
session_id = session['session_id']

# Send events
events = [
    {
        "event_type": "keystroke",
        "timestamp": "2025-06-29T00:15:30.000Z",
        "key": "a",
        "element_id": "input-1"
    }
]
await client.send_events(session_id, events)

# Analyze session
result = await client.analyze_session(session_id)
print(f"Is bot: {result['is_bot']}")
print(f"Confidence: {result['confidence_score']}")
```

### JavaScript SDK

#### Installation
```bash
npm install bot-detection-client
```

#### Usage
```javascript
import { BotDetectionClient } from 'bot-detection-client';

// Initialize client
const client = new BotDetectionClient({
  baseUrl: 'https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1'
});

// Create session (basic)
const session = await client.createSession();
const sessionId = session.session_id;

// Create session with survey metadata
const session = await client.createSession({
  survey_id: 'SV_1234567890abcdef',
  respondent_id: 'RSP_1234567890abcdef',
  platform: 'qualtrics'
});
const sessionId = session.session_id;

// Send events
const events = [
  {
    event_type: 'keystroke',
    timestamp: new Date().toISOString(),
    key: 'a',
    element_id: 'input-1'
  }
];
await client.sendEvents(sessionId, events);

// Analyze session
const result = await client.analyzeSession(sessionId);
console.log(`Is bot: ${result.is_bot}`);
console.log(`Confidence: ${result.confidence_score}`);
```

---

## Frontend Integration

### React Dashboard

The system includes a comprehensive React-based dashboard for monitoring and management:

#### Key Features
- **Live results**: Overview, Live Quality and Sessions refresh while open
- **Integration status**: Webhook URLs and whether each platform is configured
- **API Playground**: Interactive API testing interface
- **Quick Start Guide**: Step-by-step integration instructions
- **Settings**: Saves keys and options behind the admin token
- **Toast Notifications**: User feedback and alerts

#### Dashboard Components
- **layout/AppShell.jsx**: Sidebar (phone: top bar and menu) and service status
- **Overview.jsx**: Home page: last 7 days, surveys with bot rate, starts and bots per day, latest bots
- **LiveQuality.jsx** and **quality/**: One survey's live results, quality rules, data-file merge
- **SessionList.jsx** and **SessionDetails.jsx**: Sessions with verdicts, and one session's verdict, reasons and evidence
- **SurveyTracking.jsx**: Add tracking to a Decipher survey XML and upload it
- **Integrations.jsx**, **Settings.jsx**, **ApiPlayground.jsx**, **QuickStartGuide.jsx**, **ReportBuilder.jsx**, **TextAnalysis.jsx**

#### Usage
```javascript
// Access the dashboard at http://localhost:3000
// Navigate between different sections using the navigation menu
// Use the API playground to test endpoints interactively
// Check integration status and webhook URLs on Integrations
```

---

## Rate Limits & Best Practices

### Rate Limits
- **Sessions**: 100 requests per minute
- **Events**: 1000 events per minute per session
- **Analysis**: 50 requests per minute per session
- **Webhooks**: 100 requests per minute

### Best Practices

#### 1. Event Collection
- Send events in batches (10-50 events per request)
- Include accurate timestamps
- Provide meaningful element IDs
- Collect diverse event types for better analysis

#### 2. Session Management
- Create sessions early in user journey
- Monitor session status regularly
- Clean up expired sessions
- Use session IDs consistently across integrations

#### 3. Error Handling
- Implement exponential backoff for retries
- Log all API interactions
- Handle network timeouts gracefully
- Validate responses before processing

#### 4. Security
- Use HTTPS in production
- Validate webhook signatures
- Implement proper authentication
- Sanitize all input data

#### 5. Performance
- Use connection pooling
- Implement caching where appropriate
- Monitor API response times
- Optimize event payload size

### Monitoring & Alerts
- Monitor API response times
- Track error rates
- Set up alerts for high bot detection rates
- Monitor webhook delivery success rates

---

## Support & Resources

### Documentation
- [API Reference](https://docs.botdetection.com/api)
- [Integration Guides](https://docs.botdetection.com/integrations)
- [SDK Documentation](https://docs.botdetection.com/sdks)
- [Frontend Dashboard Guide](https://docs.botdetection.com/dashboard)

### Community
- [GitHub Issues](https://github.com/halderavik/bot_detection_live/issues)
- [Discussions](https://github.com/halderavik/bot_detection_live/discussions)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/bot-detection)

### Contact
- **Email**: support@botdetection.com
- **Slack**: #bot-detection
- **Status Page**: https://status.botdetection.com

---

## Hierarchical API (V2)

The Bot Detection API now includes a hierarchical structure for organizing and accessing data by **Survey → Platform → Respondent → Session**. This enables efficient navigation and aggregation at different levels.

### Key Benefits

- **Hierarchical Navigation**: Navigate through surveys, platforms, respondents, and sessions
- **Aggregated Metrics**: Get aggregated statistics at each hierarchy level
- **Backward Compatibility**: All existing V1 endpoints remain unchanged
- **Efficient Queries**: Composite indexes for fast hierarchical queries
- **Respondent Aggregation**: Summarize all session activities under a respondent
- **Survey Aggregation**: Aggregate all activities and tests under all respondents for a survey

### Hierarchy Structure

```
Survey ID
  └── Platform ID
      └── Respondent ID
          └── Session ID
```

### Survey Level Endpoints

#### List All Surveys
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
      "checked_count": 2400,
      "bot_count": 300,
      "human_count": 2100,
      "bot_rate": 12.5,
      "first_session": "2025-01-01T00:00:00Z",
      "last_session": "2025-01-15T23:59:59Z"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

`checked_count` is the number of sessions that were analysed; `human_count` is `checked_count - bot_count`; `bot_rate` is `bot_count / checked_count x 100`, counting each session once (see [How Bot Numbers Are Counted](#how-bot-numbers-are-counted)).

#### Get Survey Details
```http
GET /surveys/{survey_id}
```

**Description:** Get detailed aggregated metrics for a specific survey.

**Response:**
```json
{
  "survey_id": "SV_1234567890abcdef",
  "total_sessions": 2500,
  "total_respondents": 1250,
  "total_platforms": 2,
  "bot_detection": {
    "total_detections": 2400,
    "bot_count": 300,
    "human_count": 2100,
    "bot_rate": 12.5,
    "avg_confidence": 0.78
  },
  "platform_distribution": {
    "qualtrics": 1500,
    "decipher": 1000
  }
}
```

#### Get Survey Summary
```http
GET /surveys/{survey_id}/summary
```

**Description:** Get survey summary with key metrics.

### Platform Level Endpoints

#### List Platforms
```http
GET /surveys/{survey_id}/platforms
```

**Description:** List all platforms for a survey.

#### Get Platform Details
```http
GET /surveys/{survey_id}/platforms/{platform_id}
```

**Description:** Get platform details with aggregated metrics.

#### Get Platform Summary
```http
GET /surveys/{survey_id}/platforms/{platform_id}/summary
```

**Description:** Get platform summary with key metrics.

### Respondent Level Endpoints

#### List Respondents
```http
GET /surveys/{survey_id}/platforms/{platform_id}/respondents
```

**Description:** List all respondents for a platform.

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
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

In this list `human_count` is `session_count - bot_count`, so sessions that were never analysed count as human. Use the respondent details or summary for checked-based numbers and the bot rate.

#### Get Respondent Details
```http
GET /surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}
```

**Description:** Get respondent details with aggregated metrics across all sessions.

**Response:**
```json
{
  "survey_id": "SV_1234567890abcdef",
  "platform_id": "qualtrics",
  "respondent_id": "RSP_1234567890abcdef",
  "total_sessions": 2,
  "bot_detection": {
    "bot_rate": 0.0,
    "avg_confidence": 0.85,
    "overall_risk": "LOW"
  },
  "text_quality": {
    "avg_quality_score": 75.5,
    "flagged_percentage": 0.0
  },
  "session_timeline": [
    {
      "session_id": "e41c423d-cdfb-4228-bd25-3fee8459e591",
      "created_at": "2025-01-01T00:00:00Z",
      "is_bot": false
    }
  ]
}
```

#### Get Respondent Summary
```http
GET /surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/summary
```

**Description:** Get respondent summary with key metrics aggregated across all sessions.

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
  "session_timeline": [...]
}
```

#### List Respondent Sessions
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

### Session Level Endpoints (Hierarchical Path)

#### Get Session by Hierarchy
```http
GET /surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}
```

**Description:** Get session details via hierarchical path. This endpoint verifies that the session belongs to the specified hierarchy.

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

### Examples

```bash
# List all surveys
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys"

# Get survey details
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/SV_1234567890abcdef"

# List platforms for a survey
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/SV_1234567890abcdef/platforms"

# List respondents for a platform
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/SV_1234567890abcdef/platforms/qualtrics/respondents"

# Get respondent details (aggregates all sessions)
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/SV_1234567890abcdef/platforms/qualtrics/respondents/RSP_1234567890abcdef"

# Get respondent summary
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/SV_1234567890abcdef/platforms/qualtrics/respondents/RSP_1234567890abcdef/summary"

# List all sessions for a respondent
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/SV_1234567890abcdef/platforms/qualtrics/respondents/RSP_1234567890abcdef/sessions"

# Get session via hierarchical path
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/SV_1234567890abcdef/platforms/qualtrics/respondents/RSP_1234567890abcdef/sessions/e41c423d-cdfb-4228-bd25-3fee8459e591"
```

### Documentation

For complete hierarchical API documentation with detailed request/response formats, see [API_V2.md](API_V2.md).

### Migration Guide

The hierarchical API is fully backward compatible. To migrate:

1. **Update Session Creation**: Include `platform_id` parameter when creating sessions (or use `platform` for backward compatibility)
2. **Use Hierarchical Endpoints**: For aggregated views, use new hierarchical endpoints
3. **Update Frontend**: Use `hierarchicalService` methods in `apiService.js`
4. **Database Migration**: The `platform_id` column has been added to the `sessions` table

All existing endpoints continue to work as before.

---

*Last updated: November 2026*

---

## Frontend Deployment & Data Flow Verification

**Status:** ✅ **VERIFIED** (February 2026)

### Deployment Status
- ✅ Frontend successfully built and deployed to Cloud Storage
- ✅ All API endpoints verified returning data from Cloud SQL
- ✅ Data flow verified: Cloud SQL → Backend API → Frontend Dashboard
- ✅ Fraud detection widget integrated and operational

### Verified Endpoints
All 6 frontend-used endpoints tested and working correctly:
1. **Dashboard Overview** (`/api/v1/dashboard/overview`) - ✅ Verified
2. **Fraud Dashboard Summary** (`/api/v1/fraud/dashboard/summary`) - ✅ Verified
3. **Fraud Duplicates** (`/api/v1/fraud/dashboard/duplicates`) - ✅ Verified
4. **Sessions List** (`/api/v1/dashboard/sessions`) - ✅ Verified
5. **Surveys List** (`/api/v1/surveys`) - ✅ Verified
6. **Text Analysis Summary** (`/api/v1/text-analysis/dashboard/summary`) - ✅ Verified

### Sample Data Retrieved
- Sessions: 3 (last 7 days)
- Fraud Analysis: 2 sessions analyzed with average fraud score 0.26
- Surveys: 3 found in database
- Events: 4 total events tracked

### Frontend Configuration
- **API Base URL**: `https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1`
- **Frontend URL**: `https://storage.googleapis.com/bot-detection-frontend-20251208`
- **Configuration File**: `frontend/src/config/config.ts` (centralized config system)

---

## Changelog

### November 2026
- Added Decipher tracking endpoints (`/tracking/decipher`, `/tracking/decipher/upload`, `/tracking/decipher/options`)
- Added Live Quality endpoints (`/quality/surveys`, `/quality/results`, `/quality/export`, `/quality/rules`, `/quality/merge`)
- Added Settings endpoints (`/settings`, `/settings/check`) with the `X-Admin-Token` header
- Bot rate everywhere is bots / checked (analysed) sessions, counting each session once
- `/dashboard/sessions` returns the latest verdict per session; `risk_level`, `is_bot`, `survey_id` and `search` filters work
- `/dashboard/analytics/trends` returns `checked` and `bots` per day, with days aligned to midnight UTC
- `/surveys` returns `checked_count`

### February 2026
- ✅ Frontend deployment verified - All endpoints pulling data correctly from Cloud SQL
- ✅ Data flow verification completed - Cloud SQL → Backend API → Frontend Dashboard
- ✅ Fraud detection widget integrated into main dashboard
- ✅ Updated production URLs in all documentation

### January 2025
- ✅ Added hierarchical API structure (Survey → Platform → Respondent → Session)
- ✅ Added `platform_id` parameter to session creation (backward compatible with `platform`)
- ✅ Added respondent-level endpoints for aggregating all sessions under a respondent
- ✅ Added survey-level aggregation endpoints
- ✅ Database migration completed: `platform_id` column added to `sessions` table
- ✅ All respondent endpoints tested and verified working
- ✅ Updated production base URL to `https://bot-backend-119522247395.northamerica-northeast2.run.app` 