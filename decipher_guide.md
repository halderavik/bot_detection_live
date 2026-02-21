# Decipher Integration Guide (Survey Programmers)

This guide shows step-by-step how to integrate Bot Detection into a Decipher (Forsta/FocusVision) survey. You will: create a session, collect behavior events during the survey, trigger analysis on completion, and optionally receive results via webhook.

## Production System Status
✅ **FULLY OPERATIONAL** - All endpoints verified and working
- **API Base URL**: `https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1`
- **Frontend Dashboard**: `https://storage.googleapis.com/bot-detection-frontend-20251208/index.html`
- **Health Check**: https://bot-backend-119522247395.northamerica-northeast2.run.app/health
- **Metrics**: https://bot-backend-119522247395.northamerica-northeast2.run.app/metrics
- **API Documentation**: https://bot-backend-119522247395.northamerica-northeast2.run.app/docs
- **Database**: Connected and processing requests
- **Analysis Pipeline**: End-to-end testing completed successfully
- **Hierarchical API**: Survey → Platform → Respondent → Session structure available
- **OpenAI Integration**: GPT-4o-mini service fully operational ✅ (`openai_available: true`)
- **Hierarchical Text Analysis**: New V2 endpoints for text analysis at survey/platform/respondent/session levels ✅
- **Grid & Timing Analysis**: Stage 2 detection features deployed with hierarchical endpoints ✅
- **API Playground**: Updated with hierarchical V2 text analysis endpoints ✅ (flat session-level text analysis endpoints are still supported)

Note: Replace example IDs/variables with those from your study. All examples use HTTPS and JSON.

---

## 1) Prerequisites

- Decipher survey access with permission to add custom JavaScript and webhooks
- Backend API reachable from respondents (no corporate firewall blocks)
- If using webhooks: a Decipher project with webhook support enabled

---

## 2) Create a Bot Detection Session (Survey Start)

Create a session when the respondent starts your survey. Store the returned `session_id` in a Decipher variable (e.g., `session_id`). You can do this in a pre-load script on your first page or a custom initialization question.

**Recommended:** Include `survey_id`, `respondent_id`, and `platform_id` parameters for hierarchical tracking and aggregation.

Example (custom JavaScript, runs once at start):

```javascript
const API_BASE = 'https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1';

// Get survey identifiers from Decipher
const surveyId = getIdentifierValue('survey_id') || 'decipher_survey_123';
const respondentId = getIdentifierValue('respondent_id') || 'resp_' + Date.now();
const platformId = 'decipher'; // Platform identifier

async function createBotSession() {
  // Create session with survey metadata for hierarchical tracking
  const url = `${API_BASE}/detection/sessions?survey_id=${encodeURIComponent(surveyId)}&respondent_id=${encodeURIComponent(respondentId)}&platform_id=${encodeURIComponent(platformId)}`;
  const resp = await fetch(url, { method: 'POST' });
  const data = await resp.json();
  // Save session_id to a hidden question or Decipher variable
  // Example: write to a hidden input with id "session_id"
  document.getElementById('session_id').value = data.session_id;
}

createBotSession().catch(console.error);
```

**Note:** The `platform_id` parameter enables hierarchical data access. You can later query aggregated metrics at the survey, platform, and respondent levels using the hierarchical API endpoints.

Hidden question HTML example (Decipher page):

```html
<input type="hidden" id="session_id" name="session_id" value="">
```

---

## 3) Add the Event Tracker (During Survey)

Capture keystrokes, mouse, focus/blur, scroll, and device info. Send batched events to the API to minimize network overhead.

```javascript
const API_BASE = 'https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1';
const BATCH_SIZE = 20;
const FLUSH_MS = 3000;

let eventBuffer = [];
let flushTimer = null;

function getSessionId() {
  const el = document.getElementById('session_id');
  return el ? el.value : null;
}

function queueEvent(evt) {
  eventBuffer.push(evt);
  if (eventBuffer.length >= BATCH_SIZE) {
    flushEvents();
  } else if (!flushTimer) {
    flushTimer = setTimeout(flushEvents, FLUSH_MS);
  }
}

async function flushEvents() {
  clearTimeout(flushTimer);
  flushTimer = null;
  if (eventBuffer.length === 0) return;

  const sessionId = getSessionId();
  if (!sessionId) return; // not ready yet

  const payload = eventBuffer.slice();
  eventBuffer = [];

  try {
    await fetch(`${API_BASE}/detection/sessions/${sessionId}/events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  } catch (e) {
    // On failure, re-queue once to avoid data loss
    eventBuffer = payload.concat(eventBuffer);
  }
}

// Keystrokes
document.addEventListener('keydown', (e) => {
  queueEvent({
    event_type: 'keystroke',
    timestamp: new Date().toISOString(),
    key: e.key,
    key_code: e.keyCode,
    element_id: e.target && e.target.id
  });
});

