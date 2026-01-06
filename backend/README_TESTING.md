# Text Analysis Testing Guide

## Quick Start

To test all text analysis checks with your local backend:

### Option 1: Manual Steps

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

### Option 2: Using the PowerShell Script

```powershell
cd backend
.\run_tests_with_backend.ps1
```

## Test Script Details

The test script (`test_all_text_analysis_checks.py`) includes:

- **8 comprehensive test cases** covering all 5 text analysis checks
- **Health check verification** before running tests
- **Detailed output** for each test with analysis results
- **Summary report** at the end

## Test Cases

1. **Gibberish Detection** - Random character sequences
2. **Copy-Paste Detection** - Formal dictionary-style text
3. **Relevance Analysis** - Off-topic responses
4. **Generic Answer Detection** - Low-effort responses
5. **High Quality Response** - Ensures good responses aren't flagged
6. **Mixed Issues** - Priority filtering test
7. **Relevance Edge Case** - Partially relevant responses
8. **Wikipedia Copy-Paste** - Detects copied definitions

## Configuration

Make sure your `backend/.env` file has:
- Valid `OPENAI_API_KEY`
- `OPENAI_MODEL=gpt-4o-mini` (or your preferred model)
- Database connection configured

## Troubleshooting

### Backend won't start
- Check if port 8000 is already in use
- Verify database is running and accessible
- Check `.env` file configuration

### Tests fail with connection errors
- Ensure backend is running before running tests
- Check that backend is accessible at `http://localhost:8000`
- Verify health endpoint: `http://localhost:8000/health`

### OpenAI API errors
- Verify API key is valid and has credits
- Check API key in `.env` file
- Review backend logs for detailed error messages

## Expected Results

When all checks work correctly, you should see:
- ✅ All 8 tests passing
- Proper flag detection (gibberish, copy_paste, irrelevant, generic)
- Quality scores in expected ranges
- Detailed analysis results for each test
