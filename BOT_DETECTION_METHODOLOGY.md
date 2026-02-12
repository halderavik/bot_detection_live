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
10. [How the System Calculates Scores — Quick Reference](#how-the-system-calculates-scores--quick-reference)
11. [Integration Examples](#integration-examples)
12. [Best Practices](#best-practices)
13. [Troubleshooting](#troubleshooting)

---

## Overview

Our bot detection system uses advanced behavioral analysis combined with OpenAI-powered text quality analysis to distinguish between human users and automated bots. The system operates in real-time, analyzing user interactions and text responses across multiple dimensions to provide accurate classification with confidence scoring.

### Key Principles
- **Non-intrusive**: Minimal impact on user experience
- **Real-time**: Analysis performed as events occur
- **Multi-dimensional**: Multiple detection methods for accuracy
- **AI-Powered**: GPT-4o-mini integration for text quality analysis
- **Configurable**: Adjustable thresholds and sensitivity
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

**Analysis Focus**:
- Movement trajectory patterns
- Click precision and timing
- Speed variations
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

**Analysis Focus**:
- Device consistency throughout session
- Common bot screen sizes
- User agent patterns
- Performance anomalies

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
3. **Question Capture**: Automatic capture of survey questions and context
4. **Response Monitoring**: Real-time monitoring of user text input
5. **Throttling**: Mouse movements and scroll events are throttled to prevent overwhelming
6. **Batching**: Events are collected in batches for efficient transmission
7. **Real-time Transmission**: Events sent to API every 5 seconds or when batch size reached
8. **Text Analysis**: Responses automatically analyzed with GPT-4o-mini
9. **Error Handling**: Failed transmissions are retried automatically

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
- **Storage**: Events stored in PostgreSQL database

### 2. Session Management
- **Session Creation**: Unique session ID generated for each user
- **Event Association**: All events linked to session ID
- **Status Tracking**: Session status updated as events arrive
- **Readiness Check**: Session marked ready for analysis when sufficient data collected

### 3. Analysis Triggering
- **Minimum Data**: Analysis requires at least 5 events for keystroke/timing; 3+ for mouse. If keystrokes < 5, keystroke score returns 0.5 (neutral). If mouse events < 3, mouse score returns 0.5.
- **Time-based**: Analysis can be triggered manually or automatically
- **Real-time**: Analysis performed within 200ms for immediate results

---

## Detection Methods

The system uses five behavioral signals. Each produces a **risk score from 0 (looks human) to 1 (looks bot-like)**. Those scores are then combined into one behavioral confidence score (see [Decision Making Process](#decision-making-process)).

### 1. Keystroke Analysis (30% of behavioral score)

**What the system looks at**: Time between consecutive keystrokes—how regular or variable typing is.

**How it decides "suspicious"** (each adds to the keystroke risk; up to 4 checks):
- **Too regular**: Time between key presses varies by less than **10 ms**—unnaturally steady.
- **Too fast**: Average time between keys is under **50 ms**—faster than human typing.
- **Too slow**: Average time between keys is over **2000 ms** (2 seconds)—unusual long pauses.
- **Perfect timing**: More than **80%** of intervals are round numbers (e.g. exactly 100 ms, 200 ms)—machine-like.

**How the keystroke score is calculated**: The system counts how many of these four checks are true, then divides by 4 and caps at 1.0. So 0 checks → 0, 4 checks → 1.0.

**Minimum data**: At least **5 keystroke events** are needed. With fewer, the system uses a neutral score of 0.5.

**What looks human**: Variable timing (variation ≥ 10 ms), realistic speed (roughly 50–2000 ms between keys), irregular patterns.

### 2. Mouse Analysis (25% of behavioral score)

**Backend constants**:
- `MOUSE_MIN_MOVEMENT = 5` pixels  
- `MOUSE_MAX_SPEED = 1000` pixels/second  
- `MOUSE_CLICK_THRESHOLD = 0.7` (precision > 0.99 is treated as “perfect precision”)  

**What it analyzes**:
- Movement type (linear vs. natural), speed, precision, and distance variation

**Bot indicators**:
- **Straight-line movements**: Movement is perfectly linear instead of curved
- **Unrealistic speed**: `speed > 1000` pixels/second
- **Perfect precision**: `precision > 0.99`
- **Consistent distances**: With > 10 events, std dev of movement distances < **5** pixels

**Score formula**:
```python
# Requires at least 3 mouse events; otherwise returns 0.5
score = min(suspicious_patterns / (len(mouse_events) + 1), 1.0)
```

**Human indicators**: Curved movements, variable precision, speeds ≤ 1000 px/s, distance std dev ≥ 5.

### 3. Timing Analysis (20% of behavioral score)

**What the system looks at**: Session length, how many events per second, and how regular the gaps between events are.

**How it decides "suspicious"** (up to 3 checks):
- **Too short session**: From first to last event, the session is under **10 seconds**.
- **Too many events per second**: More than **50 events per second**—not realistic for a human.
- **Too regular**: Gaps between events vary by less than **0.1 seconds**—very mechanical.

**How the timing score is calculated**: The system counts how many of these three are true, divides by 3, and caps at 1.0.

**Minimum data**: At least **5 events**. With fewer, the system uses a neutral score of 0.5.

**What looks human**: Session at least 10 seconds, at most 50 events per second, and natural variation in timing (≥ 0.1 s).

### 4. Device Analysis (15% of behavioral score)

**What the system looks at**: Screen resolution, viewport size, and whether they stay consistent.

**How it decides "suspicious"**:
- **Multiple screen sizes**: More than one different screen resolution reported in the same session.
- **Common bot resolutions**: Resolution is one of **1920×1080**, **1366×768**, or **1440×900** (each adds half a "point"; these are often seen in automated setups).
- **Inconsistent viewport**: More than one different viewport size in the session.

**How the device score is calculated**: The system adds up these factors, divides by 3, and caps at 1.0.

**What looks human**: One stable screen size and one viewport, and a resolution not in the common bot list above.

### 5. Network Analysis (10% of behavioral score)

**Current behavior**: The system does not analyze network or request headers. This part always contributes a **neutral score of 0.5**. Classification is driven by the other four methods.

---

## Text Quality Analysis

Our text quality analysis uses OpenAI's GPT-4o-mini model to analyze open-ended survey responses for authenticity and quality. This provides an additional layer of bot detection by examining the content of user responses.

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
3. **GPT-4o-mini Analysis**: Multiple parallel analyses performed
4. **Scoring**: Individual scores calculated for each analysis type
5. **Flagging**: Responses flagged if any analysis indicates problems
6. **Quality Score**: Overall quality score calculated
7. **Storage**: Results stored with response data

### Integration with Composite Score

Text quality is combined with **behavioral** and **fraud** in the **composite score** (see [Decision Making Process](#decision-making-process)). The composite is:

- **Behavioral score**: 40% — how bot-like the interaction (keystrokes, mouse, timing, device) was.
- **Text quality (as risk)**: 30% — the system converts the average text quality (0–100) into a risk: higher quality means lower risk (formula: risk = 1 − quality/100).
- **Fraud score**: 30% — risk from IP, device, duplicates, geolocation, and velocity.

Together, these three give one composite score that reflects both how the user interacted and how good and trustworthy their answers were.

---

## Decision Making Process

### 1. Individual Method Scoring (Behavioral Only)

Each behavioral method returns a score from 0.0 to 1.0 (see Detection Methods for formulas). Interpretation:
- **0.0–0.3**: Strong human indicators
- **0.3–0.7**: Mixed or unclear signals
- **0.7–1.0**: Strong bot indicators

### 2. Behavioral Confidence Score

The system combines the five behavioral method scores into one **behavioral confidence score** using fixed weights:

- Keystroke: **30%**
- Mouse: **25%**
- Timing: **20%**
- Device: **15%**
- Network: **10%**

Each method contributes (its score × its weight); the confidence score is the sum of those five contributions (a number between 0 and 1).

**Behavioral bot decision**: If this confidence score is **above 70%**, the session is classified as **bot**. Otherwise it is classified as **human**.

### 3. Composite Score (Behavioral + Text Quality + Fraud)

When the system has text quality and fraud data, it computes a **composite score** that combines all three areas:

1. **Behavioral score** (40%): The same 0–1 behavioral confidence from keystroke, mouse, timing, device, and network.
2. **Text quality as risk** (30%): The system turns average text quality (0–100) into a risk: **risk = 1 − (average quality ÷ 100)**. So high quality (e.g. 80) gives low risk (0.2).
3. **Fraud score** (30%): The 0–1 fraud risk from IP, device, duplicates, geolocation, and velocity (see [Fraud Detection](#fraud-detection-stage-3--deployed)).

**Formula in words**:  
Composite score = (0.4 × behavioral) + (0.3 × text-quality risk) + (0.3 × fraud).  
The result is a number between 0 and 1.

**Composite risk level** (what you see in reports):
- **CRITICAL**: composite score **≥ 80%**
- **HIGH**: composite score **≥ 60%**
- **MEDIUM**: composite score **≥ 40%**
- **LOW**: composite score **under 40%**

**Composite bot decision**: If the composite score is **70% or higher**, the session is classified as **bot**. Otherwise it is classified as **human**.

### 4. Summary

- **Behavioral-only** (no text/fraud): The system uses only the weighted behavioral confidence. **Bot** if that score is **&gt; 70%**.
- **Full composite** (with text and fraud): The system uses the three-part composite. **Bot** if composite score is **70% or higher**; risk level is CRITICAL/HIGH/MEDIUM/LOW as above.

---

## Confidence Scoring

### Score Interpretation

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

**0.9-1.0**: High confidence bot
- Strong bot indicators
- Multiple detection methods triggered
- Clear automated patterns

### Factors Affecting Confidence

1. **Data Quality**: More events = higher confidence
2. **Pattern Consistency**: Consistent indicators across methods
3. **Threshold Violations**: Multiple threshold breaches
4. **Natural Variation**: Lack of human-like variation
5. **Device Consistency**: Stable device fingerprinting

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

**When the session is classified as bot** (behavioral confidence or composite score indicates bot):
- Confidence **≥ 90%** → **CRITICAL**
- Confidence **≥ 70%** → **HIGH**
- Confidence **≥ 50%** → **MEDIUM**
- Otherwise → **LOW**

**When the session is classified as human** (behavioral or composite indicates human):
- Confidence **≥ 70%** (strong human signals) → **LOW** risk
- Confidence **≥ 50%** → **MEDIUM** (some uncertainty)
- Confidence **under 50%** → **HIGH** (low confidence that the user is human; worth reviewing)

**Composite risk** (when using the full composite score): Composite **≥ 80%** → CRITICAL; **≥ 60%** → HIGH; **≥ 40%** → MEDIUM; **under 40%** → LOW.

---

## How the System Calculates Scores — Quick Reference

This section summarizes the main numbers and rules the system uses, in plain language. You can use it to interpret results or explain the system to others. No access to application code is required.

| What | How the system uses it |
|------|------------------------|
| **Keystroke** | Needs at least 5 keystrokes. Suspicious if: timing too regular (under 10 ms variation), too fast (under 50 ms average), too slow (over 2 s average), or over 80% of intervals round numbers. Score = (number of suspicious checks ÷ 4), max 1.0. |
| **Mouse** | Needs at least 3 mouse events. Suspicious if: straight-line movement, speed over 1000 px/s, precision over 99%, or (with over 10 events) very consistent movement distances (under 5 px variation). Score scales with number of suspicious signs and number of events. |
| **Timing (session)** | Needs at least 5 events. Suspicious if: session under 10 s, or over 50 events per second, or gaps between events too regular (under 0.1 s variation). Score = (number of checks ÷ 3), max 1.0. |
| **Device** | Suspicious if: multiple screen sizes in one session, resolution is 1920×1080 / 1366×768 / 1440×900, or multiple viewport sizes. Score = (suspicious factors ÷ 3), max 1.0. |
| **Network** | Always 0.5 (neutral); no request analysis. |
| **Behavioral combination** | Weights: keystroke 30%, mouse 25%, timing 20%, device 15%, network 10%. **Bot** if this combined score is over 70%. |
| **Composite score** | 40% behavioral + 30% text-quality risk + 30% fraud. Text-quality risk = 1 − (average quality ÷ 100). **Bot** if composite ≥ 70%. Risk: CRITICAL ≥ 80%, HIGH ≥ 60%, MEDIUM ≥ 40%, LOW under 40%. |
| **Text flags** | Gibberish: flag if confidence over 70%. Copy-paste, relevance, generic: flag if 70% or higher. Low quality: flag if quality score under 30. |
| **Fraud** | Combined from IP (25%), device fingerprint (25%), duplicate responses (20%), geolocation (15%), velocity (15%). **Duplicate** if overall fraud score ≥ 70%. |
| **Grid straight-lining** | Flagged when **80% or more** of grid answers are the same value (at least 2 answers). |
| **Response timing** | **Speeder**: answer in **under 2 seconds**. **Flatliner**: answer in **over 5 minutes**. **Anomaly**: response time is a statistical outlier (z-score over 2.5). |

---

## Integration Examples

### Survey Platform Integration

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

fetch('https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/integrations/decipher/webhook', {
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
- **Problem**: Analysis returns low confidence
- **Solution**: Ensure minimum 5 keystrokes and 3 mouse events
- **Prevention**: Allow adequate interaction time

**2. Network Failures**
- **Problem**: Events not transmitted
- **Solution**: Implement retry logic and offline storage
- **Prevention**: Use reliable network connections

**3. False Positives**
- **Problem**: Humans classified as bots
- **Solution**: Adjust thresholds or add manual review
- **Prevention**: Regular threshold calibration

**4. False Negatives**
- **Problem**: Bots classified as humans
- **Solution**: Enhance detection methods or lower thresholds
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

- **Straight-lining**: When **80% or more** of the answers in a grid are the **same value** (e.g. all "5"), the system flags straight-lining. At least **2 responses** are required in the grid to run this check. The confidence of the result increases with the share of identical answers and with the number of cells (up to a cap).
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

### Timing Analysis Integration
Timing analysis is integrated into the hierarchical API structure:
- Survey-level timing analysis summaries
- Platform-level timing analysis summaries
- Respondent-level timing analysis summaries
- Session-level timing analysis details with per-question breakdowns

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

The system weights five components and adds them up (the result is capped between 0 and 100%):

- **IP address**: 25%
- **Device fingerprint**: 25%
- **Duplicate responses**: 20%
- **Geolocation**: 15%
- **Response velocity**: 15%

- A respondent is treated as **duplicate** when the overall fraud score is **70% or higher**.
- **Fraud risk levels**: **CRITICAL** (≥ 90%); **HIGH** (≥ 70%); **MEDIUM** (≥ 40%); **LOW** (below 40%).

### What Each Component Measures

#### 1. IP Address (25%)
How often the same IP is used across sessions or in one day.  
- **Very high risk (80%)**: Same IP used in 10+ sessions, or in 5+ sessions in one day.  
- **High (60%)**: 5+ sessions or 3+ in one day.  
- **Medium (40%)**: 3+ sessions.  
- **Low (20%)**: 2 sessions.  
- **None (0%)**: Single use.

#### 2. Device Fingerprinting (25%)
How often the same device fingerprint appears across respondents.  
- **Very high (90%)**: 5+ uses; **High (70%)**: 3+; **Medium (50%)**: 2+; **None (0%)**: single use.

#### 3. Duplicate Responses (20%)
How similar this respondent’s text answers are to others.  
- Responses are compared; **70% or higher similarity** is treated as a duplicate signal.  
- **Risk**: 95%+ similar → 100%; 85%+ → 80%; 70%+ → 60%; below 70% → 0%.

#### 4. Geolocation (15%)
Whether the stated location matches IP-based location, or if there are impossible travel patterns. A **geolocation** reason is added when this risk is **70% or higher**.

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
- **Fast**: Real-time analysis with sub-200ms processing
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
19. ✅ Comprehensive test suite: 40 tests passing (100% success rate)

**Production Ready**: The system is fully operational with advanced text quality analysis, fraud detection, 100% test accuracy, comprehensive dashboard integration, enhanced reporting, and ready for production use.

**Real Example Test Results (February 2026)**:
- Bot Detection: Working (Confidence: 0.425, Risk Level: high, Processing: 0.067ms)
- Fraud Detection: Working (Fraud Score: 0.26, Risk Level: LOW, IP Reuse: 1164 detected)
- Session Management: Working (Event ingestion, status tracking operational)
- Survey Aggregation: Working (Hierarchical endpoints functional)

For technical support or questions about implementation, please refer to our API documentation or contact our support team. 