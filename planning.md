# Technical Planning & Stack for Production

## 1. Backend Infrastructure ✅
- **Production PostgreSQL** on AWS RDS/Azure with read replicas & backups
- **Kubernetes/ECS orchestration** with autoscaling
- **API Gateway** (e.g., AWS API Gateway) for rate limiting & WAF
- **FastAPI with async SQLAlchemy** - Implemented and tested
- **PostgreSQL integration** - Fully functional with async support
- **Architecture Documentation** - Comprehensive system design documented

## 2. CI/CD & Deployment
- **GitHub Actions** for build/test/deploy across envs
- **Blue/Green or Canary deployments** with feature flags
- **Docker Hub/ECR image management**
- **Docker Compose** - Implemented for local development

## 3. Monitoring & Logging ✅
- **Prometheus + Grafana** for metrics (latency, error rates)
- **ELK (Elasticsearch, Logstash, Kibana)** for centralized logs
- **Alerting via PagerDuty/Slack**
- **Performance testing** - Locust configuration implemented
- **Structured logging** - Implemented with configurable levels

## 4. Security & Compliance
- **IAM roles, secure secrets** with Vault/AWS Secrets Manager
- **TLS for all endpoints**, encryption at rest
- **SOC2 audit readiness**, regular vulnerability assessments
- **Input validation** - Implemented with Pydantic
- **Error handling** - Comprehensive 400/404/500 error responses

## 5. Billing System Architecture
- **Usage metering microservice** for event_count/session
- **Stripe integration** & webhook handlers
- **Customer portal** for subscription & invoice management

## 6. Developer Experience ✅
- **Interactive Swagger UI** - Available at /docs
- **SDK distribution** on PyPI/NPM - Client SDKs implemented
- **API usage dashboards** and sandbox keys
- **Performance testing tools** - Locust and async test scripts
- **Test data generation** - Scripts for development
- **Architecture Documentation** - Comprehensive system design and interaction patterns
- **API Playground** - Interactive API testing interface
- **Quick Start Guide** - Step-by-step integration guide

## 7. Bot Detection Engine ✅
- **Rule-based analysis** - Implemented with configurable thresholds
- **Behavioral pattern detection** - Keystrokes, mouse, timing, device
- **Real-time processing** - <200ms median processing time
- **Confidence scoring** - 0.0-1.0 scale with risk levels; checks combined by noisy-OR so agreeing evidence adds up (see "Detection" below)
- **Multi-method analysis** - 5 detection methods defined; keystroke, mouse, timing and device are implemented, network is not and carries no weight
- **Decisive signals** - Seven patterns people do not produce (automation, scripted_input, no_input, honeypot, untyped_answers, robotic_timing, timeline_mismatch) lift the score to 0.85 / 0.95

## 8. API Performance & Reliability ✅
- **Async database operations** - Fixed async relationship loading
- **Error handling** - Comprehensive exception management
- **Response time optimization** - Sub-100ms for most endpoints
- **Database connection pooling** - Configured for production
- **Health checks** - /health endpoint implemented
- **API Documentation** - Complete API reference with examples

## 9. Testing & Quality Assurance ✅
- **Unit testing framework** - Pytest configuration ready
- **Performance testing** - Locust load testing implemented
- **Integration testing** - End-to-end API testing
- **Test data management** - Automated test data generation
- **Error scenario testing** - Edge case handling validated

## 10. Documentation & Onboarding ✅
- **Comprehensive README** - Setup, API docs, examples
- **API documentation** - OpenAPI/Swagger integration
- **Architecture documentation** - System design and interaction patterns
- **Code comments** - Detailed inline documentation
- **Development guides** - Step-by-step setup instructions
- **Troubleshooting guides** - Common issues and solutions

