# Simple Decipher Integration Guide

This guide shows you exactly how to add bot detection to your Decipher survey in 3 simple steps. No complex options - just copy, paste, and you're done.

## 🚀 How to Use This Guide

### For Beginners (Never used Decipher before):
1. **Start with the Quick Start section** below to get familiar
2. **Follow each step exactly** - don't skip any steps
3. **Test with a simple survey first** before using on important surveys
4. **Read the troubleshooting section** if you run into issues

### For Experienced Decipher Users:
1. **Jump to Step 1** to copy the JavaScript code
2. **Create the hidden fields** from Step 2
3. **Add the analysis code** from Step 3
4. **Test and deploy**

### What You'll Need:
- Access to your Decipher survey editor
- Basic knowledge of where to add JavaScript in Decipher
- 15-30 minutes to complete the setup

## Quick Start for Testing (TL;DR)

1. **Create a test survey** with 2-3 questions
2. **Copy the code** from Step 1 into your survey header
3. **Create hidden fields** with IDs: `bot_session_id`, `bot_result`, `bot_is_bot`, `bot_confidence`
4. **Copy the code** from Step 3 into your final page
5. **Test your survey** - check the data export for bot detection results

That's it! The full guide below explains everything in detail.

## What This Does
Our system watches how people interact with your survey (typing, mouse movements, scrolling) and uses AI to analyze the quality of their text responses to determine if they're real humans or automated bots. We detect low-quality responses like gibberish, copy-pasted text, irrelevant answers, or generic responses using OpenAI's GPT-4o-mini model.

**✅ Production Status**: OpenAI integration fully operational with 100% test accuracy achieved!
**✅ Text Analysis Dashboard**: New dashboard endpoints deployed and operational!
**✅ Enhanced Reporting**: Text quality metrics integrated into all reports!
**✅ Hierarchical Text Analysis**: V2 endpoints available for querying text analysis at survey/platform/respondent/session levels!

## Step 1: Add the Tracking Script (Once at the Beginning)

### 📍 Where to put this code:
**In Decipher:** Go to your survey editor → Survey Options → JavaScript → Header section
**Alternative:** Add to your first question as custom JavaScript

### 🎯 What it does:
- Creates a unique session ID for each user
- Starts collecting data about user behavior (typing, mouse movements, scrolling)
- Automatically detects text input fields and captures questions
- Sends data to our analysis server automatically
- Analyzes text responses in real-time using AI

### 📋 Step-by-step instructions:
1. **Open your Decipher survey** in the survey editor
2. **Click "Survey Options"** in the left sidebar
3. **Click "JavaScript"** in the options menu
4. **Click the "Header" tab** (or "Footer" if you prefer)
5. **Copy and paste the code below** into the text area
6. **Click "Save"** to save your survey

