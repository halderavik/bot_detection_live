# Bot Detection API Documentation

## Table of Contents
1. [Overview](#overview)
2. [Base URL & Authentication](#base-url--authentication)
3. [Core API Endpoints](#core-api-endpoints)
4. [Integration APIs](#integration-apis)
5. [Dashboard APIs](#dashboard-apis)
6. [Health & Monitoring](#health--monitoring)
7. [Error Handling](#error-handling)
8. [Integration Guides](#integration-guides)
9. [Client SDKs](#client-sdks)
10. [Rate Limits & Best Practices](#rate-limits--best-practices)
11. [Frontend Integration](#frontend-integration)

---

## Overview

The Bot Detection API provides comprehensive bot detection capabilities through behavioral analysis, survey platform integration, and real-time monitoring. The API is built with FastAPI and supports both synchronous and asynchronous operations.

### Key Features
- **Session Management**: Create and manage bot detection sessions
- **Event Collection**: Ingest behavioral events (keystrokes, mouse movements, etc.)
- **Real-time Analysis**: Perform bot detection analysis with confidence scoring
- **Survey Integration**: Seamless integration with Qualtrics and Decipher
- **Dashboard Analytics**: Comprehensive monitoring and reporting
- **Client SDKs**: Python and JavaScript libraries for easy integration
- **Frontend Dashboard**: Complete React-based monitoring interface
- **Integration Management**: Webhook testing and status monitoring

---

## Base URL & Authentication

### Base URL
```
http://localhost:8000/api/v1
```

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

**Request Body:** Empty or `{}`

**Response:**
```json
{
  "session_id": "e41c423d-cdfb-4228-bd25-3fee8459e591",
  "created_at": "2025-06-29T00:10:01.707621+00:00",
  "status": "active"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/detection/sessions" \
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
    "webhook_url": "http://localhost:8000/api/v1/integrations/webhooks/qualtrics"
  },
  "decipher": {
    "status": "connected",
    "api_key_configured": true,
    "webhook_url": "http://localhost:8000/api/v1/integrations/webhooks/decipher"
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

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-29T00:15:30.000Z",
  "version": "1.0.0"
}
```

### 2. Metrics
```http
GET /metrics
```

**Description:** Prometheus-compatible metrics endpoint.

**Response:**
```
# HELP bot_detection_sessions_total Total number of sessions
# TYPE bot_detection_sessions_total counter
bot_detection_sessions_total 1250

# HELP bot_detection_events_total Total number of events
# TYPE bot_detection_events_total counter
bot_detection_events_total 125000

# HELP bot_detection_analysis_duration_seconds Analysis duration in seconds
# TYPE bot_detection_analysis_duration_seconds histogram
bot_detection_analysis_duration_seconds_bucket{le="0.1"} 850
bot_detection_analysis_duration_seconds_bucket{le="0.5"} 1200
bot_detection_analysis_duration_seconds_bucket{le="1.0"} 1250
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
const sessionId = '{{e://Field/sessionId}}'; // Qualtrics embedded data
const apiBaseUrl = 'http://localhost:8000/api/v1';

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
const sessionId = '${sessionId}'; // Decipher system variable
const apiBaseUrl = 'http://localhost:8000/api/v1';

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
client = BotDetectionClient(base_url="http://localhost:8000/api/v1")

# Create session
session = await client.create_session()
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
  baseUrl: 'http://localhost:8000/api/v1'
});

// Create session
const session = await client.createSession();
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

*Last updated: June 29, 2025* 