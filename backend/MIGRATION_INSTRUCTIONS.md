# Database Migration Instructions for Stage 3 Deployment

> **Current state (November 2026):** This is a record of a one-off migration for the Stage 3 deployment. It is not part of a normal deploy. New tables (`tracked_surveys`, `survey_quality_rules`, `app_settings`) are created when the backend starts (`Base.metadata.create_all` in `main.py`), so they need no migration. Existing tables were not changed. Only run SQL like this when an existing table changes. For deploy and rollback steps, see `SELECTIVE_DEPLOYMENT_GUIDE.md` and `rollback-procedures.md` in the repository root.

## Option 1: Run from Cloud Shell (Recommended)

1. Open Cloud Shell: https://console.cloud.google.com/cloudshell
   OR run: gcloud cloud-shell ssh --authorize-session

2. In Cloud Shell, clone or upload your repository:
   ```bash
   git clone <your-repo-url>
   cd bot_iden_live/backend
   ```

3. Set DATABASE_URL:
   ```bash
   export DATABASE_URL="postgresql+asyncpg://bot_user:<password>@/bot_detection_v2?host=/cloudsql/survey-bot-detection:northamerica-northeast2:bot-db-v2"
   ```

4. Install dependencies:
   ```bash
   pip3 install psycopg2-binary
   ```

5. Run migrations:
   ```bash
   python3 run_migration_sync.py
   python3 run_fraud_migration_sync.py
   python3 verify_v2_schema.py
   ```

## Option 2: Run SQL directly via Cloud SQL Console

1. Go to: https://console.cloud.google.com/sql/instances/bot-db/databases/bot_detection_v2
2. Click 'Query' tab
3. Copy and paste the contents of: combined_migration.sql
4. Execute the SQL

## Option 3: Use Cloud SQL Proxy (Local)

1. Download Cloud SQL Proxy: https://cloud.google.com/sql/docs/postgres/sql-proxy
2. Start proxy:
   ```bash
   ./cloud-sql-proxy survey-bot-detection:northamerica-northeast2:bot-db
   ```
3. In another terminal:
   ```bash
   export DATABASE_URL="postgresql://bot_user:PASSWORD@127.0.0.1:5432/bot_detection_v2"
   python run_migration_sync.py
   python run_fraud_migration_sync.py
   ```

