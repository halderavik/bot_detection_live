# Bot Detection API Documentation

## Table of Contents
1. [Overview](#overview)
2. [Base URL & Authentication](#base-url--authentication)
3. [Core API Endpoints](#core-api-endpoints)
4. [Text Quality Analysis APIs](#text-quality-analysis-apis)
5. [Integration APIs](#integration-apis)
6. [Dashboard APIs](#dashboard-apis)
7. [Health & Monitoring](#health--monitoring)
8. [Error Handling](#error-handling)
9. [Integration Guides](#integration-guides)
10. [Client SDKs](#client-sdks)
11. [Rate Limits & Best Practices](#rate-limits--best-practices)
12. [Frontend Integration](#frontend-integration)
13. [Hierarchical API (V2)](#hierarchical-api-v2)

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
Currently, the API uses basic authentication. In production, this should be replaced with JWT tokens or API keys.

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

### 1. Dashboard Overview
```http
GET /dashboard/overview
```

**Description:** Returns high-level statistics and metrics.

**Response:**
```json
{
  "total_sessions": 1250,
  "active_sessions": 45,
  "bot_detection_rate": 0.12,
  "average_confidence": 0.78,
  "total_events": 125000,
  "platforms": {
    "qualtrics": 850,
    "decipher": 400
  },
  "risk_distribution": {
    "low": 1050,
    "medium": 150,
    "high": 50
  }
}
```

### 2. Session List
```http
GET /dashboard/sessions
```

**Description:** Returns a paginated list of sessions.

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20)
- `status`: Filter by status (active, completed, expired)
- `platform`: Filter by platform (qualtrics, decipher)
- `risk_level`: Filter by risk level (low, medium, high)

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "e41c423d-cdfb-4228-bd25-3fee8459e591",
      "created_at": "2025-06-29T00:10:01.707621+00:00",
      "status": "active",
      "platform": "qualtrics",
      "event_count": 150,
      "latest_detection": {
        "is_bot": false,
        "confidence_score": 0.85,
        "risk_level": "LOW"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1250,
    "pages": 63
  }
}
```

### 3. Session Details
```http
GET /dashboard/sessions/{session_id}/details
```

**Description:** Returns detailed information about a specific session.

**Response:**
```json
{
  "session_id": "e41c423d-cdfb-4228-bd25-3fee8459e591",
  "created_at": "2025-06-29T00:10:01.707621+00:00",
  "status": "active",
  "platform": "qualtrics",
  "survey_id": "SV_1234567890abcdef",
  "respondent_id": "RSP_1234567890abcdef",
  "event_count": 150,
  "last_event_at": "2025-06-29T00:15:30.000Z",
  "detection_history": [
    {
      "is_bot": false,
      "confidence_score": 0.85,
      "risk_level": "LOW",
      "created_at": "2025-06-29T00:15:30.000Z"
    }
  ],
  "event_summary": {
    "keystrokes": 45,
    "mouse_moves": 80,
    "clicks": 15,
    "focus_events": 10
  }
}
```

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
- `401 Unauthorized`: Authentication required
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid event data",
    "details": {
      "field": "event_type",
      "issue": "Required field missing"
    }
  }
}
```

### Common Error Codes
- `SESSION_NOT_FOUND`: Session does not exist
- `INSUFFICIENT_DATA`: Not enough events for analysis
- `INVALID_EVENT_TYPE`: Unsupported event type
- `WEBHOOK_SIGNATURE_INVALID`: Invalid webhook signature
- `INTEGRATION_ERROR`: External service error

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
- **Real-time Updates**: Live session monitoring and analysis results
- **Integration Management**: Webhook testing and status monitoring
- **API Playground**: Interactive API testing interface
- **Quick Start Guide**: Step-by-step integration instructions
- **Settings Interface**: System configuration management
- **Toast Notifications**: User feedback and alerts

#### Dashboard Components
- **Dashboard.jsx**: Main dashboard with charts and statistics
- **Integrations.jsx**: Integration management and webhook testing
- **Settings.jsx**: System configuration and settings
- **ApiPlayground.jsx**: Interactive API testing interface
- **QuickStartGuide.jsx**: Getting started guide
- **SessionDetails.jsx**: Detailed session analysis view

#### Usage
```javascript
// Access the dashboard at http://localhost:3000
// Navigate between different sections using the navigation menu
// Use the API playground to test endpoints interactively
// Monitor integrations and test webhooks in real-time
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
      "bot_count": 300,
      "human_count": 2200,
      "bot_rate": 12.0
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

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
    "bot_rate": 12.0,
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
      "bot_rate": 0.0,
      "avg_confidence": 0.85
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

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

*Last updated: February 2026*

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