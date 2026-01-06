# OpenAI Connection Error Fix

## Problem Identified

The logs show that all OpenAI API calls are failing with "Connection error" messages:

```
2026-01-06 18:06:03,944 - app.services.openai_service - ERROR - OpenAI API error on attempt 1: Connection error.
2026-01-06 18:06:06,345 - app.services.openai_service - ERROR - OpenAI API error on attempt 2: Connection error.
2026-01-06 18:06:09,853 - app.services.openai_service - ERROR - OpenAI API error on attempt 3: Connection error.
```

## Root Cause

Cloud Run service has the annotation `run.googleapis.com/vpc-access-egress: private-ranges-only` which restricts all outbound traffic to private IP ranges only. This blocks access to public internet APIs like OpenAI.

**Current Service Configuration:**
```yaml
run.googleapis.com/vpc-access-connector: serverless-connector
run.googleapis.com/vpc-access-egress: private-ranges-only  # ❌ This blocks OpenAI API
```

## Solution

Remove the `vpc-access-egress` annotation to enable Cloud Run's **default split routing**:

- **Private IPs** (Cloud SQL) → VPC connector ✅
- **Public IPs** (OpenAI API) → Default internet gateway ✅

This is better than Cloud NAT because:
1. Simpler - no additional infrastructure needed
2. More efficient - public traffic doesn't go through VPC
3. Uses Cloud Run's built-in split routing feature

## Implementation

### Option 1: Quick Fix (Update Current Service)

Update the service to remove the annotation:

```powershell
gcloud run services update bot-backend `
    --region=northamerica-northeast2 `
    --project=survey-bot-detection `
    --update-annotations="run.googleapis.com/vpc-access-egress="
```

### Option 2: Redeploy (Recommended)

The deployment scripts have been updated to remove this annotation. Simply redeploy:

```powershell
.\deploy-with-bot-db-v2.ps1
```

The updated deployment script includes:
```powershell
--update-annotations="run.googleapis.com/vpc-access-egress="
```

This removes the annotation and enables split routing.

## Verification

After removing the annotation, verify the configuration:

```powershell
gcloud run services describe bot-backend `
    --region=northamerica-northeast2 `
    --project=survey-bot-detection `
    --format="value(spec.template.metadata.annotations['run.googleapis.com/vpc-access-egress'])"
```

This should return empty (no value), indicating split routing is enabled.

Then test OpenAI API calls:

```powershell
cd backend
python test_production_text_analysis.py
```

## Expected Behavior After Fix

Once the annotation is removed:
- ✅ Cloud SQL connections work through VPC connector
- ✅ OpenAI API calls work through default internet gateway
- ✅ All text analysis tests should pass
- ✅ No Cloud NAT required

## Files Updated

- `deploy-with-bot-db-v2.ps1` - Added `--update-annotations` to remove vpc-access-egress
- `redeploy-backend-fixed.ps1` - Added `--update-annotations` to remove vpc-access-egress

## Alternative Solution (Not Needed)

~~Cloud NAT setup~~ - Not required when using split routing. The `setup-cloud-nat.ps1` script is not needed for this fix.