## 11. Frontend & User Experience ✅
- **React Dashboard** - Real-time monitoring interface
- **Responsive Design** - Mobile-friendly with Tailwind CSS
- **API Integration** - Seamless backend communication
- **Error Handling** - User-friendly error messages
- **Performance Optimization** - Fast loading and updates
- **Integration Management** - Webhook URLs, setup guides and real configuration status (the simulated webhook test was removed in November 2026)
- **Settings Interface** - Saves selected settings (Decipher, Qualtrics, OpenAI, tracker address, detection threshold) behind `ADMIN_TOKEN`; see Settings model below
- **Layout** - Grouped left sidebar (Monitor, Analyse, Set up, Developers); Overview, Live Quality, Sessions, Add tracking pages (November 2026)
- **Toast Notifications** - User feedback and alerts
- **Icon Integration** - Lucide React icons with proper imports
- **Component Architecture** - Modular, reusable UI components

## 12. Integration & Webhooks ✅
- **Qualtrics Integration** - Webhook handlers with mock mode
- **Decipher Integration** - Survey platform support; tracking added to survey XML and uploaded to Decipher with pre-checks (November 2026)
- **Error Handling** - Graceful failure with fallback data
- **Testing Support** - Easy integration testing
- **Status Monitoring** - Integration status read from the backend configuration

## 13. Client SDKs ✅
- **Python SDK** - Easy integration for Python applications
- **JavaScript SDK** - Browser-based tracking client
- **Documentation** - Usage examples and best practices
- **Error Handling** - Comprehensive error management

## 14. Performance & Scalability ✅
- **Async Architecture** - Non-blocking I/O throughout
- **Database Optimization** - Connection pooling and query optimization
- **Caching Strategy** - Redis integration ready
- **Load Testing** - Locust configuration for performance validation
- **Monitoring** - Real-time performance metrics

## 15. Security & Compliance (In Progress)
- **Authentication System** - JWT tokens and API keys
- **Rate Limiting** - Request throttling and protection
- **Input Validation** - Comprehensive data sanitization
- **CORS Configuration** - Cross-origin request handling
- **Audit Logging** - Security event tracking

## 16. Production Readiness (Next Phase)
- **Container Orchestration** - Kubernetes deployment
- **Auto-scaling** - Dynamic resource allocation
- **Load Balancing** - Traffic distribution
- **Backup & Recovery** - Data protection strategies
- **Disaster Recovery** - Business continuity planning

## 17. Business Features (Future)
- **Billing System** - Usage-based pricing
- **Multi-tenancy** - Customer isolation
- **Analytics Dashboard** - Advanced reporting
- **API Marketplace** - Third-party integrations
- **Developer Portal** - Self-service API management

## 18. Advanced Features (Long-term)
- **Machine Learning** - ML-based bot detection
- **Real-time Streaming** - WebSocket support
- **Mobile SDK** - iOS and Android support
- **Advanced Analytics** - Predictive insights
- **Compliance Tools** - GDPR, CCPA support

## Documentation Status ✅
- **Architecture.md** - Comprehensive system design and interaction patterns
- **API.md** - Complete API reference with examples
- **README.md** - Project overview and setup instructions
- **Planning.md** - Technical planning and roadmap
- **PRD.md** - Product requirements and specifications
- **Task.md** - Development progress and upcoming work

## Recent Achievements ✅
- **Frontend Integration Fixes** - Resolved React component import issues
- **Toast Notifications** - Implemented user feedback system
- **Icon Library Integration** - Fixed Lucide React icon imports
- **Component Architecture** - Modular, maintainable UI components
- **Integration Management** - Complete webhook testing and monitoring
- **API Playground** - Interactive API testing interface; fraud, grid, and timing endpoint templates (February 2026)
- **Report Builder** - Fraud, grid, and timing in summary and detailed reports/CSV; respondent detail popup (click respondent ID) and full CSV per respondent with all analyses (February 2026)
- **Dashboard Deployment (February 2026)** - Frontend redeployed to GCS with API Playground and Report Builder fraud/grid/timing features
- **Quick Start Guide** - Comprehensive onboarding documentation

