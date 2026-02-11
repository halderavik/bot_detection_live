import os
import subprocess
import json
import tempfile

# Get DATABASE_URL from Secret Manager
print("Getting DATABASE_URL from Secret Manager...")
result = subprocess.run(
    ["gcloud", "secrets", "versions", "access", "latest", 
     "--secret=DATABASE_URL", "--project=survey-bot-detection"],
    capture_output=True,
    text=True
)
database_url = result.stdout.strip()
print(f"Database URL retrieved: {database_url[:50]}...")

# Parse connection details
# Format: postgresql+asyncpg://user:pass@/db?host=/cloudsql/project:region:instance
import re
match = re.search(r'postgresql\+asyncpg://([^:]+):([^@]+)@/([^?]+)', database_url)
if match:
    user, password, database = match.groups()
    print(f"User: {user}, Database: {database}")
    
    # Try to execute a simple test query via gcloud sql
    test_sql = "SELECT version();"
    print("\nTesting database connection...")
    
    # Use gcloud sql connect or try psql
    # For now, just verify we can parse the URL
    print("Connection details parsed successfully")
    print("Note: Actual migration requires Cloud Shell or Cloud SQL Proxy")
else:
    print("ERROR: Could not parse DATABASE_URL")
