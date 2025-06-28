# Product Requirements Document (PRD)

## 1. Purpose
Enhance the Bot-vs-Human Detection API + Dashboard to include real-time fraud signals, detailed performance metrics, and full PostgreSQL integration under FastAPI.

## 2. Scope
- **Behavioral Data Capture**: Keystrokes, mouse movement, focus/blur, scroll, device fingerprint, network events.
- **API**:
  - `POST /api/sessions` – start session
  - `POST /api/sessions/{sessionId}/data` – ingest batched events, return classification + `processing_time_ms` and `event_count`
  - `GET  /api/sessions/{sessionId}/status` – retrieve raw session metadata + latest detection result
- **Classification Engine**: Rule-based checks with thresholds, returns `is_human`, `reasons`, `score`, plus performance metadata.
- **Data Persistence**: PostgreSQL tables for sessions, behavior_data, detection_results including extra columns for `processing_time_ms` and `event_count`.
- **Dashboard Metrics**:
  - Latency analysis (ms)
  - Event volume per session
  - Bot/human rates over time

## 3. Key Features
1. **Session Management**: Unique `session_id` via UUID.
2. **Real-Time Checks**:
   - Keystroke rhythm (median delta)
   - Mouse speed & presence
   - Focus/blur & scroll detection
   - Device fingerprint & network anomalies
3. **Performance Metrics**: Capture and store per-request processing time and event counts.
4. **Robust API**: 400/404 error handling, debug logging of raw payloads.
5. **Dashboard**: Timeline charts + summary tables showing classification outcomes and system KPIs.

## 4. Success Metrics
- <200 ms median `processing_time_ms` per request
- ≥95% accuracy in bot/human labeling in lab tests
- <1% API 4xx/5xx error rate
- Dashboard refresh <1 s

## 5. Out of Scope
- Machine-learning training loop
- Multi-tenant billing UI

## 6. Production Version Considerations
- **Service Tiers**: Free, Standard, Enterprise plans with per-session limits and support SLAs.
- **SLAs & Uptime**: 99.9% availability, defined error budgets, support response times.
- **Developer Portal & API Gateway**: API key management, usage dashboards, sandbox endpoints, rate limiting.
- **Multi-Tenant & Isolation**: Tenant-specific configs, data isolation, custom branding options.
- **Billing & Invoicing**: Automated metering (per-session/per-event), Stripe/PayPal integration, invoice generation, payment retries.
- **Support & Onboarding**: Tiered support channels, documentation, onboarding tutorials.
- **Compliance & Security**: GDPR/CCPA, SOC2 readiness, encryption at rest/in transit, audit logging.