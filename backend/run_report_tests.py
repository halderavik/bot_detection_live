"""
Run report service tests with backend path forced first so 'app' resolves to this project.
Usage: from backend directory: python run_report_tests.py
"""
import sys
import os

# Force this backend directory first so "app" is backend/app, not another project.
# Remove any path that might point at another project (e.g. van-westendorp) to avoid wrong "app".
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [backend_dir] + [p for p in sys.path if p != backend_dir and "van-westendorp" not in p.lower() and "b3_dev" not in p]

import pytest
sys.exit(pytest.main(["-v", "--tb=short", "tests/test_report_service.py", "tests/test_report_service_text_quality.py"]))
