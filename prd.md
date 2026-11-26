# Product Requirements Document (PRD)

## 1. Purpose ✅
Enhance the Bot-vs-Human Detection API + Dashboard to include real-time fraud signals, detailed performance metrics, and full PostgreSQL integration under FastAPI.

## 2. Scope ✅
- **Behavioral Data Capture**: Keystrokes, mouse movement, focus/blur, scroll, device fingerprint, network events.
- **Text Quality Analysis**: OpenAI GPT-4o-mini powered analysis of open-ended survey responses ✅
- **Hierarchical Data Structure**: Survey → Platform → Respondent → Session structure for aggregated data access ✅
- **API**:
  - `POST /api/v1/detection/sessions` – start session ✅
  - `POST /api/v1/detection/sessions/{sessionId}/events` – ingest batched events, return classification + `processing_time_ms` and `event_count` ✅
  - `GET /api/v1/detection/sessions/{sessionId}/status` – retrieve raw session metadata + latest detection result ✅
  - `POST /api/v1/detection/sessions/{sessionId}/analyze` – perform bot detection analysis ✅
  - `POST /api/v1/detection/sessions/{sessionId}/composite-analyze` – unified analysis with text quality ✅
  - `GET /api/v1/detection/sessions/{sessionId}/ready-for-analysis` – check if session is ready for analysis ✅
  - `POST /api/v1/text-analysis/questions` – capture survey questions ✅
  - `POST /api/v1/text-analysis/responses` – analyze responses with GPT-4o-mini ✅
  - `GET /api/v1/text-analysis/sessions/{sessionId}/summary` – text quality summary ✅
  - `GET /api/v1/surveys` – list all surveys with aggregated stats ✅
  - `GET /api/v1/surveys/{survey_id}` – survey details with aggregated metrics ✅
  - `GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents` – list respondents ✅
  - `GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}` – respondent details ✅
  - `GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions` – list respondent sessions ✅
  - `GET /api/v1/surveys/{survey_id}/text-analysis/summary` – text analysis summary at survey level (hierarchical V2) ✅
  - `GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/text-analysis/summary` – text analysis summary at platform level (hierarchical V2) ✅
  - `GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/text-analysis/summary` – text analysis summary at respondent level (hierarchical V2) ✅
  - `GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}/text-analysis` – text analysis at session level (hierarchical V2) ✅
  - `GET /api/v1/text-analysis/health` – OpenAI service health check ✅
  - `GET /api/v1/surveys/{survey_id}/grid-analysis/summary` – grid analysis summary at survey level ✅
  - `GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/grid-analysis/summary` – grid analysis summary at platform level ✅
  - `GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/grid-analysis/summary` – grid analysis summary at respondent level ✅
  - `GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}/grid-analysis` – grid analysis at session level ✅
  - `GET /api/v1/surveys/{survey_id}/timing-analysis/summary` – timing analysis summary at survey level ✅
  - `GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/timing-analysis/summary` – timing analysis summary at platform level ✅
  - `GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/timing-analysis/summary` – timing analysis summary at respondent level ✅
  - `GET /api/v1/surveys/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}/timing-analysis` – timing analysis at session level ✅
  - `POST /api/v1/tracking/decipher` – add tracking to a Decipher survey XML (`?format=xml` returns the file) ✅
  - `POST /api/v1/tracking/decipher/upload` – create a Decipher survey or replace `survey.xml` of an existing one (never overwrites a live survey) ✅
  - `GET /api/v1/tracking/decipher/options` – tracking options and whether Decipher upload is configured ✅
  - `GET /api/v1/quality/surveys` – every survey, tracked ones first ✅
  - `GET /api/v1/quality/results?survey_id=` – Live Quality dashboard data under the survey's rules ✅
  - `GET /api/v1/quality/export?survey_id=` – CSV, one row per respondent ✅
  - `GET|PUT|DELETE /api/v1/quality/rules?survey_id=` – per-survey quality rules ✅
  - `POST /api/v1/quality/merge?survey_id=` – return an uploaded .sav/.csv/.xlsx data file with `LQ_` variables added ✅
  - `GET /api/v1/settings`, `POST /api/v1/settings/check`, `PUT /api/v1/settings` – read and save runtime settings (check and save need `X-Admin-Token`) ✅