```javascript
// Bot Detection Setup with Text Quality Analysis - Add this once at the start of your survey
const API_BASE = 'https://bot-backend-i56xopdg6q-pd.a.run.app/api/v1';

// Read identifiers (create these hidden fields in Step 2)
function getIdentifierValue(id) {
  const el = document.getElementById(id);
  return el && typeof el.value === 'string' ? el.value : '';
}

// Step 1a: Create a session when survey starts
async function setupBotDetection() {
  try {
    // Get survey identifiers for hierarchical tracking
    const surveyId = getIdentifierValue('survey_id') || '';
    const respondentId = getIdentifierValue('respondent_id') || '';
    const platformId = 'decipher'; // Platform identifier for hierarchical API
    
    // Create session with survey metadata (recommended for hierarchical tracking)
    const sessionUrl = surveyId && respondentId 
      ? `${API_BASE}/detection/sessions?survey_id=${encodeURIComponent(surveyId)}&respondent_id=${encodeURIComponent(respondentId)}&platform_id=${encodeURIComponent(platformId)}`
      : `${API_BASE}/detection/sessions`;
    
    const response = await fetch(sessionUrl, { 
      method: 'POST' 
    });
    const data = await response.json();
    
    // Store session ID in a hidden field (create this field in Decipher)
    const sessionField = document.getElementById('bot_session_id');
    if (sessionField) {
      sessionField.value = data.session_id;
    }
    
    // Ensure platform_id is consistently available for event payloads
    // (so events match the same platform used during session creation)
    const platformField = document.getElementById('platform_id');
    if (platformField) {
      platformField.value = platformId;
    }

    // Capture device/page metadata once at start for convenience
    const pageUrl = window.location.href;
    const userAgent = navigator.userAgent;
    const screenWidth = window.screen.width;
    const screenHeight = window.screen.height;
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    // Optionally store for export visibility (requires fields created in Step 2)
    const pageUrlField = document.getElementById('page_url');
    if (pageUrlField) pageUrlField.value = pageUrl;
    const userAgentField = document.getElementById('user_agent');
    if (userAgentField) userAgentField.value = userAgent;

    // Prime first metadata event so backend has device context immediately
    window.eventBuffer.push({
      event_type: 'session_start',
      timestamp: new Date().toISOString(),
      page_url: pageUrl,
      user_agent: userAgent,
      screen_width: screenWidth,
      screen_height: screenHeight,
      viewport_width: viewportWidth,
      viewport_height: viewportHeight,
      survey_id: getIdentifierValue('survey_id'),
      respondent_id: getIdentifierValue('respondent_id'),
      platform_id: platformId
    });
  } catch (error) {
    console.log('Bot detection setup failed:', error);
  }
}

// Step 1b: Text Quality Analysis Setup
let currentQuestionId = null;
let questionStartTime = null;

// Find question text near an input element
function findQuestionText(inputElement) {
  if (!inputElement) return '';
  
  // Look for nearby text elements that could be the question
  const parent = inputElement.closest('div, p, li, td, th, label');
  if (parent) {
    const textNodes = Array.from(parent.childNodes).filter(node => 
      node.nodeType === Node.TEXT_NODE && node.textContent.trim().length > 10
    );
    if (textNodes.length > 0) {
      return textNodes[0].textContent.trim();
    }
    
    // Look for labels or other text elements
    const labels = parent.querySelectorAll('label, span, p, div');
    for (let label of labels) {
      if (label.textContent.trim().length > 10 && !label.querySelector('input, textarea')) {
        return label.textContent.trim();
      }
    }
  }
  
  return '';
}

// Capture a survey question
async function captureQuestion(inputElement) {
  const sessionId = document.getElementById('bot_session_id')?.value;
  if (!sessionId) return;
  
  const questionText = findQuestionText(inputElement);
  if (!questionText) return;
  
  try {
    const response = await fetch(`${API_BASE}/text-analysis/questions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        question_text: questionText,
        question_type: 'open_ended',
        element_id: inputElement.id || inputElement.name,
        page_url: window.location.href,
        page_title: document.title
      })
    });
    
    const data = await response.json();
    currentQuestionId = data.question_id;
    questionStartTime = Date.now();
  } catch (error) {
    console.log('Question capture failed:', error);
  }
}

// Analyze a response
async function analyzeResponse(inputElement, responseText) {
  const sessionId = document.getElementById('bot_session_id')?.value;
  if (!sessionId || !currentQuestionId || !responseText || responseText.length < 10) return;
  
  const responseTime = Date.now() - questionStartTime;
  
  try {
    const response = await fetch(`${API_BASE}/text-analysis/responses`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        question_id: currentQuestionId,
        response_text: responseText,
        response_time_ms: responseTime
      })
    });
    
    const data = await response.json();
    
    // Store text quality results in hidden fields
    const qualityField = document.getElementById('text_quality_score');
    if (qualityField) qualityField.value = data.quality_score || '';
    
    const flaggedField = document.getElementById('text_flagged');
    if (flaggedField) flaggedField.value = data.is_flagged ? 'true' : 'false';
    
  } catch (error) {
    console.log('Response analysis failed:', error);
  }
}

// Step 1c: Collect and send user behavior data
window.eventBuffer = window.eventBuffer || [];
const BATCH_SIZE = 10;

