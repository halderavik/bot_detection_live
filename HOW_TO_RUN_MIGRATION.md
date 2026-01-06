# How to Run the Platform ID Migration

## The Issue
If you see "DO command not found", you're trying to run PostgreSQL SQL in a regular shell. The SQL needs to be executed **inside a PostgreSQL database connection** (psql).

## Method 1: Using Cloud Shell with gcloud sql connect (Recommended)

1. **Open Cloud Shell**: https://shell.cloud.google.com/

2. **Connect to the database**:
   ```bash
   gcloud sql connect bot-db --user=bot_user --database=bot_detection --project=survey-bot-detection
   ```
   This will open a `psql` session.

3. **Once you're in psql**, you can either:
   
   **Option A: Copy and paste the SQL**
   - Copy the entire content from `backend/migration_platform_id_production.sql`
   - Paste it into the psql prompt
   - Press Enter to execute
   
   **Option B: Use the simpler version**
   - Copy the content from `backend/migration_platform_id_simple.sql`
   - Paste it into psql
   - Press Enter to execute

4. **Verify it worked**:
   ```sql
   \d sessions
   ```
   You should see `platform_id` in the column list.

5. **Exit psql**:
   ```sql
   \q
   ```

## Method 2: Using Cloud SQL Console Query Tab

1. **Go to Cloud SQL Console**:
   https://console.cloud.google.com/sql/instances/bot-db?project=survey-bot-detection

2. **Click on "Databases" tab**

3. **Select database**: `bot_detection`

4. **Click "Query" tab** (if available) or **"Open Cloud Shell"**

5. **If using Query tab**:
   - Copy the SQL from `backend/migration_platform_id_simple.sql` (the simpler version without DO blocks)
   - Paste into the query editor
   - Click "Run"

6. **If using Cloud Shell**:
   - Follow Method 1 above

## Method 3: Upload SQL File to Cloud Shell

1. **Open Cloud Shell**: https://shell.cloud.google.com/

2. **Upload the SQL file**:
   - Click the "Upload" button (three dots menu) in Cloud Shell
   - Upload `backend/migration_platform_id_production.sql`

3. **Connect to database**:
   ```bash
   gcloud sql connect bot-db --user=bot_user --database=bot_detection --project=survey-bot-detection
   ```

4. **In psql, execute the file**:
   ```sql
   \i migration_platform_id_production.sql
   ```
   (Or use the path where you uploaded it)

## Which SQL File to Use?

- **`migration_platform_id_production.sql`**: Uses DO blocks (PostgreSQL-specific, needs psql)
- **`migration_platform_id_simple.sql`**: Simpler version without DO blocks (works in more contexts)

Both do the same thing - the simple version is easier if you're having issues with the DO block syntax.

## Troubleshooting

**"DO command not found"**:
- You're not in psql. Run `gcloud sql connect` first to get into psql.

**"psql: command not found"**:
- You need to install PostgreSQL client tools, OR use Cloud Shell which has them pre-installed.

**Connection timeout**:
- Make sure you're using Cloud Shell (which is already authorized) or your IP is in the authorized networks.

## Quick One-Liner (Cloud Shell)

If you're in Cloud Shell and want to do it all at once:

```bash
gcloud sql connect bot-db --user=bot_user --database=bot_detection --project=survey-bot-detection << 'EOF'
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS platform_id VARCHAR(255);
UPDATE sessions SET platform_id = platform WHERE platform IS NOT NULL AND platform_id IS NULL;
CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent_session ON sessions (survey_id, platform_id, respondent_id, id);
CREATE INDEX IF NOT EXISTS idx_survey_platform ON sessions (survey_id, platform_id);
CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent ON sessions (survey_id, platform_id, respondent_id);
CREATE INDEX IF NOT EXISTS idx_sessions_platform_id ON sessions (platform_id);
EOF
```
