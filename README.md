# Bot Detection API

A comprehensive bot detection system with behavioral analysis, survey platform integration, fraud detection, and real-time monitoring capabilities.

## ✅ **IMPLEMENTATION STATUS - COMPLETED & READY TO DEPLOY**

**All fraud detection features are fully implemented, tested, and ready for production deployment:**

### Core Features ✅ **COMPLETED**
- ✅ **Fraud Detection Service**: Complete implementation with all 5 detection methods ✅ **COMPLETED**
  - IP Address Tracking
  - Device Fingerprinting  
  - Duplicate Response Detection
  - Geolocation Consistency Checking
  - Velocity Checking
- ✅ **Composite Bot Detection**: 40% behavioral, 30% text quality, 30% fraud detection ✅ **COMPLETED**
- ✅ **Hierarchical Fraud Endpoints**: Survey/platform/respondent/session-level fraud summaries ✅ **COMPLETED**
- ✅ **Database Schema**: `fraud_indicators` table with hierarchical indexes ✅ **COMPLETED**
- ✅ **Frontend Integration**: Hierarchical fraud widgets in all detail views ✅ **COMPLETED**
- ✅ **Unit Tests**: 10/10 passing for fraud detection service ✅ **COMPLETED**
- ✅ **API Tests**: All fraud detection endpoints tested and verified ✅ **COMPLETED**
- ✅ **Database Migration**: Migration script created and ready ✅ **COMPLETED**
- ✅ **Production Deployment**: Dashboard redeployed February 2026 with fraud/grid/timing in API Playground and Report Builder

**Production URLs:**
- Backend: `https://bot-backend-119522247395.northamerica-northeast2.run.app`
- Frontend: `https://storage.googleapis.com/bot-detection-frontend-20251208/index.html`
- API Docs: `https://bot-backend-119522247395.northamerica-northeast2.run.app/docs`

**Frontend Deployment Status:** ✅ **VERIFIED** (February 2026)
- ✅ Frontend successfully deployed to Cloud Storage (`bot-detection-frontend-20251208`)
- ✅ All API endpoints verified and returning data from Cloud SQL
- ✅ Data flow verified: Cloud SQL → Backend API → Frontend Dashboard
- ✅ Fraud detection widget integrated and operational
- ✅ API Playground: Endpoint templates for fraud (flat + hierarchical), grid analysis, and timing analysis
- ✅ Report Builder: Fraud & Duplicate, Grid Analysis, and Timing Analysis in summary and detailed reports (including CSV); click respondent ID to open full-detail popup; CSV includes every analysis per respondent (text responses of interest, fraud/grid/timing explanations)
- ✅ All 6 frontend-used endpoints tested and working correctly

## 🚀 Features