- **Classification Engine**: Rule-based checks with thresholds, returns `is_bot`, `confidence_score`, `risk_level`, plus performance metadata ✅
- **Text Quality Engine**: GPT-4o-mini powered analysis for gibberish, copy-paste, relevance, generic answers, and quality scoring ✅
- **Data Persistence**: PostgreSQL tables for sessions, behavior_data, detection_results, survey_questions, survey_responses including extra columns for `processing_time_ms` and `event_count` ✅
- **Hierarchical Database Schema**: Composite indexes on `survey_id`, `platform_id`, `respondent_id` for efficient hierarchical queries ✅
- **Dashboard Metrics**:
  - Latency analysis (ms) ✅
  - Event volume per session ✅
  - Bot/human rates over time ✅
  - Bot rate = sessions judged bots / sessions checked, counting distinct sessions, the same on every page ✅
  - Session overview and trends ✅
- **Architecture Documentation**: Comprehensive system design and interaction patterns ✅
- **API Documentation**: Complete API reference with examples ✅
- **Frontend Dashboard**: Complete React-based monitoring interface with comprehensive features ✅
- **Integration Management**: Webhook URLs, real configuration status, and setup guides ✅

## 3. Key Features ✅
1. **Session Management**: Unique `session_id` via UUID ✅
2. **Real-Time Checks**:
   - Keystroke rhythm (median delta) ✅
   - Mouse speed & presence ✅
   - Focus/blur & scroll detection ✅
   - Device fingerprint & network anomalies ✅
3. **Text Quality Analysis**:
   - GPT-4o-mini powered gibberish detection ✅
   - Copy-paste content detection ✅
   - Topic relevance checking ✅
   - Generic answer detection ✅
   - Overall quality scoring (0-100) ✅
4. **Grid/Matrix Question Analysis**:
   - Straight-lining detection (identical responses across rows) ✅
   - Pattern detection (diagonal, reverse diagonal, zigzag) ✅
   - Response variance calculation ✅
   - Satisficing behavior scoring ✅
5. **Enhanced Timing Analysis**:
   - Speeder detection (< threshold) ✅
   - Flatliner detection (> threshold) ✅
   - Adaptive timing thresholds ✅
   - Timing anomaly detection (z-score based) ✅
4. **Performance Metrics**: Capture and store per-request processing time and event counts ✅
5. **Robust API**: 400/404 error handling, debug logging of raw payloads ✅
6. **Dashboard**: Timeline charts + summary tables showing classification outcomes and system KPIs ✅
7. **Text Quality Dashboard**: Real-time text analysis results with flagged responses, filtering, pagination, and CSV export ✅
8. **Client SDKs**: Python and JavaScript client libraries for easy integration ✅
9. **Enhanced JavaScript SDK**: Automatic question/answer capture with text quality tracking ✅
10. **Performance Testing**: Locust load testing and async performance validation ✅
11. **Error Handling**: Comprehensive error messages and validation ✅
12. **Integration Support**: Qualtrics and Decipher webhook handlers with mock mode ✅
13. **Architecture Design**: Well-documented system architecture with clear interaction patterns ✅
14. **Frontend Integration**: Complete React dashboard with real-time updates and comprehensive features ✅
15. **Integration Management**: Webhook URLs and real configuration status (simulated webhook test removed November 2026) ✅
16. **API Playground**: Interactive API testing interface ✅
17. **Quick Start Guide**: Step-by-step integration instructions ✅
18. **User Experience**: Toast notifications, responsive design, and error handling ✅
19. **Composite Scoring**: Unified bot detection combining behavioral + text quality analysis ✅
20. **Report Builder Respondent Detail**: Click respondent ID in detailed report to open popup with full details, responses of interest, and decision reasons; CSV export includes all analyses per respondent (text responses of interest, fraud/grid/timing explanations) ✅
21. **Decipher XML Tracking (Add tracking page)**: Upload a complete Decipher survey XML and get it back with tracking added: tracker script, Decipher's `${uuid}` as respondent id, and a hidden page with 21 `QOS_` variables. Optional privacy notice (on by default). Optional early end on a clear bot signal (off by default, decisive signals only, only on a page break every respondent reaches). Removing the tracking gives back the original file byte for byte. Survey-body fragments are refused ✅
22. **Upload to Decipher**: Create a new Decipher survey or replace the XML of an existing one from the Add tracking page. Decipher validates the file and a live survey is never overwritten. Settings Decipher would refuse (`compat` missing, below 143, or 151+ without `delphi="1"`) are caught first and nothing is sent. Decipher's own error messages are shown in full. QOS_ variables are added to saved data layouts ✅
23. **Live Quality (per survey)**: Totals, open-end, fraud, grid and timing summaries, 9 flags (Bot-like behaviour, Low-quality open ends, Pasted answers, Straight-lining, Speeder, Flatliner, Duplicate, High fraud risk, Data-centre IP), quality distribution, trend, and one row per session ✅
24. **Per-survey Quality Rules**: Bot threshold, bot signals, speeder limits, straight-lining rows, open-end reasons, pasted answers, fraud threshold, duplicates and data-centre IPs can be set per survey (defaults: bot threshold 0.7, fraud threshold 0.7). Rules apply to the dashboard, CSV and LQ_ variables, and never change stored results or the QOS_ values in Decipher ✅
25. **Quality CSV and LQ_ Merge**: Download a CSV with one row per respondent, or upload the survey's data file (.sav, .csv, .xlsx, up to 50 MB) and get the same file back with `LQ_` variables. Records match on QOS_SESSION, then QOS_RESPONDENT, then Decipher's `uuid`. SPSS labels are kept and LQ_ variables are labelled ✅
26. **Settings that Save**: Decipher, Qualtrics and OpenAI keys, OpenAI model, tracker address, tracking token secret and detection threshold can be saved from the Settings page. A saved value overrides the environment and applies within 30 s on every instance. Secrets are encrypted at rest and never shown. Saving needs `ADMIN_TOKEN`; without it the page is read-only ✅
27. **Dashboard Layout**: Grouped left sidebar (Monitor, Analyse, Set up, Developers) with service status; Overview (last 7 days, surveys with bot rate, starts and bots per day, latest bots); Sessions list with filters kept in the URL and pagination; Session details with verdict and decisive signals first. Works on phones. Production addresses use a hash (`index.html#/quality`) so every page loads from the storage bucket ✅
28. **Quant OS Compatibility**: Self-contained, with no dependency on Quant OS, but uses the same `QOS_` labels, recognises Quant OS tracking (re-tracks instead of tracking twice), and uses the same device-fingerprint text ✅
29. **No Placeholder Content**: The dashboard shows only real data; made-up trends, simulated webhook tests, fake integration logs, a fixed "Production Ready" badge, a mocked session comparison and a non-working dark-mode toggle were removed ✅

