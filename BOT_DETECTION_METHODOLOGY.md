# Bot Detection Methodology: Complete User Guide

**Who this document is for**: This guide is written for anyone using or integrating with the bot detection system—survey managers, analysts, and implementers. It explains **how the system works** and **how scores and decisions are calculated**, in plain language. You do not need access to the application’s source code; everything you need to understand and use the system is in this document.

---

## Production System Status
✅ **FULLY OPERATIONAL** - All systems verified and working
- **API Base URL**: https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1
- **Frontend Dashboard**: https://storage.googleapis.com/bot-detection-frontend-20251208/index.html
- **Health Status**: All endpoints responding correctly
- **Database**: Connected and processing requests with hierarchical structure ✅
- **Analysis Pipeline**: End-to-end testing completed successfully
- **OpenAI Integration**: GPT-4o-mini service fully operational ✅ (`openai_available: true`)
- **Text Quality Analysis**: 100% test accuracy achieved ✅
- **Health Monitoring**: Real-time OpenAI service status tracking ✅
- **Text Analysis Dashboard**: New dashboard endpoints deployed and operational ✅
- **Enhanced Reporting**: Text quality metrics integrated into all reports ✅
- **Hierarchical API**: Survey → Platform → Respondent → Session structure available ✅
- **Hierarchical Text Analysis**: V2 endpoints for text analysis at all hierarchy levels ✅
- **Database Migration**: `platform_id` column added with composite indexes ✅
- **Dashboard (February 2026)**: API Playground includes fraud, grid, and timing endpoint templates; Report Builder includes fraud, grid, and timing in summary and detailed reports; click respondent ID in detailed report to open full-detail popup (responses of interest, decision reasons); CSV export includes every analysis per respondent ✅
- **Bot threshold (November 2026)**: `DETECTION_THRESHOLD` is set on the Settings page (0.3–0.99, default 0.7) and decides the stored behavioural verdict and `composite_is_bot`; the final check's `is_bot` follows the survey's own quality rules (see [Decision Making Process](#decision-making-process))
- **Decipher XML tracking (November 2026)**: the Add tracking page adds the tracker, a hidden results page with 21 `QOS_` variables, an optional privacy notice and an optional early end on a clear bot signal
- **Live Quality (November 2026)**: per-survey quality rules re-judge results every time they are read, without changing stored results; `LQ_` variables can be added to an uploaded data file
- **Deployed (2026-11-27, revision `bot-backend-00079-lpm`)**: everything in this document is in production, including the rules-following final check, the `timeline_mismatch` signal, the noisy-OR behaviour score, the fraud reweighting, the data-file merge fix and the signed-upload protection. Production has no `TRACKING_TOKEN_SECRET` yet, so tracking there is unsigned
- **Production tests (2026-11-27)**: 54 simulated respondents in real time with up to 60 active at once: 54/54 got the expected result, every open end was checked, final check median 0.38 s (95th percentile 1.2 s) after the missing database indexes were added (it was 1.9 s / 7.9 s). Files in `test_results/respondent_pressure_2026-11-27`
- **Check against real data (2026-11-27)**: 930 real sessions from Botv13 and SURVEY_2025 re-scored with the current rules: none newly flagged as bots. Scores between 0.5 and 0.7 ("medium") rose from 2 to 54, mostly short fragments from the older tracker (it recorded the mouse every 8 ms, which trips the events-per-second timing rule); the current tracker records every 100 ms

## Table of Contents
1. [Overview](#overview)
2. [What We Capture](#what-we-capture)
3. [How We Capture Data](#how-we-capture-data)
4. [Data Processing Pipeline](#data-processing-pipeline)
5. [Detection Methods](#detection-methods)
6. [Text Quality Analysis](#text-quality-analysis)
7. [Decision Making Process](#decision-making-process)
8. [Confidence Scoring](#confidence-scoring)
9. [Risk Assessment](#risk-assessment)
10. [Live Quality: Judging Under Per-Survey Rules](#live-quality-judging-under-per-survey-rules)
11. [Decipher XML Tracking and Survey Variables](#decipher-xml-tracking-and-survey-variables)
12. [How the System Calculates Scores — Quick Reference](#how-the-system-calculates-scores--quick-reference)
13. [Integration Examples](#integration-examples)
14. [Best Practices](#best-practices)
15. [Troubleshooting](#troubleshooting)

---

## Overview

Our bot detection system uses advanced behavioral analysis combined with OpenAI-powered text quality analysis to distinguish between human users and automated bots. The system operates in real-time, analyzing user interactions and text responses across multiple dimensions to provide accurate classification with confidence scoring.

### Key Principles
- **Non-intrusive**: Minimal impact on user experience
- **Real-time**: Analysis performed as events occur
- **Multi-dimensional**: Multiple detection methods for accuracy
- **AI-Powered**: GPT-4o-mini integration for text quality analysis
- **Configurable**: The bot threshold is set on the Settings page, and each survey can have its own quality rules on Live Quality
- **Transparent**: Clear confidence scores and reasoning

---

## What We Capture

### 1. Keystroke Events
**Purpose**: Analyze typing patterns and timing consistency

**Data Captured**:
- Key pressed and key code
- Timestamp of each keystroke
- Modifier keys (Ctrl, Alt, Shift, Meta)
- Element context (input field, textarea, etc.)
- Page context (URL, title)
- Whether the browser marked the key press as a real user action (`trusted`); script-generated key presses are not trusted
- The Decipher tracker records only whether a key was a character, not which character

**Analysis Focus**:
- Inter-keystroke timing intervals
- Typing speed consistency
- Natural variation in timing
- Suspicious patterns (too regular, too fast, too slow)

### 2. Mouse Behavior
**Purpose**: Analyze mouse movement patterns and interaction naturalness

**Data Captured**:
- Mouse position (x, y coordinates)
- Click events (left, right, middle)
- Movement distance and speed
- Element context (what was clicked)
- Movement type (linear vs. natural curves)
- Whether each click was a real user action (`trusted`) and the pointer type (mouse, touch, pen)

**Analysis Focus**:
- Movement trajectory patterns (step lengths, straight paths)
- Pages answered with no mouse movement
- Clicks generated by script
- Natural vs. mechanical movements

### 3. Scroll Events
**Purpose**: Analyze scrolling behavior and patterns

**Data Captured**:
- Scroll position (x, y)
- Scroll direction and distance
- Page dimensions
- Viewport information

**Analysis Focus**:
- Scroll timing and frequency
- Natural scrolling patterns
- Consistent vs. variable behavior

### 4. Focus Events
**Purpose**: Analyze how users navigate between form elements

**Data Captured**:
- Focus in/out events
- Element transitions
- Timing between focus changes
- Element types and context

**Analysis Focus**:
- Tab order navigation
- Focus timing patterns
- Natural vs. systematic navigation

### 5. Device Characteristics
**Purpose**: Analyze device fingerprinting and consistency

**Data Captured**:
- Screen resolution
- Viewport dimensions
- User agent string
- Page load times
- Performance metrics
- Whether the browser reports it is controlled by automation (`navigator.webdriver`)
- Touch points, used to recognise phones and tablets

**Analysis Focus**:
- Device consistency throughout session
- Screen sizes that change mid-session or are reported as empty
- User agents of headless or automated browsers
- Touch devices, which have no mouse to track

### 6. Timing Patterns
**Purpose**: Analyze overall session timing and event frequency

**Data Captured**:
- Session duration
- Event frequency
- Inter-event intervals
- Page load times

**Analysis Focus**:
- Session duration patterns
- Event frequency consistency
- Natural timing variations

### 7. Text Quality Data
**Purpose**: Analyze quality and authenticity of open-ended survey responses using AI

**Data Captured**:
- Survey question text and context
- User response text
- Response timing and duration
- Question type and element information
- Page context (URL, title)

**Analysis Focus**:
- Gibberish detection (random characters, nonsensical text)
- Copy-paste detection (generic responses, dictionary definitions)
- Topic relevance analysis (on-topic vs off-topic responses)
- Generic answer detection (low-effort, uninsightful responses)
- Overall quality scoring (0-100 scale)

### 8. Survey Question Metadata
**Purpose**: Track survey questions for text quality analysis, grid analysis, and timing analysis

**Data Captured**:
- Question text (full question content)
- Question type (open_ended, multiple_choice, grid, matrix, etc.)
- HTML element ID and type (input, textarea, select, etc.)
- Element class names
- Page URL where question appears
- Page title
- Timestamp when question was asked

**Analysis Focus**:
- Question categorization for appropriate analysis type
- Grid/matrix question identification
- Question-response pairing for timing analysis
- Context for text quality relevance checking

### 9. Survey Response Data
**Purpose**: Store user responses with timing and analysis results

**Data Captured**:
- Response text (user's answer)
- Response time in milliseconds (time to answer)
- Associated question ID
- Session ID (links to behavior data)
- Timestamp when response was submitted

**Analysis Focus**:
- Text quality analysis (gibberish, copy-paste, relevance, generic)
- Response timing for speeder/flatliner detection
- Response patterns for duplicate detection
- Quality scoring and flagging

### 10. Grid/Matrix Question Responses
**Purpose**: Analyze grid and matrix questions for straight-lining, patterns, and satisficing behavior

**How grid data is captured (client integration):** The client (e.g. Decipher survey with JavaScript) registers the grid when it is shown by calling `POST /api/v1/text-analysis/questions` with `question_type: 'grid'` or `'matrix'` and stores the returned `question_id`. When the respondent completes the grid, the client sends **one** `POST /api/v1/text-analysis/responses` **per grid cell** with that same `question_id` and `response_text` set to the selected value (e.g. `"1"`, `"5"`). The backend uses these `survey_responses` (one per cell) to run grid analysis when composite-analyze or grid analysis is triggered. Step-by-step instructions: [decipher_simple_guide.md](decipher_simple_guide.md), [decipher_guide.md](decipher_guide.md).

**Data Captured**:
- Row identifier within the grid question
- Column identifier within the grid question
- Response value (selected option or rating)
- Response time per cell
- Question ID (links to survey_questions)
- Session ID (links to session and respondent)

**Analysis Focus**:
- Straight-lining detection (the same answer on every row of a grid with at least 3 rows)
- Pattern detection (diagonal, reverse diagonal, zigzag, straight line)
- Variance scoring (0-1 scale, measures response diversity)
- Satisficing behavior scoring (0-1 scale, combines variance and timing)
- Response consistency across grid rows

### 11. Per-Question Timing Data
**Purpose**: Analyze response timing for each individual question to detect speeders and flatliners

**Data Captured**:
- Question time in milliseconds (time taken to answer)
- Question ID (links to survey_questions)
- Session ID (links to session and respondent)
- Threshold used for detection (adaptive or fixed)
- Statistical anomaly score (z-score)

**Analysis Focus**:
- Speeder detection (response time < 2000ms threshold)
- Flatliner detection (response time > 300000ms / 5 minutes threshold)
- Timing anomalies (statistical outliers with z-score > 2.5)
- Adaptive threshold calculation (question-specific timing norms)
- Timing consistency patterns

### 12. Fraud Detection Data
**Purpose**: Detect duplicate respondents, IP reuse, device reuse, geolocation inconsistencies, and velocity patterns

**Data Captured**:
- IP address (from session)
- IP usage count (total sessions with same IP)
- IP sessions today (sessions with same IP created today)
- Device fingerprint (SHA256 hash of user_agent + screen/viewport + platform_id)
- Fingerprint usage count (sessions with same device fingerprint)
- Response similarity scores (text similarity between open-ended answers of 20 or more characters)
- Duplicate response count (answers 70% or more similar)
- Geolocation data (country code from IP; there is no IP-to-country lookup yet, so this is empty and the location check is left out of the fraud score)
- Geolocation consistency (matches other sessions from same respondent)
- Response velocity (responses per hour by IP, device, or respondent)

**Analysis Focus**:
- IP address reuse patterns (risk scoring based on usage frequency)
- Device fingerprint reuse (same device across multiple respondents)
- Duplicate response detection (text similarity analysis)
- Geolocation inconsistency (impossible travel patterns)
- Velocity analysis (unrealistic response rates)
- Overall fraud score calculation (weighted combination of all factors)

### 13. Hierarchical Structure Data
**Purpose**: Organize data in a hierarchical structure for efficient aggregation and analysis

**Data Captured**:
- Survey ID (unique identifier for each survey)
- Platform ID (survey platform: qualtrics, decipher, etc.)
- Respondent ID (unique identifier for each survey respondent)
- Session ID (unique identifier for each survey-taking session)
- Relationships: Survey → Platform → Respondent → Session

**Analysis Focus**:
- Aggregated analysis at each hierarchy level
- Survey-level summaries (all platforms, respondents, sessions)
- Platform-level summaries (all respondents and sessions for a platform)
- Respondent-level summaries (all sessions for a respondent)
- Session-level details (complete analysis for a single session)
- Cross-survey and cross-platform analysis

### 14. Session Metadata
**Purpose**: Track session-level information for fraud detection and analysis

**Data Captured**:
- User agent string (browser and device information)
- IP address (client IP from HTTP request)
- Referrer URL (where the user came from)
- Session creation timestamp
- Last activity timestamp (updated with each event)
- Session status (active, completed)
- Platform information (qualtrics, decipher, etc.)
- Device fingerprint (calculated after fraud analysis)

**Analysis Focus**:
- Session duration tracking
- Activity patterns
- Device consistency
- Platform identification
- Completion status

### 15. Page Submit Data (Decipher Tracker)
**Purpose**: Give the decisive bot signals and Live Quality the facts they need from each page

**Data Captured** (with each page submit):
- Time spent on the page, stored as `qos-page:<milliseconds>`. This time is measured in the browser, so a script could make it up
- Grid answers on the page, stored as `qos-grid:<values>` (for grids with 3 or more rows). The tracker sends these as a copy of the page submit with element id `qos-grid:...`; that copy is not counted as a second page
- Whether a hidden honeypot field was filled in. The honeypot is an off-screen text box labelled "Leave this empty", with no name (so it is never sent to Decipher), `tabIndex` -1 and `aria-hidden`
- How many open-ended answers (20 characters or more) appeared with no typing, pasting or dictation
- How each open end was entered: typed (including dictation and autocorrect), or pasted or dropped

**Analysis Focus**:
- Decisive signals: honeypot, untyped answers, and `timeline_mismatch` (page times compared with the time the server saw)
- Speeder and straight-lining flags on Live Quality
- Pasted answers flag on Live Quality

---

## How We Capture Data

### JavaScript Client SDK

Our JavaScript tracking client automatically captures user behavior events:

```javascript
// Initialize the tracker
const tracker = new BotDetection.Tracker({
    apiBaseUrl: 'https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1',
    batchSize: 10,
    flushInterval: 5000,
    debug: false,
    trackTextQuality: true,  // Enable text quality analysis
    minResponseLength: 10    // Minimum response length for analysis
});

// Start tracking
await tracker.init();
```

**Event Collection Process**:
1. **Automatic Setup**: Event listeners attached to DOM events
2. **Text Field Detection**: Automatic detection of text input fields and textareas
3. **Question Capture**: Automatic capture of survey questions and context (open-ended and, optionally, grid/matrix)
4. **Grid Question Capture (optional)**: For grid/matrix questions, the client registers the grid via `POST /text-analysis/questions` with `question_type: 'grid'` or `'matrix'`, then sends one `POST /text-analysis/responses` per grid cell when the respondent completes the grid (see [decipher_simple_guide.md](decipher_simple_guide.md), [decipher_guide.md](decipher_guide.md))
5. **Response Monitoring**: Real-time monitoring of user text input
6. **Throttling**: Mouse movements and scroll events are throttled to prevent overwhelming
7. **Batching**: Events are collected in batches for efficient transmission
8. **Real-time Transmission**: Events sent to API every 5 seconds or when batch size reached
9. **Text Analysis**: Responses automatically analyzed with GPT-4o-mini
10. **Error Handling**: Failed transmissions are retried automatically

### Data Transmission

Events are sent to the API in batches:

```json
[
  {
    "event_type": "keystroke",
    "timestamp": "2025-01-15T10:30:45.123Z",
    "key": "a",
    "key_code": 65,
    "element_id": "email-input",
    "element_type": "input",
    "page_url": "https://example.com/survey",
    "screen_width": 1920,
    "screen_height": 1080,
    "event_data": {
      "key": "a",
      "key_code": 65,
      "ctrl_key": false,
      "alt_key": false
    }
  }
]
```

---

## Data Processing Pipeline

### 1. Event Ingestion
- **Validation**: Events validated for required fields and data types
- **Normalization**: Timestamps converted to consistent format
- **Enrichment**: Additional context added (session info, device data)
- **Storage**: Events stored in PostgreSQL database. The stored event JSON does not repeat fields kept in their own columns or once on the session (page_url, page_title, user_agent, screen and viewport sizes, survey_id, respondent_id, platform_id, element ids, timestamp, event_type)
- **Rejected events**: Logged by event type only, because the page address can hold personal details
- **Personal details (November 2026)**: page addresses and referrers are stored without their query string or fragment. The tracker leaves text boxes that ask for contact or identity details alone (email address, phone number, name, address, postcode, date of birth, government ids; also boxes whose autocomplete, id or name says so). The service applies the same wording check on arrival, so trackers already in live surveys are covered too: such questions are stored as `personal`, their answers are not kept, text-checked, compared for duplicates, or flagged for entry method. Emails and phone numbers inside other answers are masked before the OpenAI call (`utils/privacy.py`)
- **Repeated events**: Events the tracker sent twice (same type, timestamp, element, x, y and key) are counted once in the analysis

### 2. Session Management
- **Session Creation**: Unique session ID generated for each user
- **Event Association**: All events linked to session ID
- **Status Tracking**: Session status updated as events arrive
- **Readiness Check**: Session marked ready for analysis when sufficient data collected

### 3. Analysis Triggering
- **Minimum Data**: Analysis runs on whatever events exist. With fewer than 5 key presses the keystroke score is 0.3 (leans human); with fewer than 5 events in total the timing score is 0.4. A session with no events cannot be analysed.
- **When**: The Decipher tracker calls `composite-analyze` when the respondent submits the last page. That call stores a fresh behavioural verdict, then runs the grid, timing, fraud and composite checks. If the early end is turned on, the tracker also calls `analyze` on one chosen page (see [Decipher XML Tracking and Survey Variables](#decipher-xml-tracking-and-survey-variables)). Analysis can also be triggered through the API.
- **Speed of the final check**: `composite-analyze` saves timing and grid results in one batch (24 database round trips, down from 71). Measured in production: median 1.7 s under load and 1.1 s idle (was 4.8 s and 2.8 s), within the tracker's 3-second wait on the last page

---

## Detection Methods

The system uses four behavioural methods that are scored, plus a check for decisive signals. Each method produces a **risk score from 0 (looks human) to 1 (looks bot-like)**. The four scores are combined into one behaviour score, and decisive signals can then raise it (see [Decision Making Process](#decision-making-process)). Each method has a **reliability** (how much a full score from it counts as evidence of a bot); the reliabilities are given in the headings below.

### 1. Keystroke Analysis (reliability 0.5)

**What the system looks at**: Time between consecutive key presses. Gaps of 2 seconds or more are normal typing pauses and are left out; only the gaps within bursts of typing count.

**How it decides "suspicious"** (each adds to the keystroke risk; 3 checks, run when there are at least 4 in-burst gaps):
- **Too regular**: In-burst gaps vary by less than **10 ms**—a machine-steady rhythm.
- **Too fast**: The average in-burst gap is under **50 ms**—faster than people type.
- **Rounded timing**: More than **80%** of in-burst gaps are multiples of 10 ms—timer-like.

**How the keystroke score is calculated**: The number of checks that are true, divided by 3, capped at 1.0.

**Minimum data**: With fewer than **5 key presses**, the score is **0.3** (too few to judge; leans human).

**What looks human**: Variable timing (variation of 10 ms or more), realistic speed, and pauses.

### 2. Mouse Analysis (reliability 0.45)

**What it analyzes**: The path of mouse movements and whether pages were answered without the mouse moving.

**How the mouse score is set**:
- **Touch device** (phone or tablet): **0.3**. There is no pointer to track.
- **No mouse movement, but key presses**: **0.4**. Keyboard-only respondents are rare but real.
- **No mouse movement, but clicks or page submits** on a desktop: **0.8**.
- **No events of either kind**: **0.4**.
- **With movement** (10 or more points), two checks: every step the same length (variation under 1 pixel), and a perfectly straight path with no turns. Events from older SDK versions also count if they report a linear movement or a speed over 1000 pixels per second.

**Score formula**: suspicious points ÷ 2, capped at 1.0.

**Human indicators**: Curved paths and step lengths that vary.

### 3. Timing Analysis (reliability 0.35)

**What the system looks at**: Session length, how many events per second, and how regular the gaps between events are.

**How it decides "suspicious"** (up to 3 checks):
- **Too short session**: From first to last event, the session is under **10 seconds**.
- **Too many events per second**: More than **50 events per second**—not realistic for a human.
- **Too regular**: Gaps between events vary by less than **0.1 seconds**—clockwork.

**How the timing score is calculated**: The system counts how many of these three are true, divides by 3, and caps at 1.0.

**Minimum data**: With fewer than **5 events**, the score is **0.4**.

**What looks human**: Session at least 10 seconds, at most 50 events per second, and natural variation in timing (0.1 s or more).

### 4. Device Analysis (reliability 0.4)

**What the system looks at**: Automation flags, the user agent, and whether the screen size stays the same.

**How it decides "suspicious"**:
- **Automation**: The browser reports `navigator.webdriver`, or the user agent names a headless or automated browser (for example headless, puppeteer, playwright, selenium, phantomjs, or bot/crawler/spider/scraper). The device score is then **1.0**.
- **Screen changed**: More than one screen size reported in the same session (1 point).
- **Empty screen**: A width or height of 0, common in headless browsers (1 point).
- **No screen size on a desktop**: half a point.

**How the device score is calculated**: Points ÷ 2, capped at 1.0 (unless automation already set it to 1.0).

**What looks human**: One stable, non-empty screen size and an ordinary browser.

### 5. Network Analysis (reliability 0)

**Current behavior**: Network analysis is not implemented. It returns 0.0 and has a reliability of **0**, so it adds nothing to the behaviour score. Classification is driven by the other four methods and the decisive signals.

### 6. Decisive Signals

Some patterns are things people do not produce. When one is found, it raises the behaviour score regardless of the four methods above. There are seven:

| Code | What it means |
|------|---------------|
| `automation` | The browser reports it is controlled by automation (`navigator.webdriver`), or the user agent belongs to a headless or automated browser |
| `scripted_input` | At least 3 clicks and key presses, and at least half of them, were generated by script (not trusted) |
| `no_input` | On a non-touch device with 2 or more pages submitted: no mouse or keyboard activity at all, or 3 or more clicks with no mouse movement and no key presses. A grid page counts as one page |
| `honeypot` | The hidden "Leave this empty" text box was filled in |
| `untyped_answers` | One or more open-ended answers appeared without any typing, pasting or dictation |
| `robotic_timing` | Typing or mouse movement with machine-exact timing (see below) |
| `timeline_mismatch` | Page times longer than the time the server saw (see below) |

**`robotic_timing`** fires on either of these:
- **Typing**: at least 3 separate stretches of 8 or more printable keys, where the gaps between keys vary by under 3 ms (standard deviation), and every stretch of 8 or more keys looks like this. A stretch ends at a change of field or a pause of 2 seconds or more. Only printable keys count, so holding Backspace or an arrow key never triggers it.
- **Mouse**: with 30 or more mouse points, at least 3 ruler-straight runs of equal steps (4 or more points each, steps of at least 10 px, steps and line within 1.5 px; shorter steps from trackers that sample every few milliseconds are not judged), covering at least 40% of the points.

**`timeline_mismatch`**: the page times the browser reports (`qos-page:`) add up to 60 seconds or more and exceed the time the server observed by more than the larger of 30 seconds and 25% of the reported time. The server's time runs from session creation to the last event received. Page times are measured in the browser and could be made up; the server's own arrival times cannot.

**Effect on the score**: One decisive signal raises the behaviour score to at least **0.85**; two or more raise it to at least **0.95**. The score before this lift is stored as `base_score`, and the codes that fired as `decisive_codes`, so Live Quality can apply a survey's own rules later. The analysis summary then names the signals ("Bot detected: ...").

---

## Text Quality Analysis

Our text quality analysis uses OpenAI's GPT-4o-mini model to analyze open-ended survey responses for authenticity and quality. This provides an additional layer of bot detection by examining the content of user responses.

**One request per answer**: a single OpenAI call covers all five checks below (gibberish, copy-paste, relevance, generic, quality), and every check is judged against the question. Answers shorter than 3 characters are not sent; they are flagged as too short with quality 0.

**Request limit**: each server instance allows `OPENAI_REQUESTS_PER_MINUTE` calls (default 300). When the limit is reached, an answer waits up to `OPENAI_RATE_WAIT_SECONDS` (default 20) for a slot instead of failing.

### 1. Gibberish Detection
**Purpose**: Identify nonsensical or random text responses

**What it detects**:
- Random character sequences (e.g., "asdfghjkl")
- Completely incoherent text
- Mixed languages without meaning
- Keyboard mashing patterns

**When the system flags a response**: The system flags the response when its confidence that the text is gibberish is **above 70%**.
- Random character patterns
- No coherent meaning

**Human Indicators**:
- Meaningful text with coherent structure
- Proper grammar and spelling
- Contextually relevant content

### 2. Copy-Paste Detection
**Purpose**: Identify responses that appear to be copied from external sources

**What it detects**:
- Dictionary definitions
- Wikipedia-style content
- Generic, formal language
- Overly polished responses
- Responses that don't match question context

**When the system flags a response**: The system flags the response when its confidence that the text is copy-pasted is **70% or higher**.
- Generic, impersonal language
- Dictionary-style definitions
- Responses that are too formal for the context

**Human Indicators**:
- Personal, informal language
- Original thoughts and opinions
- Contextually appropriate responses

### 3. Relevance Analysis
**Purpose**: Determine if responses are relevant to the questions asked

**What it detects**:
- Off-topic responses
- Completely unrelated answers
- Responses that ignore the question
- Tangential or irrelevant content

**When the system flags a response**: The system uses a "relevance risk" score; when that score is **70% or higher** (meaning the response is likely not relevant to the question), it flags the response.
- Completely off-topic responses
- Responses that ignore the question entirely

**Human Indicators**:
- Directly relevant answers
- Contextually appropriate responses
- Responses that address the question asked

### 4. Generic Answer Detection
**Purpose**: Identify low-effort, generic responses

**What it detects**:
- Very short, uninformative answers
- Generic phrases like "I don't know" or "It's okay"
- Responses with no specific details
- Low-effort, template-style answers

**When the system flags a response**: The system flags the response when its confidence that the text is generic/low-effort is **above 70%**.
- Very short, uninformative responses
- Template-style answers
- Lack of specific details

**Human Indicators**:
- Detailed, specific responses
- Personal insights and opinions
- Thoughtful, considered answers

### 5. Overall Quality Scoring
**Purpose**: Provide a comprehensive quality score for each response (0–100 from GPT-4o-mini).

**Scoring Scale (0–100)**:
- **90–100**: Excellent quality, detailed, insightful
- **70–89**: Good quality, relevant, informative
- **50–69**: Average quality, acceptable but basic
- **30–49**: Poor quality, minimal effort
- **0–29**: Very poor quality, likely problematic

**When the system flags for low quality**: If the overall quality score (0–100) is **below 30**, the response is flagged as low quality.

**Priority rules** (so one issue does not pile on redundant flags): If a response is flagged as **gibberish**, the system does not also flag it as generic or low quality. If it is flagged as **irrelevant**, the system does not also flag it as generic.

**Overall confidence** (per response): The system averages the confidence from the four checks (gibberish, copy-paste, relevance, generic) to produce one confidence value for that response.

**Quality factors** the system considers:
- Relevance to question
- Depth and detail
- Originality and authenticity
- Grammar and coherence
- Personal insight

### Text Analysis Process

1. **Response Submission**: User submits text response
2. **Question Context**: System retrieves associated question
3. **GPT-4o-mini Analysis**: One request returns all five checks, each judged against the question
4. **Scoring**: Individual scores calculated for each analysis type
5. **Flagging**: Responses flagged if any analysis indicates problems
6. **Quality Score**: Overall quality score calculated
7. **Storage**: Results stored with response data (or stored as not checked; see below)

### Unchecked Open Ends

An answer that still cannot be checked (OpenAI unavailable, or the request limit still reached after the wait) is stored as **not checked**: `quality_score` is null, `analysis_details` is `{"unchecked": true, "error": ...}`, and it is not flagged. It is never given a neutral 50 and never counted as acceptable. Live Quality counts these per respondent (`text_unchecked`) and in the totals (`text.unchecked`), and the CSV export has a `text_unchecked` column. The average quality used in the composite score and in `QOS_OES` is taken over checked answers only.

### Entry Method

Separately from the AI checks, each open end records how it was entered: **pasted** when at least half of an answer of 20 or more characters was pasted, and **no_typing** when an answer of 20 or more characters had no input events. These count toward the Pasted answers flag on Live Quality, not toward low-quality open ends.

### Integration with Composite Score

Text quality is combined with **behavioral** and **fraud** in the **composite score** (see [Decision Making Process](#decision-making-process)). The composite is:

- **Behavioral score**: 40% — how bot-like the interaction (keystrokes, mouse, timing, device) was.
- **Text quality (as risk)**: 30% — the system converts the average text quality (0–100) of checked answers into a risk: higher quality means lower risk (formula: risk = 1 − quality/100). If the respondent has no checked answers, the composite uses 50 for this part (risk 0.5).
- **Fraud score**: 30% — risk from IP, device, duplicates, and velocity (location is left out until there is an IP-to-country lookup).

Together, these three give one composite score that reflects both how the user interacted and how good and trustworthy their answers were.

---

## Decision Making Process

### 1. Individual Method Scoring (Behavioral Only)

Each behavioral method returns a score from 0.0 to 1.0 (see Detection Methods for formulas). Interpretation:
- **0.0–0.3**: Strong human indicators
- **0.3–0.7**: Mixed or unclear signals
- **0.7–1.0**: Strong bot indicators

### 2. Behavioral Confidence Score

The system combines the method scores into one **behavioral confidence score** (a bot probability: 0 looks human, 1 looks like a bot). Agreeing evidence adds up (a "noisy-OR"): each method's score times its reliability is its chance of meaning "bot", and the result is the chance that at least one of them does:

**score = 1 − product of (1 − reliability × method score)**

Reliabilities:
- Keystroke: **0.5**
- Mouse: **0.45**
- Timing: **0.35**
- Device: **0.4**
- Network: **0** (not implemented)

Two strong methods together reach the default 0.7 threshold; one alone does not. (Before, the score was a weighted average with keystroke 0.3, mouse 0.25, timing 0.2 and device 0.15, where even perfect keystroke and mouse scores only reached 0.61.) This score is the `base_score`.

**Decisive signals**: If one decisive signal fired, the score is raised to at least **0.85**; if two or more fired, to at least **0.95** (see [Decisive Signals](#6-decisive-signals)).

**Behavioral bot decision**: If the score is **at or above the bot threshold**, the session is stored as **bot**. Otherwise it is stored as **human**. The threshold is `DETECTION_THRESHOLD`, set on the Settings page (0.3–0.99, default **0.7**). A saved value applies at once on the instance that saved it, and every other instance picks it up within 30 seconds. Analyses already stored keep the verdict they were given.

**Final check verdict (`composite-analyze`)**: The `is_bot` returned by the final check, and `behavioral_details.is_bot`, follow the survey's quality rules (its bot threshold applied to `base_score`, and its enabled bot signals), so they give the same verdict as Live Quality. `behavioral_details.engine_is_bot` keeps the verdict under the global `DETECTION_THRESHOLD`. Only behaviour decides `is_bot`; text quality and fraud are reported as their own flags and scores. A behavioural bot gets a composite `risk_level` of at least HIGH.

### 3. Composite Score (Behavioral + Text Quality + Fraud)

When the system has text quality and fraud data, it computes a **composite score** that combines all three areas:

1. **Behavioral score** (40%): The behavioural confidence above, after any decisive-signal lift.
2. **Text quality as risk** (30%): The system turns average text quality (0–100) into a risk: **risk = 1 − (average quality ÷ 100)**. So high quality (e.g. 80) gives low risk (0.2).
3. **Fraud score** (30%): The 0–1 fraud risk from IP, device, duplicates and velocity; geolocation is left out until there is an IP-to-country lookup (see [Fraud Detection](#fraud-detection-stage-3--deployed)).

**Formula in words**:  
Composite score = (0.4 × behavioral) + (0.3 × text-quality risk) + (0.3 × fraud).  
The result is a number between 0 and 1.

**Composite risk level** (what you see in reports):
- **CRITICAL**: composite score **≥ 80%**
- **HIGH**: composite score **≥ 60%**
- **MEDIUM**: composite score **≥ 40%**
- **LOW**: composite score **under 40%**

**Composite threshold result**: Whether the composite score alone is **at or above** `DETECTION_THRESHOLD` (default 0.7) is kept as `composite_is_bot`. It does not decide the final check's `is_bot`, which follows behaviour under the survey's rules (see above).

### 4. Summary

- **Stored behavioural verdict**: **Bot** if the behaviour score (after any decisive-signal lift) is at or above `DETECTION_THRESHOLD`.
- **Final check (`composite-analyze`)**: **Bot** if the survey's rules judge the behaviour a bot (`base_score` at or above the survey's bot threshold, or an enabled bot signal fired). The composite score, `composite_is_bot` and the risk level (CRITICAL/HIGH/MEDIUM/LOW, at least HIGH for a behavioural bot) are reported alongside.
- **Live Quality**: Judges stored results again under each survey's own rules, on every read, without changing what is stored (see [Live Quality](#live-quality-judging-under-per-survey-rules)).

---

## Confidence Scoring

### Score Interpretation

The ranges below describe the behaviour score with the default threshold of 0.7. If the threshold is changed, the bot verdict moves with it.

**0.0-0.3**: High confidence human
- Strong human behavior patterns
- Natural variations in all metrics
- Realistic timing and movements

**0.3-0.5**: Likely human
- Mostly human patterns
- Some minor anomalies
- Generally natural behavior

**0.5-0.7**: Uncertain
- Mixed signals
- Insufficient data
- Borderline cases

**0.7-0.9**: Likely bot
- Multiple bot indicators
- Suspicious patterns
- Automated behavior signs
- One decisive signal puts a session here (0.85) or higher

**0.9-1.0**: High confidence bot
- Strong bot indicators
- Multiple detection methods triggered
- Clear automated patterns
- Two or more decisive signals put a session here (0.95) or higher

### Factors Affecting Confidence

1. **Data Quality**: More events = higher confidence
2. **Pattern Consistency**: Consistent indicators across methods
3. **Threshold Violations**: Multiple threshold breaches
4. **Natural Variation**: Lack of human-like variation
5. **Decisive Signals**: Patterns people do not produce override a low combined score

---

## Risk Assessment

### Risk Levels

**LOW**: 
- High confidence human classification
- Natural behavior patterns
- No suspicious indicators

**MEDIUM**: 
- Mixed signals or low confidence
- Some suspicious patterns
- Requires manual review

**HIGH**: 
- Strong bot indicators
- Multiple detection methods triggered
- Automated behavior patterns

**CRITICAL**: 
- Very high confidence bot
- Multiple strong indicators
- Clear automated patterns

### Risk Level Determination

**Stored behavioural risk** (from the behaviour score, a bot probability; a low score is low risk whatever the verdict):
- Score **≥ 90%** → **CRITICAL**
- Score **≥ 70%**, or the session was judged a bot → **HIGH**
- Score **≥ 50%** → **MEDIUM**
- Otherwise → **LOW**

**Composite risk** (when using the full composite score): Composite **≥ 80%** → CRITICAL; **≥ 60%** → HIGH; **≥ 40%** → MEDIUM; **under 40%** → LOW. In the final check, a respondent the survey's rules judge a behavioural bot is raised to at least HIGH.

**Live Quality risk**: Shown from the stored behaviour score (HIGH from 70%, MEDIUM from 50%, otherwise LOW), and raised to HIGH for any respondent the survey's rules judge a bot.

---

## Live Quality: Judging Under Per-Survey Rules

Live Quality (the `/quality` page) shows one survey's respondents, judged under that survey's quality rules. Rules are applied every time results are read: on the dashboard, in the CSV export (`GET /api/v1/quality/export?survey_id=`), and in the `LQ_` variables added to an uploaded data file. Changing a rule never changes stored results or the `QOS_` values already written into Decipher; the final check uses the rules in force when a respondent finishes. A survey with no saved rules uses the defaults. Rules are read and saved with `GET|PUT|DELETE /api/v1/quality/rules?survey_id=` (DELETE goes back to the defaults).

### Rules and Defaults

| Rule | Default | Meaning |
|------|---------|---------|
| Bot threshold (`bot_threshold`) | 0.7 | Bot when the stored `base_score` is at or above this |
| Bot signals (`bot_signals`) | automation, scripted_input, no_input, honeypot, untyped_answers, robotic_timing, timeline_mismatch | Decisive signals that make a respondent a bot on their own |
| Seconds per page (`speeder_page_seconds`) | 3.5 | Speeder when pages average under this |
| Share of median (`speeder_median_share`) | 0.5 | Speeder when total time is under this share of the median; needs 5 checked respondents with page times; 0 turns it off |
| Smallest straight-lined grid (`straightline_min_rows`) | 3 rows | Grids smaller than this do not count |
| Text reasons (`text_reasons`) | gibberish, generic, irrelevant, copy_paste, low_quality | Which text-check reasons count as low-quality open ends |
| Flag pasted answers (`flag_pasted`) | on | Flag answers that were pasted or appeared without typing |
| Fraud threshold (`fraud_threshold`) | 0.7 | High fraud risk when the fraud score is at or above this |
| Flag duplicates (`flag_duplicates`) | on | Flag respondents the fraud check marked as duplicates |
| Flag data-centre IPs (`flag_datacenter`) | on | Flag data-centre, VPN or proxy IP addresses |

**Signals added later**: saved rules record which bot signals existed when they were saved. A signal added after a survey saved its rules starts switched on for that survey; signals the survey switched off stay off.

### How Each Flag Is Decided

- **Bot-like behaviour**: The stored `base_score` (the behaviour score before decisive signals raised it) is at or above the survey's bot threshold, or one of the survey's enabled decisive signals fired. Results stored before `base_score` existed are judged on their stored score. Because the survey's threshold applies to `base_score`, a decisive signal the survey has switched off does not make a respondent a bot.
- **Speeder**: Uses page times (time on each tracked page). A respondent is a speeder when their pages average under the seconds-per-page rule, or, once 5 or more checked respondents have page times, when their total time is under the share-of-median rule. Per-answer timing is not used here, because a quick short answer would count.
- **Straight-lining**: A grid where every row has the same answer and the grid has at least the minimum number of rows, read from the grid answers the tracker stores for each page. A grid already flagged by the grid analysis (every row the same, at least 3 rows) also counts.
- **Flatliner**: The per-question timing analysis found a flatliner (an answer that took over 5 minutes).
- **Pasted answers**: An open end the text check marked as pasted or entered without typing (only when the pasted-answers rule is on).
- **Low-quality open ends**: An open end the text check flagged for a reason the survey counts (gibberish, generic, off-topic, copied or repeated text, low effort). A flag with no reason, or with another content reason, always counts. Flags about how an answer was entered (pasted, not typed) count only toward Pasted answers.
- **High fraud risk**: The fraud score is at or above the fraud threshold. If no fraud score is stored, a stored fraud risk level of HIGH or CRITICAL counts.
- **Duplicate**: The fraud check marked the respondent as a duplicate (only when the duplicates rule is on).
- **Data-centre IP**: The fraud check found a data-centre, VPN or proxy address (`datacenter_ip`; only when the data-centre rule is on).

**Respondent status**: `checked` once analysed, `in_progress` if active in the last 20 minutes, otherwise `dropped`. Only checked respondents get a bot or human verdict.

**Unchecked open ends**: open ends that could not be checked (see [Unchecked Open Ends](#unchecked-open-ends)) are counted per respondent as `text_unchecked` and in the totals as `text.unchecked`; the CSV export has a `text_unchecked` column.

### Repeat Sessions per Respondent

One person (one respondent id, which is the Decipher uuid) can have several sessions. `totals.respondents` counts people (sessions sharing a respondent id count once); `totals.sessions` still counts sessions. Each row has `other_sessions`. When `LQ_` variables are added to a data file and a uuid has several sessions, the checked session is used first, then the latest (before, the oldest was used, which was often an abandoned one).

### Bot Rate

Everywhere in the service (Overview, Sessions, survey, platform and respondent pages, and the `/dashboard/overview` and `/surveys` endpoints), the **bot rate is distinct sessions judged bots ÷ distinct sessions checked (analysed)**. A session analysed twice counts once. These pages use the stored verdicts. The Live Quality bot count is the number of checked respondents its rules judge bots.

### LQ_ Variables for Data Files

`POST /api/v1/quality/merge?survey_id=` takes a data file (.sav, .csv or .xlsx, up to 50 MB) and returns the same file with `LQ_` variables added, judged under the survey's rules. Records are matched on `QOS_SESSION`, then `QOS_RESPONDENT`, then Decipher's `uuid`. The variables are: LQ_MATCHED, LQ_STATUS, LQ_VERDICT, LQ_BOT_SCORE, LQ_BOT_RISK, LQ_BOT_SIGNALS, LQ_SECONDS, LQ_PAGES, LQ_SEC_PER_PAGE, LQ_TEXT_QUALITY, LQ_FRAUD_SCORE, LQ_FRAUD_RISK, one 0/1 variable per flag (LQ_F_BOT, LQ_F_TEXT, LQ_F_PASTED, LQ_F_STRAIGHT, LQ_F_SPEEDER, LQ_F_FLATLINE, LQ_F_DUPLICATE, LQ_F_FRAUD, LQ_F_DATACENTRE), LQ_NFLAGS and LQ_FLAGS. SPSS files keep their labels, and the `LQ_` variables get labels and value labels. Uploading again replaces existing `LQ_` columns.

---

## Decipher XML Tracking and Survey Variables

### Adding Tracking

On the Add tracking page (`POST /api/v1/tracking/decipher`), a complete Decipher survey XML gets:
- the tracker script as a `respview.client.js` style with `mode="after"`, so the survey's own page scripts keep working;
- Decipher's `${uuid}` as the respondent id;
- a hidden results page with 21 `QOS_` variables that the tracker fills on the last page;
- optionally, a short privacy notice at the top of the first page (`QOS_privacy`, on by default);
- optionally, an early end on a clear bot signal (`QOS_EARLY` and `QOS_bot_term`, off by default).

Nothing else in the file changes, and removing the tracking gives back the original file byte for byte. Survey settings Decipher would refuse (no `compat`, `compat` below 143, or `compat` 151 and above without `delphi="1"`) are reported before anything is sent to Decipher.

### Signed Tracking

With `TRACKING_TOKEN_SECRET` set, the tracker carries an HMAC token of the survey id, and a survey that requires tokens refuses unsigned sessions. A successful upload of a signed tracked file to Decipher marks the survey as requiring signed sessions at once. (Before, this happened only when its first signed respondent arrived, so fake unsigned sessions were accepted until then.) Making the tracked file alone does not protect the survey, because the live survey may still run an older unsigned tracker.

The token stops outsiders who never saw the survey; anyone who opens the survey page can read it. Production currently has no `TRACKING_TOKEN_SECRET`, so tracking there is unsigned.

Rate limits per IP address, per server instance: new sessions 30 per minute, other writes 600 per minute, Fix with AI 20 per hour.

### Early End on a Clear Bot Signal

When turned on, a hidden `QOS_EARLY` question is placed on a page break that every respondent reaches (page 2 by default; page breaks inside loops or conditional blocks are skipped). When that page is submitted, the tracker holds it for at most 2.5 seconds, scores the behaviour so far, and writes `bot` only if one of the decisive signals chosen for the survey fired. The `QOS_bot_term` termination ends the survey for those respondents. A high behaviour score without a decisive signal, an error, or a timeout leaves the respondent in the survey. If the survey has no suitable page break, the early check is not added and the final check still runs.

### Final Check and QOS_ Variables

On the last page the tracker holds the submit for at most 3 seconds while `composite-analyze` runs, then fills the hidden results page. The values reach Decipher's own data exports (SPSS, Excel, CSV). They follow the survey's quality rules in force at that moment: only enabled bot signals become reason codes, `datacenter_ip` only when `flag_datacenter` is on, and the low-quality open-end reason only for text reasons the rules count. They are fixed when written: later changes to the rules on Live Quality do not change them.

| Variable | Meaning |
|----------|---------|
| QOS_RESPONDENT, QOS_SESSION | Respondent id (Decipher uuid) and session id in this service |
| QOS_FLAG | bot, human, or unknown if the check did not finish |
| QOS_SCORE | Composite score (behaviour score if the composite did not run) |
| QOS_RISK | Risk level |
| QOS_STATUS | 1 human, 2 suspect, 3 bot. Bot when the final check's verdict is bot (behaviour under the survey's rules); suspect when any reason code applies or the composite risk is MEDIUM or higher |
| QOS_BEHAV | Behaviour bot score 0–100 (higher is worse) |
| QOS_OES | Open-ended answer quality 0–100 (higher is better) |
| QOS_FRAUD | Fraud score 0–100 |
| QOS_DUP, QOS_DUP_SCORE | Duplicate respondent (1/0) and the highest of the device risk, IP risk and duplicate-answer risk 0–100. The duplicate-answer part is the risk (similarity under 0.70 gives 0, from 0.70 gives 0.6, from 0.85 gives 0.8, from 0.95 gives 1.0), not the raw similarity, which is kept in `fraud_details.response_similarity` |
| QOS_IP_RISK, QOS_DEVICE_RISK, QOS_GEO_RISK, QOS_VELOCITY | Fraud component scores 0–100 |
| QOS_DATACENTER | Data-centre, VPN or proxy IP (1/0) |
| QOS_SPEEDER | Pages answered too fast: the number of pages faster than the survey's `speeder_page_seconds` rule. If no page times were received, the number of answers the per-question timing analysis found too fast |
| QOS_STRAIGHTLINE | Number of straight-lined grid questions |
| QOS_FLAGCOUNT | Number of reason codes |
| QOS_REASON | Main (lowest-numbered, most severe) reason code; 0 for none |
| QOS_REASONS | All reason codes, comma-separated |

Scores other than QOS_OES are risk scores (higher is worse). A value is left blank when its check had nothing to work on.

**Reason codes**:

| Code | Reason |
|------|--------|
| 1 | Automated or headless browser (`automation`) |
| 2 | Clicks and key presses generated by script (`scripted_input`) |
| 3 | Pages answered with no mouse or keyboard use (`no_input`) |
| 4 | Hidden honeypot field filled in (`honeypot`) |
| 5 | Open ends that appeared without typing (`untyped_answers`) |
| 6 | Bot-like behaviour score (`behaviour`; only when judged a bot with no enabled decisive signal) |
| 7 | Typing or mouse movement with machine-exact timing (`robotic_timing`) |
| 8 | Page times longer than the time the server saw (`timeline_mismatch`) |
| 10 | Data centre, VPN or proxy IP address (`datacenter_ip`) |
| 11 | Same device seen on other sessions of this survey (`device_reuse`) |
| 12 | Same IP address used repeatedly (`ip_reuse`) |
| 13 | Answers copied from another respondent (`duplicate_responses`) |
| 14 | Many surveys started in a short time (`high_velocity`) |
| 15 | Same respondent seen from different countries within an hour (`geolocation_inconsistency`) |
| 20 | Low-quality open-ended answers (`low_quality_open_ends`) |
| 21 | Straight-lined grid questions (`straight_lining`) |
| 22 | Questions answered too fast (`speeder`): pages average under the survey's `speeder_page_seconds`, as on the dashboard. If no page times were received, any answer the per-question timing analysis found too fast |

---

## How the System Calculates Scores — Quick Reference

This section summarizes the main numbers and rules the system uses, in plain language. You can use it to interpret results or explain the system to others. No access to application code is required.

| What | How the system uses it |
|------|------------------------|
| **Keystroke** | Under 5 key presses: 0.3. Only gaps under 2 s count. Suspicious if: gaps too regular (under 10 ms variation), too fast (under 50 ms average), or over 80% of gaps multiples of 10 ms. Score = (number of suspicious checks ÷ 3), max 1.0. |
| **Mouse** | Touch device: 0.3. No movement: 0.4 with key presses, 0.8 with clicks or page submits, else 0.4. With 10+ movement points, suspicious if every step is the same length or the path is perfectly straight. Score = (suspicious points ÷ 2), max 1.0. |
| **Timing (session)** | Under 5 events: 0.4. Suspicious if: session under 10 s, or over 50 events per second, or gaps between events too regular (under 0.1 s variation). Score = (number of checks ÷ 3), max 1.0. |
| **Device** | Automation flag or headless user agent: 1.0. Otherwise suspicious if the screen size changes mid-session or is empty (1 point each), or no screen size on a desktop (half a point). Score = (points ÷ 2), max 1.0. |
| **Network** | Not implemented; returns 0.0 with reliability 0. |
| **Behavioral combination** | Noisy-OR: score = 1 − product(1 − reliability × method score). Reliabilities: keystroke 0.5, mouse 0.45, timing 0.35, device 0.4, network 0. Two strong methods reach 0.7; one alone does not. This is `base_score`. Events sent twice are counted once. |
| **Decisive signals** | automation, scripted_input, no_input, honeypot, untyped_answers, robotic_timing, timeline_mismatch. One raises the score to at least 0.85, two or more to at least 0.95. |
| **Bot threshold** | `DETECTION_THRESHOLD` (Settings page, 0.3–0.99, default 0.7). Stored verdict: **Bot** if the behaviour score is at or above it. The final check's `is_bot` uses the survey's own bot threshold and bot signals. |
| **Composite score** | 40% behavioral + 30% text-quality risk + 30% fraud. Text-quality risk = 1 − (average quality of checked answers ÷ 100); 0.5 when no answer was checked. `composite_is_bot` if composite is at or above `DETECTION_THRESHOLD`; it does not decide `is_bot`. Risk: CRITICAL ≥ 80%, HIGH ≥ 60%, MEDIUM ≥ 40%, LOW under 40%; at least HIGH for a behavioural bot. |
| **Text flags** | One OpenAI request per answer covers all five checks. Gibberish: flag if confidence over 70%. Copy-paste, relevance, generic: flag if 70% or higher. Low quality: flag if quality score under 30. An answer that cannot be checked is stored as not checked (quality null, not flagged), never as 50. |
| **Fraud** | Combined from IP (25%), device fingerprint (25%), duplicate responses (20%), velocity (15%); geolocation (15%) is left out until there is an IP-to-country lookup, and the other weights are renormalised. A device seen only on other networks counts half. **Duplicate** if overall fraud score ≥ 70%. A data-centre, VPN or proxy IP raises the fraud score to at least 75%. |
| **Grid straight-lining** | Grid analysis: flagged when every answer in a grid of at least 3 rows is the same. Live Quality: every row the same in a grid of at least `straightline_min_rows` rows (survey rule, default 3). |
| **Response timing** | Per-question: **Speeder** under **2 seconds**, **Flatliner** over **5 minutes**, **Anomaly** z-score over 2.5. Live Quality speeder: pages average under 3.5 s, or total time under half the median once 5 respondents are checked (survey rules). |
| **Live Quality rules** | Per survey; applied on every read; never change stored results or `QOS_` values. Defaults are listed in [Live Quality](#live-quality-judging-under-per-survey-rules). |
| **Bot rate** | Distinct bot sessions ÷ distinct checked (analysed) sessions. |

---

## Integration Examples

### Survey Platform Integration

**Decipher (XML tracking)**: For Decipher surveys, use the Add tracking page instead of writing code. It adds the tracker, the `QOS_` results page and the optional privacy notice and early end to the survey XML, and can upload the result to Decipher (see [Decipher XML Tracking and Survey Variables](#decipher-xml-tracking-and-survey-variables)). The examples below are for custom setups with the JavaScript SDK.

**Qualtrics Integration**:
```javascript
// Qualtrics embedded data
Qualtrics.SurveyEngine.addOnload(function() {
    const tracker = new BotDetection.Tracker({
        apiBaseUrl: 'https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1',
        sessionId: '${e://Field/session_id}',
        trackTextQuality: true  // Enable text quality analysis
    });
    
    tracker.init().then(() => {
        // Track survey completion
        Qualtrics.SurveyEngine.addOnPageSubmit(function() {
            // Get composite analysis (behavioral + text quality)
            tracker.compositeAnalyze().then(result => {
                Qualtrics.SurveyEngine.setEmbeddedData('bot_detection_result', 
                    JSON.stringify(result));
                Qualtrics.SurveyEngine.setEmbeddedData('text_quality_score', 
                    result.text_quality_score || 0);
                Qualtrics.SurveyEngine.setEmbeddedData('text_flagged', 
                    result.text_flagged || false);
            });
        });
    });
});
```

**Decipher Integration**:
```javascript
// Decipher webhook integration
const webhookData = {
    session_id: sessionId,
    survey_id: surveyId,
    respondent_id: respondentId,
    bot_detection_result: analysisResult,
    text_quality_score: textQualityScore,
    text_flagged: textFlagged,
    composite_score: compositeScore
};

fetch('https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/integrations/webhooks/decipher', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(webhookData)
});
```

### Custom Implementation

**Basic Integration**:
```javascript
// Initialize tracking
const tracker = new BotDetection.Tracker({
    apiBaseUrl: 'https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1',
    trackTextQuality: true
});

// Start tracking
await tracker.init();

// Analyze when needed (behavioral only)
const behavioralResult = await tracker.analyze();

// Get composite analysis (behavioral + text quality)
const compositeResult = await tracker.compositeAnalyze();
console.log('Composite bot detection result:', compositeResult);
```

**Advanced Integration**:
```javascript
// Custom configuration
const tracker = new BotDetection.Tracker({
    apiBaseUrl: 'https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1',
    batchSize: 5,
    flushInterval: 3000,
    debug: true,
    trackKeystrokes: true,
    trackMouse: true,
    trackScroll: false,  // Disable scroll tracking
    trackTextQuality: true,  // Enable text quality analysis
    minResponseLength: 15    // Minimum response length for analysis
});

// Custom event handling
tracker.on('analysis_complete', (result) => {
    if (result.is_bot) {
        showCaptcha();
    } else {
        proceedWithForm();
    }
});

// Text quality event handling
tracker.on('text_analysis_complete', (textResult) => {
    console.log('Text quality score:', textResult.quality_score);
    if (textResult.is_flagged) {
        console.log('Response flagged:', textResult.flag_reasons);
    }
});
```

---

## Best Practices

### 1. Implementation Guidelines

**Timing**:
- Initialize tracker early in page load
- Allow sufficient time for data collection (minimum 10 seconds)
- Analyze after meaningful user interaction

**Configuration**:
- Use appropriate batch sizes (5-10 events)
- Set reasonable flush intervals (3-5 seconds)
- Enable debug mode during development

**Error Handling**:
- Implement fallback mechanisms
- Handle network failures gracefully
- Provide user feedback for analysis delays

### 2. Data Collection Optimization

**Event Filtering**:
- Focus on meaningful interactions
- Avoid tracking sensitive data
- Respect user privacy preferences

**Performance**:
- Throttle high-frequency events
- Use efficient data structures
- Minimize network overhead

### 3. Analysis Timing

**When to Analyze**:
- After form completion
- At natural break points
- When sufficient data collected
- Before critical actions

**Analysis Frequency**:
- Avoid over-analysis
- Respect user experience
- Consider session context

### 4. Result Handling

**Immediate Actions**:
- Show appropriate UI feedback
- Implement progressive enhancement
- Handle edge cases gracefully

**Long-term Actions**:
- Log results for analysis
- Update user profiles
- Implement adaptive measures

---

## Troubleshooting

### Common Issues

**1. Insufficient Data**
- **Problem**: Scores sit near the middle, with no clear verdict
- **Solution**: With fewer than 5 key presses or 5 events, the keystroke and timing methods return fixed scores (0.3 and 0.4); more interaction gives them something to measure. Decisive signals do not depend on the amount of data
- **Prevention**: Allow adequate interaction time

**2. Network Failures**
- **Problem**: Events not transmitted
- **Solution**: Implement retry logic and offline storage
- **Prevention**: Use reliable network connections

**3. False Positives**
- **Problem**: Humans classified as bots
- **Solution**: Raise `DETECTION_THRESHOLD` on the Settings page (affects new analyses), or raise the survey's bot threshold or switch off a bot signal on Live Quality (re-judges stored results at once), or add manual review
- **Prevention**: Regular threshold calibration

**4. False Negatives**
- **Problem**: Bots classified as humans
- **Solution**: Lower `DETECTION_THRESHOLD` or the survey's bot threshold on Live Quality, or enhance detection methods
- **Prevention**: Continuous monitoring and updates

### Debug Mode

Enable debug mode for detailed logging:

```javascript
const tracker = new BotDetection.Tracker({
    debug: true,
    apiBaseUrl: 'https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1'
});
```

**Debug Information**:
- Event collection details
- Network transmission logs
- Analysis method scores
- Confidence calculations

### Performance Monitoring

**Key Metrics**:
- Event collection rate
- Analysis processing time
- Network transmission success
- Confidence score distribution

**Monitoring Tools**:
- Browser developer tools
- Network tab analysis
- Console logging
- API response monitoring

---

## Survey-Specific Detection (Stage 2) ✅ **DEPLOYED**

### Overview
The survey-specific detection system provides specialized analysis for grid/matrix questions and enhanced timing analysis to identify satisficing behavior, straight-lining patterns, and suspicious response timing.

### Detection Methods

#### 1. Grid/Matrix Question Analysis

The system looks at how respondents answer grid (matrix) questions—e.g. several rows of options with the same scale.

- **Straight-lining**: When **every** answer in a grid is the **same value** (e.g. all "5") and the grid has at least **3 rows**, the system flags straight-lining. (Before, 80% identical answers was enough.) The confidence of the result increases with the share of identical answers and with the number of cells (up to a cap).
- **Pattern detection**: The system can also detect diagonal, reverse diagonal, and zigzag patterns; it needs at least **3 responses**. Variance and satisficing scores are derived from the same set of answers.

#### 2. Enhanced Timing Analysis (Response-Level)

The system evaluates how long respondents take to answer each question.

- **Speeders**: A response is flagged as a **speeder** if it was submitted in **under 2 seconds** (2000 ms). This suggests the question may not have been read.
- **Flatliners**: A response is flagged as a **flatliner** if it took **over 5 minutes** (300 000 ms). This can indicate the respondent left the page or was distracted.
- **Timing anomalies**: The system computes a statistical measure (z-score) for each response time. If the time is far from the typical time for that question (z-score **over 2.5** in either direction), the response is flagged as an outlier—either very fast (speeder-like) or very slow (flatliner-like). At least **3 responses** are needed for this check.
- **Adaptive thresholds**: When enough data is available, the system can use question-specific averages and variation to set slightly different speeder/flatliner bounds, while keeping them within 0.5–2 seconds for speeders and 5–10 minutes for flatliners.

### Grid Analysis Integration
Grid analysis is integrated into the hierarchical API structure:
- Survey-level grid analysis summaries
- Platform-level grid analysis summaries
- Respondent-level grid analysis summaries
- Session-level grid analysis details

### Grid/Matrix Analysis for Fraud Detection

**How Grid Analysis Identifies Fraudulent Behavior**:

Grid/matrix question analysis detects patterns that indicate fraudulent or low-quality responses, which are strong indicators of bot activity or satisficing behavior:

1. **Straight-lining Detection** (`detect_straight_lining()`):
   - **Algorithm**: Counts occurrences of each response value in the grid. If one value is given on every row (`straight_line_threshold = 1.0`) and the grid has at least 3 rows (`straight_line_min_rows = 3`), the grid is flagged as straight-lined.
   - **Confidence Calculation**: `confidence = min(percentage, 1.0) * min(len(values) / 10.0, 1.0)` - confidence increases with both the percentage of identical values and the total number of responses (capped at 10 responses).
   - **Fraud Indicator**: Straight-lining suggests the respondent is not reading questions and is providing mechanical responses, which is a strong indicator of fraudulent or low-quality participation.

2. **Pattern Detection** (`detect_patterns()`):
   - **Diagonal Pattern**: Checks if values are strictly increasing (1, 2, 3, 4...). Requires at least 3 responses.
   - **Reverse Diagonal Pattern**: Checks if values are strictly decreasing. Requires at least 3 responses.
   - **Zigzag Pattern**: Checks if values alternate between increasing and decreasing. Requires at least 4 responses.
   - **Straight Line Pattern**: All values are identical (detected separately from straight-lining check).
   - **Fraud Indicator**: Mechanical patterns indicate automated or scripted responses rather than genuine human consideration.

3. **Variance Scoring** (`calculate_variance()`):
   - **Algorithm**: Calculates standard deviation of response values, then normalizes using coefficient of variation: `cv = std_dev / abs(mean_val)`, capped at 1.0. Returns 0.0 for no variance, 1.0 for high variance.
   - **Fraud Indicator**: Low variance (score < 0.3) indicates responses lack diversity and may be fraudulent or satisficing.

4. **Satisficing Scoring** (`calculate_satisficing_score()`):
   - **Algorithm**: Combines three factors with weights:
     - **Low variance** (40% weight): Inverted variance score (1.0 - variance) - low variance = high satisficing
     - **Fast response times** (30% weight): Normalized based on average response time (< 2 seconds = high satisficing, > 10 seconds = low satisficing)
     - **Pattern consistency** (30% weight): Confidence score from pattern detection if pattern is straight_line, diagonal, or reverse_diagonal
   - **Formula**: `satisficing_score = (variance_score * 0.4) + (time_score * 0.3) + (pattern_score * 0.3)`, capped between 0.0 and 1.0
   - **Fraud Indicator**: High satisficing scores (≥ 0.7) indicate low-effort, fraudulent responses.

**Storage and Integration**:
- Grid analysis results are stored in `grid_responses` table with hierarchical fields (`survey_id`, `platform_id`, `respondent_id`, `session_id`) for efficient aggregation.
- Each grid response record includes: `is_straight_lined`, `pattern_type`, `variance_score`, `satisficing_score`.
- Results are aggregated at survey/platform/respondent/session levels using hierarchical queries.
- While grid analysis is not directly included in the fraud score calculation, it provides complementary fraud indicators that are displayed alongside fraud detection results in reports and dashboards.

### Timing Analysis Integration
Timing analysis is integrated into the hierarchical API structure:
- Survey-level timing analysis summaries
- Platform-level timing analysis summaries
- Respondent-level timing analysis summaries
- Session-level timing analysis details with per-question breakdowns

### Hierarchical Structure Data for Fraud Detection

**How Hierarchical Structure Enables Fraud Detection**:

The hierarchical structure (Survey → Platform → Respondent → Session) is essential for fraud detection algorithms. The system uses denormalized hierarchical fields stored in fraud detection tables to efficiently identify fraudulent patterns:

1. **Duplicate Response Detection** (`_analyze_duplicate_responses()`):
   - **Hierarchical Scope**: Compares responses **only within the same `survey_id`** to avoid false positives from legitimate similar responses across different surveys.
   - **Algorithm**: 
     - Uses only open-ended answers of 20 or more characters (`MIN_DUPLICATE_CHARS = 20`), so grid rows and choices such as "3" no longer match each other
     - Retrieves those answers for the current session, and from other sessions where `Session.survey_id == session.survey_id AND Session.id != session.id`
     - Finds exact copies (ignoring case and surrounding spaces) across the whole survey
     - Finds near copies among the latest 2,000 answers (`MAX_DUPLICATE_COMPARE = 2000`) using difflib sequence matching
     - Counts duplicates when similarity ≥ 70% (`similarity_threshold = 0.70`)
   - **Why Hierarchical**: Without `survey_id`, the system would compare responses across different surveys, leading to false positives. The hierarchical structure ensures comparisons are contextually appropriate.

2. **Velocity Analysis** (`_analyze_velocity()`):
   - **Hierarchical Tracking**: Calculates responses per hour using three identifiers:
     - **By IP address**: Counts sessions with same `ip_address` created in the last hour
     - **By device fingerprint**: Counts sessions with same `device_fingerprint` created in the last hour  
     - **By respondent_id**: Counts sessions with same `respondent_id` created in the last hour
   - **Algorithm**: Uses maximum of the three counts as the velocity metric: `responses_per_hour = max(ip_sessions_per_hour, fp_sessions_per_hour, resp_sessions_per_hour)`
   - **Why Hierarchical**: The `respondent_id` allows tracking the same person across multiple sessions, while `ip_address` and `device_fingerprint` catch cases where the same person uses different accounts or where multiple people share devices/IPs.

3. **Geolocation Consistency Checking** (`_analyze_geolocation()`):
   - **Hierarchical Scope**: Checks consistency for the same `respondent_id` across sessions within a 1-hour window.
   - **Algorithm**:
     - Extracts country code from IP using `extract_geolocation_from_ip()`. There is no IP-to-country lookup yet, so this returns no country, and the location score is left out of the fraud score (not counted as 0)
     - Finds other sessions where `Session.respondent_id == session.respondent_id AND Session.created_at >= session.created_at - timedelta(hours=1)`
     - If country codes differ within 1 hour, flags as inconsistent (risk_score = 0.9)
   - **Why Hierarchical**: Using `respondent_id` ensures we're checking if the same person appears to be in multiple countries simultaneously, which is physically impossible and indicates fraud.

4. **Efficient Fraud Aggregation** (`_aggregate_fraud_data()`):
   - **Denormalized Fields**: Fraud indicators are stored with denormalized hierarchical fields (`survey_id`, `platform_id`, `respondent_id`) copied from the session at analysis time.
   - **Efficient Queries**: Instead of joining `fraud_indicators` → `sessions` → filtering by hierarchy, queries directly filter `fraud_indicators` by hierarchical fields:
     ```python
     fraud_conditions = [FraudIndicator.survey_id == survey_id]
     if platform_id:
         fraud_conditions.append(FraudIndicator.platform_id == platform_id)
     if respondent_id:
         fraud_conditions.append(FraudIndicator.respondent_id == respondent_id)
     ```
   - **Aggregation Levels**: Enables efficient aggregation at:
     - Survey level: All fraud indicators for a survey
     - Platform level: All fraud indicators for a platform within a survey
     - Respondent level: All fraud indicators for a respondent within a platform
     - Session level: Individual fraud indicator for a session
   - **Why Denormalized**: Denormalization eliminates expensive JOINs and enables fast aggregation queries using composite indexes (`idx_fraud_survey`, `idx_fraud_survey_platform`, `idx_fraud_survey_platform_respondent`, `idx_fraud_survey_platform_respondent_session`).

5. **IP and Device Fingerprint Tracking**:
   - **IP Analysis** (`_analyze_ip_address()`): Counts total sessions and sessions today with the same `ip_address` in the session's own survey (all sessions when it has no survey id), then calculates risk score based on usage frequency. If the device fingerprint is not seen on any other session, the IP risk is halved (a shared connection, not a repeat respondent).
   - **Device Fingerprint Analysis** (`_analyze_device_fingerprint()`): Generates SHA256 hash from `user_agent + screen_width + screen_height + viewport_width + viewport_height + platform_id`, then counts sessions with the same fingerprint in the session's own survey. If the fingerprint is seen only on other networks (IPv4 /24, IPv6 /48), the device risk is halved, because identical phone models look alike; on the same network it counts fully.
   - **Why Hierarchical**: IP and device reuse are counted within one survey; the hierarchical structure also allows filtering results by `platform_id` or `respondent_id` when needed for reporting.

**Database Schema**:
- `fraud_indicators` table includes: `survey_id`, `platform_id`, `respondent_id` (denormalized from sessions)
- `grid_responses` table includes: `survey_id`, `platform_id`, `respondent_id`, `session_id` (denormalized for efficient queries)
- `timing_analysis` table includes: `survey_id`, `platform_id`, `respondent_id`, `session_id` (denormalized for efficient queries)
- Composite indexes enable fast hierarchical queries without JOINs

**Summary**: The hierarchical structure enables fraud detection by providing contextual scope (e.g., comparing duplicates within the same survey), enabling efficient aggregation (denormalized fields with composite indexes), and allowing multi-level analysis (survey/platform/respondent/session) for comprehensive fraud monitoring.

### API Endpoints
```http
# Grid Analysis Endpoints
GET /api/v1/surveys/{survey_id}/grid-analysis/summary
GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/grid-analysis/summary
GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/grid-analysis/summary
GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}/grid-analysis

# Timing Analysis Endpoints
GET /api/v1/surveys/{survey_id}/timing-analysis/summary
GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/timing-analysis/summary
GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/timing-analysis/summary
GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}/timing-analysis
```

### Real Example Results (Production Testing - February 2026)
**Grid Analysis:**
- Straight-lining detection: Working (detects identical responses across grid rows)
- Pattern detection: Working (diagonal, reverse diagonal, zigzag patterns detected)
- Variance scoring: Working (calculates response variance 0-1 scale)
- Satisficing scoring: Working (combines variance and timing for satisficing behavior)

**Timing Analysis:**
- Speeder detection: Working (< 2000ms threshold)
- Flatliner detection: Working (> 300000ms threshold)
- Anomaly detection: Working (z-score based statistical analysis)
- Adaptive thresholds: Working (context-aware threshold calculation)

**Integration Status:**
- ✅ All grid analysis endpoints operational
- ✅ All timing analysis endpoints operational
- ✅ Hierarchical summaries working at all levels
- ✅ Frontend widgets integrated and operational
- ✅ Production deployment verified (February 2026)

## Fraud Detection (Stage 3) ✅ **DEPLOYED**

The fraud module combines several signals into one **overall fraud score** (0–100%). That score is used in the composite bot score and to mark respondents as duplicate when appropriate.

### How the Overall Fraud Score Is Built

The system takes a weighted average of five components (the result is capped between 0 and 100%):

- **IP address**: 25%
- **Device fingerprint**: 25%
- **Duplicate responses**: 20%
- **Geolocation**: 15%
- **Response velocity**: 15%

There is no IP-to-country lookup yet, so the geolocation component has no value. It is left out instead of counting as 0, and the score is the weighted average over the other four (IP 0.25, device 0.25, duplicate answers 0.20, velocity 0.15, divided by their total of 0.85).

- A respondent is treated as **duplicate** when the overall fraud score is **70% or higher**.
- A session from a data-centre, VPN or proxy IP address has its fraud score raised to at least **75%** and gets the `datacenter_ip` reason. This happens after the duplicate check, so it does not by itself mark the respondent as a duplicate.
- **Fraud risk levels**: **CRITICAL** (≥ 90%); **HIGH** (≥ 70%); **MEDIUM** (≥ 40%); **LOW** (below 40%).

### What Each Component Measures

#### 1. IP Address (25%)
How often the same IP is used across sessions of the survey, or in one day. Halved when this session's device is not seen on any other session.  
- **Very high risk (80%)**: Same IP used in 10+ sessions, or in 5+ sessions in one day.  
- **High (60%)**: 5+ sessions or 3+ in one day.  
- **Medium (40%)**: 3+ sessions.  
- **Low (20%)**: 2 sessions.  
- **None (0%)**: Single use.

#### 2. Device Fingerprinting (25%)
How often the same device fingerprint appears across sessions of the survey.  
- **Very high (90%)**: 5+ uses; **High (70%)**: 3+; **Medium (50%)**: 2+; **None (0%)**: single use.
- A fingerprint seen only on **other** networks (IPv4 /24, IPv6 /48) counts half, because identical phone models look alike; on the same network it counts fully.

#### 3. Duplicate Responses (20%)
How similar this respondent’s open-ended answers are to others in the same survey.  
- Only open-ended answers of **20 or more characters** are compared; grid rows and choices such as "3" are not.  
- Exact copies are found across the whole survey; near copies (**70% or higher similarity**) among the latest 2,000 answers.  
- **Risk**: 95%+ similar → 100%; 85%+ → 80%; 70%+ → 60%; below 70% → 0%.

#### 4. Geolocation (15%, currently left out)
Whether the same respondent is seen from different countries within an hour. There is no IP-to-country lookup yet, so this check has no value and is left out of the fraud score. A **geolocation** reason would be added when this risk is **70% or higher**.

#### 5. Velocity (15%)
How many responses per hour the respondent (or IP/device) submits.  
- **20+ per hour** → 100%; **10+** → 80%; **5+** → 60%; **3+** → 40%; below 3 → 0%.

### When You See Fraud “Reasons” in Reports

The system attaches labels when a component passes a threshold:  
- **IP reuse**: IP risk ≥ 60%  
- **Device reuse**: device risk ≥ 50%  
- **Duplicate responses**: duplicate risk ≥ 60%  
- **Geolocation**: geolocation risk ≥ 70%  
- **High velocity**: velocity risk ≥ 60%
- **Data-centre IP**: the IP address is in a published AWS, Google Cloud, Oracle or DigitalOcean range

These reasons become `QOS_` reason codes 10–15 in the survey data, and Live Quality turns them into the Duplicate, High fraud risk and Data-centre IP flags under the survey's rules.

### Fraud Detection Integration
Fraud detection is integrated into the composite bot detection scoring:
- **Behavioral Analysis**: 40% weight
- **Text Quality Analysis**: 30% weight
- **Fraud Detection**: 30% weight

### API Endpoints
```http
# Trigger fraud analysis for a session
POST /api/v1/fraud/analyze/{session_id}

# Get fraud indicators for a session
GET /api/v1/fraud/sessions/{session_id}

# Get fraud summary at survey level
GET /api/v1/surveys/{survey_id}/fraud/summary

# Get fraud summary at platform level
GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/fraud/summary
```

### Real Example Results (Production Testing - February 2026)
**Fraud Detection Analysis:**
- Overall Fraud Score: 0.26 (26%)
- Is Duplicate: False
- Risk Level: LOW
- IP Reuse Detection: Working (1164 previous uses detected, high severity)
- Processing Time: Sub-second response times

**Integration Status:**
- ✅ All fraud detection endpoints operational
- ✅ Hierarchical fraud summaries working
- ✅ IP tracking and device fingerprinting active
- ✅ Duplicate detection functional
- ✅ Production deployment verified

## Conclusion

Our bot detection methodology provides comprehensive, real-time analysis of user behavior combined with AI-powered text quality analysis and fraud detection to accurately distinguish between human users and automated bots. The multi-dimensional approach ensures high accuracy while maintaining a non-intrusive user experience.

**Key Benefits**:
- **Accurate**: Multiple detection methods for reliable classification
- **AI-Powered**: GPT-4o-mini integration for text quality analysis
- **Composite Analysis**: Unified scoring combining behavioral and text quality
- **Fast**: Final check median 1.7 s under load and 1.1 s idle in production, within the tracker's 3-second wait
- **Flexible**: Configurable thresholds and detection methods
- **Transparent**: Clear confidence scores and reasoning
- **Scalable**: Efficient data collection and processing

**System Verification Completed**:
1. ✅ JavaScript client SDK implemented and tested
2. ✅ Detection thresholds configured and operational
3. ✅ OpenAI GPT-4o-mini integration operational
4. ✅ Text quality analysis pipeline tested
5. ✅ Composite scoring system implemented (40% behavioral, 30% text quality, 30% fraud)
6. ✅ Monitoring and metrics endpoints active
7. ✅ Integration with survey platforms verified
8. ✅ Performance optimized (sub-100ms response times)
9. ✅ OpenAI API key integration completed
10. ✅ 100% test classification accuracy achieved
11. ✅ Health monitoring endpoint operational
12. ✅ Production validation completed
13. ✅ Fraud detection system deployed and operational (February 2026)
14. ✅ Real example testing completed with comprehensive results (February 2026)
15. ✅ All fraud detection endpoints verified working in production
16. ✅ Grid and timing analysis system deployed and operational (February 2026)
17. ✅ All grid and timing analysis endpoints verified working in production
18. ✅ Frontend widgets integrated and operational (February 2026)
19. ✅ Comprehensive test suite: 275 backend tests passing (November 2026)

**Production Ready**: The system is fully operational with advanced text quality analysis, fraud detection, 100% test accuracy, comprehensive dashboard integration, enhanced reporting, and ready for production use.

**Real Example Test Results (February 2026)**:
- Bot Detection: Working (Confidence: 0.425, Risk Level: high, Processing: 0.067ms)
- Fraud Detection: Working (Fraud Score: 0.26, Risk Level: LOW, IP Reuse: 1164 detected)
- Session Management: Working (Event ingestion, status tracking operational)
- Survey Aggregation: Working (Hierarchical endpoints functional)

For technical support or questions about implementation, please refer to our API documentation or contact our support team. 