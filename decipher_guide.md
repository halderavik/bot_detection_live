# Decipher Integration Guide (Survey Programmers)

This guide shows step-by-step how to integrate Bot Detection into a Decipher (Forsta/FocusVision) survey. You will: create a session, collect behavior events during the survey, trigger analysis on completion, and optionally receive results via webhook.

## Production System Status
✅ **FULLY OPERATIONAL** - All endpoints verified and working
- **API Base URL**: `https://bot-backend-i56xopdg6q-pd.a.run.app/api/v1`
- **Health Check**: https://bot-backend-i56xopdg6q-pd.a.run.app/health
- **Metrics**: https://bot-backend-i56xopdg6q-pd.a.run.app/metrics
- **Database**: Connected and processing requests
- **Analysis Pipeline**: End-to-end testing completed successfully

Note: Replace example IDs/variables with those from your study. All examples use HTTPS and JSON.

---

## 1) Prerequisites

- Decipher survey access with permission to add custom JavaScript and webhooks
- Backend API reachable from respondents (no corporate firewall blocks)
- If using webhooks: a Decipher project with webhook support enabled

---

## 2) Create a Bot Detection Session (Survey Start)

Create a session when the respondent starts your survey. Store the returned `session_id` in a Decipher variable (e.g., `session_id`). You can do this in a pre-load script on your first page or a custom initialization question.

Example (custom JavaScript, runs once at start):

```javascript
const API_BASE = 'https://bot-backend-i56xopdg6q-pd.a.run.app/api/v1';

async function createBotSession() {
  const resp = await fetch(`${API_BASE}/detection/sessions`, { method: 'POST' });
  const data = await resp.json();
  // Save session_id to a hidden question or Decipher variable
  // Example: write to a hidden input with id "session_id"
  document.getElementById('session_id').value = data.session_id;
}

createBotSession().catch(console.error);
```

Hidden question HTML example (Decipher page):

```html
<input type="hidden" id="session_id" name="session_id" value="">
```

---

## 3) Add the Event Tracker (During Survey)

Capture keystrokes, mouse, focus/blur, scroll, and device info. Send batched events to the API to minimize network overhead.

```javascript
const API_BASE = 'https://bot-backend-i56xopdg6q-pd.a.run.app/api/v1';
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

## 4) Trigger Analysis (On Completion)

On the final page or submit event, call the analyze endpoint. You can also check readiness first.

```javascript
async function analyzeSession() {
  const sessionId = document.getElementById('session_id').value;
  if (!sessionId) return;

  // Optional: ensure session is ready
  const readyResp = await fetch(`${API_BASE}/detection/sessions/${sessionId}/ready-for-analysis`);
  const ready = await readyResp.json();
  if (!ready.ready) {
    // Optionally flush any remaining buffered events
    await flushEvents();
  }

  const resp = await fetch(`${API_BASE}/detection/sessions/${sessionId}/analyze`, {
    method: 'POST'
  });
  const result = await resp.json();
  // Save the result to a hidden field or embedded data for export
  document.getElementById('bot_result').value = JSON.stringify(result);
}

// Call analyzeSession on final submit / thank-you page
```

Hidden field for storing results:

```html
<input type="hidden" id="bot_result" name="bot_result" value="">
```

---

## 5) Optional: Webhook Delivery to Decipher Endpoint

If you prefer server-to-server delivery, configure a webhook to your integration endpoint.

- Endpoint (example): `https://bot-backend-i56xopdg6q-pd.a.run.app/api/v1/integrations/decipher/webhook`
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
curl -s https://bot-backend-i56xopdg6q-pd.a.run.app/health
# Response: {"status":"healthy","service":"bot-detection-api"}

# Metrics Endpoint ✅ VERIFIED
curl -s https://bot-backend-i56xopdg6q-pd.a.run.app/metrics
# Response: Prometheus-compatible metrics

# Create session ✅ VERIFIED
curl -s -X POST \
  https://bot-backend-i56xopdg6q-pd.a.run.app/api/v1/detection/sessions
# Response: {"session_id":"uuid","created_at":"timestamp","status":"active"}

# Ingest example events ✅ VERIFIED
curl -s -X POST \
  https://bot-backend-i56xopdg6q-pd.a.run.app/api/v1/detection/sessions/<SESSION_ID>/events \
  -H "Content-Type: application/json" \
  -d '[{"event_type":"keystroke","timestamp":"2025-01-01T00:00:00Z","key":"a","element_id":"q1"}]'
# Response: {"session_id":"uuid","events_processed":1,"total_events":1,"status":"success"}

# Analyze session ✅ VERIFIED
curl -s -X POST \
  https://bot-backend-i56xopdg6q-pd.a.run.app/api/v1/detection/sessions/<SESSION_ID>/analyze
# Response: {"session_id":"uuid","is_bot":false,"confidence_score":0.25,"risk_level":"high",...}
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

## 9) Contact

For support or integration questions, contact your engineering liaison or submit an issue in the repository.