## 4. Success Metrics ✅
- <200 ms median `processing_time_ms` per request ✅ (Achieved: ~100ms average)
- ≥95% accuracy in bot/human labeling in lab tests ✅ (Achieved: 100% test accuracy)
- <1% API 4xx/5xx error rate ✅ (Comprehensive error handling)
- Dashboard refresh <1 s ✅ (Fast API responses)
- Sub-100ms response times for most endpoints ✅ (Achieved)
- Comprehensive documentation coverage ✅ (Architecture, API, and guides)
- Frontend integration with real-time updates ✅ (React dashboard implemented)
- Integration management with webhook testing ✅ (Complete interface implemented)
- OpenAI text quality analysis operational ✅ (100% test accuracy achieved)
- Production OpenAI service health monitoring ✅ (Real-time status tracking)
- Production deployment on GCP ✅ (Cloud Run + Cloud SQL fully operational)
- Cloud SQL connectivity ✅ (VPC egress optimization implemented)
- Secret sanitization ✅ (CRLF/whitespace stripping for API keys)
- Production test validation ✅ (100% passing rate on all endpoints)

## 5. Out of Scope
- Machine-learning training loop
- Multi-tenant billing UI

## 6. Production Version Considerations
- **Service Tiers**: Free, Standard, Enterprise plans with per-session limits and support SLAs
- **SLAs & Uptime**: 99.9% availability, defined error budgets, support response times
- **Developer Portal & API Gateway**: API key management, usage dashboards, sandbox endpoints, rate limiting
- **Multi-Tenant & Isolation**: Tenant-specific configs, data isolation, custom branding options
- **Billing & Invoicing**: Automated metering (per-session/per-event), Stripe/PayPal integration, invoice generation, payment retries
- **Support & Onboarding**: Tiered support channels, documentation, onboarding tutorials
- **Compliance & Security**: GDPR/CCPA, SOC2 readiness, encryption at rest/in transit, audit logging

## 7. Technical Implementation Status ✅
- **Backend**: FastAPI with async SQLAlchemy and PostgreSQL ✅
- **Frontend**: React with Tailwind CSS and responsive design ✅
- **Database**: PostgreSQL with optimized schemas and relationships ✅
- **Testing**: Unit tests, integration tests, and performance testing ✅
- **Documentation**: Comprehensive API docs, architecture docs, and setup guides ✅
- **Deployment**: Docker Compose for local development + Google Cloud Run for production ✅
- **Production Infrastructure**: Cloud Run + Cloud SQL + VPC Connector + Secret Manager ✅
- **Networking**: VPC egress optimization for Cloud SQL and external API access ✅
- **Secrets Management**: Sanitized OpenAI API keys with CRLF/whitespace stripping ✅
- **Monitoring**: Health checks and structured logging ✅
- **Integrations**: Survey platform webhook handlers ✅
- **Client SDKs**: Python and JavaScript libraries ✅
- **Frontend Integration**: Complete React dashboard with comprehensive features ✅
- **User Experience**: Toast notifications, responsive design, and error handling ✅

