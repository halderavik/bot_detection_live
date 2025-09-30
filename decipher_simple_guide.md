# Simple Decipher Integration Guide

This guide shows you exactly how to add bot detection to your Decipher survey in 3 simple steps. No complex options - just copy, paste, and you're done.

## What This Does
Our system watches how people interact with your survey (typing, mouse movements, scrolling) and determines if they're real humans or automated bots.

## Step 1: Add the Tracking Script (Once at the Beginning)

**Where to put this:** Add this to your survey's header or first page as custom JavaScript.

**What it does:** Creates a session and starts collecting data about user behavior.

```javascript
// Bot Detection Setup - Add this once at the start of your survey
const API_BASE = 'https://bot-backend-i56xopdg6q-pd.a.run.app/api/v1';

// Step 1a: Create a session when survey starts
async function setupBotDetection() {
  try {
    const response = await fetch(`${API_BASE}/detection/sessions`, { 
      method: 'POST' 
    });
    const data = await response.json();
    
    // Store session ID in a hidden field (create this field in Decipher)
    const sessionField = document.getElementById('bot_session_id');
    if (sessionField) {
      sessionField.value = data.session_id;
    }
  } catch (error) {
    console.log('Bot detection setup failed:', error);
  }
}

// Step 1b: Collect and send user behavior data
let eventBuffer = [];
const BATCH_SIZE = 10;

function sendEvents() {
  const sessionId = document.getElementById('bot_session_id')?.value;
  if (!sessionId || eventBuffer.length === 0) return;
  
  fetch(`${API_BASE}/detection/sessions/${sessionId}/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(eventBuffer)
  }).then(() => {
    eventBuffer = []; // Clear buffer after sending
  }).catch(() => {
    // If sending fails, keep events for next attempt
  });
}

// Step 1c: Track user interactions
document.addEventListener('keydown', (e) => {
  eventBuffer.push({
    event_type: 'keystroke',
    timestamp: new Date().toISOString(),
    key: e.key,
    element_id: e.target?.id || 'unknown'
  });
  
  if (eventBuffer.length >= BATCH_SIZE) {
    sendEvents();
  }
});

document.addEventListener('mousemove', (e) => {
  eventBuffer.push({
    event_type: 'mouse_move',
    timestamp: new Date().toISOString(),
    x: e.clientX,
    y: e.clientY
  });
});

document.addEventListener('scroll', () => {
  eventBuffer.push({
    event_type: 'scroll',
    timestamp: new Date().toISOString(),
    delta_y: window.scrollY
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

Create these hidden fields in your Decipher survey to store the results:

1. **Field ID:** `bot_session_id` (Text field, hidden)
2. **Field ID:** `bot_result` (Text field, hidden) 
3. **Field ID:** `bot_is_bot` (Text field, hidden)
4. **Field ID:** `bot_confidence` (Text field, hidden)

## Step 3: Analyze on Survey Completion (Once at the End)

**Where to put this:** Add this to your final page or thank you page as custom JavaScript.

**What it does:** Analyzes all the collected data and saves the bot detection result.

```javascript
// Bot Detection Analysis - Add this at the end of your survey
async function analyzeBotDetection() {
  const sessionId = document.getElementById('bot_session_id')?.value;
  if (!sessionId) return;
  
  try {
    // Send any remaining events before analysis
    const remainingEvents = eventBuffer.length;
    if (remainingEvents > 0) {
      await fetch(`${API_BASE}/detection/sessions/${sessionId}/events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(eventBuffer)
      });
      eventBuffer = [];
    }
    
    // Analyze the session
    const response = await fetch(`${API_BASE}/detection/sessions/${sessionId}/analyze`, {
      method: 'POST'
    });
    const result = await response.json();
    
    // Save results to hidden fields
    document.getElementById('bot_result').value = JSON.stringify(result);
    document.getElementById('bot_is_bot').value = result.is_bot ? 'true' : 'false';
    document.getElementById('bot_confidence').value = result.confidence_score;
    
  } catch (error) {
    console.log('Bot analysis failed:', error);
    // Set default values if analysis fails
    document.getElementById('bot_result').value = '{"error": "analysis_failed"}';
    document.getElementById('bot_is_bot').value = 'unknown';
    document.getElementById('bot_confidence').value = '0';
  }
}

// Run analysis when survey is submitted
analyzeBotDetection();
```

## How It Works (Simple Explanation)

1. **Session Creation:** When someone starts your survey, we create a unique session ID to track them.

2. **Data Collection:** Our script automatically watches for:
   - **Keystrokes:** What keys they press and how fast
   - **Mouse movements:** How they move their mouse around
   - **Scrolling:** How they scroll through pages
   - **Focus changes:** When they click on different parts of the page

3. **Data Sending:** Every 10 events or every 5 seconds, we send the collected data to our analysis server.

4. **Analysis:** When the survey is complete, we analyze all the collected behavior data to determine if it looks like human or bot behavior.

5. **Results:** The final result is saved in your hidden fields:
   - `bot_is_bot`: "true" if detected as bot, "false" if human
   - `bot_confidence`: A number from 0-1 showing how confident we are
   - `bot_result`: Full analysis details

## What You Get in Your Data Export

After the survey, you'll see these new columns in your Decipher data:
- `bot_is_bot`: true/false/unknown
- `bot_confidence`: 0.0 to 1.0 (higher = more confident)
- `bot_result`: Complete analysis details in JSON format

## Troubleshooting

**Nothing shows up in my data?**
- Make sure you created the hidden fields with the exact field IDs shown above
- Check that the JavaScript is running (look for errors in browser console)

**Getting errors?**
- The system will still work even if some requests fail
- Check that your survey can access the internet (no firewall blocks)

**Need help?**
- Contact your technical team with any integration questions

## That's It!

Copy the code from Step 1 to your survey start, create the hidden fields from Step 2, and add the code from Step 3 to your survey end. The system will automatically handle everything else.
