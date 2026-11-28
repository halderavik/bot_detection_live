# Testing Guide

## Automated Test Suite

The main backend tests run with pytest. They need no running server and no PostgreSQL. Tests that need a database create a temporary SQLite file through `aiosqlite` (listed in `requirements-test.txt`).

1. **Install the test requirements** (once, inside your virtualenv):
   ```powershell
   cd backend
   pip install -r requirements.txt -r requirements-test.txt
   ```

2. **Run the tests**:
   ```powershell
   cd backend
   $env:SECRET_KEY = "test"; python -m pytest tests
   ```
   In bash: `SECRET_KEY=test python -m pytest tests` (with the project virtualenv on Windows: `SECRET_KEY=test .venv/Scripts/python.exe -m pytest -q tests`)

All 349 tests should pass (count from 2026-11-27).

**Timeline check in tests.** `backend/tests/conftest.py` holds a shared fixture that runs for every test and switches the `timeline_mismatch` check off, because integration tests post minutes of page time within milliseconds, which the check would rightly call made up. A test that needs the check marks itself with `@pytest.mark.timeline` (the marker is registered in the same file).

The tests are in `backend/tests/`. They cover detection, fraud, grid and timing analysis, text analysis, reports, dashboard numbers (`test_dashboard_numbers.py`), Decipher tracking and upload (`test_decipher_tracking.py`, `test_tracking_upload_endpoint.py`, `test_decipher_upload.py`), Live Quality and the LQ_ file merge (`test_quality_variables.py`, `test_live_quality.py`, `test_live_quality_endpoints.py`, `test_quality_merge.py`) and the Settings page store (`test_runtime_settings.py`). Example Decipher surveys used by the tracking tests are in `backend/tests/fixtures/`.

If collection fails with `ModuleNotFoundError`, you are probably using a Python without the backend requirements. Activate the backend virtualenv first.

## Respondent Pressure Test (Simulator)

`test_results/respondent_pressure_2026-11-27/simulate.py` plays many simulated respondents (people of several kinds, bots of each signal type, a device farm, dropouts) through the same API calls the live tracker makes from a Decipher survey, then reads the Live Quality results and the CSV export and scores each respondent against what its type should get.

```bash
python simulate.py <out_dir> [survey_id]
```

- `out_dir`: where the results are written (summary, scored respondents, open-end answers, the CSV export).
- `survey_id`: optional; defaults to `PRESSURE_RESP_<date>_<time>`.
- Environment: `BASE` (API base URL, default the production API) and `CONCURRENCY` (respondents played at once, default 6).

It needs `httpx`. It waits in real time to match the page times it reports (otherwise the `timeline_mismatch` check would rightly flag them), so a full run takes a few minutes. It sends real requests and creates real sessions on the target server, including AI checks of open ends. Results from 2026-11-27 are in `test_results/respondent_pressure_2026-11-27` (first run) and its `after_fixes` folder.

## Text Analysis Checks Against a Running Backend

The rest of this guide covers a separate script that sends real requests to a running backend and calls OpenAI.

### Quick Start

To test all text analysis checks with your local backend:

#### Option 1: Manual Steps

1. **Start the backend server** (in one terminal):
   ```powershell
   cd backend
   python main.py
   ```

2. **Wait for the server to start** (you should see "Application startup complete")

3. **Run the tests** (in another terminal):
   ```powershell
   cd backend
   python test_all_text_analysis_checks.py
   ```

#### Option 2: Using the PowerShell Script

```powershell
cd backend
.\run_tests_with_backend.ps1
```

### Test Script Details

The test script (`test_all_text_analysis_checks.py`) includes:

- **8 comprehensive test cases** covering all 5 text analysis checks
- **Health check verification** before running tests
- **Detailed output** for each test with analysis results
- **Summary report** at the end

### Test Cases

1. **Gibberish Detection** - Random character sequences
2. **Copy-Paste Detection** - Formal dictionary-style text
3. **Relevance Analysis** - Off-topic responses
4. **Generic Answer Detection** - Low-effort responses
5. **High Quality Response** - Ensures good responses aren't flagged
6. **Mixed Issues** - Priority filtering test
7. **Relevance Edge Case** - Partially relevant responses
8. **Wikipedia Copy-Paste** - Detects copied definitions

### Configuration

Make sure your `backend/.env` file has:
- Valid `OPENAI_API_KEY`
- `OPENAI_MODEL=gpt-4o-mini` (or your preferred model)
- Database connection configured
- Optional: `OPENAI_REQUESTS_PER_MINUTE` (default 300) and `OPENAI_RATE_WAIT_SECONDS` (default 20). One OpenAI call per answer covers all five checks. An answer that cannot be checked (OpenAI unavailable, or the limit still reached after the wait) is stored as not checked (`quality_score` null, `analysis_details.unchecked` true) instead of passing

### Troubleshooting

#### Backend won't start
- Check if port 8000 is already in use
- Verify database is running and accessible
- Check `.env` file configuration

#### Tests fail with connection errors
- Ensure backend is running before running tests
- Check that backend is accessible at `http://localhost:8000`
- Verify health endpoint: `http://localhost:8000/health`

#### OpenAI API errors
- Verify API key is valid and has credits
- Check API key in `.env` file
- Review backend logs for detailed error messages

### Expected Results

When all checks work correctly, you should see:
- ✅ All 8 tests passing
- Proper flag detection (gibberish, copy_paste, irrelevant, generic)
- Quality scores in expected ranges
- Detailed analysis results for each test
