# Production Rollback Procedures

## Backend Rollback (Cloud Run)

### Current State
- **Active Revision**: `bot-backend-00069-28j` (100% traffic, image tag `cfc4499`)
- **Previous Revision**: `bot-backend-00068-2rf` (rollback target)
- **Service**: `bot-backend`
- **Region**: `northamerica-northeast2`
- **Project**: `survey-bot-detection`
- **Resources**: 1 CPU, 1 GiB memory, min 1 / max 10 instances
- **Cloud SQL**: `bot-db` and `bot-db-v2`; VPC connector `serverless-connector`

Switching traffic back to an older revision does not change the database. The
tables added in this release (`tracked_surveys`, `survey_quality_rules`,
`app_settings`) stay in place and the older revision ignores them. Existing
tables were not changed, so no database rollback is needed.

### Rollback Commands

#### Option 1: Switch to Previous Revision (Recommended)
```bash
# Switch 100% traffic to previous revision
gcloud run services update-traffic bot-backend \
  --to-revisions=bot-backend-00068-2rf=100 \
  --region=northamerica-northeast2 \
  --project=survey-bot-detection
```

#### Option 2: Gradual Rollback (Canary)
```bash
# Split traffic 50/50 between current and previous
gcloud run services update-traffic bot-backend \
  --to-revisions=bot-backend-00069-28j=50,bot-backend-00068-2rf=50 \
  --region=northamerica-northeast2 \
  --project=survey-bot-detection
```

#### Option 3: Complete Rollback to Specific Revision
```bash
# List revisions first
gcloud run revisions list --service=bot-backend \
  --region=northamerica-northeast2 \
  --project=survey-bot-detection

# Rollback to any specific revision
gcloud run services update-traffic bot-backend \
  --to-revisions=<revision-name>=100 \
  --region=northamerica-northeast2 \
  --project=survey-bot-detection
```

#### Rolling forward again
To send traffic back to the newest revision after a fix:
```bash
gcloud run services update-traffic bot-backend \
  --to-latest \
  --region=northamerica-northeast2 \
  --project=survey-bot-detection
```

Do not roll back by running `deploy-backend.ps1`. As written it uses
`--set-env-vars` and `--set-secrets`, which replace all environment variables
and secrets, and it connects only `bot-db`. Running it as is drops settings
(including `ADMIN_TOKEN`) and the `bot-db-v2` connection. See
`SELECTIVE_DEPLOYMENT_GUIDE.md` for the safe deploy commands.

### Verification Commands
```bash
# Check current traffic distribution
gcloud run services describe bot-backend \
  --region=northamerica-northeast2 \
  --project=survey-bot-detection \
  --format="value(status.traffic[].revisionName,status.traffic[].percent)"

# Test health endpoint
curl https://bot-backend-119522247395.northamerica-northeast2.run.app/health

# Check metrics endpoint
curl https://bot-backend-119522247395.northamerica-northeast2.run.app/metrics
```

## Frontend Rollback (Cloud Storage)

### Current State
- **Bucket**: `bot-detection-frontend-20251208`
- **Region**: `northamerica-northeast2`
- **Project**: `survey-bot-detection`
- **Addresses**: the dashboard uses hash URLs, for example
  `https://storage.googleapis.com/bot-detection-frontend-20251208/index.html#/quality`

### Rollback Commands

#### Option 1: Re-deploy Previous Build
```bash
# Check out the previous commit and rebuild
git checkout HEAD~1
cd frontend
npm ci
npx vite build --mode production
cd ..

# Sync previous build to bucket
gcloud storage rsync -r frontend/dist gs://bot-detection-frontend-20251208 \
  --project=survey-bot-detection

# Restore cache headers
gcloud storage objects update gs://bot-detection-frontend-20251208/index.html \
  --cache-control="no-cache" \
  --project=survey-bot-detection

gcloud storage objects update "gs://bot-detection-frontend-20251208/assets/**" \
  --cache-control="public, max-age=31536000, immutable" \
  --project=survey-bot-detection

# Go back to main afterwards
git checkout main
```

Do not add `--delete-unmatched-destination-objects` to the rsync. The bucket
holds `tracking-client.js`, which live surveys may load. It is not part of the
frontend build and must not be deleted.

#### Option 2: Restore from Backup (if available)
```bash
# If you have a backup of the previous dist folder
gcloud storage rsync -r backup-dist/ gs://bot-detection-frontend-20251208 \
  --project=survey-bot-detection
```

### Verification Commands
```bash
# Test frontend accessibility
curl https://storage.googleapis.com/bot-detection-frontend-20251208/index.html

# Check if API calls work from frontend
# Open in a browser: https://storage.googleapis.com/bot-detection-frontend-20251208/index.html#/
```

## Emergency Rollback Checklist

### When to Rollback
- [ ] Health endpoint returns 5xx errors
- [ ] API response times > 5 seconds
- [ ] Database connection failures
- [ ] Frontend shows blank page or errors
- [ ] User reports of broken functionality
- [ ] Error rates spike > 10%

### Rollback Decision Tree
1. **Immediate Impact**: If service is completely down → Full rollback
2. **Performance Issues**: If slow but functional → Gradual rollback
3. **Minor Issues**: If only some features broken → Investigate first

### Post-Rollback Actions
1. **Verify Service**: Test all critical endpoints
2. **Monitor Metrics**: Watch error rates and response times
3. **Notify Team**: Update stakeholders on rollback status
4. **Investigate**: Analyze logs to understand failure cause
5. **Plan Fix**: Prepare corrected deployment for next release

## Quick Reference

### Backend Rollback (1 command)
```bash
gcloud run services update-traffic bot-backend --to-revisions bot-backend-00068-2rf=100 --region northamerica-northeast2 --project survey-bot-detection
```

### Frontend Rollback
```bash
git checkout HEAD~1 && cd frontend && npx vite build --mode production && cd ..
gcloud storage rsync -r frontend/dist gs://bot-detection-frontend-20251208 --project=survey-bot-detection
gcloud storage objects update gs://bot-detection-frontend-20251208/index.html --cache-control="no-cache" --project=survey-bot-detection
gcloud storage objects update "gs://bot-detection-frontend-20251208/assets/**" --cache-control="public, max-age=31536000, immutable" --project=survey-bot-detection
```

### Health Check URLs
- **Backend Health**: https://bot-backend-119522247395.northamerica-northeast2.run.app/health
- **Backend Metrics**: https://bot-backend-119522247395.northamerica-northeast2.run.app/metrics
- **Frontend**: https://storage.googleapis.com/bot-detection-frontend-20251208/index.html

---
**Last Updated**: 2026-11-26
**Current Deployment**: Revision `bot-backend-00069-28j` (image tag `cfc4499`)