// Mouse movement (throttled)
let lastMouseTs = 0;
document.addEventListener('mousemove', (e) => {
  const now = Date.now();
  if (now - lastMouseTs < 100) return; // throttle 10/s
  lastMouseTs = now;
  queueEvent({
    event_type: 'mouse_move',
    timestamp: new Date().toISOString(),
    x: e.clientX,
    y: e.clientY
  });
});

// Scroll (throttled)
let lastScrollTs = 0;
document.addEventListener('scroll', () => {
  const now = Date.now();
  if (now - lastScrollTs < 200) return;
  lastScrollTs = now;
  queueEvent({
    event_type: 'scroll',
    timestamp: new Date().toISOString(),
    delta_y: window.scrollY
  });
}, { passive: true });

// Focus/Blur
document.addEventListener('focusin', (e) => {
  queueEvent({
    event_type: 'focus',
    timestamp: new Date().toISOString(),
    element_id: e.target && e.target.id
  });
});
document.addEventListener('focusout', (e) => {
  queueEvent({
    event_type: 'blur',
    timestamp: new Date().toISOString(),
    element_id: e.target && e.target.id
  });
});

// Device info (once)
queueEvent({
  event_type: 'device_info',
  timestamp: new Date().toISOString(),
  screen_width: window.screen.width,
  screen_height: window.screen.height,
  user_agent: navigator.userAgent
});

