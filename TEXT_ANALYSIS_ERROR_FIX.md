# Text Analysis Error Fix

## Problem
Text analysis tests are failing in production. All analysis checks return "Analysis failed" with no details about what went wrong. The health check shows OpenAI is available, but actual API calls are failing.

## Root Cause
The error handling in `text_analysis_service.py` was catching exceptions from OpenAI API calls but only logging generic "Analysis failed" messages without the actual error details. This made it impossible to diagnose the real issue.

## Solution Implemented

### 1. Enhanced Error Logging
Updated `backend/app/services/text_analysis_service.py` to:
- Log actual exception details with full stack traces
- Include error messages in the analysis result reasons
- Use `logger.error()` with `exc_info=result` to capture full exception context

### Changes Made
- Modified the `analyze_response()` method to properly log exceptions
- Added a `process_result()` helper function that:
  - Detects when results are exceptions
  - Logs the full error with stack trace
  - Includes the actual error message in the returned result

### Code Changes
```python
def process_result(result, name, default_result):
    """Process a single analysis result, handling exceptions."""
    if isinstance(result, Exception):
        error_msg = str(result)
        logger.error(f"Text analysis failed for {name}: {error_msg}", exc_info=result)
        # Create a copy and include error details
        error_result = default_result.copy() if isinstance(default_result, dict) else default_result
        if isinstance(error_result, dict):
            if "reason" in error_result:
                error_result["reason"] = f"Analysis failed: {error_msg}"
            elif "reasoning" in error_result:
                error_result["reasoning"] = f"Analysis failed: {error_msg}"
        return error_result
    return result
```

## Next Steps

### 1. Redeploy Backend
Deploy the updated code to production:
```powershell
.\deploy-with-bot-db-v2.ps1
```

### 2. Check Cloud Run Logs
After redeployment, check the logs to see actual error messages:
```powershell
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bot-backend" --limit 50 --format json --project survey-bot-detection
```

Or view in Cloud Console:
- Go to Cloud Run → bot-backend → Logs
- Filter for "Text analysis failed" or "OpenAI"

### 3. Common Issues to Check

#### API Key Issues
- Verify the secret exists and has the correct value:
  ```powershell
  gcloud secrets versions access latest --secret=OPENAI_API_KEY --project survey-bot-detection
  ```
- Check if the API key is valid and has credits/quota

#### Network Issues
- Cloud Run might not have internet access (check VPC connector configuration)
- OpenAI API might be blocked by firewall rules

#### Timeout Issues
- Current timeout is 30 seconds (OPENAI_TIMEOUT)
- May need to increase if OpenAI API is slow

#### Rate Limiting
- Check if OpenAI API rate limits are being hit
- Current rate limiter allows 100 requests/minute

### 4. Test Again
After identifying and fixing the root cause, run the test again:
```powershell
cd backend
python test_production_text_analysis.py
```

## Expected Behavior After Fix

Once the root cause is fixed, you should see:
- Detailed error messages in Cloud Run logs showing the actual OpenAI API error
- Analysis results that either:
  - Successfully analyze text and return proper flags
  - Show specific error messages (e.g., "Analysis failed: OpenAI API error: Invalid API key")

## Files Modified
- `backend/app/services/text_analysis_service.py` - Enhanced error logging

## Related Files
- `backend/test_production_text_analysis.py` - Test script
- `backend/app/services/openai_service.py` - OpenAI service implementation
- `backend/app/config.py` - Configuration (OPENAI_API_KEY, OPENAI_TIMEOUT, etc.)