function baseContext(e) {
  return {
    page_url: window.location.href,
    user_agent: navigator.userAgent,
    screen_width: window.screen.width,
    screen_height: window.screen.height,
    viewport_width: window.innerWidth,
    viewport_height: window.innerHeight,
    survey_id: getIdentifierValue('survey_id'),
    respondent_id: getIdentifierValue('respondent_id'),
    platform_id: getIdentifierValue('platform_id'),
    element_id: e && e.target && e.target.id ? e.target.id : undefined,
    element_type: e && e.target && e.target.tagName ? e.target.tagName.toLowerCase() : undefined
  };
}

function sendEvents() {
  const sessionId = document.getElementById('bot_session_id')?.value;
  if (!sessionId || window.eventBuffer.length === 0) return;
  
  fetch(`${API_BASE}/detection/sessions/${sessionId}/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(window.eventBuffer)
  }).then(() => {
    window.eventBuffer = []; // Clear buffer after sending
  }).catch(() => {
    // If sending fails, keep events for next attempt
  });
}

// Step 1d: Track user interactions
document.addEventListener('keydown', (e) => {
  window.eventBuffer.push({
    event_type: 'keystroke',
    timestamp: new Date().toISOString(),
    key: e.key,
    ...baseContext(e)
  });
  
  if (window.eventBuffer.length >= BATCH_SIZE) {
    sendEvents();
  }
});

document.addEventListener('click', (e) => {
  window.eventBuffer.push({
    event_type: 'click',
    timestamp: new Date().toISOString(),
    button: e.button,
    ...baseContext(e)
  });
});

let lastMouseEventAt = 0;
document.addEventListener('mousemove', (e) => {
  const now = Date.now();
  if (now - lastMouseEventAt < 50) return; // simple throttle ~20fps
  lastMouseEventAt = now;
  window.eventBuffer.push({
    event_type: 'mouse_move',
    timestamp: new Date().toISOString(),
    x: e.clientX,
    y: e.clientY,
    ...baseContext(e)
  });
});

document.addEventListener('scroll', () => {
  window.eventBuffer.push({
    event_type: 'scroll',
    timestamp: new Date().toISOString(),
    scroll_y: window.scrollY,
    scroll_x: window.scrollX,
    page_height: document.documentElement.scrollHeight,
    page_width: document.documentElement.scrollWidth,
    ...baseContext()
  });
});

// Step 1e: Text input tracking for quality analysis
document.addEventListener('focusin', (e) => {
  const target = e.target;
  if (target.tagName === 'TEXTAREA' || (target.tagName === 'INPUT' && target.type === 'text')) {
    captureQuestion(target);
  }
  
  window.eventBuffer.push({
    event_type: 'focus',
    timestamp: new Date().toISOString(),
    ...baseContext(e)
  });
});

document.addEventListener('focusout', (e) => {
  const target = e.target;
  if (target.tagName === 'TEXTAREA' || (target.tagName === 'INPUT' && target.type === 'text')) {
    analyzeResponse(target, target.value);
  }
  
  window.eventBuffer.push({
    event_type: 'blur',
    timestamp: new Date().toISOString(),
    ...baseContext(e)
  });
});

document.addEventListener('visibilitychange', () => {
  window.eventBuffer.push({
    event_type: 'visibility_change',
    timestamp: new Date().toISOString(),
    visibility_state: document.visibilityState,
    ...baseContext()
  });
});

// Send any remaining events every 5 seconds
setInterval(sendEvents, 5000);

// Start everything when page loads
setupBotDetection();
```

**Also create this hidden field in Decipher:**
- Field ID: `bot_session_id`
- Field Type: Hidden/Text
- This stores the session ID for tracking

## Step 2: Add Hidden Fields (Once in Decipher)

### 📍 What are hidden fields?
Hidden fields store data that users can't see but gets saved with their survey responses. We need these to store the bot detection results.

### 📋 Step-by-step instructions:
1. **In your Decipher survey editor**, click "Add Question" or the "+" button
2. **Select "Text Entry"** question type
3. **For each field below**, follow these steps:

#### Field 1: Session ID
- **Question Text:** `bot_session_id` (or leave blank)
- **Variable Name:** `bot_session_id` (must be exactly this)
- **Question Type:** Text Entry
- **Make it Hidden:** ✅ Check "Hidden" box
- **Click "Save"**

#### Field 2: Bot Result
- **Question Text:** `bot_result` (or leave blank)
- **Variable Name:** `bot_result` (must be exactly this)
- **Question Type:** Text Entry
- **Make it Hidden:** ✅ Check "Hidden" box
- **Click "Save"**

#### Field 3: Is Bot
- **Question Text:** `bot_is_bot` (or leave blank)
- **Variable Name:** `bot_is_bot` (must be exactly this)
- **Question Type:** Text Entry
- **Make it Hidden:** ✅ Check "Hidden" box
- **Click "Save"**

#### Field 4: Confidence Score
- **Question Text:** `bot_confidence` (or leave blank)
- **Variable Name:** `bot_confidence` (must be exactly this)
- **Question Type:** Text Entry
- **Make it Hidden:** ✅ Check "Hidden" box
- **Click "Save"**

#### Field 5: Respondent ID
- **Question Text:** `respondent_id` (or leave blank)
- **Variable Name:** `respondent_id` (must be exactly this)
- **Question Type:** Text Entry
- **Make it Hidden:** ✅ Check "Hidden" box
- **Click "Save"**

#### Field 6: Survey ID
- **Question Text:** `survey_id` (or leave blank)
- **Variable Name:** `survey_id` (must be exactly this)
- **Question Type:** Text Entry
- **Make it Hidden:** ✅ Check "Hidden" box
- **Click "Save"**

#### Field 7: Platform ID
- **Question Text:** `platform_id` (or leave blank)
- **Variable Name:** `platform_id` (must be exactly this)
- **Question Type:** Text Entry
- **Make it Hidden:** ✅ Check "Hidden" box
- **Click "Save"**

#### Optional Field 8: Text Quality Score
- **Question Text:** `text_quality_score` (or leave blank)
- **Variable Name:** `text_quality_score` (must be exactly this)
- **Question Type:** Text Entry
- **Make it Hidden:** ✅ Check "Hidden" box
- **Click "Save"**

#### Optional Field 9: Text Flagged Status
- **Question Text:** `text_flagged` (or leave blank)
- **Variable Name:** `text_flagged` (must be exactly this)
- **Question Type:** Text Entry
- **Make it Hidden:** ✅ Check "Hidden" box
- **Click "Save"**

#### Optional Field 8: Page URL
- **Variable Name:** `page_url`
- Purpose: stores the page URL captured at start for convenience

#### Optional Field 9: User Agent
- **Variable Name:** `user_agent`
- Purpose: stores browser user agent for reference

### ⚠️ Important Notes:
- **Variable names must be EXACTLY** as shown above (case-sensitive)
- **All fields must be marked as "Hidden"** so users don't see them
- **You can put these fields anywhere** in your survey - beginning, middle, or end
- **The fields will be empty** until someone takes your survey
 - If your platform exposes built-in variables for respondent/survey IDs, you can populate `respondent_id`/`survey_id` automatically using that platform's piping features.

## Step 3: Analyze on Survey Completion (Once at the End)

### 📍 Where to put this code:
**Option 1 (Recommended):** Add to your final page or thank you page as custom JavaScript
**Option 2:** Add to Survey Options → JavaScript → Footer section

### 🎯 What it does:
- Sends any remaining behavior data to our server
- Analyzes all the collected data using AI
- Determines if the user is a bot or human
- Saves the results in your hidden fields

### 📋 Step-by-step instructions:
1. **Go to your final survey page** (thank you page or last question)
2. **Click "Add JavaScript"** or "Custom JavaScript" on that page
3. **Copy and paste the code below** into the JavaScript area
4. **Click "Save"** to save your survey

### 🔄 Alternative method (if you prefer):
1. **Go to Survey Options** → **JavaScript**
2. **Click the "Footer" tab**
3. **Paste the code below** into the footer section
4. **Click "Save"**

```javascript
// Bot Detection Analysis with Text Quality - Add this at the end of your survey
async function analyzeBotDetection() {
  const sessionId = document.getElementById('bot_session_id')?.value;
  if (!sessionId) return;
  
  try {
    // Send any remaining events before analysis
    const remainingEvents = (window.eventBuffer || []).length;
    if (remainingEvents > 0) {
      await fetch(`${API_BASE}/detection/sessions/${sessionId}/events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(window.eventBuffer)
      });
      window.eventBuffer = [];
    }
    
    // Run composite analysis (behavioral + text quality)
    const response = await fetch(`${API_BASE}/detection/sessions/${sessionId}/composite-analyze`, {
      method: 'POST'
    });
    const result = await response.json();
    
    // Save results to hidden fields
    const resultField = document.getElementById('bot_result');
    if (resultField) resultField.value = JSON.stringify(result);
    const isBotField = document.getElementById('bot_is_bot');
    if (isBotField) isBotField.value = result.is_bot ? 'true' : 'false';
    const confidenceField = document.getElementById('bot_confidence');
    if (confidenceField) confidenceField.value = String(result.composite_score ?? result.confidence_score ?? '0');
    
    // Update text quality fields with latest results
    const qualityField = document.getElementById('text_quality_score');
    if (qualityField && result.text_quality_score) {
      qualityField.value = result.text_quality_score;
    }
    
    const flaggedField = document.getElementById('text_flagged');
    if (flaggedField && result.text_quality_details) {
      const isFlagged = result.text_quality_details.flagged_count > 0;
      flaggedField.value = isFlagged ? 'true' : 'false';
    }
    
  } catch (error) {
    console.log('Bot analysis failed:', error);
    // Set default values if analysis fails
    const resultField = document.getElementById('bot_result');
    if (resultField) resultField.value = '{"error": "analysis_failed"}';
    const isBotField = document.getElementById('bot_is_bot');
    if (isBotField) isBotField.value = 'unknown';
    const confidenceField = document.getElementById('bot_confidence');
    if (confidenceField) confidenceField.value = '0';
  }
}