// Ensure buffer is flushed before page unload
window.addEventListener('beforeunload', () => { flushEvents(); });
```

Place the above on a shared header template or relevant pages to ensure coverage across the study.

---

## 3b) Grid/Matrix Question Capture (Optional)

To enable **grid/matrix analysis** (straight-lining, response patterns, variance), capture grid questions as follows.

**1. Register the grid when it is shown**  
Call `POST /text-analysis/questions` once per grid with `question_type: 'grid'` or `'matrix'`. Store the returned `question_id` (e.g. in a variable keyed by your Decipher question/variable name).

**2. When the respondent has completed the grid** (e.g. on "Next" or page leave), collect each selected value (one per cell) and send **one** `POST /text-analysis/responses` **per cell** with that same `question_id`, `response_text` = the cell value (e.g. `"1"`, `"5"`), and optionally `response_time_ms` for the grid.

Example – register grid question:

```javascript
async function registerGridQuestion(questionText, elementId) {
  const sessionId = document.getElementById('session_id')?.value; // or bot_session_id
  if (!sessionId) return null;
  const resp = await fetch(`${API_BASE}/text-analysis/questions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      question_text: questionText || 'Grid question',
      question_type: 'grid',
      element_id: elementId || '',
      page_url: window.location.href,
      page_title: document.title
    })
  });
  const data = await resp.json();
  return data.question_id;
}
```

Example – send grid cell values (one request per cell):

```javascript
async function sendGridResponses(questionId, responseTimeMs, cellValues) {
  const sessionId = document.getElementById('session_id')?.value;
  if (!sessionId || !questionId || !cellValues?.length) return;
  for (const value of cellValues) {
    await fetch(`${API_BASE}/text-analysis/responses`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        question_id: questionId,
        response_text: String(value),
        response_time_ms: responseTimeMs || null
      })
    });
  }
}
```

Get `cellValues` from your grid DOM (e.g. collect each selected input/radio value in row order) or from Decipher’s JS API if available. Grid analysis runs when you call the composite-analyze endpoint on completion (see section 4).

---

## 4) Trigger Analysis (On Completion)

On the final page or submit event, call the analysis endpoint. **Recommended:** use **composite-analyze**, which combines behavioral, text quality, fraud, grid, and timing analysis. You can also check readiness first via `ready-for-analysis`.

**Composite analyze (recommended)** – includes behavioral + text quality + fraud + grid + timing:

```javascript
async function analyzeSession() {
  const sessionId = document.getElementById('session_id').value; // or bot_session_id
  if (!sessionId) return;

  // Optional: ensure session is ready for analysis
  const readyResp = await fetch(`${API_BASE}/detection/sessions/${sessionId}/ready-for-analysis`);
  const ready = await readyResp.json();
  if (!ready.is_ready) {
    await flushEvents();
  }

  // Composite analyze: behavioral + text quality + fraud + grid + timing
  const resp = await fetch(`${API_BASE}/detection/sessions/${sessionId}/composite-analyze`, {
    method: 'POST'
  });
  const result = await resp.json();
  document.getElementById('bot_result').value = JSON.stringify(result);
  // Optional: save is_bot, composite_score, etc. to separate hidden fields
}

// Call analyzeSession on final submit / thank-you page
```

**Behavioral-only analyze** – if you only need keystroke/mouse/scroll analysis:

```javascript
const resp = await fetch(`${API_BASE}/detection/sessions/${sessionId}/analyze`, { method: 'POST' });
const result = await resp.json();
```

Hidden field for storing results:

```html
<input type="hidden" id="bot_result" name="bot_result" value="">
```

---

## 5) Optional: Webhook Delivery to Decipher Endpoint

If you prefer server-to-server delivery, configure a webhook to your integration endpoint.

- Endpoint (example): `https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/integrations/webhooks/decipher`
- Payload contains `session_id`, survey identifiers, and the analysis result.

Example server-to-server POST (what our API expects):

```json
{
  "session_id": "<SESSION_ID>",
  "survey_id": "<DECIPHER_SURVEY_ID>",
  "respondent_id": "<RESPONDENT_ID>",
  "bot_detection_result": {
    "is_bot": false,
    "confidence_score": 0.82,
    "risk_level": "low",
    "method_scores": { "keystroke_analysis": 0.9 }
  }
}
```

Coordinate with your Decipher project admin to set the webhook call on completion.

---

## 6) QA / Smoke Tests

Use curl to verify the backend (all endpoints verified operational):

```bash
# Health Check ✅ VERIFIED
curl -s https://bot-backend-119522247395.northamerica-northeast2.run.app/health
# Response: {"status":"healthy","service":"bot-detection-api"}

# Metrics Endpoint ✅ VERIFIED
curl -s https://bot-backend-119522247395.northamerica-northeast2.run.app/metrics
# Response: Prometheus-compatible metrics

# Create session (basic) ✅ VERIFIED
curl -s -X POST \
  https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/detection/sessions
# Response: {"session_id":"uuid","created_at":"timestamp","status":"active"}

# Create session with survey metadata (recommended) ✅ VERIFIED
curl -s -X POST \
  "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/detection/sessions?survey_id=decipher_survey_123&respondent_id=resp_789&platform_id=decipher"
# Response: {"session_id":"uuid","created_at":"timestamp","status":"active"}

# Ingest example events ✅ VERIFIED
curl -s -X POST \
  https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/detection/sessions/<SESSION_ID>/events \
  -H "Content-Type: application/json" \
  -d '[{"event_type":"keystroke","timestamp":"2025-01-01T00:00:00Z","key":"a","element_id":"q1"}]'
# Response: {"session_id":"uuid","events_processed":1,"total_events":1,"status":"success"}

# Analyze session (behavioral only) ✅ VERIFIED
curl -s -X POST \
  https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/detection/sessions/<SESSION_ID>/analyze
# Response: {"session_id":"uuid","is_bot":false,"confidence_score":0.25,"risk_level":"high",...}

# Composite analyze (behavioral + text + fraud + grid + timing) ✅ VERIFIED
curl -s -X POST \
  https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/detection/sessions/<SESSION_ID>/composite-analyze
# Response: composite_score, is_bot, text_quality_score, fraud_score, etc.

# Ready for analysis check ✅ VERIFIED
curl -s -X GET \
  https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/detection/sessions/<SESSION_ID>/ready-for-analysis
# Response: {"is_ready": true/false, ...}

# Get respondent details (hierarchical API) ✅ VERIFIED
curl -s -X GET \
  "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/decipher_survey_123/platforms/decipher/respondents/resp_789"
# Response: Aggregated metrics across all sessions for this respondent

# Get text analysis summary (hierarchical V2) ✅ VERIFIED
curl -s -X GET \
  "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/decipher_survey_123/text-analysis/summary"
# Response: Text quality summary aggregated at survey level

# Get text analysis health ✅ VERIFIED
curl -s -X GET \
  https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/text-analysis/health
# Response: {"status":"healthy","openai_available":true,"model":"gpt-4o-mini",...}

# Grid analysis summary (hierarchical) ✅ VERIFIED
curl -s -X GET \
  "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/decipher_survey_123/grid-analysis/summary"
# Response: straight_lined_count, pattern_distribution, avg_variance_score, etc.

# Timing analysis summary (hierarchical) ✅ VERIFIED
curl -s -X GET \
  "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/decipher_survey_123/timing-analysis/summary"
# Response: speeder_count, flatliner_count, timing metrics by level

# Fraud summary (hierarchical) ✅ VERIFIED
curl -s -X GET \
  "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/decipher_survey_123/fraud/summary"
# Response: average_fraud_score, fraud_methods, duplicate counts, etc.
```

---

## 7) Troubleshooting

- Blank page or no events: ensure the tracker script loads on each survey page and `session_id` is populated before events are flushed.
- 403/401 errors: confirm the API URL is correct and reachable; check corporate proxy rules.
- CORS errors in console: our backend allows public requests; if using a custom domain, ensure CORS origins include your domain.
- Large respondents: increase `BATCH_SIZE` or lower throttle for high-interaction pages.

---

## 8) Security & Privacy Notes

- Do not capture PII in raw events. Only capture interaction metadata needed for behavioral analysis.
- Transport is HTTPS; data at rest is stored in Cloud SQL.
- If you need to disable specific event types for a page (e.g., open-ended PII), wrap listeners with page-level guards.

---

## 9) Hierarchical API Access

With `platform_id` included in session creation, you can access aggregated data through the hierarchical API:

### Get Respondent Summary
Aggregate all sessions for a respondent:
```javascript
const surveyId = 'decipher_survey_123';
const platformId = 'decipher';
const respondentId = 'resp_789';

const url = `${API_BASE}/surveys/${surveyId}/platforms/${platformId}/respondents/${respondentId}/summary`;
const response = await fetch(url);
const summary = await response.json();
// Returns: total_sessions, bot_rate, avg_confidence, overall_risk, etc.
```

### List All Sessions for a Respondent
```javascript
const url = `${API_BASE}/surveys/${surveyId}/platforms/${platformId}/respondents/${respondentId}/sessions`;
const response = await fetch(url);
const sessions = await response.json();
// Returns: Array of all sessions with detection results
```

### Get Survey-Level Aggregation
```javascript
const url = `${API_BASE}/surveys/${surveyId}`;
const response = await fetch(url);
const surveyData = await response.json();
// Returns: Aggregated metrics for entire survey across all platforms and respondents
```

### Get Text Analysis Summary (Hierarchical V2)
Access text quality analysis at different hierarchy levels.

**Good to know:**
- If you only have a `session_id`, you can use the **flat** session summary endpoint: `GET /api/v1/text-analysis/sessions/{sessionId}/summary`
- If you have `survey_id`/`platform_id`/`respondent_id`, use the **hierarchical** V2 endpoints below for aggregated views.

```javascript
// Session-level text analysis summary (flat; requires only sessionId)
const flatSessionSummaryUrl = `${API_BASE}/text-analysis/sessions/${sessionId}/summary`;
const flatSessionSummaryResp = await fetch(flatSessionSummaryUrl);
const flatSessionSummary = await flatSessionSummaryResp.json();
// Returns: session-level text quality summary

// Survey-level text analysis summary
const surveyTextUrl = `${API_BASE}/surveys/${surveyId}/text-analysis/summary`;
const surveyTextResponse = await fetch(surveyTextUrl);
const surveyTextData = await surveyTextResponse.json();
// Returns: Aggregated text quality metrics for entire survey

// Platform-level text analysis summary
const platformTextUrl = `${API_BASE}/surveys/${surveyId}/platforms/${platformId}/text-analysis/summary`;
const platformTextResponse = await fetch(platformTextUrl);
const platformTextData = await platformTextResponse.json();
// Returns: Aggregated text quality metrics for platform within survey

// Respondent-level text analysis summary
const respondentTextUrl = `${API_BASE}/surveys/${surveyId}/platforms/${platformId}/respondents/${respondentId}/text-analysis/summary`;
const respondentTextResponse = await fetch(respondentTextUrl);
const respondentTextData = await respondentTextResponse.json();
// Returns: Aggregated text quality metrics for respondent

// Session-level text analysis (hierarchical V2)
const sessionTextUrl = `${API_BASE}/surveys/${surveyId}/platforms/${platformId}/respondents/${respondentId}/sessions/${sessionId}/text-analysis`;
const sessionTextResponse = await fetch(sessionTextUrl);
const sessionTextData = await sessionTextResponse.json();
// Returns: Complete text analysis details for specific session
```

**Tip:** Use hierarchical endpoints when you want aggregated reporting by survey/platform/respondent. Use the flat session endpoint for quick session-only lookups.

### Grid, Timing, and Fraud (Hierarchical V2)

The same hierarchy applies to **grid analysis**, **timing analysis**, and **fraud detection**:

- **Grid:** `GET /surveys/{survey_id}/grid-analysis/summary`, `.../platforms/{platform_id}/grid-analysis/summary`, `.../respondents/{respondent_id}/grid-analysis/summary`, `.../sessions/{session_id}/grid-analysis` — straight-lining, patterns, variance.
- **Timing:** `GET /surveys/{survey_id}/timing-analysis/summary`, and similarly at platform/respondent/session levels — speeders, flatliners, per-question timing.
- **Fraud:** `GET /surveys/{survey_id}/fraud/summary`, and similarly at platform/respondent/session levels — IP, device fingerprint, duplicate responses, velocity.

Grid and timing data are populated when you capture grid questions (section 3b) and when you call **composite-analyze** on completion (section 4). Fraud is computed as part of composite-analyze.

For full request/response shapes and all variants, see [API_V2.md](API_V2.md) or the main [API.md](API.md).

---

## 10) Contact

For support or integration questions, contact your engineering liaison or submit an issue in the repository.


