# Next Steps to Fix Production Session Creation

## Current Status

### ✅ Completed
1. **Diagnosed root cause**: Missing Cloud SQL Client permissions + Unix socket connection issues
2. **Improved error logging**: Backend now logs detailed errors for debugging  
3. **Fixed test script**: Removed bugs in `test_production_text_analysis.py`
4. **Granted permissions**: Service account now has `roles/cloudsql.client`
5. **Redeployed backend**: Latest image with all fixes deployed
6. **Created diagnostic tools**: Scripts to test and fix database connection

### ⚠️ Current Issue
Session creation still fails with: `FileNotFoundError: [Errno 2] No such file or directory`

This means the Cloud SQL Unix socket is not being created at `/cloudsql/survey-bot-detection:northamerica-northeast2:bot-db`

## Option 1: Wait and Retry (Recommended First)

IAM permissions can take 5-10 minutes to fully propagate. 

**Wait 10 minutes, then test:**
```powershell
Invoke-RestMethod -Uri "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/detection/sessions?platform=web" -Method Post -Headers @{"User-Agent"="Test"}
```

**If successful**, run the full test suite:
```powershell
cd backend
python test_production_text_analysis.py
```

## Option 2: Use TCP Connection Instead of Unix Socket

If Option 1 doesn't work after 10 minutes, switch to TCP connection:

### Step 1: Get Cloud SQL Instance IP
```powershell
gcloud sql instances describe bot-db --format="value(ipAddresses[0].ipAddress)" --project=survey-bot-detection
```

### Step 2: Update DATABASE_URL Secret
Replace `INSTANCE_IP` with the IP from Step 1:
```powershell
$NEW_DB_URL = "postgresql+asyncpg://bot_user:NewPassword123!@INSTANCE_IP:5432/bot_detection"
echo $NEW_DB_URL | gcloud secrets versions add DATABASE_URL --data-file=- --project=survey-bot-detection
```

### Step 3: Redeploy Backend
```powershell
.\redeploy-backend-fixed.ps1
```

### Step 4: Test
```powershell
Invoke-RestMethod -Uri "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/detection/sessions?platform=web" -Method Post -Headers @{"User-Agent"="Test"}
```

## Option 3: Verify and Fix Database Schema

The database might be missing the `platform_id` column. To check:

### Using Cloud Shell (Recommended)
1. Open Cloud Shell: https://console.cloud.google.com/
2. Connect to database:
   ```bash
   gcloud sql connect bot-db --user=bot_user --database=bot_detection --project=survey-bot-detection
   ```
3. Check schema:
   ```sql
   \d sessions
   ```
4. If `platform_id` column is missing, run:
   ```sql
   ALTER TABLE sessions ADD COLUMN platform_id VARCHAR(255);
   CREATE INDEX idx_sessions_platform_id ON sessions(platform_id);
   ```

## Quick Check Commands

### Check Latest Logs
```powershell
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bot-backend" --limit=5 --format="value(timestamp,textPayload)" --project=survey-bot-detection
```

### Check Cloud SQL Instance Status
```powershell
gcloud sql instances describe bot-db --format="value(state)" --project=survey-bot-detection
```

### Check Service Account Permissions
```powershell
gcloud projects get-iam-policy survey-bot-detection --flatten="bindings[].members" --filter="bindings.members:119522247395-compute@developer.gserviceaccount.com"
```

## Files Created for You

1. **`backend/test_production_db_connection.py`** - Test database connectivity
2. **`redeploy-backend-fixed.ps1`** - Automated redeployment
3. **`run-production-schema-fix.ps1`** - Database schema migration
4. **`PRODUCTION_SESSION_FIX_SUMMARY.md`** - Detailed analysis of the issue
5. **`NEXT_STEPS_FOR_USER.md`** - This file

## Recommended Action Plan

1. ⏰ **Wait 10 minutes** (for IAM propagation)
2. 🧪 **Test session creation** 
3. ✅ **If works**: Run production test suite
4. ❌ **If still fails**: Try Option 2 (TCP connection)
5. 🔍 **If TCP works**: Great! Database schema might need fixing
6. 🔧 **Verify schema**: Use Option 3 to check/fix database
7. 🎉 **Run full tests**: `python backend/test_production_text_analysis.py`

## Success Criteria

When everything works, you should see:
```json
{
  "session_id": "some-uuid-here",
  "created_at": "2026-01-05T...",
  "status": "active"
}
```

And all 5 text analysis tests should pass with 100% success rate.

## Need Help?

- Check `PRODUCTION_SESSION_FIX_SUMMARY.md` for detailed technical analysis
- Review Cloud Run logs for latest errors
- The diagnostic scripts are ready to use when needed

---

**Current Service URL**: https://bot-backend-119522247395.northamerica-northeast2.run.app

**Current Image**: `northamerica-northeast2-docker.pkg.dev/survey-bot-detection/backend/bot-backend:fix-db-connection`

**Latest Revision**: `bot-backend-00036-hav` (test), `bot-backend-00035-xxx` (main)
