# Selective Deployment Guide

This guide explains how to push only specific changes to GitHub instead of pushing all modifications at once. This is useful for incremental deployments, feature rollouts, or when you want to deploy only certain components.

Pushing to GitHub does not deploy anything. The production backend (Cloud Run) and frontend (Cloud Storage) are deployed by hand with the commands in [Deploying to Production](#deploying-to-production).

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Checking Current Changes](#checking-current-changes)
3. [Selective Staging](#selective-staging)
4. [Common Deployment Scenarios](#common-deployment-scenarios)
5. [Deploying to Production](#deploying-to-production)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Git installed and configured
- Access to the repository: `https://github.com/halderavik/bot_detection_live.git`
- Understanding of your project structure (backend, frontend, migrations, etc.)

---

## Checking Current Changes

Before deploying, always check what has changed:

### View All Changes
```powershell
# Check status of all files
git status

# See detailed changes
git diff

# See staged changes
git diff --cached
```

### View Changes by Directory
```powershell
# Check backend changes only
git status backend/

# Check frontend changes only
git status frontend/

# Check documentation changes
git status *.md
```

### View Specific File Changes
```powershell
# See what changed in a specific file
git diff path/to/file.py
git diff backend/app/services/fraud_detection_service.py
```

---

## Selective Staging

### Method 1: Stage Individual Files

```powershell
# Stage a single file
git add path/to/file.py

# Stage multiple specific files
git add file1.py file2.py file3.jsx

# Stage all files in a directory
git add backend/app/services/

# Stage all files matching a pattern
git add backend/migrations/*.sql
```

### Method 2: Stage by File Type

```powershell
# Stage only Python files
git add *.py

# Stage only SQL files
git add *.sql

# Stage only Markdown files
git add *.md
```

### Method 3: Interactive Staging (Recommended)

```powershell
# Open interactive staging menu
git add -i

# Or use patch mode for fine-grained control
git add -p
```

**Interactive staging (`git add -i`)** allows you to:
- Select files to stage
- Stage/unstage individual files
- See file status
- Review changes before staging

**Patch mode (`git add -p`)** allows you to:
- Review each change line by line
- Stage only specific parts of a file
- Skip changes you don't want to include

---

## Common Deployment Scenarios

### Scenario 1: Deploy Only Backend Changes

```powershell
# 1. Check backend changes
git status backend/

# 2. Stage only backend files
git add backend/app/
git add backend/requirements.txt
git add backend/migrations/*.sql

# 3. Verify what's staged
git status

# 4. Commit
git commit -m "Deploy: Backend fraud detection service updates"

# 5. Push
git push origin main
```

### Scenario 2: Deploy Only Frontend Changes

```powershell
# 1. Check frontend changes
git status frontend/

# 2. Stage only frontend files
git add frontend/src/
git add frontend/package.json

# 3. Verify what's staged
git status

# 4. Commit
git commit -m "Deploy: Frontend fraud detection widgets"

# 5. Push
git push origin main
```

### Scenario 3: Deploy Only Database Migrations

New tables do not need a migration. The backend creates any missing table at startup (`Base.metadata.create_all` in `backend/main.py`). This is how `tracked_surveys`, `survey_quality_rules` and `app_settings` were added. A migration script is only needed when an existing table changes (a new column or index, for example). The example below is from the earlier fraud detection change.

```powershell
# 1. Check migration files
git status backend/migrations/

# 2. Stage migration files only (example)
git add backend/migrations/add_fraud_detection_tables.sql
git add backend/run_fraud_detection_migration.py

# 3. Verify
git status

# 4. Commit
git commit -m "Deploy: Fraud detection database migration"

# 5. Push
git push origin main
```

### Scenario 4: Deploy Only Documentation

```powershell
# 1. Check documentation changes
git status *.md

# 2. Stage documentation files
git add API_V2.md
git add architecture.md
git add bot_detection_flow.md
git add README.md
git add task.md

# 3. Verify
git status

# 4. Commit
git commit -m "Docs: Update fraud detection documentation"

# 5. Push
git push origin main
```

### Scenario 5: Deploy Only Tests

```powershell
# 1. Check test files
git status backend/tests/

# 2. Stage test files
git add backend/tests/test_fraud_detection*.py

# 3. Verify
git status

# 4. Commit
git commit -m "Tests: Add fraud detection unit tests"

# 5. Push
git push origin main
```

### Scenario 6: Deploy Specific Feature (Fraud Detection Example)

```powershell
# 1. Check all fraud detection related files
git status | Select-String "fraud"

# 2. Stage fraud detection files
git add backend/app/services/fraud_detection_service.py
git add backend/app/controllers/fraud_detection_controller.py
git add backend/app/models/fraud_indicator.py
git add backend/app/utils/fraud_helpers.py
git add backend/migrations/add_fraud_detection_tables.sql
git add frontend/src/components/FraudDetectionWidget.jsx
git add frontend/src/components/HierarchicalFraudWidget.jsx

# 3. Verify
git status

# 4. Commit
git commit -m "Feature: Add fraud detection service with hierarchical API support"

# 5. Push
git push origin main
```

### Scenario 7: Deploy Configuration Changes Only

```powershell
# 1. Stage config files
git add backend/.env.example
git add frontend/.env.example
git add docker-compose.yml

# 2. Verify
git status

# 3. Commit
git commit -m "Config: Update environment configuration"

# 4. Push
git push origin main
```

---

## Complete Workflow Example

### Deploying Fraud Detection Feature Incrementally

#### Step 1: Database Migration
```powershell
# Stage and commit migration only
git add backend/migrations/add_fraud_detection_tables.sql
git add backend/run_fraud_detection_migration.py
git commit -m "Migration: Add fraud_indicators table"
git push origin main
```

#### Step 2: Backend Service
```powershell
# Stage and commit backend service
git add backend/app/services/fraud_detection_service.py
git add backend/app/utils/fraud_helpers.py
git add backend/app/models/fraud_indicator.py
git commit -m "Backend: Implement fraud detection service"
git push origin main
```

#### Step 3: Backend API
```powershell
# Stage and commit API endpoints
git add backend/app/controllers/fraud_detection_controller.py
git add backend/app/routes/api_router.py
git commit -m "API: Add fraud detection endpoints"
git push origin main
```

#### Step 4: Frontend Components
```powershell
# Stage and commit frontend
git add frontend/src/components/FraudDetectionWidget.jsx
git add frontend/src/components/HierarchicalFraudWidget.jsx
git add frontend/src/services/apiService.js
git commit -m "Frontend: Add fraud detection widgets"
git push origin main
```

#### Step 5: Documentation
```powershell
# Stage and commit documentation
git add API_V2.md architecture.md bot_detection_flow.md README.md task.md
git commit -m "Docs: Update fraud detection documentation"
git push origin main
```

---

## Advanced Techniques

### Exclude Files from Commit

If you have changes you don't want to commit yet:

```powershell
# Stash unrelated changes temporarily
git stash push -m "WIP: unrelated changes"

# Commit your selected changes
git add selected-files
git commit -m "Deploy: specific feature"
git push origin main

# Restore your stashed changes
git stash pop
```

### Unstage Files (If You Staged Too Much)

```powershell
# Unstage a specific file
git reset HEAD path/to/file.py

# Unstage all files
git reset HEAD

# Unstage but keep changes
git restore --staged path/to/file.py
```

### Review Before Committing

```powershell
# See what will be committed
git diff --cached

# See summary of staged changes
git status --short
```

### Commit Without Pushing

```powershell
# Commit but don't push yet
git commit -m "Your commit message"

# Push later
git push origin main
```

---

## Deploying to Production

Production runs in project `survey-bot-detection`, region `northamerica-northeast2`.

- Backend: Cloud Run service `bot-backend`, https://bot-backend-119522247395.northamerica-northeast2.run.app
- Frontend: bucket `bot-detection-frontend-20251208`, https://storage.googleapis.com/bot-detection-frontend-20251208/index.html

### Warning: do not run deploy-backend.ps1 as written

`deploy-backend.ps1` uses `--set-env-vars` and `--set-secrets`. These replace all environment variables and secrets on the service. It also passes `--add-cloudsql-instances` with only `bot-db` and sets `--memory 512Mi`. Running it as is drops settings (such as `ADMIN_TOKEN`), drops the `bot-db-v2` connection and lowers memory below what the service needs. Use the commands below instead. They change only the image (and anything you pass with `--update-*`) and keep everything else.

### Backend

1. Check what will be uploaded. `backend/.gcloudignore` keeps `.env` files, virtualenvs, `*.db`, `tests/`, logs and caches out of the upload. `backend/.dockerignore` keeps the same files out of the image.
   ```powershell
   gcloud meta list-files-for-upload backend
   ```
   Make sure no `.env` file or local database is in the list.

2. Build the image, tagged with the short git sha of the commit you are deploying:
   ```powershell
   $sha = git rev-parse --short HEAD
   gcloud builds submit ./backend --tag northamerica-northeast2-docker.pkg.dev/survey-bot-detection/backend/bot-backend:$sha --project survey-bot-detection
   ```

3. Deploy the image:
   ```powershell
   gcloud run deploy bot-backend --image northamerica-northeast2-docker.pkg.dev/survey-bot-detection/backend/bot-backend:$sha --region northamerica-northeast2 --project survey-bot-detection
   ```
   Add only what changes, for example:
   - `--memory 1Gi` (the service runs with 1 GiB; pandas needs more than 512 MiB)
   - `--update-secrets ADMIN_TOKEN=ADMIN_TOKEN:latest` to add or change one secret
   - `--update-env-vars KEY=value` to add or change one environment variable

   Never use `--set-env-vars` or `--set-secrets` here.

4. Check the new revision:
   ```powershell
   gcloud run services describe bot-backend --region northamerica-northeast2 --project survey-bot-detection --format="value(status.traffic[].revisionName,status.traffic[].percent)"
   curl https://bot-backend-119522247395.northamerica-northeast2.run.app/health
   ```

The service runs with 1 CPU, 1 GiB memory, min 1 / max 10 instances, Cloud SQL instances `bot-db` and `bot-db-v2`, and VPC connector `serverless-connector`. Its secrets are `DATABASE_URL`, `SECRET_KEY`, `OPENAI_API_KEY` and `ADMIN_TOKEN`.

New tables are created at startup, so a backend deploy needs no migration step unless an existing table changed.

### ADMIN_TOKEN

`ADMIN_TOKEN` unlocks saving on the Settings page. Without it the page is read-only. To read it:
```powershell
gcloud secrets versions access latest --secret ADMIN_TOKEN --project survey-bot-detection
```
After a fresh deploy, open the deployed Settings page, unlock it with this token, and enter the Decipher API key to turn on Upload to Decipher.

### Frontend

```powershell
cd frontend
npx vite build --mode production
cd ..
gcloud storage rsync -r frontend/dist gs://bot-detection-frontend-20251208
gcloud storage objects update gs://bot-detection-frontend-20251208/index.html --cache-control="no-cache"
gcloud storage objects update "gs://bot-detection-frontend-20251208/assets/**" --cache-control="public, max-age=31536000, immutable"
```

- Do not delete unmatched files (no `--delete-unmatched-destination-objects`). `tracking-client.js` in the bucket is not part of the build and may be used by live surveys.
- The production build uses hash addresses (`VITE_ROUTER_MODE=hash` in `frontend/.env.production`), for example `https://storage.googleapis.com/bot-detection-frontend-20251208/index.html#/quality`. Local dev uses normal paths.

### Rollback

The live revision is `bot-backend-00079-lpm` (image tag `8f89c0f`). The rollback target is `bot-backend-00078-2hw`:
```powershell
gcloud run services update-traffic bot-backend --to-revisions bot-backend-00078-2hw=100 --region northamerica-northeast2 --project survey-bot-detection
```
See `rollback-procedures.md` for the full steps.

---

## Best Practices

### 1. **Always Review Before Committing**
```powershell
# See what's staged
git status
git diff --cached
```

### 2. **Use Descriptive Commit Messages**
```powershell
# Good commit messages
git commit -m "Deploy: Backend fraud detection service"
git commit -m "Feature: Add hierarchical fraud detection endpoints"
git commit -m "Fix: Correct fraud score calculation in detection engine"

# Avoid vague messages
git commit -m "updates"
git commit -m "changes"
```

### 3. **Test Before Pushing**
- Run the backend tests locally before pushing (see `backend/README_TESTING.md`):
  ```powershell
  cd backend
  $env:SECRET_KEY = "test"; python -m pytest tests
  ```
- Verify migrations work correctly (only when an existing table changed)
- Test API endpoints if backend changes
- Test UI if frontend changes

### 4. **Deploy in Logical Groups**
- Database migrations first (when an existing table changed; new tables are created at startup)
- Backend services before API endpoints
- Backend before frontend
- Features before documentation

### 5. **Keep Related Changes Together**
```powershell
# Good: Related files together
git add backend/app/services/fraud_service.py
git add backend/app/controllers/fraud_controller.py
git commit -m "Feature: Fraud detection API"

# Avoid: Mixing unrelated changes
git add backend/app/services/fraud_service.py
git add frontend/src/components/TextWidget.jsx  # Unrelated!
git commit -m "updates"
```

### 6. **Use Branches for Major Features**
```powershell
# Create feature branch
git checkout -b feature/fraud-detection

# Make changes and commit
git add ...
git commit -m "Feature: Fraud detection"

# Merge to main when ready
git checkout main
git merge feature/fraud-detection
git push origin main
```

### 7. **Document Deployment Steps**
- Note which files were changed
- Document any manual steps required
- Include migration instructions if needed
- Note any breaking changes

---

## Deployment Checklist

Before pushing, verify:

- [ ] Reviewed all staged changes (`git diff --cached`)
- [ ] Only relevant files are staged
- [ ] Tests pass locally
- [ ] Migration scripts work (if applicable)
- [ ] Commit message is descriptive
- [ ] No sensitive data in committed files
- [ ] Related changes are grouped together

---

## Troubleshooting

### Problem: Staged Too Many Files

**Solution:**
```powershell
# Unstage everything
git reset HEAD

# Stage only what you need
git add specific-file.py
```

### Problem: Accidentally Committed Wrong Files

**Solution:**
```powershell
# Undo last commit, keep changes
git reset --soft HEAD~1

# Stage correct files and recommit
git add correct-files
git commit -m "Correct commit message"
```

### Problem: Need to Exclude Certain Changes

**Solution:**
```powershell
# Use .gitignore for files that should never be committed
# Or use git stash for temporary exclusion
git stash push -m "Exclude these changes"
```

### Problem: Want to See What's Different from Remote

**Solution:**
```powershell
# Fetch latest from remote
git fetch origin

# See what's different
git diff origin/main

# See commits that aren't pushed
git log origin/main..HEAD
```

### Problem: Conflicts After Selective Push

**Solution:**
```powershell
# Pull latest changes
git pull origin main

# Resolve conflicts
# Then push again
git push origin main
```

---

## Quick Reference Commands

```powershell
# Check status
git status

# Stage specific file
git add path/to/file

# Stage all files in directory
git add directory/

# Stage files by pattern
git add *.py

# Interactive staging
git add -i

# Patch mode (line-by-line)
git add -p

# Unstage file
git reset HEAD path/to/file

# See staged changes
git diff --cached

# Commit
git commit -m "Your message"

# Push
git push origin main

# Stash changes
git stash push -m "message"

# Restore stashed changes
git stash pop
```

---

## Example: Complete Selective Deployment

Here's a complete example of deploying only fraud detection changes:

```powershell
# 1. Check what's changed
git status

# 2. Review changes
git diff backend/app/services/fraud_detection_service.py

# 3. Stage only fraud detection files
git add backend/app/services/fraud_detection_service.py
git add backend/app/controllers/fraud_detection_controller.py
git add backend/app/models/fraud_indicator.py
git add backend/app/utils/fraud_helpers.py
git add backend/migrations/add_fraud_detection_tables.sql
git add frontend/src/components/FraudDetectionWidget.jsx
git add frontend/src/components/HierarchicalFraudWidget.jsx

# 4. Verify staging
git status

# 5. Review staged changes
git diff --cached

# 6. Commit
git commit -m "Feature: Fraud detection system with hierarchical API support

- Implemented fraud detection service with 5 detection methods
- Added hierarchical fraud detection endpoints
- Created fraud detection widgets for frontend
- Added database migration for fraud_indicators table"

# 7. Push
git push origin main

# 8. Verify push
git log origin/main -1
```

---

## Notes

- **Never commit sensitive data**: Always check `.env` files, API keys, passwords
- **Test migrations separately**: Database migrations should be tested before pushing. New tables need no migration; they are created at startup
- **Coordinate with team**: Let team members know what you're deploying
- **Use branches for major changes**: Feature branches make selective deployment easier
- **Keep commits small**: Smaller, focused commits are easier to review and rollback

---

**Last Updated**: November 2026
