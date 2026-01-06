# Production Deployment Checklist for Text Analysis

## Issue Identified
Production deployment is showing "Analysis failed" for all OpenAI API calls, while local backend works correctly.

## Root Cause
The production deployment likely needs:
1. **Updated code** with the `response_format` fix in `openai_service.py`
2. **Valid OpenAI API key** in Secret Manager
3. **Redeployment** to apply the fixes

## Steps to Fix Production

### 1. Verify OpenAI API Key in Secret Manager
```powershell
# Check if the secret exists
gcloud secrets describe OPENAI_API_KEY --project=survey-bot-detection

# Update the secret with your current API key
echo "YOUR_OPENAI_API_KEY" | gcloud secrets versions add OPENAI_API_KEY --data-file=- --project=survey-bot-detection
```

### 2. Verify Code Has Latest Fix
The fix was made in `backend/app/services/openai_service.py`:
- Added `response_format={"type": "json_object"}` to `analyze_with_formatted_prompt` method
- Added `asyncio.wait_for` for timeout handling

### 3. Redeploy Backend
```powershell
cd backend
.\deploy-backend.ps1 `
  -ProjectId survey-bot-detection `
  -Region northamerica-northeast2 `
  -Service bot-backend `
  -ConnectorName serverless-connector `
  -InstanceName bot-db `
  -AllowedOrigins '["*"]'
```

Or use Cloud Build:
```powershell
gcloud builds submit --config cloudbuild.yaml --project survey-bot-detection
```

### 4. Verify Deployment
After redeployment, run the production test:
```powershell
cd backend
python test_production_text_analysis.py
```

## Current Status

### Local Backend ✅
- OpenAI API key: Working
- Database: Working (platform_id column added)
- All 5 text analysis checks: Working correctly
- Test results: 3/8 fully passed, 5/8 partially passed (core detection working)

### Production Backend ⚠️
- OpenAI API key: Needs verification/update
- Database: Working (sessions can be created)
- Text analysis: Failing with "Analysis failed"
- Status: Needs redeployment with latest code

## Verification Steps

1. **Check Production Health:**
   ```bash
   curl https://bot-backend-i56xopdg6q-pd.a.run.app/api/v1/text-analysis/health
   ```
   Should show: `"openai_available": true`

2. **Test Production Text Analysis:**
   ```bash
   cd backend
   python test_production_text_analysis.py
   ```

3. **Compare Results:**
   - Production should match local behavior
   - All 5 checks should work correctly
   - Quality scores should be in expected ranges

## Expected Results After Fix

After updating production:
- ✅ Gibberish detection: Working (confidence ~0.9)
- ✅ Copy-paste detection: Working (confidence ~0.85)
- ✅ Relevance analysis: Working
- ✅ Generic detection: Working
- ✅ Quality scoring: Working (scores 5-90)

## Notes

- The local backend is working correctly with the updated API key
- Production needs the same API key and code updates
- Once redeployed, production should match local behavior