- **Advanced Bot Detection**: Rule-based analysis of user behavior patterns with 5 detection methods
- **OpenAI Text Quality Analysis**: GPT-4o-mini powered analysis of open-ended survey responses ✅ **100% Test Accuracy**
- **Grid/Matrix Question Analysis**: Straight-lining detection, pattern detection (diagonal, zigzag), variance scoring, and satisficing behavior analysis ✅ **DEPLOYED**
- **Enhanced Timing Analysis**: Speeder/flatliner detection, timing anomaly detection, and adaptive threshold calculation ✅ **DEPLOYED**
- **Fraud Detection Service**: Complete fraud detection system with IP tracking, device fingerprinting, duplicate detection, geolocation, and velocity checking ✅ **COMPLETED**
- **Composite Bot Detection**: Unified scoring algorithm (40% behavioral + 30% text quality + 30% fraud detection) ✅ **COMPLETED**
- **Text Analysis Dashboard**: Real-time text quality analysis with filtering, pagination, and CSV export
- **Grid Analysis Dashboard**: Grid/matrix question analysis widgets with straight-lining and pattern detection ✅ **DEPLOYED**
- **Timing Analysis Dashboard**: Response timing analysis widgets with speeder/flatliner alerts ✅ **DEPLOYED**
- **Fraud Detection Dashboard**: Hierarchical fraud widgets integrated into all detail views ✅ **COMPLETED**
- **Multi-Platform Integration**: Support for Qualtrics and Decipher survey platforms
- **Live Quality dashboard**: Per-survey quality rules, live bot and fraud results with charts and a respondent table, CSV export, and `LQ_` flags added to a Decipher data file (see [Live quality](#live-quality))
- **Decipher XML tracking**: Upload a Decipher survey XML in the dashboard and download it with live tracking added, ready to import (see [Add tracking to a Decipher survey](#add-tracking-to-a-decipher-survey))
- **Real-time Analytics**: Live dashboard with session monitoring and detection statistics
- **Enhanced Report Builder**: Comprehensive reporting system with text quality, fraud & duplicate detection, grid/matrix analysis, and timing analysis metrics in summary and detailed reports; clickable respondent ID opens a popup with full details, responses of interest, and decision reasons; CSV export includes all analyses per respondent
- **Scalable Architecture**: FastAPI backend with PostgreSQL deployed on Google Cloud Platform
- **Client SDKs**: Python and JavaScript client libraries for easy integration
- **Enhanced JavaScript SDK**: Automatic question/answer capture with text quality tracking
- **Webhook Support**: Automated survey response processing
- **Monitoring & Logging**: Comprehensive observability with Prometheus and Grafana
- **Performance Testing**: Locust load testing and async performance validation
- **Error Handling**: Comprehensive validation and user-friendly error messages
- **Architecture Documentation**: Comprehensive system architecture and interaction patterns
- **Frontend Dashboard**: Complete React-based monitoring interface with real-time updates
- **Integration Management**: Webhook testing, status monitoring, and setup guides
- **Hierarchical API**: Survey → Platform → Respondent → Session structure for aggregated data access ✅ **DEPLOYED**
- **Grid Analysis Hierarchical Endpoints**: Survey/platform/respondent/session-level grid analysis summaries ✅ **DEPLOYED**
- **Timing Analysis Hierarchical Endpoints**: Survey/platform/respondent/session-level timing analysis summaries ✅ **DEPLOYED**
- **Fraud Detection Hierarchical Endpoints**: Survey/platform/respondent/session-level fraud summaries ✅ **COMPLETED**
- **Production Ready**: Fully deployed on GCP with health monitoring and metrics

## 🏗️ Architecture

For detailed architecture information, see [Architecture Documentation](architecture.md).

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Database      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │   Redis Cache   │              │
         │              └─────────────────┘              │
         │                                              │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client SDKs   │    │   Integrations  │    │   Monitoring    │
│   (Python/JS)   │    │   (Webhooks)    │    │   (Prometheus)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Architectural Features

- **Async/Await Pattern**: Non-blocking I/O operations throughout the system
- **Layered Architecture**: Clear separation between API, business logic, and data layers
- **Real-time Updates**: WebSocket support for live dashboard updates
- **Error Handling**: Comprehensive error handling at all layers
- **Performance Optimization**: Database optimization, caching, and frontend optimizations
- **Security**: Multi-layered security approach with validation and protection
- **Frontend Integration**: Seamless React dashboard with comprehensive UI components

## 📁 Project Structure

```
bot_iden_live/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── config.py          # Configuration settings
│   │   ├── database.py        # Database setup
│   │   ├── models/            # SQLAlchemy models
│   │   │   ├── survey_question.py    # Survey question model
│   │   │   └── survey_response.py    # Survey response model
│   │   ├── services/          # Business logic
│   │   │   ├── openai_service.py     # OpenAI API integration
│   │   │   └── text_analysis_service.py # Text quality analysis
│   │   ├── controllers/       # API controllers
│   │   │   └── text_analysis_controller.py # Text analysis endpoints
│   │   ├── utils/             # Utility functions
│   │   └── routes/            # API routes
│   ├── main.py               # Application entry point
│   ├── requirements.txt      # Python dependencies
│   ├── requirements-test.txt # Test dependencies
│   ├── create_test_data.py  # Test data generation
│   ├── performance_test.py  # Async performance testing
│   ├── locustfile.py        # Load testing configuration
│   └── .env.example         # Environment variables
├── frontend/                  # React frontend
│   ├── public/
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── Dashboard.jsx # Main dashboard
│   │   │   ├── Integrations.jsx # Integration management
│   │   │   ├── Settings.jsx  # System settings
│   │   │   ├── ApiPlayground.jsx # API testing interface
│   │   │   ├── QuickStartGuide.jsx # Getting started guide
│   │   │   ├── SessionDetails.jsx # Session analysis view
│   │   │   └── TextQualityWidget.jsx # Text quality analysis display
│   │   ├── services/         # API services
│   │   ├── utils/            # Utility functions
│   │   └── styles/           # CSS styles
│   ├── package.json
│   └── vite.config.js
├── client-sdk/               # Client SDKs
│   ├── python/               # Python client
│   └── javascript/           # JavaScript client
├── docker-compose.yml        # Docker orchestration
├── architecture.md           # System architecture documentation
├── API.md                    # API reference documentation
├── planning.md               # Technical planning document
├── prd.md                    # Product requirements document
├── task.md                   # Development tasks and progress
└── README.md                # This file
```

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework with async support
- **SQLAlchemy**: Database ORM with async support and relationship management
- **PostgreSQL**: Primary database with optimized schemas
- **Redis**: Caching and session storage
- **Pydantic**: Data validation and settings management
- **Uvicorn**: ASGI server for production deployment
- **OpenAI**: GPT-4o-mini integration for text quality analysis

### Frontend
- **React**: UI framework with modern hooks
- **Vite**: Build tool and dev server for fast development
- **Tailwind CSS**: Utility-first CSS framework with responsive design
- **Axios**: HTTP client for API communication
- **React Router**: Client-side routing
- **React Toastify**: Toast notifications
- **Lucide React**: Icon library
- **Centralized Configuration**: Environment-based config system for zero-code environment switching

### Infrastructure
- **Docker**: Containerization for consistent environments
- **Docker Compose**: Multi-container orchestration
- **Prometheus**: Metrics collection and monitoring
- **Grafana**: Monitoring dashboards and visualization

### Testing & Performance
- **Locust**: Load testing and performance validation
- **Pytest**: Unit testing framework
- **AsyncIO**: Asynchronous performance testing

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)
- OpenAI API key (for text quality analysis)

### 1. Clone the Repository
```bash
git clone https://github.com/halderavik/bot_detection_live.git
cd bot_iden_live
```

### 2. Environment Setup
```bash
# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit configuration files with your settings
```

### 3. Start with Docker Compose
```bash
# Start all services
docker-compose up -d

# Start with monitoring
docker-compose --profile monitoring up -d

# Start production stack
docker-compose --profile production up -d
```

### 4. Access Services

#### Local Development
- **API Documentation**: http://localhost:8000/docs
- **Frontend Dashboard**: http://localhost:3000
- **Grafana Monitoring**: http://localhost:3001 (if monitoring enabled)

#### Production (GCP)
- **Backend API**: https://bot-backend-119522247395.northamerica-northeast2.run.app
- **API Documentation**: https://bot-backend-119522247395.northamerica-northeast2.run.app/docs
- **Frontend Dashboard**: https://storage.googleapis.com/bot-detection-frontend-20251208/index.html
- **Health Check**: https://bot-backend-119522247395.northamerica-northeast2.run.app/health
- **Metrics Endpoint**: https://bot-backend-119522247395.northamerica-northeast2.run.app/metrics
- **Text Analysis Health**: https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/text-analysis/health

## Add tracking to a Decipher survey

Open **Add Tracking** in the dashboard (`/tracking`), choose the survey's XML file (exported from Decipher's XML editor, `.xml` or `.txt` holding the XML, up to 5 MB), pick the options, and click **Add tracking**. You get:

- a summary of what was added, with the survey id, question and page counts, and any warnings;
- **Download** for the tracked XML (`<name>_tracked.xml`): in Decipher, replace the survey's XML with it and save;
- **Upload to Decipher** (when `DECIPHER_API_KEY` is set): sends the tracked XML straight to Decipher (see below);
- **Open the survey dashboard**, the survey's page (`/surveys/<survey id>`) where its responses appear while people take it.

What goes into the file (nothing else changes):

- the tracker script (`backend/app/assets/live_quality_tracker.js`) as a `respview.client.js` style with `mode="after"`, so it runs on every page alongside the survey's own scripts. It sends behaviour (keys, mouse, scrolling, focus), open-end text, page timing, and grid answers to this API, and runs the composite check on the last page. It never blocks the survey: every call times out, and when the API is slow or unreachable the respondent carries on;
- the respondent id: the tracker reports each respondent under Decipher's own `uuid`, which Decipher writes into the script as it renders the page (`${uuid}`, the only Decipher expression in the script). The same value is the `uuid` variable in Decipher's SPSS, Excel and CSV exports, so a respondent's row in the Decipher data and its results here share one id. In a preview where Decipher does not render it, the tracker makes its own id;
- a hidden results page at the end with the quality variables below, which the tracker fills so each respondent's results are in the Decipher data (SPSS, Excel, CSV) too;
- **Show a privacy notice** (on by default): a short notice at the top of the first page (`QOS_privacy`). The wording can be changed; `$` and square brackets are refused because Decipher would read them as code;
- **End the survey on a clear bot signal** (off by default): a hidden `QOS_EARLY` question on the page you choose and a termination (`QOS_bot_term`) after it. Only the decisive signals you tick end the survey (automated browser, scripted clicks, no mouse or keyboard use, honeypot, open ends that appeared without typing); a score on its own never does. The check only goes on a page break every respondent reaches, never inside a loop or a conditional block; when there is no such page, it is left out and the summary says so.

**Quality variables in the data export.** The tracker fills these on the last page, from the composite check. Text questions come through as strings, number questions as numeric variables. They are filled for respondents who reach the end of the survey; terminates and drop-outs have them blank (their results are still here under the same `uuid`). A number is blank when its check had nothing to work on (for example `QOS_STRAIGHTLINE` in a survey with no grids).

| Variable | Type | Meaning |
|---|---|---|
| `QOS_RESPONDENT` | text | Respondent id here; Decipher's `uuid` |
| `QOS_SESSION` | text | Session id here (opens the respondent's details) |
| `QOS_FLAG` | text | `bot`, `human`, or `unknown` (service not reached) |
| `QOS_SCORE` | text | Composite score 0-1 (40% behaviour, 30% open-end quality, 30% fraud); bot from 0.7 |
| `QOS_RISK` | text | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `QOS_STATUS` | 1-3 | 1 human, 2 suspect (a reason below, or medium risk or worse), 3 bot |
| `QOS_BEHAV` | 0-100 | Behaviour bot score; higher is worse |
| `QOS_OES` | 0-100 | Open-ended answer quality; **higher is better** |
| `QOS_FRAUD` | 0-100 | Fraud score (IP, device, duplicates, location, velocity); higher is worse |
| `QOS_DUP` | 0/1 | Duplicate: same device, repeated IP, or copied answers |
| `QOS_DUP_SCORE` | 0-100 | Highest of the device, IP and copied-answer risks |
| `QOS_IP_RISK` | 0-100 | IP address reuse risk |
| `QOS_DEVICE_RISK` | 0-100 | Same device on other sessions of this survey |
| `QOS_GEO_RISK` | 0-100 | Location does not match the browser's time zone or language |
| `QOS_VELOCITY` | 0-100 | Many surveys started in a short time |
| `QOS_DATACENTER` | 0/1 | Data centre, VPN or proxy IP address |
| `QOS_SPEEDER` | count | Questions answered too fast |
| `QOS_STRAIGHTLINE` | count | Straight-lined grid questions |
| `QOS_FLAGCOUNT` | count | Number of reason codes |
| `QOS_REASON` | code | Main reason (the most severe), 0 for none |
| `QOS_REASONS` | text | Every reason code, comma-separated, for example `10,11,22` |
| `QOS_EARLY` | text | Only with **End the survey on a clear bot signal**: `bot` or `human` at the mid-survey check |

Reason codes (`backend/app/services/quality_variables.py`), most severe first: 1 automated or headless browser, 2 scripted clicks and key presses, 3 pages answered with no mouse or keyboard use, 4 honeypot filled in, 5 open ends that appeared without typing, 6 bot-like behaviour score, 10 data centre / VPN / proxy IP, 11 same device reused, 12 same IP reused, 13 answers copied from another respondent, 14 many surveys in a short time, 15 location mismatch, 20 low-quality open ends, 21 straight-lined grids, 22 speeding.

A survey tracked before these variables existed keeps working; upload it again to add them. If you import the XML in Decipher yourself instead of using **Upload to Decipher**, and the survey has saved data layouts, add the `QOS_` variables to the layout you export with (or export with all variables).

**Survey id.** Responses are grouped under the survey id. By default it is the survey's title (`alt`), for example `Coffee Machine Study`; enter your own id to override it. Each upload creates or updates the survey's record (`tracked_surveys` table).

**Upload to Decipher.** With `DECIPHER_API_KEY` set on the service (your Decipher REST API key, with `DECIPHER_API_BASE` and `DECIPHER_COMPANY`), the result has an **Upload to Decipher** panel. Choose where the file goes:

- **Create a new Decipher survey**, named after the survey id (the default the first time);
- **Update the survey uploaded last time**: the Decipher path is remembered per survey id, so later uploads replace that survey's XML instead of creating another survey;
- **Replace the XML of an existing survey**: paste its path (`selfserve/53b/240101`) or its link.

Decipher checks the file before saving it (`validate=true`) and never replaces the XML of a live survey (`overwriteLive=false`). When Decipher refuses the file, its messages are shown; if a new survey was already created, it is remembered, so uploading again updates it instead of creating another. Only XML that carries tracking for that survey id is sent. After the upload, the quality variables are added to each of the survey's saved data layouts (`layouts.json`) that lacks them: a saved layout lists its export columns one by one, so without this an SPSS or Excel export using that layout would leave them out. A survey without saved layouts is left alone; if the layouts cannot be updated, the upload still succeeds and says so. The API key goes only to Decipher, as the `x-apikey` header, and is removed from any error text. Without the key, the panel says how to set it up and the download still works.

**Uploading again.** A file that already has tracking (from this service, or from another survey builder that writes the same `QOS_*` pieces, such as Quant OS) is not tracked twice: the old tracking is taken out and added again with the current options, and the file's survey id is kept unless you enter a different one. Uploading the same file with the same options gives the same file back.

**Settings Decipher refuses** are caught before anything is sent: a survey with no `compat` (Decipher reads it as 0), a `compat` below 143 (retired), or `compat` 151 and above without `delphi="1"`. **Add tracking** still adds tracking but warns ("Decipher will refuse this file: ..."), and **Upload to Decipher** stops with the reason without contacting Decipher, so no empty survey is left in the Decipher account. XML exported from Decipher always passes.

**What is refused**, with the reason: files that are not a `<survey>` XML, XML that is not well-formed or not UTF-8, files with a DOCTYPE, and surveys that already use `QOS_` labels of their own.

**Signing.** With `TRACKING_TOKEN_SECRET` set, the tracker carries a token signed for its survey id; after the first signed session, the service refuses sessions for that survey without it, so nobody can add fake sessions under its name. Signing is optional: without the secret, tracking works the same, just unsigned, and nothing warns about it.

**Which API the tracker calls.** Set `TRACKER_API_BASE` to the service's public URL, for example `https://bot-backend-<id>.run.app/api/v1`. Without it, the upload uses the address the request came in on. It must be `https://` (Decipher pages are https); plain `http://` is only allowed for `localhost`, and the summary warns that such a file only works on your own computer.

API (used by the screen; also usable directly):

JSON with the tracked `xml`, what was added, warnings, and `dashboard_path`:

```bash
curl -F "file=@coffee_machine_study.xml" -F "terminate=true" -F "after_page=2" -F "signals=automation,honeypot" -F "privacy_notice=true" "http://localhost:8000/api/v1/tracking/decipher"
```

The tracked file itself:

```bash
curl -F "file=@coffee_machine_study.xml" -o coffee_machine_study_tracked.xml "http://localhost:8000/api/v1/tracking/decipher?format=xml"
```

`GET /api/v1/tracking/decipher/options` lists the bot signals, the default privacy wording, whether tracking is signed, and whether Decipher upload is set up.

`POST /api/v1/tracking/decipher/upload` with JSON `{"xml": ..., "survey_id": ..., "survey_path": null, "create_new": false}` sends tracked XML to Decipher and returns `survey_path` and `survey_url`.

Tests: `backend/tests/test_decipher_tracking.py` (injection: plain survey, already-tracked survey, loops and blocks, invalid XML) and `backend/tests/test_tracking_upload_endpoint.py` (the endpoint and a signed session landing in the survey), `backend/tests/test_decipher_upload.py` (Decipher upload against a mocked Decipher API), and `backend/tests/test_quality_variables.py` (the quality variables and their hidden questions). `backend/tests/fixtures/espresso_machine_tracker.xml` is a made-up survey with a loop and a conditional block to try the screen with; it has Decipher's current survey settings (compat 155, `delphi="1"`) and was accepted by Decipher. `backend/tests/fixtures/coffee_demo_survey.xml` is a small, complete demo survey (screener, rating grid, two open ends) that has been run end to end: tracked, uploaded to Decipher, taken as a respondent, and its results seen on Live Quality and in the `QOS_` columns of Decipher's data.

From `backend/` (needs `aiosqlite` from `requirements-test.txt`):

```bash
SECRET_KEY=test python -m pytest tests/test_decipher_tracking.py tests/test_tracking_upload_endpoint.py tests/test_decipher_upload.py
```

## Live quality

Open **Live Quality** in the dashboard (`/quality`, or `/quality?survey=<survey id>`). The left list shows surveys that had tracking added through **Add Tracking** (switch to **All surveys** for surveys sending data through other integrations). For the chosen survey you get, refreshed every 8 seconds while the tab is visible (Pause stops it):

- tiles for started, checked, flagged, bot-like, low-quality text, straight-liners, speeders and duplicates;
- starts over time (clean and flagged, by hour or by day), open-end quality as a histogram, and the number of respondents with each flag (click a bar to filter the table);
- the respondent table: status, text quality, time, flags; click a row for the reasons (behaviour, fraud signals, grid, timing, each flagged open end) and a link to the session;
- **Export CSV**: one row per respondent with the verdict, scores and flags.

**Quality rules** are saved per survey id (`survey_quality_rules` table, created at startup) and start on the recommended defaults. They decide:

| Rule | Default | Meaning |
|---|---|---|
| Bot score threshold | 0.7 | Behaviour score (before decisive signals) at which a respondent is a bot |
| Signals that always mean bot | all five | Automated browser, scripted input, no input, honeypot, untyped open ends |
| Speeder: seconds per page | 3.5 | Average page time below this is a speeder (from the tracker's page times) |
| Speeder: share of median | 0.5 | Also a speeder under this share of the median total time, once 5 respondents are checked (0 turns it off) |
| Straight-lining: minimum grid rows | 3 | Same answer on every row of a grid this size or larger |
| Low-quality reasons | all five | Gibberish, generic, off-topic, copied, low effort |
| Flag pasted answers | on | Open ends that were mostly pasted or appeared without typing |
| High fraud risk threshold | 0.7 | Fraud score at which a respondent is high risk |
| Flag duplicates / data-centre IPs | on / on | |

Rules apply on every read, so the dashboard, the CSV export and the `LQ_` variables follow them as soon as they are saved. They don't change what the service stores, or the `QOS_*` values the tracker writes into the Decipher data (those use the standard scoring). Ending the survey on a bot signal and the privacy notice are chosen on **Add Tracking**.

**Add flags to a data file.** Upload the survey's Decipher export (SPSS `.sav`, `.csv` or `.xlsx`, up to 50 MB) and you get the same file back as `<name>_quality.<ext>` with these variables added at the end. Records match on `QOS_SESSION`, then `QOS_RESPONDENT`, then Decipher's `uuid` (the tracker reports respondents under it), so exports without the `QOS_` columns still match.

| Variable | Meaning |
|---|---|
| `LQ_MATCHED` | 1 when the record was found in the live quality results |
| `LQ_STATUS` | 1 checked, 2 in progress, 3 dropped or ended early |
| `LQ_VERDICT` | 1 human, 2 bot, 3 not checked yet (under the survey's rules) |
| `LQ_BOT_SCORE`, `LQ_BOT_RISK`, `LQ_BOT_SIGNALS` | Behaviour score 0-1, its band (1 low, 2 medium, 3 high), decisive signals that fired |
| `LQ_SECONDS`, `LQ_PAGES`, `LQ_SEC_PER_PAGE` | Time on tracked pages |
| `LQ_TEXT_QUALITY` | Average open-end quality 0-100 |
| `LQ_FRAUD_SCORE`, `LQ_FRAUD_RISK` | Fraud score 0-1 and its band |
| `LQ_F_BOT`, `LQ_F_TEXT`, `LQ_F_PASTED`, `LQ_F_STRAIGHT`, `LQ_F_SPEEDER`, `LQ_F_FLATLINE`, `LQ_F_DUPLICATE`, `LQ_F_FRAUD`, `LQ_F_DATACENTRE` | One 0/1 variable per flag |
| `LQ_NFLAGS`, `LQ_FLAGS` | Number of flags, and all flags as text |

In SPSS files the `LQ_` variables get variable and value labels, and existing variables keep theirs. A file that already has `LQ_` variables gets them replaced, so uploading again after changing the rules refreshes them. CSV and Excel cells are read as text, so ids and codes such as leading zeros come back unchanged.

API (used by the screen; also usable directly; the survey id goes in the query string):

```http
GET    /api/v1/quality/surveys                  # surveys, tracked ones first
GET    /api/v1/quality/results?survey_id=...    # dashboard payload under the survey's rules
GET    /api/v1/quality/export?survey_id=...     # CSV, one row per respondent
GET    /api/v1/quality/rules?survey_id=...      # rules, defaults, what changed, labels
PUT    /api/v1/quality/rules?survey_id=...      # save rules (JSON body: the full rules)
DELETE /api/v1/quality/rules?survey_id=...      # back to the defaults
POST   /api/v1/quality/merge?survey_id=...      # multipart "file"; returns the file, report in X-Quality-Report
```

Tests: `backend/tests/test_live_quality.py` (rows, totals, rules, trend, CSV), `backend/tests/test_quality_merge.py` (matching, CSV, Excel and SPSS round trips), and `backend/tests/test_live_quality_endpoints.py` (the endpoints against SQLite with sessions sent through the API). The data file needs `pandas`, `pyreadstat` and `openpyxl` (in `requirements.txt`).

## Using the dashboard

The dashboard has a left sidebar (a menu button on phones), grouped by task:

- **Monitor**: **Overview** (home: sessions, checks and bots over the last 7 days, every survey with its bot rate, starts and bots per day, the latest bots), **Live Quality** (one survey's live results under its own rules), **Sessions** (every session with its latest verdict; filter by verdict, risk, platform or id; filters stay in the address so a view can be bookmarked).
- **Analyse**: **Open-end quality** and **Reports**.
- **Set up**: **Add tracking** (Decipher XML), **Integrations**, **Settings**.
- **Developers**: **Quick start** and **API playground**.

The old `/dashboard` and `/surveys` addresses open the Overview. Clicking a session opens its page: the verdict and the decisive signals behind it first, then behaviour scores, the session facts, fraud, open ends, grids and timing, with the raw event log and analysis output folded away at the bottom.

**Bot rate** means the same everywhere: sessions judged bots out of sessions that were checked (analysed). A session analysed more than once counts once.

## Settings page

**Settings** shows the keys and options the service uses and where each value comes from (saved here, the environment, or not set):

| Setting | Environment variable |
|---|---|
| Decipher API key, API address, company | `DECIPHER_API_KEY`, `DECIPHER_API_BASE`, `DECIPHER_COMPANY` |
| Qualtrics API token | `QUALTRICS_API_TOKEN` |
| OpenAI API key and model (open-end scoring) | `OPENAI_API_KEY`, `OPENAI_MODEL` |
| Tracker API address, tracking signing secret | `TRACKER_API_BASE`, `TRACKING_TOKEN_SECRET` |
| Bot threshold (verdict stored with each new analysis) | `DETECTION_THRESHOLD` |

A value saved on the page overrides the environment variable and applies at once on the instance that saved it; every other instance re-reads saved values every 30 seconds. **Remove saved value** goes back to the environment. Saved values live in the `app_settings` table (created at startup); keys and secrets are encrypted with a key derived from `SECRET_KEY` and are never sent back to the browser, so the page only shows whether they are set. If `SECRET_KEY` changes, saved secrets can no longer be read and the environment values are used (the log says so).

Changing settings needs `ADMIN_TOKEN` (environment only; it can't be set from the page). Without it the page is read-only. With it, unlock the page with the token; it is kept for that browser tab only. The API: `GET /api/v1/settings`, `PUT /api/v1/settings` with header `X-Admin-Token` and body `{"changes": {"KEY": "value" | null}}`.

Per-survey rules (what counts as a bot, speeder, poor answer or fraud for one survey) stay on **Live Quality**.

Tests: `backend/tests/test_runtime_settings.py` (admin token, encryption at rest, live apply, going back to the environment, refused values) and `backend/tests/test_dashboard_numbers.py` (the same bot rate on every page, session verdicts and filters).

## 📚 Documentation

### Core Documentation
- **[Architecture Documentation](architecture.md)**: Comprehensive system architecture and interaction patterns
- **[API Reference](API.md)**: Complete API documentation with examples
- **[Technical Planning](planning.md)**: Production deployment and scaling considerations
- **[Product Requirements](prd.md)**: Product specifications and success metrics
- **[Development Tasks](task.md)**: Current progress and upcoming features

### API Documentation

#### Core Endpoints

#### Sessions
```http
POST /api/v1/detection/sessions
GET /api/v1/detection/sessions/{session_id}/status
GET /api/v1/detection/sessions/{session_id}/ready-for-analysis
```

#### Events
```http
POST /api/v1/detection/sessions/{session_id}/events
```

#### Analysis
```http
POST /api/v1/detection/sessions/{session_id}/analyze
POST /api/v1/detection/sessions/{session_id}/composite-analyze
```

#### Dashboard
```http
GET /api/v1/dashboard/overview
GET /api/v1/dashboard/sessions
GET /api/v1/dashboard/sessions/{session_id}/details
```

#### Text Quality Analysis
```http
POST /api/v1/text-analysis/questions
POST /api/v1/text-analysis/responses
GET /api/v1/text-analysis/sessions/{session_id}/summary
GET /api/v1/text-analysis/stats
GET /api/v1/text-analysis/dashboard/summary
GET /api/v1/text-analysis/dashboard/respondents
GET /api/v1/text-analysis/health
```

#### Integrations
```http
POST /api/v1/integrations/webhooks/qualtrics
POST /api/v1/integrations/webhooks/decipher
POST /api/v1/tracking/decipher              # Upload a Decipher survey XML, get it back with tracking
POST /api/v1/tracking/decipher/upload       # Send tracked XML to Decipher (new survey or existing path)
GET  /api/v1/tracking/decipher/options      # Bot signals and defaults for the upload screen
GET /api/v1/integrations/status
```

#### Report Builder
```http
GET /api/v1/reports/surveys
GET /api/v1/reports/summary/{survey_id}
GET /api/v1/reports/detailed/{survey_id}
GET /api/v1/reports/detailed/{survey_id}/csv
GET /api/v1/reports/summary/{survey_id}/pdf
POST /api/v1/reports/generate
```

#### Hierarchical API (V2) ✅ **COMPLETED**
```http
GET /api/v1/surveys
GET /api/v1/surveys/{survey_id}
GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents
GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}
GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions
GET /api/v1/surveys/{survey_id}/text-analysis/summary
GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/text-analysis/summary
GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/text-analysis/summary
GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}/text-analysis
```

#### Fraud Detection API ✅ **COMPLETED & DEPLOYED**
```http
# Flat endpoints (session-based)
GET /api/v1/fraud/sessions/{session_id}
GET /api/v1/fraud/ip/{ip_address}
GET /api/v1/fraud/fingerprint/{fingerprint}
GET /api/v1/fraud/dashboard/summary
GET /api/v1/fraud/dashboard/duplicates
POST /api/v1/fraud/analyze/{session_id}

# Hierarchical endpoints (V2)
GET /api/v1/surveys/{survey_id}/fraud/summary
GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/fraud/summary
GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/fraud/summary
GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}/fraud
```

**Note**: Fraud detection endpoints use `/api/v1/fraud/` prefix (not `/api/v1/fraud-detection/`).

#### Health & Monitoring
```http
GET /health
GET /metrics
```

**Production Status**: ✅ All endpoints operational
- **Health**: 200 OK - `{"status":"healthy","service":"bot-detection-api"}`
- **Metrics**: 200 OK - Prometheus-compatible metrics exposed
- **Reports**: 200 OK - Report builder fully functional with CSV exports and text quality metrics
- **Text Analysis Dashboard**: 200 OK - Real-time text quality analysis with filtering and pagination
- **OpenAI Integration**: 200 OK - GPT-4o-mini service operational with 100% test accuracy

### Example Usage

#### 1. Create a Session
```bash
# Local
curl -X POST "http://localhost:8000/api/v1/detection/sessions" \
  -H "Content-Type: application/json"

# Production
curl -X POST "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/detection/sessions" \
  -H "Content-Type: application/json"
```

#### 2. Send Events
```bash
# Local
curl -X POST "http://localhost:8000/api/v1/detection/sessions/{session_id}/events" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "event_type": "keystroke",
      "timestamp": "2024-01-01T12:00:00Z",
      "key": "a",
      "element_id": "input-1"
    }
  ]'

# Production
curl -X POST "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/detection/sessions/{session_id}/events" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "event_type": "keystroke",
      "timestamp": "2024-01-01T12:00:00Z",
      "key": "a",
      "element_id": "input-1"
    }
  ]'
```

#### 3. Check if Session is Ready for Analysis
```bash
# Local
curl -X GET "http://localhost:8000/api/v1/detection/sessions/{session_id}/ready-for-analysis"

# Production
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/detection/sessions/{session_id}/ready-for-analysis"
```

#### 4. Analyze Session
```bash
# Local
curl -X POST "http://localhost:8000/api/v1/detection/sessions/{session_id}/analyze"

# Production
curl -X POST "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/detection/sessions/{session_id}/analyze"
```

#### 5. Text Quality Analysis
```bash
# Capture a survey question
curl -X POST "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/text-analysis/questions" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "question_text": "What is your favorite color?",
    "question_type": "open_ended",
    "element_id": "color-input"
  }'

# Analyze a response
curl -X POST "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/text-analysis/responses" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "question_id": "question-id",
    "response_text": "My favorite color is blue because it reminds me of the ocean.",
    "response_time_ms": 2500
  }'

# Get text quality summary
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/text-analysis/sessions/{session_id}/summary"

# Composite analysis (behavioral + text quality)
curl -X POST "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/detection/sessions/{session_id}/composite-analyze"

# Hierarchical text analysis endpoints (V2)
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/{survey_id}/text-analysis/summary"
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/{survey_id}/platforms/{platform_id}/text-analysis/summary"
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/text-analysis/summary"
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}/text-analysis"
```

#### 6. Fraud Detection Analysis
```bash
# Get fraud summary for a survey
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/{survey_id}/fraud/summary"

# Get fraud summary for a platform
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/{survey_id}/platforms/{platform_id}/fraud/summary"

# Get fraud summary for a respondent
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/fraud/summary"

# Get fraud details for a session
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}/fraud"

# Trigger fraud analysis for a session
curl -X POST "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/fraud/analyze/{session_id}"

# Get fraud dashboard summary
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/fraud/dashboard/summary?days=7"

# Get duplicate sessions
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/fraud/dashboard/duplicates?limit=50"
```

#### 7. Generate Reports
```bash
# Get available surveys
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/reports/surveys"

# Generate summary report
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/reports/summary/SURVEY_001"

# Generate detailed report
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/reports/detailed/SURVEY_001"

# Download CSV report
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/reports/detailed/SURVEY_001/csv" \
  -o survey_report.csv

# Get text analysis dashboard summary
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/text-analysis/dashboard/summary?days=7"

# Get respondent-level text analysis
curl -X GET "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1/text-analysis/dashboard/respondents?days=7&limit=10"
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/bot_detection

# Security
SECRET_KEY=your-super-secret-key
TRACKING_TOKEN_SECRET=shared-secret-for-signed-survey-tokens
TRACKER_API_BASE=https://your-api-domain.com/api/v1   # URL the survey tracker calls
ADMIN_TOKEN=a-long-random-token   # lets the Settings page save changes; unset = read-only
ALLOWED_ORIGINS=["http://localhost:3000"]

# Integrations
QUALTRICS_API_TOKEN=your-qualtrics-token
DECIPHER_API_KEY=your-decipher-key
DECIPHER_API_BASE=https://selfserve.decipherinc.com/api/v1
DECIPHER_COMPANY=self

# Bot Detection
DETECTION_THRESHOLD=0.7
SESSION_TIMEOUT_MINUTES=30

# OpenAI settings (for text quality analysis)
# If not set, text analysis will use fallback mode with basic scoring
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=500
OPENAI_TEMPERATURE=0.3
OPENAI_TIMEOUT=30
OPENAI_MAX_RETRIES=3

# Debug Mode
DEBUG=true
```

#### Text Analysis Configuration

The text analysis feature uses OpenAI GPT-4o-mini for advanced quality scoring. If `OPENAI_API_KEY` is not set:

- Text analysis endpoints will still be available
- Analysis will use fallback scoring (quality score: 50, no flags)
- All endpoints return 200 responses with basic analysis results
- Check `/api/v1/text-analysis/stats` to see OpenAI availability status

#### Frontend (.env)
```env
# Local Development
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_FRONTEND_BASE_URL=http://localhost:3000
VITE_APP_NAME=Bot Detection Dashboard

# Production (.env.production)
VITE_API_BASE_URL=https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1
VITE_FRONTEND_BASE_URL=https://storage.googleapis.com/bot-detection-frontend-20251208
VITE_APP_NAME=Bot Detection Dashboard
```

#### Centralized Configuration
The frontend uses a centralized configuration system (`frontend/src/config/config.ts`) that automatically derives all URLs from environment variables:

- **API URLs**: Automatically constructed from `VITE_API_BASE_URL`
- **Webhook URLs**: Dynamically generated for integrations
- **Documentation URLs**: Auto-linked to API docs
- **Frontend URLs**: Used for integration guides and links

This enables zero-code environment switching by simply changing environment variables.

## 🧪 Testing

### Backend Tests
```bash
cd backend
pip install -r requirements.txt
pip install -r requirements-test.txt
pytest
```

### Performance Testing
```bash
# Run Locust load testing
cd backend
locust -f locustfile.py

# Run async performance test
python performance_test.py
```

### Create Test Data
```bash
cd backend
python create_test_data.py
```

### Frontend Tests
```bash
cd frontend
npm install
npm test
```

### Integration Tests
```bash
# Run with Docker
docker-compose exec backend pytest tests/integration/
```

## 📊 Monitoring

### Metrics
The application exposes Prometheus metrics at `/metrics`:
- Request duration
- Error rates
- Session counts
- Detection accuracy
- Processing time statistics

### Logging
Structured logging with configurable levels:
```python
import logging
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
logger.info("Application started")
```

### Health Checks
- **Health endpoint**: `/health` - Basic system status ✅ **OPERATIONAL**
- **Metrics endpoint**: `/metrics` - Prometheus-compatible metrics ✅ **OPERATIONAL**
- **Database connectivity**: Automatic connection testing ✅ **VERIFIED**
- **API responsiveness**: Response time monitoring ✅ **SUB-100MS**

## 🔒 Security

### Authentication
- API key authentication for external integrations
- JWT tokens for user sessions (planned)
- CORS configuration for cross-origin requests

### Data Protection
- Input validation and sanitization with Pydantic
- SQL injection prevention with parameterized queries
- XSS protection
- Rate limiting (configurable)

### Error Handling
- Comprehensive 400/404/500 error responses
- User-friendly error messages
- Detailed logging for debugging
- Input validation with clear feedback

## 🚀 Deployment

### Local Development
```bash
# Build and deploy
docker-compose --profile production up -d

# With monitoring
docker-compose --profile production --profile monitoring up -d
```

### Production Deployment (GCP)
The application is currently deployed on Google Cloud Platform:

#### Backend (Cloud Run)
- **URL**: https://bot-backend-119522247395.northamerica-northeast2.run.app
- **Database**: Cloud SQL PostgreSQL
- **Secrets**: Secret Manager (including OPENAI_API_KEY)
- **Networking**: VPC Connector
- **OpenAI Integration**: Fully operational with `openai_available: true`

#### Frontend (Cloud Storage)
- **URL**: https://storage.googleapis.com/bot-detection-frontend-20251208/index.html
- **CDN**: Cloud CDN enabled
- **Caching**: Optimized for static assets
- **Data Flow**: ✅ Verified - All endpoints pulling data correctly from Cloud SQL (February 2026)
- **Configuration**: Centralized config system with correct production API URLs
- **Components**: Fraud detection widget integrated and operational

#### Deployment Scripts
- `provision-cloudsql.ps1` - Database and networking setup
- `deploy-backend.ps1` - Backend deployment to Cloud Run
- `deploy-frontend.ps1` - Frontend deployment to Cloud Storage
- `cloudbuild.yaml` - CI/CD pipeline configuration

#### Frontend Deployment Verification (February 2026)
**Status:** ✅ **VERIFIED**
- ✅ Frontend successfully built and deployed to Cloud Storage
- ✅ All API endpoints verified returning data from Cloud SQL
- ✅ Data flow verified: Cloud SQL → Backend API → Frontend Dashboard
- ✅ Fraud detection widget integrated and operational
- ✅ All 6 frontend-used endpoints tested and working:
  - Dashboard Overview (`/api/v1/dashboard/overview`)
  - Fraud Dashboard Summary (`/api/v1/fraud/dashboard/summary`)
  - Fraud Duplicates (`/api/v1/fraud/dashboard/duplicates`)
  - Sessions List (`/api/v1/dashboard/sessions`)
  - Surveys List (`/api/v1/surveys`)
  - Text Analysis Summary (`/api/v1/text-analysis/dashboard/summary`)
- ✅ Cache headers configured for optimal performance
- ✅ Frontend configuration updated with correct production URLs

### Environment-Specific Configs
- **Development**: `docker-compose.yml`
- **Staging**: `docker-compose.staging.yml`
- **Production**: GCP Cloud Run + Cloud Storage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for frontend
- Write comprehensive tests
- Update documentation
- Run performance tests before submitting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [Architecture Guide](architecture.md)
- [API Reference](API.md)
- [Integration Guide](API.md#integration-apis)
- [Deployment Guide](planning.md)

### Community
- [Issues](https://github.com/halderavik/bot_detection_live/issues)
- [Discussions](https://github.com/halderavik/bot_detection_live/discussions)

### Contact
- Email: support@botdetection.com
- Slack: #bot-detection

## 🗺️ Roadmap

### Phase 1 (Current) ✅
- ✅ Core bot detection engine
- ✅ Basic API endpoints
- ✅ Survey platform integrations
- ✅ Dashboard UI with comprehensive features
- ✅ Performance testing
- ✅ Error handling improvements
- ✅ Client SDKs
- ✅ Architecture documentation
- ✅ Comprehensive API documentation
- ✅ Frontend integration fixes and enhancements
- ✅ Integration management interface
- ✅ API playground and quick start guide
- ✅ **Production deployment on GCP**
- ✅ **Cloud Run backend with Cloud SQL**
- ✅ **Cloud Storage frontend with CDN**
- ✅ **Automated deployment scripts**
- ✅ **Metrics endpoint deployed and operational**
- ✅ **Full system health verification completed**
- ✅ **Centralized Configuration System** - Environment-based config for zero-code switching
- ✅ **Environment-Agnostic Frontend** - All URLs dynamically derived from environment variables
- ✅ **OpenAI Text Quality Analysis** - GPT-4o-mini powered analysis of open-ended responses
- ✅ **Composite Bot Detection** - Unified scoring combining behavioral + text quality
- ✅ **Enhanced JavaScript SDK** - Automatic question/answer capture and text quality tracking
- ✅ **OpenAI API Key Integration** - Production OpenAI service fully operational
- ✅ **100% Test Classification Accuracy** - All test cases passing with perfect accuracy
- ✅ **Text Analysis Health Monitoring** - Real-time OpenAI service status tracking
- ✅ **Text Analysis Dashboard Integration** - Complete backend and frontend implementation
- ✅ **Enhanced Report Service** - Text quality, fraud, grid, and timing metrics in summary/detailed reports and CSV export
- ✅ **Comprehensive Test Suite** - 14 passing tests for all new functionality
- ✅ **Production Deployment** - All new features deployed and operational
- ✅ **Hierarchical API Structure** - Survey → Platform → Respondent → Session hierarchy implemented
- ✅ **Database Migration** - `platform_id` column and composite indexes deployed
- ✅ **Respondent Aggregation** - All respondent endpoints tested and verified working
- ✅ **Fraud Detection Service** - Complete implementation with IP tracking, device fingerprinting, duplicate detection, geolocation, and velocity checking
- ✅ **Fraud Detection Database Schema** - `fraud_indicators` table with hierarchical fields and composite indexes ✅ **COMPLETED**
- ✅ **Composite Bot Detection** - Updated to 40% behavioral, 30% text quality, 30% fraud detection
- ✅ **Fraud Detection Hierarchical Endpoints** - Survey/platform/respondent/session-level fraud summaries operational
- ✅ **Fraud Detection Frontend Integration** - Hierarchical fraud widgets integrated into all detail views
- ✅ **Unit Tests** - Comprehensive test suite with 100% passing rate for fraud detection
- ✅ **Database Migration** - Fraud detection schema migration executed successfully

### Phase 2 (Next)
- 🔄 Machine learning models
- 🔄 Advanced analytics
- 🔄 Mobile SDK
- 🔄 Real-time alerts
- 🔄 Authentication system
- 🔄 Rate limiting

### Phase 3 (Future)
- 📋 Multi-language support
- 📋 Advanced reporting
- 📋 Enterprise features
- 📋 API marketplace
- 📋 Billing system
- 📋 Multi-tenant support

## 🎯 Performance Achievements

- **Response Times**: Sub-100ms for most endpoints
- **Database**: Async operations with connection pooling
- **Error Handling**: Comprehensive validation and user-friendly messages
- **Scalability**: Modular architecture ready for horizontal scaling
- **Testing**: Automated performance validation with Locust
- **Architecture**: Well-documented system design with clear interaction patterns
- **Frontend**: Fast, responsive React dashboard with real-time updates
- **Integration**: Seamless survey platform integration with webhook testing
- **Production**: Successfully deployed on GCP with Cloud Run and Cloud Storage
- **Infrastructure**: Automated deployment with PowerShell scripts and Cloud Build
- **Monitoring**: Health checks and metrics exposed for production monitoring ✅ **VERIFIED**
- **System Health**: All endpoints operational, database connected, full analysis pipeline tested
- **Configuration**: Centralized config system enables zero-code environment switching
- **Environment Management**: All URLs dynamically derived from environment variables
- **Text Quality Analysis**: GPT-4o-mini integration with caching, rate limiting, and cost optimization ✅ **100% TEST ACCURACY ACHIEVED**
- **Fraud Detection**: Complete fraud detection system with IP tracking, device fingerprinting, duplicate detection, geolocation, and velocity checking ✅ **FULLY OPERATIONAL**
- **Composite Detection**: Unified bot detection combining behavioral patterns (40%), text quality (30%), and fraud detection (30%) ✅ **FULLY OPERATIONAL**
- **Real-time Processing**: Automatic question/answer capture and immediate text analysis
- **OpenAI Integration**: Production-ready with 100% classification accuracy on test cases ✅ **VERIFIED**
- **Hierarchical Fraud Detection**: Survey/platform/respondent/session-level fraud summaries with efficient database queries ✅ **COMPLETED**

---

**Built with ❤️ for secure and reliable bot detection** 