- **Live Quality, Decipher XML tracking, real Settings and dashboard redesign (November 2026)** - Deployed 2026-11-26 as Cloud Run revision `bot-backend-00069-28j` and to the frontend bucket
- **Detection review and pressure test (2026-11-27)** - 52 simulated respondents on production: 52/52 expected results and 150/150 open ends checked after the fixes. Fixes up to the grid-page count deployed as revision `bot-backend-00076-9q8`; the review fixes (see "Detection" below) are not deployed yet

## Current Architecture & Constraints (November 2026)

### Self-contained, Quant OS compatible
- The folder has no dependency on Quant_Sys (Quant OS).
- It stays compatible with surveys Quant OS tracked: same `QOS_` labels, it recognises the Quant OS tracking marker and re-tracks instead of tracking twice, and it uses the same device-fingerprint text.
- `TRACKING_TOKEN_SECRET` is optional. Share it only if both systems should issue matching tokens. With it set, trackers carry an HMAC token of the survey id and a survey that requires tokens refuses unsigned sessions; a successful Upload to Decipher of a signed tracked file marks the survey as requiring them at once (in code, not yet deployed). The token stops outsiders who never saw the survey; anyone who opens the survey page can read it. Production has no secret set yet, so tracking there is unsigned.

### Stack
- **Backend**: FastAPI with async SQLAlchemy on Cloud SQL PostgreSQL. pandas, pyreadstat and openpyxl read and write .sav, .csv and .xlsx files for the LQ_ merge.
- **Frontend**: React (Vite, Tailwind CSS). Shared UI kit in `frontend/src/components/ui/index.jsx`; layout in `frontend/src/components/layout/AppShell.jsx` (grouped left sidebar, top bar and slide-out menu on phones).
- **Routing**: production uses hash addresses (`index.html#/quality`) because the dashboard is served from a storage bucket with no server-side rewrites (`VITE_ROUTER_MODE=hash` in `frontend/.env.production`). Local dev uses normal paths.
- **Decipher**: tracking is added to the survey XML itself (tracker script, `${uuid}` as respondent id, hidden page with 21 `QOS_` variables). Upload uses Decipher's API with `validate=true` and `overwriteLive=false`, so a live survey is never overwritten. Settings Decipher would refuse (`compat` missing, below 143, or 151+ without `delphi="1"`) are caught before anything is sent.
- **Live Quality**: per-survey rules (table `survey_quality_rules`) are applied on every read (dashboard, CSV, LQ_ variables), and by the final check (composite-analyze) when it sets `is_bot` and the QOS_ values. Changing them later never changes stored results or the QOS_ values already written into Decipher. Saved rules record which bot signals existed when saved, so signals added later start switched on. The respondent total counts people (sessions sharing a respondent id count once); the LQ_ merge uses a uuid's checked session first, then the latest.

### Detection (review of 2026-11-27)
Deployed up to commit 7dd5d5a (revision `bot-backend-00076-9q8`); items marked (not deployed) are in the code only.
- **Open ends**: one OpenAI call per answer covers gibberish, copy_paste, relevance, generic and quality, all judged against the question. Per-server limit `OPENAI_REQUESTS_PER_MINUTE` (300); an answer waits up to `OPENAI_RATE_WAIT_SECONDS` (20) for a slot, and if it still cannot be checked it is stored as not checked (score null, `analysis_details.unchecked`), never as a neutral 50. Live Quality and the CSV count these (`text_unchecked`).
- **Behaviour score** (not deployed): score = 1 − Π(1 − reliability × check score), reliabilities keystroke 0.5, mouse 0.45, timing 0.35, device 0.4, network 0. Two strong checks reach 0.7; one alone does not. Events sent twice are counted once (not deployed); a grid page's extra submit copy is not counted as a second page.
- **Final check**: `is_bot` follows the survey's rules and behaviour only (not deployed); `behavioral_details.engine_is_bot` keeps the verdict under `DETECTION_THRESHOLD`; `composite_is_bot` keeps the combined-score verdict. Timing and grid results are saved in one batch (median 1.7 s under load, within the tracker's 3 s wait).
- **Fraud** (not deployed): location left out until an IP-to-country lookup exists, weights renormalised over IP 0.25, device 0.25, duplicate answers 0.20, velocity 0.15; a fingerprint seen only on other networks (/24, /48) counts half; `QOS_DUP_SCORE` uses the duplicate risk.
- **Stored events** (not deployed): event JSON no longer repeats fields kept in columns or on the session; rejected events are logged by type only.
- **Limits** (unchanged): per IP, per instance: new sessions 30/min, other writes 600/min, Fix with AI 20/hour. The tracker holds the last page at most 3 s for the final check, 2.5 s for the in-survey check, 1.5 s for answers.

