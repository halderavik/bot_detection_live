# Bot Detection System Architecture

## Table of Contents
1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Backend Architecture](#backend-architecture)
4. [Frontend Architecture](#frontend-architecture)
5. [Database Design](#database-design)
6. [API Layer Design](#api-layer-design)
7. [API-Backend-Frontend Interaction Patterns](#api-backend-frontend-interaction-patterns)
8. [Integration Architecture](#integration-architecture)
9. [Data Flow Diagrams](#data-flow-diagrams)
10. [Security Architecture](#security-architecture)
11. [Performance & Scalability](#performance--scalability)
12. [Deployment Architecture](#deployment-architecture)
13. [Monitoring & Observability](#monitoring--observability)

---

## System Overview

The Bot Detection System is a comprehensive platform that combines behavioral analysis, OpenAI-powered text quality analysis, fraud detection, survey platform integration, and real-time monitoring to detect and prevent bot activity. The system is a single FastAPI backend service with a modular internal design, a React frontend, and PostgreSQL for data persistence. It can also add live tracking to a Forsta Decipher survey XML, show each tracked survey's results on a Live Quality page under per-survey rules, and write quality scores back into the survey's own data.

**Self-contained.** This repository has no dependency on Quant OS (Quant_Sys). It stays compatible with surveys that Quant OS tracked: it uses the same `QOS_` variable labels, recognises the Quant OS tracking marker in a survey XML and re-tracks the survey instead of tracking it twice, and builds the same device-fingerprint text. `TRACKING_TOKEN_SECRET` is optional; it only needs to be shared with Quant OS if both systems should issue matching tokens.

## Implementation Status ✅ **COMPLETED & READY TO DEPLOY**

### ✅ **FULLY IMPLEMENTED & TESTED**
- **Fraud Detection Service**: Complete implementation with all 5 detection methods ✅ **COMPLETED**
- **Database Schema**: fraud_indicators table with hierarchical support ✅ **COMPLETED**
- **API Endpoints**: All hierarchical fraud detection endpoints implemented ✅ **COMPLETED**
- **Frontend Components**: Hierarchical fraud widgets integrated ✅ **COMPLETED**
- **Composite Scoring**: 40/30/30 weighting (behavioral/text/fraud) integrated ✅ **COMPLETED**
- **Unit Tests**: 100% passing rate ✅ **COMPLETED**
- **Migration**: Database migration script created and ready ✅ **COMPLETED**
- ✅ **Production Deployment**: Dashboard redeployed February 2026 with fraud/grid/timing in API Playground and Report Builder
- **Decipher XML tracking**: Add tracking page and `/tracking` API add the live tracker and 21 hidden `QOS_` variables to a Decipher survey XML, and can upload it to Decipher (deployed November 2026)
- **Live Quality**: `/quality` page and API with per-survey quality rules, CSV export, and `LQ_` variables merged into a data file (deployed November 2026)
- **Settings that save**: `/settings` API stores overrides in the database, encrypted for secrets, behind `ADMIN_TOKEN` (deployed November 2026)

**Deployment Status**: 
- ✅ **FULLY DEPLOYED** (Behavioral Detection, Text Analysis, Hierarchical API, Fraud Detection) on Google Cloud Platform (February 2026)
- ✅ **PRODUCTION DEPLOYED** (Stage 3 - Fraud & Duplicate Detection) - Fully operational and tested
- ✅ **Dashboard redeployed February 2026**: API Playground fraud/grid/timing templates; Report Builder fraud, grid, and timing in summary and detailed reports/CSV; respondent detail popup and full CSV per respondent
- **Backend**: Cloud Run at `https://bot-backend-119522247395.northamerica-northeast2.run.app`
- **Frontend**: static site in the Cloud Storage bucket `bot-detection-frontend-20251208`, served directly at `https://storage.googleapis.com/bot-detection-frontend-20251208/index.html` (no CDN in front of it; the only Cloud CDN backend in the project points at the older `bot-detection-frontend-20250929` bucket)
- **Database**: Cloud SQL PostgreSQL (instances `bot-db` and `bot-db-v2`) with VPC Connector
- **Secrets**: Secret Manager for DATABASE_URL, SECRET_KEY, OPENAI_API_KEY, and ADMIN_TOKEN
- **Production Testing**: 100% passing rate on all endpoints including fraud detection
- **Real Example Testing**: Comprehensive testing completed with all endpoints verified operational (February 2026)

### Core Components (Deployment Status)
- **Backend API**: FastAPI-based REST API with async support ✅ **DEPLOYED**
- **Frontend Dashboard**: React-based real-time monitoring interface with comprehensive features ✅ **DEPLOYED**
- **Bot Detection Engine**: Rule-based behaviour analysis with seven decisive signals; the verdict follows each survey's quality rules. A composite score (40% behavioral + 30% text quality + 30% fraud) is still calculated and reported, but does not decide bot or human (see [Detection logic](#detection-logic)) ✅ **DEPLOYED**
- **Text Quality Engine**: OpenAI GPT-4o-mini powered analysis for response authenticity, one call per answer ✅ **DEPLOYED**
- **Fraud Detection Service**: IP tracking, device fingerprinting, duplicate detection, velocity checking, data-centre IPs; the geolocation check is left out of the fraud score until there is an IP-to-country lookup ✅ **COMPLETED**
- **Hierarchical API**: Survey → Platform → Respondent → Session structure for aggregated data access ✅ **DEPLOYED**
- **Fraud Detection Hierarchical Endpoints**: Survey/platform/respondent/session-level fraud summaries ✅ **COMPLETED**
- **Integration Layer**: Webhook handlers for Qualtrics and Decipher with testing interface ✅ **DEPLOYED**
- **Decipher Tracking**: Adds the live tracker to a Decipher survey XML and uploads it to Decipher (`decipher_tracking.py`, `decipher_upload.py`, `quality_variables.py`) **DEPLOYED**
- **Live Quality**: Per-survey results under per-survey rules, CSV export, and `LQ_` data-file merge (`live_quality.py`, `quality_rules.py`, `quality_merge.py`) **DEPLOYED**
- **Runtime Settings**: Settings page overrides stored in `app_settings`, applied without a redeploy (`runtime_settings.py`, `settings_controller.py`) **DEPLOYED**
- **Database Layer**: PostgreSQL with async SQLAlchemy ORM, fraud_indicators table, and composite indexes ✅ **DEPLOYED**
- **Client SDKs**: Python and JavaScript libraries for easy integration ✅ **DEPLOYED**
- **Authentication & Authorization**: JWT tokens, API keys, role-based access control ⏳ **PLANNED**
- **Rate Limiting**: Per IP, per server instance: new sessions 30/min, other writes 600/min, Fix with AI 20/hour (`utils/rate_limit.py`); OpenAI calls limited by `OPENAI_REQUESTS_PER_MINUTE` **IMPLEMENTED**
- **Machine Learning Models**: ML-based bot detection algorithms ⏳ **PLANNED**

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Applications                      │
├─────────────────────────────────────────────────────────────────┤
│  Web Browsers  │  Mobile Apps  │  Survey Platforms  │  SDKs    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway Layer                        │
├─────────────────────────────────────────────────────────────────┤
│  Rate Limiting  │  Authentication  │  CORS  │  Request Routing  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Backend Services                         │
├─────────────────────────────────────────────────────────────────┤
│  Detection  │  Text Analysis  │  Dashboard  │  Tracking  │  Live   │
│  Quality  │  Settings  │  Integrations  │  Health                │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Business Logic Layer                     │
├─────────────────────────────────────────────────────────────────┤
│  Bot Detection  │  Text Quality  │  Fraud     │  Decipher       │
│  Engine         │  Engine (AI)   │  Detection │  Tracking/Upload│
│  Live Quality + Rules  │  Runtime Settings  │  Aggregation    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Data Layer                               │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL  │  OpenAI API  │  Decipher API  │  Qualtrics API   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Backend Architecture

### Technology Stack
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL with async SQLAlchemy
- **Caching**: Redis is configured (`REDIS_URL`) but not required; no Redis service is deployed
- **ORM**: SQLAlchemy with async support
- **Validation**: Pydantic for data validation
- **AI Integration**: OpenAI GPT-4o-mini for text quality analysis
- **Data files**: pandas, pyreadstat, and openpyxl for reading and writing SPSS, CSV, and Excel files (Live Quality merge)
- **Authentication**: JWT tokens (planned)
- **Documentation**: OpenAPI/Swagger auto-generation

### Backend Structure
```
backend/
├── app/
│   ├── config.py              # Configuration (environment variables)
│   ├── database.py            # Database connection setup
│   ├── assets/
│   │   └── live_quality_tracker.js  # Tracker script added to Decipher surveys
│   ├── models/                # SQLAlchemy data models
│   │   ├── session.py, behavior_data.py, detection_result.py
│   │   ├── survey_question.py, survey_response.py
│   │   ├── fraud_indicator.py, grid_response.py, timing_analysis.py
│   │   ├── tracked_survey.py         # Surveys tracking was added to
│   │   ├── survey_quality_rules.py   # Per-survey quality rules
│   │   ├── protected_survey.py       # Surveys that require signed tracking
│   │   └── app_setting.py            # Settings page overrides
│   ├── services/              # Business logic services
│   │   ├── bot_detection_engine.py    # Core detection logic
│   │   ├── openai_service.py          # OpenAI API integration
│   │   ├── text_analysis_service.py   # Text quality analysis
│   │   ├── fraud_detection_service.py # Fraud detection
│   │   ├── grid_analysis_service.py, timing_analysis_service.py
│   │   ├── aggregation_service.py     # Survey/platform/respondent totals
│   │   ├── report_service.py
│   │   ├── qualtrics_integration.py, decipher_integration.py  # Webhooks
│   │   ├── decipher_tracking.py       # Add/remove tracking in a Decipher XML
│   │   ├── decipher_upload.py         # Upload tracked XML to Decipher
│   │   ├── quality_variables.py       # QOS_ values written into survey data
│   │   ├── live_quality.py            # Live Quality dashboard payload and CSV
│   │   ├── quality_rules.py           # Per-survey rules and defaults
│   │   ├── quality_merge.py           # LQ_ variables added to a data file
│   │   └── runtime_settings.py        # Saved settings, 30 s refresh, change hooks
│   ├── controllers/           # API controllers
│   │   ├── detection_controller.py, text_analysis_controller.py
│   │   ├── dashboard_controller.py, hierarchical_controller.py
│   │   ├── fraud_detection_controller.py, report_controller.py
│   │   ├── integration_controller.py
│   │   ├── survey_tracking_controller.py  # /tracking
│   │   ├── live_quality_controller.py     # /quality
│   │   └── settings_controller.py         # /settings (ADMIN_TOKEN)
│   ├── routes/
│   │   └── __init__.py        # Main router; all controllers under /api/v1
│   ├── migrations/            # SQL migrations for older tables
│   └── utils/                 # logger, helpers, fraud_helpers, ip_intel,
│                              # rate_limit, survey_tokens
├── main.py                    # Application entry point and startup tasks
├── requirements.txt           # Python dependencies
└── .env.example               # Environment variables (copy to .env)
```

### Newer Backend Components

#### Decipher tracking (`decipher_tracking.py`, `decipher_upload.py`, `quality_variables.py`)
- `decipher_tracking.py` adds the tracker script to a Decipher survey XML as a `respview.client.js` style with `mode="after"`, uses Decipher's `${uuid}` as the respondent id, and adds a hidden results page with 21 `QOS_` variables. It can also add a privacy notice (on by default) and an early end on a clear bot signal (off by default). Removing the tracking gives back the original file byte for byte, so a tracked file is re-tracked instead of tracked twice. It checks the survey's `compat` and `delphi` settings first and warns when Decipher would refuse the file.
- `decipher_upload.py` creates a new Decipher survey (Research Hub) or replaces `survey.xml` of an existing one. Decipher validates the file and never overwrites a live survey. The `QOS_` variables are added to any saved data layouts. The Decipher API key stays on the server.
- `quality_variables.py` turns a composite analysis into the `QOS_` values (scores 0 to 100, reason codes). The composite analysis returns them under `survey_variables`. They follow the survey's quality rules: only enabled bot signals become reason codes, `datacenter_ip` only when `flag_datacenter` is on, and the low-quality open-end reason only for text reasons the rules count. `QOS_SPEEDER` is the number of pages faster than the survey's `speeder_page_seconds` ("Pages answered too fast"), and the speeder reason (22) applies when pages average under that rule. `QOS_DUP_SCORE` uses the duplicate risk (0 under 0.70 similarity, 0.6 from 0.70, 0.8 from 0.85, 1.0 from 0.95), not the raw similarity.
- Signed tracking (`utils/survey_tokens.py`): with `TRACKING_TOKEN_SECRET` set, the tracker carries an HMAC token of the survey id, and a survey listed in `protected_surveys` refuses unsigned sessions. A survey is added there when a signed tracked file is uploaded to Decipher successfully (`_protect_if_signed` in `survey_tracking_controller.py`), or when its first signed session arrives. Making the tracked file alone does not protect it, because the live survey may still run an older unsigned tracker. The token stops outsiders who never saw the survey; anyone who opens the survey page can read it. Production currently has no `TRACKING_TOKEN_SECRET`.

#### Live Quality (`live_quality.py`, `quality_rules.py`, `quality_merge.py`)
- `live_quality.py` builds one survey's dashboard payload: totals, text, fraud, grid and timing summaries, nine flag counts, a quality distribution, a trend, and one row per session. It also writes the CSV export. `totals.respondents` counts people (sessions sharing a respondent id, the Decipher uuid, count once); `totals.sessions` counts sessions. Each row has `other_sessions` and `text_unchecked`; `text.unchecked` is the total of open ends not checked. Straight-lining uses the survey's `straightline_min_rows` when the tracker sent grid answers.
- `quality_rules.py` holds the per-survey rules (stored in `survey_quality_rules`) and the defaults. Rules apply on every read; they do not change stored results or the `QOS_` values already in Decipher. Saved rules also record `known_signals` (the bot signals that existed when they were saved), so signals added later start switched on for that survey while signals it switched off stay off.
- `quality_merge.py` takes a data file (.sav, .csv, .xlsx, up to 50 MB), matches each record on `QOS_SESSION`, then `QOS_RESPONDENT`, then Decipher's `uuid`, and returns the same file with `LQ_` variables added. A uuid with several sessions uses the checked session first, then the latest.

#### Runtime settings (`runtime_settings.py`, `settings_controller.py`)
- Editable keys: `DECIPHER_API_KEY`, `DECIPHER_API_BASE`, `DECIPHER_COMPANY`, `QUALTRICS_API_TOKEN`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `TRACKER_API_BASE`, `TRACKING_TOKEN_SECRET`, `DETECTION_THRESHOLD` (0.3 to 0.99, default 0.7; used by the detection engine for the stored verdict).
- A saved value (table `app_settings`) overrides the environment variable of the same name. It applies at once on the instance that saved it, and every instance re-reads the table every 30 seconds (`keep_fresh`). Removing a saved value goes back to the environment value.
- Environment-only OpenAI limits: `OPENAI_REQUESTS_PER_MINUTE` (default 300, per server) and `OPENAI_RATE_WAIT_SECONDS` (default 20, how long an answer waits for a free slot).
- Other code registers change hooks with `runtime_settings.on_change()`; they run whenever values change. At startup `main.py` registers `openai_service.reload`, so a new OpenAI key or model is used without a restart.
- Secrets are encrypted at rest with a Fernet key derived from `SECRET_KEY` and are never returned to the browser.
- `settings_controller.py`: `GET /api/v1/settings` is open (secrets only report set/not set and their source). `POST /api/v1/settings/check` and `PUT /api/v1/settings` need the `X-Admin-Token` header to match the `ADMIN_TOKEN` environment variable. Without `ADMIN_TOKEN` the settings are read-only (403); a wrong token gets 401.

#### Startup (`main.py`)
On startup the backend creates any missing tables with `create_all` (this is how `tracked_surveys`, `survey_quality_rules`, `app_settings` and `protected_surveys` are created; there is no migration for them), loads saved settings, registers the settings change hooks, and starts the 30-second settings refresh task.

#### Detection logic
- **Behaviour score** (`utils/helpers.py` `calculate_confidence_score`, `services/bot_detection_engine.py`): the checks are combined so agreeing evidence adds up (noisy-OR): score = 1 - product(1 - reliability x check score). Reliabilities: keystroke 0.5, mouse 0.45, timing 0.35, device 0.4, network 0 (not implemented). Two strong checks reach the 0.7 bot threshold; one alone does not. Events the tracker sent twice (same type, timestamp, element, x, y, key) are counted once, and the copy of a grid page's submit that carries grid answers (element id `qos-grid:...`) is not counted as a second page.
- **Decisive signals** (`BOT_SIGNALS` in `services/decipher_tracking.py`), seven in all: `automation`, `scripted_input`, `no_input`, `honeypot`, `untyped_answers`, `robotic_timing` (machine-exact key gaps in at least 3 stretches of 8+ keys, or ruler-straight runs of equal mouse steps covering at least 40% of 30+ mouse points) and `timeline_mismatch` (browser-reported page times of 60+ s that exceed the time the server observed by more than 30 s or 25% of the reported time, whichever is larger). One lifts the behaviour score to 0.85, two or more to 0.95.
- **Final check** (`POST /detection/sessions/{id}/composite-analyze`, `detection_controller.py`): runs behaviour, text, grid, timing and fraud, saving timing and grid results in one batch. `is_bot` and `behavioral_details.is_bot` follow the survey's quality rules (bot threshold, enabled signals), the same verdict as Live Quality. `behavioral_details.engine_is_bot` keeps the verdict under the global `DETECTION_THRESHOLD`, and `composite_is_bot` keeps whether the 40/30/30 composite score alone reached the threshold. Only behaviour decides `is_bot`; text and fraud are their own flags and scores. A behavioural bot gets `risk_level` at least HIGH.
- **Open-end check** (`text_analysis_service.py`, `openai_service.py`): one OpenAI call per answer covers gibberish, copy_paste, relevance, generic and quality, all judged against the question. A per-server limit (`OPENAI_REQUESTS_PER_MINUTE`, default 300) applies; when it is reached an answer waits up to `OPENAI_RATE_WAIT_SECONDS` (default 20). An answer that still cannot be checked is stored as not checked (`quality_score` null, `analysis_details` `{"unchecked": true, "error": ...}`, not flagged), never as a neutral 50.
- **Grids**: straight-lining is the same answer on every row of a grid with at least 3 rows.
- **Fraud** (`fraud_detection_service.py`, `utils/fraud_helpers.py`): weights IP 0.25, device 0.25, duplicate answers 0.20, velocity 0.15, geolocation 0.15. There is no IP-to-country lookup yet, so the location score is left out and the other weights are renormalised. A device fingerprint seen only on other networks (IPv4 /24, IPv6 /48) counts half. Duplicate answers compare only open ends of 20+ characters: exact copies across the whole survey, near copies (70%+ similar) among the latest 2,000 answers. Data-centre IPs give a fraud score of at least 0.75.
- **Stored events**: `behavior_data.event_data` keeps only the event's own fields; fields kept in their own columns or once on the session are not repeated. Rejected events are logged by type only.

### Backend Design Patterns

#### 1. Layered Architecture ✅ **DEPLOYED**
```
┌─────────────────┐
│   API Layer     │ ← Controllers & Routes ✅ DEPLOYED
├─────────────────┤
│ Business Logic  │ ← Services ✅ DEPLOYED
├─────────────────┤
│   Data Layer    │ ← Models & Database ✅ DEPLOYED
└─────────────────┘
```

#### 2. Dependency Injection ✅ **DEPLOYED**
- FastAPI's dependency injection system ✅ **DEPLOYED**
- Database session management ✅ **DEPLOYED**
- Service layer injection ✅ **DEPLOYED**
- Configuration management ✅ **DEPLOYED**

#### 3. Async/Await Pattern ✅ **DEPLOYED**
- Non-blocking I/O operations ✅ **DEPLOYED**
- Database connection pooling ✅ **DEPLOYED**
- Concurrent request handling ✅ **DEPLOYED**
- Background task processing ⏳ **PARTIAL** (basic implementation, advanced queuing planned)

---

## Frontend Architecture

### Technology Stack
- **Framework**: React 18 with hooks
- **Build Tool**: Vite for fast development
- **Styling**: Tailwind CSS for utility-first styling
- **State Management**: React hooks (component state)
- **HTTP Client**: Axios for API communication
- **Charts**: Recharts for data visualization
- **Routing**: React Router; `HashRouter` in production (`VITE_ROUTER_MODE=hash`), `BrowserRouter` in local development
- **Icons**: Lucide React for consistent iconography
- **Notifications**: React Toastify for user feedback

### Frontend Structure
```
frontend/
├── public/                    # Static assets
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   └── AppShell.jsx   # Grouped sidebar, phone menu, service status
│   │   ├── ui/
│   │   │   └── index.jsx      # Shared UI kit (PageHeader, Card, StatCard,
│   │   │                      # Button, Badge, VerdictBadge, RiskBadge,
│   │   │                      # EmptyState, Loading, ErrorBanner, RateBar,
│   │   │                      # formatters)
│   │   ├── quality/           # Live Quality parts (rules, data file, widgets)
│   │   ├── Overview.jsx       # Home page (replaces the old Dashboard)
│   │   ├── LiveQuality.jsx    # Per-survey live results
│   │   ├── SessionList.jsx, SessionDetails.jsx
│   │   ├── SurveyDetails.jsx, PlatformDetails.jsx, RespondentDetails.jsx
│   │   ├── TextAnalysis.jsx, ReportBuilder.jsx
│   │   ├── SurveyTracking.jsx # Add tracking (Decipher XML)
│   │   ├── Integrations.jsx, Settings.jsx
│   │   ├── QuickStartGuide.jsx, ApiPlayground.jsx
│   │   └── *Widget.jsx        # Text, fraud, grid, timing widgets
│   ├── services/
│   │   └── apiService.js      # API communication (Axios)
│   ├── config/                # Frontend configuration
│   ├── styles/                # CSS styles
│   ├── App.jsx                # Routes
│   └── main.jsx               # App entry point
├── .env.production            # Production API URL, VITE_ROUTER_MODE=hash
├── package.json
├── vite.config.js
└── tailwind.config.js
```

### Layout and Routes
`AppShell.jsx` wraps every page. On wide screens it shows a grouped left sidebar; on phones, a top bar with a slide-out menu. The service status (from the health check, refreshed every minute) sits at the bottom of the sidebar. Pages are built from the shared UI kit in `components/ui/index.jsx`.

| Group | Page | Route |
|-------|------|-------|
| Monitor | Overview | `/` (`/dashboard` and `/surveys` redirect here) |
| Monitor | Live Quality | `/quality` |
| Monitor | Sessions | `/sessions` |
| Analyse | Open-end quality | `/text-analysis` |
| Analyse | Reports | `/reports` |
| Set up | Add tracking | `/tracking` |
| Set up | Integrations | `/integrations` |
| Set up | Settings | `/settings` |
| Developers | Quick start | `/quick-start` |
| Developers | API playground | `/api-playground` |

Detail routes: `/surveys/:surveyId`, `/surveys/:surveyId/platforms/:platformId`, `.../respondents/:respondentId`, `.../sessions/:sessionId`, and `/sessions/:sessionId`. Unknown paths show a "page doesn't exist" view.

The production frontend is static files in a Cloud Storage bucket, which cannot send every path to `index.html`. Production therefore uses hash addresses, for example `https://storage.googleapis.com/bot-detection-frontend-20251208/index.html#/quality`. Local development uses normal paths.

### Frontend Design Patterns

#### 1. Component-Based Architecture ✅ **DEPLOYED**
- Reusable UI components ✅ **DEPLOYED**
- Props-based data flow ✅ **DEPLOYED**
- Component composition ✅ **DEPLOYED**
- Separation of concerns ✅ **DEPLOYED**

#### 2. Service Layer Pattern ✅ **DEPLOYED**
- Centralized API communication ✅ **DEPLOYED**
- Error handling ✅ **DEPLOYED**
- Request/response interceptors ✅ **DEPLOYED**
- Data transformation ✅ **DEPLOYED**

#### 3. Custom Hooks Pattern ✅ **DEPLOYED**
- Reusable state logic ✅ **DEPLOYED**
- API data fetching ✅ **DEPLOYED**
- Real-time updates ⏳ **PARTIAL** (polling implemented, WebSocket planned)
- Local state management ✅ **DEPLOYED**

#### 4. Error Boundary Pattern ✅ **DEPLOYED**
- Graceful error handling ✅ **DEPLOYED**
- User-friendly error messages ✅ **DEPLOYED**
- Fallback UI components ✅ **DEPLOYED**
- Error logging and reporting ⏳ **PARTIAL** (console logging, advanced monitoring planned)

---

## Database Design

### Database Schema

#### 1. Sessions Table
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active',
    platform VARCHAR(50),  -- Legacy field, maintained for backward compatibility
    platform_id VARCHAR(50),  -- Hierarchical field for platform identification
    survey_id VARCHAR(255),
    respondent_id VARCHAR(255),
    is_completed BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Composite indexes for hierarchical queries
CREATE INDEX idx_survey_platform_respondent_session 
    ON sessions (survey_id, platform_id, respondent_id, id);
CREATE INDEX idx_survey_platform 
    ON sessions (survey_id, platform_id);
CREATE INDEX idx_survey_platform_respondent 
    ON sessions (survey_id, platform_id, respondent_id);
```

#### 2. Behavior Data Table
```sql
CREATE TABLE behavior_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    event_data JSONB NOT NULL,  -- the event's own fields only; page details, ids and sizes have their own columns (see database.md)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 3. Detection Results Table
```sql
CREATE TABLE detection_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    is_bot BOOLEAN NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    processing_time_ms INTEGER,
    event_count INTEGER,
    analysis_summary TEXT,
    method_scores JSONB,
    fraud_score DECIMAL(3,2),  -- ✅ DEPLOYED: Fraud detection score
    fraud_indicators JSONB,     -- ✅ DEPLOYED: Fraud detection details
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 3b. Fraud Indicators Table ✅ **DEPLOYED**
```sql
CREATE TABLE fraud_indicators (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    
    -- Hierarchical fields for efficient querying ✅ DEPLOYED
    survey_id VARCHAR(255),
    platform_id VARCHAR(255),
    respondent_id VARCHAR(255),
    
    -- IP Analysis ✅ DEPLOYED
    ip_address VARCHAR(45),
    ip_usage_count INTEGER DEFAULT 0,
    ip_sessions_today INTEGER DEFAULT 0,
    ip_risk_score DECIMAL(3,2),
    ip_country_code VARCHAR(2),
    ip_city VARCHAR(100),
    
    -- Device Fingerprint ✅ DEPLOYED
    device_fingerprint TEXT,
    fingerprint_usage_count INTEGER DEFAULT 0,
    fingerprint_risk_score DECIMAL(3,2),
    
    -- Response Pattern ✅ DEPLOYED
    response_similarity_score DECIMAL(3,2),
    duplicate_response_count INTEGER DEFAULT 0,
    
    -- Geolocation ✅ DEPLOYED
    geolocation_consistent BOOLEAN DEFAULT TRUE,
    geolocation_risk_score DECIMAL(3,2),
    
    -- Velocity ✅ DEPLOYED
    responses_per_hour DECIMAL(5,2),
    velocity_risk_score DECIMAL(3,2),
    
    -- Overall ✅ DEPLOYED
    overall_fraud_score DECIMAL(3,2),
    is_duplicate BOOLEAN DEFAULT FALSE,
    fraud_confidence DECIMAL(3,2),
    
    -- Metadata
    flag_reasons JSONB,
    analysis_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Hierarchical indexes for efficient aggregation queries ✅ DEPLOYED
CREATE INDEX idx_fraud_survey ON fraud_indicators(survey_id);
CREATE INDEX idx_fraud_survey_platform ON fraud_indicators(survey_id, platform_id);
CREATE INDEX idx_fraud_survey_platform_respondent ON fraud_indicators(survey_id, platform_id, respondent_id);
```

#### 4. Survey Questions Table
```sql
CREATE TABLE survey_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) NOT NULL,
    element_id VARCHAR(255),
    page_url TEXT,
    page_title TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 5. Survey Responses Table
```sql
CREATE TABLE survey_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    question_id UUID REFERENCES survey_questions(id) ON DELETE CASCADE,
    response_text TEXT NOT NULL,
    response_time_ms DECIMAL(10,2),
    quality_score DECIMAL(5,2),  -- NULL when the answer could not be checked
    is_flagged BOOLEAN DEFAULT FALSE,
    flag_reasons JSONB,
    analysis_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    analyzed_at TIMESTAMP WITH TIME ZONE
);
```

#### 6. Tables created at startup (no migration)
`backend/main.py` runs `create_all` at startup, which creates these tables if they are missing and leaves existing tables unchanged. Full column lists are in [database.md](database.md).

- **tracked_surveys**: one row per survey id that had tracking added (survey_id PK, title, source_filename, platform_id, signed, terminate, privacy_notice, decipher_path, uploads, created_at, updated_at).
- **survey_quality_rules**: per-survey Live Quality rules (survey_id PK, rules JSON, updated_at).
- **app_settings**: Settings page overrides (key PK, value, is_secret, updated_at). Secret values are encrypted with a key derived from `SECRET_KEY`.
- **protected_surveys**: survey ids that require a signed tracking token (survey_id PK, created_at).

These tables are keyed by survey id or setting name and have no foreign keys to `sessions`.

### Counting Rule
Bot rate everywhere is sessions judged bots divided by sessions checked (analysed), counting distinct sessions: a session analysed twice counts once. This applies to `/dashboard/overview`, `/dashboard/analytics/trends`, `/surveys`, `/surveys/{id}`, and the platform and respondent aggregations.

### Database Relationships
```
sessions (1) ──── (N) behavior_data
sessions (1) ──── (N) detection_results
sessions (1) ──── (N) survey_questions
sessions (1) ──── (N) survey_responses
sessions (1) ──── (N) fraud_indicators ✅ DEPLOYED
survey_questions (1) ──── (N) survey_responses
```

### Database Optimization
- **Indexes**: On frequently queried columns
- **Partitioning**: By date for large tables
- **Connection Pooling**: Async connection management
- **Query Optimization**: Eager loading for relationships

---

## API Layer Design

### API Structure

#### 1. RESTful Endpoints
```
/api/v1/
├── detection/
│   ├── sessions                    # Session management
│   ├── sessions/{id}/events        # Event ingestion
│   ├── sessions/{id}/status        # Session status
│   ├── sessions/{id}/analyze       # Bot detection analysis
│   ├── sessions/{id}/composite-analyze # Composite analysis
│   └── sessions/{id}/ready-for-analysis
├── surveys/                        # Hierarchical API (V2) ✅ DEPLOYED
│   ├── ""                          # List all surveys
│   ├── {survey_id}                 # Survey details
│   ├── {survey_id}/summary         # Survey summary
│   ├── {survey_id}/platforms       # List platforms
│   ├── {survey_id}/platforms/{platform_id}  # Platform details
│   ├── {survey_id}/platforms/{platform_id}/respondents  # List respondents
│   ├── {survey_id}/platforms/{platform_id}/respondents/{respondent_id}  # Respondent details
│   ├── {survey_id}/platforms/{platform_id}/respondents/{respondent_id}/summary  # Respondent summary
│   ├── {survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions  # List sessions
│   ├── {survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}  # Session by hierarchy
│   ├── {survey_id}/fraud/summary   # Survey fraud summary ✅ DEPLOYED
│   ├── {survey_id}/platforms/{platform_id}/fraud/summary  # Platform fraud summary ✅ DEPLOYED
│   ├── {survey_id}/platforms/{platform_id}/respondents/{respondent_id}/fraud/summary  # Respondent fraud summary ✅ DEPLOYED
│   └── {survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}/fraud  # Session fraud details ✅ DEPLOYED
├── text-analysis/
│   ├── questions                   # Question capture
│   ├── responses                   # Response analysis
│   ├── sessions/{id}/summary       # Text quality summary
│   ├── stats                       # OpenAI usage stats
│   ├── health                      # OpenAI service health
│   ├── dashboard/summary            # Dashboard summary
│   └── dashboard/respondents       # Respondent-level analysis
├── fraud/                          # Fraud Detection API ✅ DEPLOYED
│   ├── sessions/{id}               # Get fraud indicators for session
│   ├── ip/{ip_address}             # Get sessions by IP
│   ├── fingerprint/{fingerprint}   # Get sessions by device fingerprint
│   ├── dashboard/summary           # Fraud dashboard summary
│   ├── dashboard/duplicates        # Duplicate sessions list
│   └── analyze/{session_id}        # Trigger fraud analysis
├── surveys/                        # Hierarchical API (V2) ✅ DEPLOYED
│   ├── {survey_id}/text-analysis/summary  # Survey-level text analysis
│   ├── {survey_id}/platforms/{platform_id}/text-analysis/summary  # Platform-level text analysis
│   ├── {survey_id}/platforms/{platform_id}/respondents/{respondent_id}/text-analysis/summary  # Respondent-level text analysis
│   └── {survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}/text-analysis  # Session-level text analysis
├── dashboard/
│   ├── overview                    # Dashboard overview (distinct-session counts)
│   ├── sessions                    # Session list (newest first, filters)
│   ├── sessions/{id}/details       # Session details
│   └── analytics/trends            # Day buckets aligned to midnight UTC
├── tracking/
│   ├── decipher                    # POST: add tracking to a Decipher XML
│   ├── decipher/upload             # POST: upload tracked XML to Decipher
│   └── decipher/options            # GET: signals, privacy text, upload configured
├── quality/                        # Live Quality (?survey_id= on each)
│   ├── surveys                     # Every survey, tracked ones first
│   ├── results                     # Dashboard payload under the survey's rules
│   ├── export                      # CSV, one row per respondent
│   ├── rules                       # GET/PUT/DELETE per-survey rules
│   └── merge                       # POST data file, returns it with LQ_ variables
├── settings                        # GET (open); PUT needs X-Admin-Token
│   └── check                       # POST, needs X-Admin-Token
├── integrations/
│   ├── webhooks/qualtrics          # Qualtrics webhook
│   ├── webhooks/decipher           # Decipher webhook
│   └── status                      # Integration status
└── health                          # Health check
```

#### 2. Request/Response Flow
```
Client Request → API Gateway → Controller → Service → Database
                ↓                              ↓
Client Response ← Serializer ← Service ← Database ← Query
                ↓                              ↓
Text Analysis Request → OpenAI API → GPT-4o-mini → Analysis Results
```

#### 3. Error Handling
- **HTTP Status Codes**: Standard REST status codes
- **Error Response Format**: Consistent error structure
- **Validation**: Pydantic model validation
- **Logging**: Structured error logging

### API Design Principles

#### 1. RESTful Design
- Resource-based URLs
- HTTP method semantics
- Stateless operations
- Consistent response formats

#### 2. Async Operations
- Non-blocking I/O
- Concurrent request handling
- Background processing
- Real-time updates

#### 3. Data Validation
- Request validation with Pydantic
- Response serialization
- Type safety
- Schema documentation

---

## API-Backend-Frontend Interaction Patterns

### Real-Time Dashboard Updates

#### 1. Dashboard Data Flow
```
Frontend Dashboard → API Request → Backend Controller → Database Query
       ↓
   React State ← JSON Response ← Service Layer ← Aggregated Data
       ↓
   UI Re-render ← State Update ← useEffect Hook ← Data Change
```

#### 2. Polling Strategy
- **Interval-based Updates**: The Overview page reloads every 60 seconds while the browser tab is visible; the sidebar service status checks health every 60 seconds
- **Background Updates**: Non-blocking data refresh
- **Error Handling**: Graceful fallback to cached data

#### 3. State Management
```javascript
// Frontend state management pattern
const [sessions, setSessions] = useState([]);
const [loading, setLoading] = useState(false);
const [error, setError] = useState(null);

useEffect(() => {
  const fetchSessions = async () => {
    setLoading(true);
    try {
      const response = await apiService.getSessions();
      setSessions(response.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  fetchSessions();
  const interval = setInterval(fetchSessions, 30000);
  return () => clearInterval(interval);
}, []);
```

### Session Management Workflow

#### 1. Session Creation Flow
```
Client SDK → POST /api/v1/detection/sessions → Backend Controller
    ↓
Session Created ← Database Insert ← Service Layer ← Validation
    ↓
Session ID Returned ← JSON Response ← Serialization ← Session Object
    ↓
Client Stores Session ID for Event Tracking
```

#### 2. Event Ingestion Flow
```
Client SDK → POST /api/v1/detection/sessions/{id}/events → Backend Controller
    ↓
Event Stored ← Database Insert ← Service Layer ← Event Processing
    ↓
Event Count Updated ← Session Update ← Relationship Loading ← Event Data
    ↓
Real-time Dashboard Update ← WebSocket/SSE ← Event Notification
```

#### 3. Analysis Trigger Flow
```
Dashboard UI → POST /api/v1/detection/sessions/{id}/analyze → Backend Controller
    ↓
Analysis Started ← Background Task ← Bot Detection Engine ← Event Data
    ↓
Results Stored ← Database Insert ← Analysis Complete ← Detection Logic
    ↓
Dashboard Updated ← Real-time Notification ← Result Available
```

### Backend Service Layer Patterns

#### 1. Controller-Service Pattern
```python
# Controller handles HTTP concerns
@router.post("/sessions/{session_id}/analyze")
async def analyze_session(session_id: str, db: Session = Depends(get_db)):
    try:
        result = await detection_service.analyze_session(session_id, db)
        return {"success": True, "data": result}
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")
    except AnalysisError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Service handles business logic
class DetectionService:
    async def analyze_session(self, session_id: str, db: Session):
        session = await self.get_session(session_id, db)
        events = await self.get_session_events(session_id, db)
        return await self.bot_detection_engine.analyze(session, events)
```

#### 2. Async Database Operations
```python
# Async database operations with connection pooling
async def get_session_events(session_id: str, db: AsyncSession):
    query = select(BehaviorData).where(
        BehaviorData.session_id == session_id
    ).order_by(BehaviorData.timestamp)
    
    result = await db.execute(query)
    return result.scalars().all()
```

#### 3. Error Handling and Validation
```python
# Pydantic models for request/response validation
class EventCreate(BaseModel):
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]

class SessionResponse(BaseModel):
    id: str
    status: str
    event_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### Frontend-Backend Communication

#### 1. API Service Layer
```javascript
// Centralized API communication
class ApiService {
  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async getSessions() {
    try {
      const response = await this.client.get('/api/v1/dashboard/sessions');
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch sessions: ${error.message}`);
    }
  }

  async analyzeSession(sessionId) {
    try {
      const response = await this.client.post(
        `/api/v1/detection/sessions/${sessionId}/analyze`
      );
      return response.data;
    } catch (error) {
      throw new Error(`Analysis failed: ${error.message}`);
    }
  }
}
```

#### 2. Real-time Updates
```javascript
// WebSocket connection for real-time updates
class RealTimeService {
  constructor() {
    this.ws = null;
    this.callbacks = new Map();
  }

  connect() {
    this.ws = new WebSocket('ws://localhost:8000/ws');
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };
  }

  handleMessage(data) {
    switch (data.type) {
      case 'session_updated':
        this.callbacks.get('session_updated')?.(data.payload);
        break;
      case 'analysis_complete':
        this.callbacks.get('analysis_complete')?.(data.payload);
        break;
    }
  }

  on(event, callback) {
    this.callbacks.set(event, callback);
  }
}
```

### Data Synchronization Patterns

#### 1. Optimistic Updates
```javascript
// Optimistic UI updates for better UX
const updateSessionStatus = async (sessionId, newStatus) => {
  // Optimistically update UI
  setSessions(prev => prev.map(s => 
    s.id === sessionId ? { ...s, status: newStatus } : s
  ));

  try {
    // Make API call
    await apiService.updateSessionStatus(sessionId, newStatus);
  } catch (error) {
    // Revert on error
    setSessions(prev => prev.map(s => 
      s.id === sessionId ? { ...s, status: s.status } : s
    ));
    throw error;
  }
};
```

#### 2. Caching Strategy
```javascript
// React Query for intelligent caching
const { data: sessions, isLoading, error } = useQuery({
  queryKey: ['sessions'],
  queryFn: () => apiService.getSessions(),
  staleTime: 30000, // Data considered fresh for 30 seconds
  cacheTime: 300000, // Cache kept for 5 minutes
  refetchOnWindowFocus: true,
  refetchInterval: 30000, // Refetch every 30 seconds
});
```

#### 3. Error Boundaries
```javascript
// React error boundary for graceful error handling
class DashboardErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Dashboard error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-container">
          <h2>Something went wrong</h2>
          <button onClick={() => window.location.reload()}>
            Reload Dashboard
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### Performance Optimization Patterns

#### 1. Backend Optimization
```python
# Eager loading to prevent N+1 queries
async def get_sessions_with_events(db: AsyncSession):
    query = select(Session).options(
        selectinload(Session.behavior_data),
        selectinload(Session.detection_results)
    )
    result = await db.execute(query)
    return result.scalars().all()

# Connection pooling for database efficiency
DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/bot_detection"
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)
```

#### 2. Frontend Optimization
```javascript
// Virtual scrolling for large datasets
import { FixedSizeList as List } from 'react-window';

const SessionList = ({ sessions }) => (
  <List
    height={600}
    itemCount={sessions.length}
    itemSize={80}
    itemData={sessions}
  >
    {({ index, style, data }) => (
      <SessionItem
        session={data[index]}
        style={style}
      />
    )}
  </List>
);

// Memoization for expensive components
const SessionItem = React.memo(({ session, style }) => (
  <div style={style} className="session-item">
    <h3>{session.id}</h3>
    <p>Status: {session.status}</p>
    <p>Events: {session.event_count}</p>
  </div>
));
```

### Security Patterns

#### 1. CORS Configuration
```python
# Backend CORS setup
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 2. Input Validation
```python
# Backend input validation
from pydantic import BaseModel, validator

class EventData(BaseModel):
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    
    @validator('event_type')
    def validate_event_type(cls, v):
        allowed_types = ['click', 'scroll', 'keypress', 'mouse_move']
        if v not in allowed_types:
            raise ValueError(f'Event type must be one of {allowed_types}')
        return v
```

#### 3. Frontend Security
```javascript
// XSS prevention
const sanitizeInput = (input) => {
  return input.replace(/[<>]/g, '');
};

// CSRF protection
const apiService = {
  async makeRequest(url, options = {}) {
    const token = localStorage.getItem('csrf_token');
    return fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'X-CSRF-Token': token,
      },
    });
  },
};
```

---

## Integration Architecture

### Webhook Integration Flow

#### 1. Qualtrics Integration
```
Qualtrics Survey → Webhook → API Gateway → Integration Controller
                                    ↓
                            Qualtrics Service → Database
                                    ↓
                            Bot Detection Engine → Analysis
```

#### 2. Decipher Integration
```
Decipher Survey → Webhook → API Gateway → Integration Controller
                                    ↓
                            Decipher Service → Database
                                    ↓
                            Bot Detection Engine → Analysis
```

Client-side (in-survey) capture: behavior events (`POST /detection/sessions/{id}/events`), question metadata (`POST /text-analysis/questions`), and responses (`POST /text-analysis/responses`). For **grid/matrix questions**, the client registers the grid with `question_type: 'grid'` or `'matrix'` when shown, then sends one `POST /text-analysis/responses` per grid cell when the respondent completes the grid. See [decipher_simple_guide.md](decipher_simple_guide.md) and [decipher_guide.md](decipher_guide.md).

#### 3. Decipher XML Tracking Round Trip
```
Survey XML (Add tracking page, POST /tracking/decipher)
        │  decipher_tracking.py adds the tracker script, ${uuid} as respondent id,
        │  hidden results page with 21 QOS_ variables (optional privacy notice,
        │  optional early end on a clear bot signal)
        ▼
Tracked XML ──(download, or POST /tracking/decipher/upload)──▶ Decipher
        │  decipher_upload.py: new survey or replace survey.xml; Decipher
        │  validates; never overwrites a live survey; QOS_ added to saved layouts
        ▼
Respondent's browser runs the tracker (live_quality_tracker.js)
        │  POST /detection/sessions, /events, /text-analysis/questions and
        │  /responses, then /detection/sessions/{id}/composite-analyze
        ▼
API stores sessions, events, answers and results; composite analysis returns
`survey_variables` (quality_variables.py)
        │
        ▼
Tracker writes the QOS_ values into the hidden results page, so they are
saved in Decipher's own data and appear in its exports
        │
        ▼
Live Quality page (/quality) reads the same results under the survey's rules;
a Decipher export can be uploaded to /quality/merge to add LQ_ variables
```

The tracker sends to `TRACKER_API_BASE`, or, when that is not set, to the address the upload came in on. It must be https except on localhost. Signing with `TRACKING_TOKEN_SECRET` is optional; a successful upload of a signed tracked file marks the survey as requiring signed sessions. The tracker holds the last page at most 3 s for the final check, 2.5 s for the in-survey check and 1.5 s for answers. Survey settings Decipher refuses (no `compat`, `compat` below 143, or `compat` 151 and above without `delphi="1"`) are caught first: adding tracking warns, and the upload stops with HTTP 422 before anything is sent to Decipher.

### Integration Components

#### 1. Webhook Handlers
- **Signature Validation**: HMAC-SHA256 verification
- **Payload Processing**: JSON parsing and validation
- **Error Handling**: Graceful failure handling
- **Retry Logic**: Exponential backoff

#### 2. Service Layer
- **API Communication**: HTTP client with retries
- **Data Transformation**: Platform-specific data mapping
- **Caching**: Response caching for performance
- **Mock Mode**: Fallback for testing

#### 3. Event Processing
- **Event Collection**: Behavioral data gathering
- **Real-time Analysis**: Immediate bot detection
- **Result Storage**: Analysis result persistence
- **Notification**: Alert systems for suspicious activity

#### 4. Integration Management Interface
- **Webhook Testing**: Interactive webhook testing interface
- **Status Monitoring**: Real-time integration status
- **Setup Guides**: Step-by-step integration instructions
- **Error Reporting**: Comprehensive error handling and reporting

---

## Data Flow Diagrams

### 1. Session Creation Flow
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│   API       │───▶│ Controller  │───▶│  Database   │
│             │    │  Gateway    │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       │                   ▼                   ▼                   ▼
       │            ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
       └───────────▶│   Response  │◀───│   Service   │◀───│   Session   │
                    │             │    │             │    │   Created   │
                    └─────────────┘    └─────────────┘    └─────────────┘
```

### 2. Event Processing Flow
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│   API       │───▶│ Controller  │───▶│  Database   │
│  (Events)   │    │  Gateway    │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       │                   ▼                   ▼                   ▼
       │            ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
       └───────────▶│   Response  │◀───│   Service   │◀───│  Events     │
                    │             │    │             │    │  Stored     │
                    └─────────────┘    └─────────────┘    └─────────────┘
```

### 3. Bot Detection Analysis Flow
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│   API       │───▶│ Controller  │───▶│  Database   │
│ (Analysis)  │    │  Gateway    │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       │                   ▼                   ▼                   ▼
       │            ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
       └───────────▶│   Response  │◀───│ Detection   │◀───│  Analysis   │
                    │             │    │  Engine     │    │  Results    │
                    └─────────────┘    └─────────────┘    └─────────────┘
```

### 4. Dashboard Data Flow
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Frontend   │───▶│   API       │───▶│ Controller  │───▶│  Database   │
│  Dashboard  │    │  Gateway    │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       │                   ▼                   ▼                   ▼
       │            ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
       └───────────▶│   UI        │◀───│   Service   │◀───│  Aggregated │
                    │  Update     │    │             │    │    Data     │
                    └─────────────┘    └─────────────┘    └─────────────┘
```

### 5. Integration Management Flow
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Frontend   │───▶│   API       │───▶│ Controller  │───▶│  External   │
│ Integration │    │  Gateway    │    │             │    │   Service   │
│   Interface │    │             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       │                   ▼                   ▼                   ▼
       │            ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
       └───────────▶│   UI        │◀───│   Service   │◀───│ Integration │
                    │  Update     │    │             │    │   Status    │
                    └─────────────┘    └─────────────┘    └─────────────┘
```

---

## Security Architecture

### Security Layers

#### 1. API Security
- **Authentication**: JWT token-based authentication ⏳ **PLANNED**
- **Authorization**: Role-based access control ⏳ **PLANNED**
- **Rate Limiting**: Request throttling per IP, per server instance (new sessions 30/min, other writes 600/min, Fix with AI 20/hour) **IMPLEMENTED**
- **Input Validation**: Data sanitization ✅ **DEPLOYED** (Pydantic validation)
- **Settings changes**: `PUT /settings` and `POST /settings/check` need the `X-Admin-Token` header to match `ADMIN_TOKEN` (env only); without `ADMIN_TOKEN` settings are read-only

#### 2. Data Security
- **Encryption**: Data encryption at rest ✅ **DEPLOYED** (Cloud SQL encryption)
- **TLS**: Transport layer security ✅ **DEPLOYED** (HTTPS for all endpoints)
- **Database Security**: Connection encryption ✅ **DEPLOYED** (VPC Connector + private IP)
- **Backup Security**: Encrypted backups ✅ **DEPLOYED** (Cloud SQL automated backups)

#### 3. Integration Security
- **Webhook Signatures**: HMAC-SHA256 verification ⏳ **PLANNED**
- **API Keys**: Secure key management ✅ **DEPLOYED** (Secret Manager; keys saved on the Settings page are stored in `app_settings`, encrypted with a key derived from `SECRET_KEY`, and never returned to the browser)
- **Decipher API key**: Sent only as the `x-apikey` header from the server and removed from any error text Decipher echoes back
- **CORS**: Cross-origin resource sharing ✅ **DEPLOYED** (configured for all origins)
- **IP Whitelisting**: Allowed origins ⏳ **PLANNED**

### Security Best Practices
- **Principle of Least Privilege**: Minimal required permissions ✅ **DEPLOYED** (IAM roles)
- **Defense in Depth**: Multiple security layers ✅ **DEPLOYED** (VPC, Secret Manager, TLS)
- **Regular Audits**: Security assessments ⏳ **PLANNED**
- **Incident Response**: Security incident handling ⏳ **PLANNED**

---

## Performance & Scalability

### Performance Optimization

#### 1. Backend Performance
- **Async Operations**: Non-blocking I/O ✅ **DEPLOYED**
- **Database Optimization**: Query optimization and indexing ✅ **DEPLOYED** (composite indexes)
- **Caching**: Redis for frequently accessed data ⏳ **PLANNED**
- **Connection Pooling**: Database connection management ✅ **DEPLOYED**

#### 2. Frontend Performance
- **Code Splitting**: Lazy loading of components ⏳ **PARTIAL** (basic implementation)
- **Bundle Optimization**: Tree shaking and minification ✅ **DEPLOYED** (Vite build)
- **Caching**: Browser caching via Cache-Control headers on the bucket (`index.html` no-cache, hashed assets cached for a year)
- **Image Optimization**: Compressed and optimized images ✅ **DEPLOYED**

#### 3. API Performance
- **Response Time**: Sub-100ms for most endpoints ✅ **ACHIEVED** (~100ms average)
- **Throughput**: 1000+ requests per second ⏳ **NOT TESTED** (load testing planned)
- **Concurrency**: Async request handling ✅ **DEPLOYED**
- **Monitoring**: Real-time performance metrics ✅ **DEPLOYED** (Prometheus metrics endpoint)

### Scalability Strategy

#### 1. Horizontal Scaling
- **Load Balancing**: Multiple server instances ✅ **DEPLOYED** (Cloud Run auto-scaling)
- **Database Sharding**: Data distribution ⏳ **PLANNED**
- **Microservices**: Service decomposition ⏳ **PARTIAL** (monolithic with modular design)
- **Containerization**: Docker-based deployment ✅ **DEPLOYED** (Cloud Run containers)

#### 2. Vertical Scaling
- **Resource Optimization**: CPU and memory optimization ✅ **DEPLOYED** (1 vCPU, 1GB RAM)
- **Database Tuning**: Query and index optimization ✅ **DEPLOYED** (composite indexes)
- **Caching Strategy**: Multi-level caching ⏳ **PARTIAL** (in-memory caching, Redis planned)
- **CDN Integration**: Not in front of the current dashboard bucket (a Cloud CDN backend exists only for the older `bot-detection-frontend-20250929` bucket)

---

## Deployment Architecture

### Development Environment ✅ **AVAILABLE**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```
**Status**: ✅ **DEPLOYED** via Docker Compose for local development

### Production Environment (Google Cloud Platform) ✅ **DEPLOYED**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Cloud Storage   │    │   Cloud Run     │    │   Cloud SQL     │
│ bucket (Front-  │◄──►│ bot-backend     │◄──►│ bot-db,         │
│ end, hash URLs) │    │ (1 CPU, 1 GiB)  │    │ bot-db-v2       │
│   ✅ DEPLOYED   │    │   ✅ DEPLOYED   │    │   ✅ DEPLOYED   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Secret        │    │   VPC           │    │   Artifact      │
│   Manager       │◄──►│   Connector     │◄──►│   Registry      │
│   ✅ DEPLOYED   │    │   ✅ DEPLOYED   │    │   ✅ DEPLOYED   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Production URLs**:
- Backend: `https://bot-backend-119522247395.northamerica-northeast2.run.app`
- Frontend: `https://storage.googleapis.com/bot-detection-frontend-20251208/index.html`
- Backend (alternate URL): `https://bot-backend-i56xopdg6q-pd.a.run.app`
- API Docs: `https://bot-backend-119522247395.northamerica-northeast2.run.app/docs`
- Project `survey-bot-detection`, region `northamerica-northeast2`

**Infrastructure Details**:
- **Cloud Run**: Service `bot-backend`, auto-scaling (min 1, max 10 instances), 1 CPU, 1 GiB memory (needed for pandas in the Live Quality merge)
- **Cloud SQL**: PostgreSQL instances `bot-db` and `bot-db-v2` attached to the service, VPC private IP, automated backups
- **VPC Connector**: `serverless-connector` with `private-ranges-only` egress
- **Secret Manager**: DATABASE_URL, SECRET_KEY, OPENAI_API_KEY, ADMIN_TOKEN
- **Artifact Registry**: Docker images for Cloud Run deployment (`northamerica-northeast2-docker.pkg.dev/survey-bot-detection/backend/bot-backend:<git-sha>`)
- **Frontend bucket**: `gs://bot-detection-frontend-20251208`, built with `VITE_ROUTER_MODE=hash`; `index.html` is served `no-cache`, `assets/**` as `public, max-age=31536000, immutable`. Older files such as `tracking-client.js` stay in the bucket because live surveys may use them.
- **Database tables**: created at startup by `create_all`; no migration step in deployment
- **Deploying**: update only what changes (`--update-env-vars`, `--update-secrets`). `deploy-backend.ps1` uses `--set-env-vars`/`--set-secrets` and attaches only `bot-db`, so running it as is drops settings and the `bot-db-v2` connection.

### Containerization
```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/bot_detection
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=bot_detection
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

---

## Monitoring & Observability

### Monitoring Stack

#### 1. Application Monitoring
- **Prometheus**: Metrics collection ⏳ **PARTIAL** (metrics endpoint deployed, dashboard planned)
- **Grafana**: Metrics visualization ⏳ **PLANNED**
- **AlertManager**: Alert management ⏳ **PLANNED**
- **Custom Metrics**: Business-specific metrics ✅ **DEPLOYED** (via `/metrics` endpoint)

#### 2. Logging
- **Structured Logging**: JSON-formatted logs ✅ **DEPLOYED** (Python logging)
- **Log Aggregation**: Centralized log collection ✅ **DEPLOYED** (Cloud Run logs)
- **Log Analysis**: Search and analysis tools ✅ **DEPLOYED** (gcloud logs)
- **Log Retention**: Configurable retention policies ✅ **DEPLOYED** (Cloud Logging)

#### 3. Health Checks
- **Liveness Probes**: Application health ✅ **OPERATIONAL** (`/health` endpoint)
- **Readiness Probes**: Service readiness ✅ **VERIFIED** (Cloud Run health checks)
- **Database Health**: Connection status ✅ **CONNECTED** (Cloud SQL via VPC)
- **Metrics Endpoint**: Prometheus metrics ✅ **ACTIVE** (`/metrics` endpoint)
- **Integration Health**: External service status ✅ **DEPLOYED** (`/text-analysis/health` for OpenAI)

### Key Metrics

#### 1. Performance Metrics
- **Response Time**: API response times
- **Throughput**: Requests per second
- **Error Rate**: Error percentage
- **Availability**: Uptime percentage

#### 2. Business Metrics
- **Session Count**: Active sessions
- **Event Volume**: Events processed
- **Bot Detection Rate**: Bot detection percentage
- **Integration Success**: Webhook success rate

#### 3. Infrastructure Metrics
- **CPU Usage**: Server CPU utilization
- **Memory Usage**: Memory consumption
- **Disk I/O**: Storage performance
- **Network I/O**: Network performance

### Alerting Strategy
- **Critical Alerts**: Service downtime
- **Warning Alerts**: Performance degradation
- **Info Alerts**: Business metrics
- **Escalation**: Alert escalation procedures

---

## Future Architecture Considerations

### Planned Enhancements

#### 1. Machine Learning Integration ⏳ **PLANNED**
- **ML Pipeline**: Automated model training ⏳ **PLANNED**
- **Feature Engineering**: Advanced feature extraction ⏳ **PLANNED**
- **Model Serving**: Real-time ML inference ⏳ **PLANNED**
- **A/B Testing**: Model comparison framework ⏳ **PLANNED**

#### 2. Real-time Processing ⏳ **PARTIAL**
- **WebSocket Support**: Real-time communication ⏳ **PLANNED**
- **Event Streaming**: Kafka integration ⏳ **PLANNED**
- **Stream Processing**: Real-time analytics ⏳ **PLANNED**
- **Live Dashboard**: Real-time updates ⏳ **PARTIAL** (polling implemented, WebSocket planned)

#### 3. Microservices Evolution ⏳ **PARTIAL**
- **Service Decomposition**: Further service splitting ⏳ **PLANNED**
- **API Gateway**: Advanced routing and filtering ⏳ **PLANNED**
- **Service Mesh**: Inter-service communication ⏳ **PLANNED**
- **Event Sourcing**: Event-driven architecture ⏳ **PLANNED**

#### 4. Cloud Native Features ⏳ **PARTIAL**
- **Kubernetes**: Container orchestration ⏳ **PLANNED** (currently using Cloud Run)
- **Serverless**: Function-as-a-Service ✅ **DEPLOYED** (Cloud Run is serverless)
- **Auto-scaling**: Automatic resource scaling ✅ **DEPLOYED** (Cloud Run auto-scaling 1-10 instances)
- **Multi-region**: Geographic distribution ⏳ **PLANNED**

---

## Conclusion

The Bot Detection System architecture is designed for scalability, maintainability, and performance. The modular design allows for easy extension and modification while maintaining high availability and security standards.

### Key Architectural Benefits
- **Scalability**: Horizontal and vertical scaling capabilities
- **Maintainability**: Clear separation of concerns
- **Performance**: Optimized for high-throughput operations
- **Security**: Multi-layered security approach
- **Observability**: Comprehensive monitoring and logging
- **Flexibility**: Easy integration with external systems
- **User Experience**: Comprehensive frontend with real-time updates

### Technology Choices Justification
- **FastAPI**: High performance, async support, automatic documentation
- **React**: Component-based UI, large ecosystem, developer productivity
- **PostgreSQL**: ACID compliance, JSON support, scalability
- **Redis**: High-performance caching, session storage
- **Docker**: Containerization, deployment consistency, scalability

### Recent Achievements (January 2026)
- **Frontend Integration**: Complete React dashboard with comprehensive features ✅ **DEPLOYED**
- **Integration Management**: Webhook testing and status monitoring interface ✅ **DEPLOYED**
- **User Experience**: Toast notifications, responsive design, and error handling ✅ **DEPLOYED**
- **Component Architecture**: Modular, maintainable UI components ✅ **DEPLOYED**
- **API Playground**: Interactive API testing interface ✅ **DEPLOYED**
- **Quick Start Guide**: Comprehensive onboarding documentation ✅ **DEPLOYED**
- **Production Deployment**: Full GCP deployment with Cloud Run and Cloud Storage ✅ **DEPLOYED**
- **System Health**: Complete health verification with all endpoints operational ✅ **DEPLOYED**
- **Metrics Monitoring**: Prometheus metrics endpoint deployed and active ✅ **DEPLOYED**
- **Database Connectivity**: Verified PostgreSQL connection and data persistence ✅ **DEPLOYED**
- **OpenAI Integration**: GPT-4o-mini service fully operational with 100% test accuracy ✅ **DEPLOYED**
- **Text Quality Analysis**: Production-ready with comprehensive quality scoring and flagging ✅ **DEPLOYED**
- **Health Monitoring**: Real-time OpenAI service status tracking with `/api/v1/text-analysis/health` ✅ **DEPLOYED**
- **Test Infrastructure**: Enhanced testing with health checks and 100% classification accuracy ✅ **DEPLOYED**
- **Hierarchical Text Analysis**: V2 endpoints for text analysis at survey/platform/respondent/session levels ✅ **DEPLOYED**
- **Fraud Detection System**: Complete fraud detection service with IP tracking, device fingerprinting, duplicate detection, geolocation, and velocity checking ✅ **COMPLETED**
- **Fraud Detection Hierarchical Endpoints**: Survey/platform/respondent/session-level fraud summaries with efficient database queries ✅ **COMPLETED**
- **Composite Bot Detection**: Updated scoring algorithm (40% behavioral, 30% text quality, 30% fraud detection) ✅ **DEPLOYED**
- **Fraud Detection Frontend**: Hierarchical fraud widgets integrated into all detail views ✅ **DEPLOYED**
- **VPC Networking**: VPC Connector with `private-ranges-only` egress for Cloud SQL and external APIs ✅ **DEPLOYED**
- **Secret Sanitization**: CRLF/whitespace stripping for OpenAI API keys to prevent header errors ✅ **DEPLOYED**
- **Production URLs**: Backend: `https://bot-backend-i56xopdg6q-pd.a.run.app`, Frontend: `https://storage.googleapis.com/bot-detection-frontend-20251208/index.html` ✅ **DEPLOYED**

### Deployment Summary
This architecture is **fully operational in production** on Google Cloud Platform with:
- ✅ **Backend**: Cloud Run with auto-scaling (1-10 instances), 1 CPU, 1 GiB
- ✅ **Frontend**: Cloud Storage bucket, hash routing
- ✅ **Database**: Cloud SQL PostgreSQL (`bot-db`, `bot-db-v2`) with VPC private IP
- ✅ **Networking**: VPC Connector with optimized egress routing
- ✅ **Secrets**: Secret Manager with sanitized credentials (DATABASE_URL, SECRET_KEY, OPENAI_API_KEY, ADMIN_TOKEN)
- ✅ **Monitoring**: Health checks, metrics endpoint, and Cloud Logging
- ✅ **Testing**: 100% passing rate on all production endpoints

This architecture provides a solid foundation for the current requirements while allowing for future growth and evolution of the system.

---

### Recent Achievements - Fraud Detection (January 2026)
- **Fraud Detection Service**: Complete implementation with IP tracking, device fingerprinting, duplicate detection, geolocation, and velocity checking ✅ **COMPLETED**
- **Database Migration**: `fraud_indicators` table with hierarchical fields and composite indexes ✅ **COMPLETED**
- **Composite Scoring**: Updated to 40% behavioral, 30% text quality, 30% fraud detection ✅ **COMPLETED**
- **Hierarchical Fraud Endpoints**: Survey/platform/respondent/session-level fraud summaries ✅ **COMPLETED**
- **Frontend Integration**: Hierarchical fraud widgets integrated into all detail views ✅ **COMPLETED**
- **Unit Tests**: Comprehensive test suite with 100% passing rate ✅ **COMPLETED**
- **API Tests**: Integration tests for all fraud detection endpoints ✅ **COMPLETED**
- ⏳ **Production Deployment**: All fraud detection features ready for deployment

*Last updated: November 26, 2026*