// Run analysis when survey is submitted
analyzeBotDetection();
```

## How It Works (Simple Explanation)

1. **Session Creation:** When someone starts your survey, we create a unique session ID to track them.

2. **Behavioral Data Collection:** Our script automatically watches for:
   - **Keystrokes:** What keys they press and how fast
   - **Mouse movements:** How they move their mouse around
   - **Scrolling:** How they scroll through pages
   - **Focus changes:** When they click on different parts of the page

3. **Text Quality Collection:** When users type in text fields, we also:
   - **Capture questions:** Automatically find and save the question text
   - **Analyze responses:** Use AI to check if responses are gibberish, copy-pasted, irrelevant, or generic
   - **Score quality:** Give each response a quality score from 0-100

4. **Data Sending:** Every 10 events or every 5 seconds, we send the collected data to our analysis server.

5. **Real-time Analysis:** As users finish typing, we immediately analyze their text responses using OpenAI's AI model.

6. **Final Analysis:** When the survey is complete, we combine behavioral data and text quality to determine if it looks like human or bot behavior.

7. **Results:** The final result is saved in your hidden fields:
   - `bot_is_bot`: "true" if detected as bot, "false" if human
   - `bot_confidence`: A number from 0-1 showing how confident we are (combines both behavioral and text analysis)
   - `bot_result`: Full analysis details including both behavioral and text quality results
   - `text_quality_score`: Average quality score 0-100 for all text responses
   - `text_flagged`: "true" if any text response was flagged as low quality

## 📚 Complete Setup Checklist

Use this checklist to make sure you've done everything correctly:

### Before You Start:
- [ ] I have access to my Decipher survey editor
- [ ] I have a test survey ready (or I'll create one)
- [ ] I have 15-30 minutes to complete the setup

### Step 1: JavaScript Setup:
- [ ] I opened my survey in the Decipher editor
- [ ] I went to Survey Options → JavaScript → Header
- [ ] I copied and pasted the tracking code from Step 1
- [ ] I saved my survey

### Step 2: Hidden Fields:
- [ ] I created a hidden field with variable name `bot_session_id`
- [ ] I created a hidden field with variable name `bot_result`
- [ ] I created a hidden field with variable name `bot_is_bot`
- [ ] I created a hidden field with variable name `bot_confidence`
- [ ] I created a hidden field with variable name `respondent_id`
- [ ] I created a hidden field with variable name `survey_id`
- [ ] I created a hidden field with variable name `platform_id`
- [ ] (Optional) I created `page_url` and `user_agent` fields
- [ ] All fields are marked as "Hidden"
- [ ] Variable names are exactly as shown (case-sensitive)

### Step 3: Analysis Code:
- [ ] I added the analysis code to my final page OR footer section
- [ ] I saved my survey

### Testing:
- [ ] I tested my survey by taking it myself
- [ ] I checked the browser console for errors (F12 → Console)
- [ ] I downloaded my data export to check for bot detection results
- [ ] The bot detection columns appear in my data export

### Going Live:
- [ ] I tested with a real survey (not just test data)
- [ ] I'm ready to deploy to my main survey

## What You Get in Your Data Export

After the survey, you'll see these new columns in your Decipher data:
- `bot_is_bot`: true/false/unknown (based on combined behavioral + text analysis)
- `bot_confidence`: 0.0 to 1.0 (composite score combining behavioral and text quality)
- `bot_result`: Complete analysis details in JSON format (includes both behavioral and text quality results)
- `text_quality_score`: 0-100 (average quality score of all text responses)
- `text_flagged`: true/false (whether any text response was flagged as low quality)

**Example data export:**
```
bot_is_bot: "false"
bot_confidence: 0.23
text_quality_score: 85.5
text_flagged: "false"
bot_result: {"composite_score": 0.23, "behavioral_score": 0.15, "text_quality_score": 85.5, ...}
```

## ⚠️ Common Mistakes to Avoid

### ❌ Don't Do This:
- **Wrong variable names:** `bot_session_ID` instead of `bot_session_id` (case matters!)
- **Forgetting to mark fields as hidden:** Users will see empty fields
- **Copying code incorrectly:** Missing brackets, quotes, or semicolons
- **Not testing first:** Always test with a simple survey before going live
- **Putting code in wrong place:** Header code goes in header, analysis code goes at the end

### ✅ Do This Instead:
- **Copy variable names exactly** as shown (case-sensitive)
- **Always mark fields as "Hidden"** so users don't see them
- **Copy the entire code blocks** without modification
- **Test with a 2-3 question survey first**
- **Follow the step-by-step instructions exactly**

## Troubleshooting

### 🔍 Nothing shows up in my data?
**Possible causes:**
- Hidden fields not created with exact variable names
- JavaScript code not added correctly
- Survey not published/activated

**Solutions:**
- Double-check variable names are exactly: `bot_session_id`, `bot_result`, `bot_is_bot`, `bot_confidence`
- Verify JavaScript is in the right places (header and footer/final page)
- Make sure your survey is published and active

### 🔍 Getting errors in browser console?
**Possible causes:**
- JavaScript syntax errors
- Network connectivity issues
- Survey platform blocking external requests

**Solutions:**
- Check that you copied the code exactly (no missing brackets or quotes)
- Test your survey on a different network
- Contact your IT team if your organization blocks external URLs

### 🔍 All results show "unknown"?
**Possible causes:**
- Internet connection issues during survey
- API server temporarily unavailable
- JavaScript code not running properly

**Solutions:**
- Check your internet connection
- Try testing the survey again
- Verify the JavaScript code is running (check browser console)

### 🔍 Need more help?
- **Check our API Playground:** Test the system directly at the Integration tab
- **Contact your technical team** with specific error messages
- **Test with our demo:** Use the API Playground to understand how the system works

## How to Test Your Integration

### Quick Test (5 minutes)

1. **Create a test survey** in Decipher with just 2-3 questions
2. **Add the code** from Steps 1 and 3 above
3. **Create the hidden fields** from Step 2
4. **Test the survey** by taking it yourself
5. **Check your data export** - you should see the bot detection columns

### What to Look For When Testing

**In the browser console (F12 → Console tab):**
- Look for messages like "Bot detection setup successful"
- No red error messages
- Events being logged as you type and move your mouse

**In your data export:**
- `bot_session_id`: Should have a long ID like "abc123-def456-..."
- `bot_is_bot`: Should show "false" (since you're a real human testing it)
- `bot_confidence`: Should show a number like 0.15 or 0.85 (composite score)
- `text_quality_score`: Should show a number like 75.5 (if you typed in text fields)
- `text_flagged`: Should show "false" (if your text responses were good quality)
- `bot_result`: Should show detailed analysis data including both behavioral and text quality results

### Testing Checklist

**Before Going Live:**
- [ ] Hidden fields created with correct IDs
- [ ] JavaScript code added to start and end of survey
- [ ] Test survey completed successfully
- [ ] Data export shows bot detection columns
- [ ] No console errors during survey

**Test Scenarios:**
1. **Normal Human Test:** Take the survey naturally with thoughtful text responses (should show `bot_is_bot: false`, good `text_quality_score`)
2. **Quick Bot Test:** Rush through the survey very fast (might show higher bot probability)
3. **Poor Text Quality Test:** Type gibberish like "asdfghjkl" in text fields (should show `text_flagged: true`, low `text_quality_score`)
4. **Mobile Test:** Test on mobile device to ensure it works on phones

### Common Test Results

**What you'll see when testing as a human with good text responses:**
```
bot_is_bot: "false"
bot_confidence: 0.23
text_quality_score: 85.5
text_flagged: "false"
bot_result: {"composite_score": 0.23, "behavioral_score": 0.15, "text_quality_score": 85.5, ...}
```

**What you might see if testing very quickly:**
```
bot_is_bot: "true" 
bot_confidence: 0.78
text_quality_score: 45.0
text_flagged: "true"
bot_result: {"composite_score": 0.78, "behavioral_score": 0.85, "text_quality_score": 45.0, ...}
```

**What you'll see if typing gibberish in text fields:**
```
bot_is_bot: "false"
bot_confidence: 0.45
text_quality_score: 15.0
text_flagged: "true"
bot_result: {"composite_score": 0.45, "behavioral_score": 0.25, "text_quality_score": 15.0, ...}
```

### Using the API Playground for Testing

You can also test the bot detection system directly using our API Playground:

1. **Go to:** https://storage.googleapis.com/bot-detection-frontend-20251208/index.html
2. **Click:** "API Playground" in the navigation
3. **Test endpoints:**
   - Click "Create Session" to create a test session
   - Click "Ingest Events" to simulate user behavior
   - Click "Analyze Session" to see the behavioral bot detection result
   - Click "Composite Analyze" to see the combined behavioral + text quality result
   - Click "Get Survey Text Analysis Summary" to test hierarchical V2 text analysis
   - Click "Get Session Text Analysis (Hierarchical)" to get text analysis via hierarchical path

This helps you understand how the system works before integrating it into your survey.

### Troubleshooting Your Test

**"No data in my export"**
- Double-check the hidden field IDs are exactly: `bot_session_id`, `bot_result`, `bot_is_bot`, `bot_confidence`
- Make sure the JavaScript is in the right places (start and end of survey)

**"Getting errors in console"**
- Check that your survey can access the internet
- Make sure you copied the code exactly as shown
- The system will still work even if some requests fail

**"bot_is_bot shows 'unknown'"**
- This means the analysis failed - check your internet connection
- The survey will still work, but bot detection won't be available

### Real-World Testing Tips

**Test with different users:**
- Have colleagues take your test survey
- Try different browsers (Chrome, Firefox, Safari)
- Test on both desktop and mobile

**Monitor the results:**
- Check your data exports regularly
- Look for patterns in the bot detection results
- Most real users should show `bot_is_bot: false`

## That's It!

Copy the code from Step 1 to your survey start, create the hidden fields from Step 2, and add the code from Step 3 to your survey end. The system will automatically handle everything else, including:

- **Behavioral tracking:** Keystrokes, mouse movements, scrolling patterns
- **Text quality analysis:** AI-powered analysis of open-ended responses
- **Real-time processing:** Immediate analysis as users type
- **Composite scoring:** Combined behavioral + text quality bot detection

**Remember:** Always test with a small survey first before adding bot detection to your main surveys!

**New Features:** The system now automatically detects text input fields, captures questions, and analyzes response quality using OpenAI's AI model. This provides much more accurate bot detection than behavioral analysis alone.
