# Backend Database Connection Issue

## Symptom
The backend is running but session creation fails with HTTP 500 errors. This is almost always a database problem. This guide covers a local backend first, then production.

## What to Check

### 1. Check Backend Logs
Look at the terminal where you started the backend (`python main.py`). You should see error messages like:
- Database connection errors
- Table creation errors
- SQL errors

### 2. Verify Database is Running
```powershell
# Check if PostgreSQL is running on port 5432
Test-NetConnection -ComputerName localhost -Port 5432
```

### 3. Verify Database Exists
The backend expects a database named `bot_detection`. Check if it exists:
```powershell
# Connect to PostgreSQL (adjust credentials as needed)
psql -U postgres -h localhost
# Then in psql:
\l  # List databases
```

### 4. Common Issues

#### Database doesn't exist
Create it:
```sql
CREATE DATABASE bot_detection;
```

#### Wrong credentials
Check `DATABASE_URL` in `backend/.env`. The example in `backend/.env.example` is:
```
DATABASE_URL=postgresql+asyncpg://postgres:<password>@localhost/bot_detection
```
Make sure the username, password and database name match your local PostgreSQL.

#### Tables not created
The backend creates any missing table on startup (`Base.metadata.create_all` in `main.py`), including `tracked_surveys`, `survey_quality_rules` and `app_settings`. No migration is needed for new tables. If tables are missing, check the startup logs for errors. `create_all` does not add new columns to a table that already exists.

### 5. Quick Fix - Use Docker Compose
If you have Docker, the easiest way is:
```powershell
docker-compose up -d postgres
# Wait a few seconds, then
docker-compose up backend
```

This will:
- Start PostgreSQL with the correct configuration (user `bot_user`, database `bot_detection`)
- Create the database automatically
- Start the backend with proper database connection

## Production (Cloud Run)

The production backend is the Cloud Run service `bot-backend` in project `survey-bot-detection`, region `northamerica-northeast2`. Read its recent logs with:
```powershell
gcloud run services logs read bot-backend --region northamerica-northeast2 --project survey-bot-detection --limit 100
```

Things to check if production returns 500 errors:
- The service must keep both Cloud SQL connections (`bot-db` and `bot-db-v2`) and its secrets (`DATABASE_URL`, `SECRET_KEY`, `OPENAI_API_KEY`, `ADMIN_TOKEN`). Running `deploy-backend.ps1` as written replaces the secrets and env vars and drops `bot-db-v2`. See `SELECTIVE_DEPLOYMENT_GUIDE.md` for the safe deploy commands.
- The service runs with 1 GiB memory, raised from 512 MiB because the backend now loads pandas (for the Live Quality file merge). A deploy with `--memory 512Mi` lowers it again.
- If the latest revision is broken, send traffic back to the previous one (see `rollback-procedures.md`).

## Next Steps
Once the database is working, re-run the test against your local backend:
```powershell
cd backend
python test_all_text_analysis_checks.py
```
The automated test suite (`python -m pytest tests`) does not need PostgreSQL. See `README_TESTING.md`.