## 8. API Endpoints Implemented ✅
- **Detection API**: Session creation, event ingestion, analysis
- **Dashboard API**: Overview statistics, session lists, detailed views
- **Integration API**: Webhook handlers for survey platforms
- **Health API**: System status and monitoring endpoints

## 9. Performance Achievements ✅
- **Response Times**: Sub-100ms for most endpoints
- **Database**: Async operations with connection pooling
- **Error Handling**: Comprehensive validation and user-friendly messages
- **Scalability**: Modular architecture ready for horizontal scaling
- **Testing**: Automated performance validation with Locust
- **Documentation**: Complete system architecture and API reference
- **Frontend**: Fast, responsive React dashboard with real-time updates
- **Integration**: Seamless survey platform integration with webhook testing

## 10. Architecture & Design ✅
- **System Architecture**: Comprehensive documentation of system design
- **API-Backend-Frontend Interaction**: Detailed interaction patterns
- **Data Flow**: Clear data flow diagrams and processing pipelines
- **Security Patterns**: Multi-layered security approach
- **Performance Optimization**: Database and frontend optimizations
- **Deployment Architecture**: Containerization and scaling strategies

## 11. Integration Capabilities ✅
- **Qualtrics Integration**: Webhook handlers with graceful error handling
- **Decipher Integration**: Survey platform support with mock mode; tracking added to survey XML and uploaded to Decipher with pre-checks
- **Error Handling**: Comprehensive error management for external services
- **Testing Support**: Easy integration testing and validation
- **Status Monitoring**: Integration status read from the backend configuration

## 12. Client SDKs ✅
- **Python SDK**: Easy integration for Python applications
- **JavaScript SDK**: Browser-based tracking client
- **Documentation**: Usage examples and best practices
- **Error Handling**: Comprehensive error management

## 13. Documentation Coverage ✅
- **Architecture Documentation**: System design and interaction patterns
- **API Reference**: Complete endpoint documentation with examples
- **Setup Guides**: Step-by-step installation and configuration
- **Integration Guides**: Survey platform integration instructions
- **Performance Testing**: Load testing and optimization guides
- **Troubleshooting**: Common issues and solutions

## 14. Frontend Implementation ✅
- **React Dashboard**: Complete monitoring interface with real-time updates
- **Integration Management**: Webhook URLs, setup guides and real configuration status
- **Live Quality and Add tracking**: Per-survey quality dashboard, rules, CSV and LQ_ merge; Decipher XML tracking and upload
- **API Playground**: Interactive API testing interface
- **Quick Start Guide**: Step-by-step integration instructions
- **Settings Interface**: Saves selected settings behind `ADMIN_TOKEN`; read-only without it
- **Toast Notifications**: User feedback and alerts
- **Responsive Design**: Mobile-friendly interface with Tailwind CSS
- **Error Handling**: User-friendly error messages and fallback states
- **Component Architecture**: Modular, maintainable UI components

