# Production Rollback Procedures

## Backend Rollback (Cloud Run)

### Current State
- **Active Revision**: `bot-backend-00018-7qv` (100% traffic)
- **Previous Revision**: `bot-backend-00017-ljv` (available for rollback)
- **Service**: `bot-backend`
- **Region**: `northamerica-northeast2`
- **Project**: `survey-bot-detection`

### Rollback Commands

#### Option 1: Switch to Previous Revision (Recommended)
```bash
# Switch 100% traffic to previous revision
gcloud run services update-traffic bot-backend \
  --to-revisions=bot-backend-00017-ljv=100 \
  --region=northamerica-northeast2 \
  --project=survey-bot-detection
```

#### Option 2: Gradual Rollback (Canary)
```bash
# Split traffic 50/50 between current and previous
gcloud run services update-traffic bot-backend \
  --to-revisions=bot-backend-00018-7qv=50,bot-backend-00017-ljv=50 \
  --region=northamerica-northeast2 \
  --project=survey-bot-detection
```

#### Option 3: Complete Rollback to Specific Revision
```bash
# Rollback to any specific revision
gcloud run services update-traffic bot-backend \
  --to-revisions=bot-backend-00016-kj8=100 \
  --region=northamerica-northeast2 \
  --project=survey-bot-detection
```

### Verification Commands
```bash
# Check current traffic distribution
gcloud run services describe bot-backend \
  --region=northamerica-northeast2 \
  --project=survey-bot-detection \
  --format="value(status.traffic[].revisionName,status.traffic[].percent)"

# Test health endpoint
curl https://bot-backend-i56xopdg6q-pd.a.run.app/health

# Check metrics endpoint
curl https://bot-backend-i56xopdg6q-pd.a.run.app/metrics
```

## Frontend Rollback (Cloud Storage)

### Current State
- **Bucket**: `bot-detection-frontend-20250929`
- **Region**: `northamerica-northeast2`
- **Project**: `survey-bot-detection`

### Rollback Commands

#### Option 1: Re-deploy Previous Build
```bash
# Checkout previous commit and rebuild
git checkout HEAD~1
cd frontend
npm ci
npm run build

# Sync previous build to bucket
gcloud storage rsync -r frontend/dist gs://bot-detection-frontend-20250929 \
  --project=survey-bot-detection

# Restore cache headers
gcloud storage objects update gs://bot-detection-frontend-20250929/index.html \
  --cache-control="no-cache" \
  --project=survey-bot-detection

gcloud storage objects update gs://bot-detection-frontend-20250929/assets/** \
  --cache-control="public, max-age=31536000, immutable" \
  --project=survey-bot-detection
```

#### Option 2: Restore from Backup (if available)
```bash
# If you have a backup of the previous dist folder
gcloud storage rsync -r backup-dist/ gs://bot-detection-frontend-20250929 \
  --project=survey-bot-detection
```

### Verification Commands
```bash
# Test frontend accessibility
curl https://storage.googleapis.com/bot-detection-frontend-20250929/index.html

# Check if API calls work from frontend
# Open browser and test: https://storage.googleapis.com/bot-detection-frontend-20250929/index.html
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
gcloud run services update-traffic bot-backend --to-revisions=bot-backend-00017-ljv=100 --region=northamerica-northeast2 --project=survey-bot-detection
```

### Frontend Rollback (3 commands)
```bash
git checkout HEAD~1 && cd frontend && npm run build
gcloud storage rsync -r frontend/dist gs://bot-detection-frontend-20250929 --project=survey-bot-detection
gcloud storage objects update gs://bot-detection-frontend-20250929/index.html --cache-control="no-cache" --project=survey-bot-detection
```

### Health Check URLs
- **Backend Health**: https://bot-backend-i56xopdg6q-pd.a.run.app/health
- **Backend Metrics**: https://bot-backend-i56xopdg6q-pd.a.run.app/metrics
- **Frontend**: https://storage.googleapis.com/bot-detection-frontend-20250929/index.html

---
**Last Updated**: 2025-10-15
**Current Deployment**: Commit 1123f2d (chore(prod): deploy plan & GCP prod configs)
