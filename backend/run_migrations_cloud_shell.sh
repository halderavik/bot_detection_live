#!/bin/bash
# Migration script for Cloud Shell
# Run this in Cloud Shell to apply Stage 3 database migrations

set -e

echo "=========================================="
echo "Stage 3 Database Migration Script"
echo "=========================================="
echo ""

# Get DATABASE_URL from Secret Manager
echo "Step 1: Getting DATABASE_URL from Secret Manager..."
export DATABASE_URL=$(gcloud secrets versions access latest --secret=DATABASE_URL --project=survey-bot-detection)
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: Could not retrieve DATABASE_URL"
    exit 1
fi
echo "[OK] DATABASE_URL retrieved"
echo ""

# Install psycopg2 if needed
echo "Step 2: Checking Python dependencies..."
if ! python3 -c "import psycopg2" 2>/dev/null; then
    echo "Installing psycopg2-binary..."
    pip3 install --user psycopg2-binary
fi
echo "[OK] Dependencies ready"
echo ""

# Run platform_id migration
echo "Step 3: Running platform_id migration..."
python3 run_migration_sync.py
if [ $? -ne 0 ]; then
    echo "ERROR: Platform ID migration failed"
    exit 1
fi
echo "[OK] Platform ID migration completed"
echo ""

# Run fraud detection migration
echo "Step 4: Running fraud detection migration..."
python3 run_fraud_migration_sync.py
if [ $? -ne 0 ]; then
    echo "ERROR: Fraud detection migration failed"
    exit 1
fi
echo "[OK] Fraud detection migration completed"
echo ""

# Verify schema
echo "Step 5: Verifying database schema..."
python3 verify_v2_schema.py
if [ $? -ne 0 ]; then
    echo "WARNING: Schema verification failed - check output above"
    exit 1
fi
echo "[OK] Schema verification passed"
echo ""

echo "=========================================="
echo "Migration completed successfully!"
echo "=========================================="