## 15. Recent Achievements ✅
- **Frontend Integration Fixes**: Resolved React component import issues
- **Toast Notifications**: Implemented user feedback system
- **Icon Library Integration**: Fixed Lucide React icon imports
- **Component Architecture**: Modular, maintainable UI components
- **Integration Management**: Complete webhook testing and monitoring
- **API Playground**: Interactive API testing interface
- **Quick Start Guide**: Comprehensive onboarding documentation
- **Error Boundaries**: Graceful error handling and fallback states
- **Text Analysis Dashboard Integration**: Complete backend and frontend implementation with filtering and pagination
- **Enhanced Report Service**: Text quality metrics integrated into all report generation methods
- **Comprehensive Test Suite**: 14 passing tests for all new functionality
- **Production Deployment**: All new features deployed and operational on GCP
- **Cloud Run VPC Egress Fix**: Resolved Cloud SQL connection timeouts by configuring `--vpc-egress=private-ranges-only` for split routing (January 2026)
- **OpenAI API Key Sanitization**: Fixed `Illegal header value` errors by stripping CRLF/whitespace from secrets (January 2026)
- **Production Test Suite**: 100% passing rate on all text analysis tests in production environment (January 2026)
- **Documentation Refresh**: Updated Decipher integration guides and API V2 documentation to reflect current endpoints (January 2026)
- **Hierarchical API V2**: Complete implementation of Survey → Platform → Respondent → Session structure with text analysis at all levels (January 2026)
- **Database Migration**: Successfully deployed `platform_id` column with composite indexes for hierarchical queries (January 2026)
- **Stage 3 Deployment**: Fraud & Duplicate Detection fully deployed and tested in production (February 2026)
- **Stage 2 Deployment**: Grid & Timing Analysis fully deployed and tested in production (February 2026)
- **Production Testing**: Comprehensive real example testing completed with all endpoints verified operational (February 2026)
- **Frontend Deployment**: Frontend successfully deployed and verified pulling data from Cloud SQL (February 2026)
- **Data Flow Verification**: Complete end-to-end verification of Cloud SQL → Backend API → Frontend Dashboard (February 2026)
- **Grid & Timing Analysis**: Complete implementation with 8 new hierarchical endpoints and 3 frontend widgets (February 2026)
- **Test Coverage**: 40 comprehensive tests covering grid and timing analysis (100% passing rate) (February 2026)
- **Dashboard Redeploy (February 2026)**: Frontend redeployed to GCS with API Playground fraud/grid/timing endpoint templates and Report Builder fraud, grid, and timing in summary blocks and detailed table/CSV; respondent detail popup (click respondent ID) and full CSV per respondent (text responses of interest, decision reasons)
- **Live Quality and Decipher Tracking (November 2026)**: Per-survey Live Quality with rules, CSV and LQ_ merge; Decipher XML tracking and upload with pre-checks; Settings that save behind ADMIN_TOKEN; redesigned dashboard with consistent bot rate; 275 backend tests passing

## 16. Production Deployment Status ✅
- **Backend Service**: Deployed on Google Cloud Run at `https://bot-backend-119522247395.northamerica-northeast2.run.app`
- **Frontend Dashboard**: Deployed as a static site in Cloud Storage at `https://storage.googleapis.com/bot-detection-frontend-20251208/index.html` (pages use hash addresses, e.g. `index.html#/quality`)
- **Database**: Cloud SQL PostgreSQL with hierarchical schema and composite indexes
- **Networking**: VPC Connector with optimized egress routing for Cloud SQL and external APIs
- **Secrets**: Secret Manager integration for DATABASE_URL, SECRET_KEY, OPENAI_API_KEY and ADMIN_TOKEN
- **OpenAI Integration**: Fully operational with GPT-4o-mini for text quality analysis
- **Health Monitoring**: Real-time health checks and metrics endpoints
- **Deployment Automation**: PowerShell scripts for backend and frontend deployment. The top-level `deploy-backend.ps1` replaces all env vars and secrets and connects only `bot-db`; current deploys use `gcloud run deploy` with `--update-env-vars`/`--update-secrets`
- **Testing**: Production test suite with 100% passing rate
- **Documentation**: Complete integration guides for Decipher and other survey platforms
- **Stage 3 Deployment**: Fraud & Duplicate Detection fully operational with comprehensive testing completed (February 2026)
- **Frontend Deployment**: Frontend deployed to Cloud Storage with all components verified operational (February 2026)
- **Dashboard Update (February 2026)**: API Playground includes fraud, grid, and timing templates; Report Builder includes Fraud & Duplicate, Grid Analysis, and Timing Analysis in summary and detailed reports/CSV; clickable respondent ID opens full-detail popup; CSV includes every analysis per respondent (text responses of interest, fraud/grid/timing explanations)
- **Cloud SQL Data Flow**: All frontend endpoints verified pulling data correctly from Cloud SQL database (February 2026)
- **November 2026 Release**: Live Quality, Decipher XML tracking and upload, saving Settings and the redesigned dashboard deployed 2026-11-26 as Cloud Run revision `bot-backend-00069-28j` (1 GiB memory; rollback target `bot-backend-00068-2rf`) and to the frontend bucket. New tables `tracked_surveys`, `survey_quality_rules`, `app_settings` are created at startup. Upload to Decipher turns on once the Decipher API key is entered on the deployed Settings page

## 17. Next Phase Requirements
- **Authentication & Security**: JWT tokens, API keys, rate limiting
- **Advanced Scaling**: Kubernetes migration, auto-scaling policies, load balancing
- **CI/CD Pipeline**: Automated testing and deployment with Cloud Build triggers
- **Business Features**: Billing system, multi-tenancy, analytics
- **Machine Learning**: ML-based detection algorithms
- **Real-time Features**: WebSocket support, live updates
- **Advanced Monitoring**: Prometheus/Grafana integration, alerting, distributed tracing