### Settings model
- A small set of keys can be edited on the Settings page: DECIPHER_API_KEY, DECIPHER_API_BASE, DECIPHER_COMPANY, QUALTRICS_API_TOKEN, OPENAI_API_KEY, OPENAI_MODEL, TRACKER_API_BASE, TRACKING_TOKEN_SECRET, DETECTION_THRESHOLD.
- A saved value (table `app_settings`) overrides the environment variable of the same name. It applies at once on that instance; every instance re-reads every 30 s. Removing the saved value goes back to the environment.
- Secrets are encrypted at rest with a key derived from SECRET_KEY and are never returned to the browser.
- Saving needs header `X-Admin-Token` matching env `ADMIN_TOKEN`. `ADMIN_TOKEN` is env only; without it the page is read-only.
- `DETECTION_THRESHOLD` (default 0.7) is used by the detection engine for the stored verdict. The final check reports that verdict as `engine_is_bot` and sets `is_bot` from the survey's own bot threshold (not yet deployed).

### Numbers
- Bot rate everywhere = sessions judged bots / sessions checked, counting distinct sessions.

### Database
- New tables (`tracked_surveys`, `survey_quality_rules`, `app_settings`) are created at startup by `create_all`. Existing tables were not changed, so no migration was needed.

### Deployment approach
- Project `survey-bot-detection`, region `northamerica-northeast2`.
- Backend: Cloud Run service `bot-backend` (1 CPU, 1 GiB memory, min 1 / max 10 instances, Cloud SQL instances `bot-db` and `bot-db-v2`, VPC connector `serverless-connector`). Secrets: DATABASE_URL, SECRET_KEY, OPENAI_API_KEY, ADMIN_TOKEN.
- Build with `gcloud builds submit ./backend --tag .../bot-backend:<git-sha>`, then `gcloud run deploy bot-backend --image ...:<git-sha>`, passing only what changes (`--update-env-vars`, `--update-secrets`). Do not use `--set-env-vars`/`--set-secrets`, which replace everything.
- The top-level `deploy-backend.ps1` still uses `--set-env-vars`/`--set-secrets` and only connects `bot-db`; running it as is drops settings and the `bot-db-v2` connection.
- `backend/.gcloudignore` and `backend/.dockerignore` keep `.env`, virtualenvs, `*.db`, tests and caches out of the upload and image.
- Frontend: `npx vite build --mode production`, then `gcloud storage rsync -r frontend/dist gs://bot-detection-frontend-20251208` without deleting unmatched files (`tracking-client.js` may be used by live surveys). Cache headers: index.html `no-cache`, assets immutable.
- Rollback: send traffic back to the previous Cloud Run revision with `gcloud run services update-traffic`.

## Next Steps
1. **Authentication & Security** - Implement JWT and rate limiting
2. **Production Deployment** - Kubernetes and cloud infrastructure
3. **Advanced Testing** - Comprehensive test coverage
4. **Performance Optimization** - Further optimization and scaling
5. **Business Features** - Billing and multi-tenancy
6. **Machine Learning** - ML-based detection algorithms