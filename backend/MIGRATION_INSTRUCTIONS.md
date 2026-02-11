# Database Migration Instructions for Stage 3 Deployment

## Option 1: Run from Cloud Shell (Recommended)

1. Open Cloud Shell: https://console.cloud.google.com/cloudshell
   OR run: gcloud cloud-shell ssh --authorize-session

2. In Cloud Shell, clone or upload your repository:
   `ash
   git clone <your-repo-url>
   cd bot_iden_live/backend
   `

3. Set DATABASE_URL:
   `ash
   export DATABASE_URL=\postgresql+asyncpg://bot_user:NewPassword123!@/bot_detection_v2?host=/cloudsql/survey-bot-detection:northamerica-northeast2:bot-db-v2 
   `

4. Install dependencies:
   `ash
   pip3 install psycopg2-binary
   `

5. Run migrations:
   `ash
   python3 run_migration_sync.py
   python3 run_fraud_migration_sync.py
   python3 verify_v2_schema.py
   `

## Option 2: Run SQL directly via Cloud SQL Console

1. Go to: https://console.cloud.google.com/sql/instances/bot-db/databases/bot_detection_v2
2. Click 'Query' tab
3. Copy and paste the contents of: combined_migration.sql
4. Execute the SQL

## Option 3: Use Cloud SQL Proxy (Local)

1. Download Cloud SQL Proxy: https://cloud.google.com/sql/docs/postgres/sql-proxy
2. Start proxy:
   `ash
   ./cloud-sql-proxy survey-bot-detection:northamerica-northeast2:bot-db
   `
3. In another terminal:
   `ash
   export DATABASE_URL="postgresql://bot_user:PASSWORD@127.0.0.1:5432/bot_detection_v2"
   python run_migration_sync.py
   python run_fraud_migration_sync.py
   `

