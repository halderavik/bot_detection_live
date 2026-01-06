# Backend Database Connection Issue

## Current Status
The backend is running but session creation is failing with HTTP 500 errors.

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
Check `backend/.env`:
```
DATABASE_URL=postgresql+asyncpg://postgres:Password123!@localhost/bot_detection
```
Make sure:
- Username: `postgres`
- Password: `Password123!` (or your actual password)
- Database: `bot_detection`

#### Tables not created
The backend should create tables automatically on startup. If not, check the startup logs for errors.

### 5. Quick Fix - Use Docker Compose
If you have Docker, the easiest way is:
```powershell
docker-compose up -d postgres
# Wait a few seconds, then
docker-compose up backend
```

This will:
- Start PostgreSQL with the correct configuration
- Create the database automatically
- Start the backend with proper database connection

## Next Steps
Once the database is working, re-run the test:
```powershell
cd backend
python test_all_text_analysis_checks.py
```
