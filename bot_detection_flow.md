# Bot Detection Flow - Mermaid Diagrams

## Production Status (November 2026)
✅ **DEPLOYED & OPERATIONAL** - All core systems verified and working in production

## Implementation & Deployment Status Summary

### ✅ **COMPLETED** - Core Features
- **Behavioral Bot Detection**: Fully operational ✅ **DEPLOYED**
- **Text Quality Analysis**: OpenAI GPT-4o-mini integrated ✅ **DEPLOYED**
- **Fraud Detection Service**: Complete implementation with all 5 methods ✅ **COMPLETED**
  - IP Address Tracking ✅ **COMPLETED**
  - Device Fingerprinting ✅ **COMPLETED**
  - Duplicate Response Detection ✅ **COMPLETED**
  - Geolocation Consistency Checking ✅ **COMPLETED**
  - Velocity Checking ✅ **COMPLETED**
- **Composite Scoring**: 40% behavioral, 30% text quality, 30% fraud detection ✅ **COMPLETED**
- **Hierarchical API**: Survey → Platform → Respondent → Session structure ✅ **DEPLOYED**
- **Fraud Detection Hierarchical Endpoints**: All levels implemented ✅ **COMPLETED**
- **Grid/Matrix Analysis**: Straight-lining, pattern detection, variance, satisficing ✅ **DEPLOYED**
- **Per-Question Timing Analysis**: Speeder/flatliner detection, anomaly scoring ✅ **DEPLOYED**
- **Configurable Bot Threshold**: `DETECTION_THRESHOLD` (Settings page, 0.3–0.99, default 0.7) decides the stored verdict and the composite verdict **DEPLOYED**
- **Decisive Bot Signals**: automation, scripted_input, no_input, honeypot, untyped_answers lift the behaviour score; the score before the lift is kept as `base_score` and the signals as `decisive_codes` **DEPLOYED**
- **Decipher XML Tracking**: Add tracking page adds the tracker, the hidden `QOS_` results page, an optional privacy notice and an optional early end on a clear bot signal **DEPLOYED**
- **Live Quality**: per-survey quality rules that re-judge results on every read without changing stored results; `LQ_` variables added to uploaded data files **DEPLOYED**
- **Database**: fraud_indicators, grid_responses, timing_analysis tables with hierarchical indexes ✅ **COMPLETED**
- **Frontend Integration**: Hierarchical fraud, grid, and timing widgets in all detail views ✅ **COMPLETED**
- **Migration**: Database migration scripts created and deployed ✅ **COMPLETED**
- ✅ **Production Deployment**: All features deployed and operational (February 2026)

### ⏳ **PLANNED** - Future Enhancements
- Authentication & Authorization (JWT, API keys)
- Rate Limiting
- WebSocket Support
- Machine Learning Models

### Production URLs
- **Backend API**: `https://bot-backend-119522247395.northamerica-northeast2.run.app` (also `https://bot-backend-i56xopdg6q-pd.a.run.app`) (Google Cloud Run) ✅ **DEPLOYED**
- **Health Check**: `https://bot-backend-i56xopdg6q-pd.a.run.app/health` ✅ **OPERATIONAL**
- **Metrics**: `https://bot-backend-i56xopdg6q-pd.a.run.app/metrics` ✅ **OPERATIONAL**
- **Frontend Dashboard**: `https://storage.googleapis.com/bot-detection-frontend-20251208/index.html` (Cloud Storage + CDN; pages use hash addresses such as `index.html#/quality`) ✅ **DEPLOYED**

### Deployed Features
- **Behavioral Bot Detection**: Rule-based analysis with composite scoring ✅ **DEPLOYED**
- **OpenAI Text Quality Analysis**: GPT-4o-mini integration with 100% test accuracy ✅ **DEPLOYED**
- **Hierarchical API (V2)**: Survey → Platform → Respondent → Session structure ✅ **DEPLOYED**

### Other Deployed Features
- **Fraud Detection Service**: IP tracking, device fingerprinting, duplicate detection, geolocation, velocity checking ✅ **COMPLETED**
- **Composite Scoring**: 40% behavioral, 30% text quality, 30% fraud detection ✅ **COMPLETED**
- **Fraud Detection Hierarchical Endpoints**: Survey/platform/respondent/session-level fraud summaries ✅ **COMPLETED**
- **Database**: Cloud SQL PostgreSQL with `fraud_indicators` table and hierarchical indexes ✅ **DEPLOYED**
- **VPC Networking**: VPC Connector with optimized egress routing (`private-ranges-only`) ✅ **DEPLOYED**
- **Secrets Management**: Secret Manager with sanitized API keys (CRLF/whitespace stripping) ✅ **DEPLOYED**
- **Text Analysis Dashboard**: Real-time monitoring with filtering and pagination ✅ **DEPLOYED**
- **Fraud Detection Dashboard**: Hierarchical fraud widgets integrated into detail views ✅ **DEPLOYED**
- **Enhanced Reporting**: Text quality and fraud metrics integrated into all reports ✅ **DEPLOYED**
- **Health Monitoring**: Real-time OpenAI service status tracking ✅ **DEPLOYED**
- **Production Testing**: Automated test suite with 100% passing rate ✅ **DEPLOYED**

### Not Yet Deployed
- **Authentication & Authorization**: JWT tokens, API keys, role-based access control ⏳ **PLANNED**
- **Rate Limiting**: Request throttling and quota management ⏳ **PLANNED**
- **WebSocket Support**: Real-time bidirectional communication ⏳ **PLANNED**
- **Machine Learning Models**: ML-based bot detection algorithms ⏳ **PLANNED**
- **Multi-tenancy**: Tenant isolation and custom branding ⏳ **PLANNED**
- **Billing System**: Usage metering and payment processing ⏳ **PLANNED**
- **Advanced Monitoring**: Prometheus/Grafana dashboards, distributed tracing ⏳ **PLANNED**

## 1. Overall System Architecture

**Status**: ✅ **DEPLOYED** - All core components operational in production (GCP Cloud Run + Cloud SQL)

```mermaid
graph TB
    subgraph "Client Side (Survey Respondent) ✅ DEPLOYED"
        A0[Decipher survey with tracking added<br/>live_quality_tracker.js] --> A
        A[User Takes Survey] --> B[JavaScript SDK]
        B --> C[Event Listeners]
        C --> D[Data Collection]
        D --> E[Event Batching]
        E --> F[Network Transmission]
        B --> T[Text Capture]
        T --> U[Question/Answer Tracking]
        U --> V[Real-time Analysis]
    end
    
    subgraph "Server Side (GCP) ✅ DEPLOYED"
        subgraph "Cloud Run: FastAPI Backend ✅ DEPLOYED"
            F --> G[Event Ingestion]
            G --> H[Data Validation]
            H --> I[Session Management]
            I --> J[Analysis Triggering]
            J --> K[Detection Engine]
            K --> K1[Decisive Signals +<br/>DETECTION_THRESHOLD]
            K1 --> L[Result Generation]
            L --> M[Response to Client]
            V --> W[Text Quality Analysis]
            W --> X[OpenAI GPT-4o-mini]
            X --> Y[Quality Scoring]
            Y --> Z[Composite Analysis]
            Z --> AA[Unified Bot Detection]
            AA --> QV[QOS_ survey variables<br/>written back into Decipher]
            LQ[Live Quality<br/>per-survey rules applied on read]
            I --> AB[Fraud Detection Service ✅ DEPLOYED]
            AB --> AC[IP Tracking]
            AB --> AD[Device Fingerprinting]
            AB --> AE[Duplicate Detection]
            AB --> AF[Geolocation Check]
            AB --> AG[Velocity Check]
            AC --> Z
            AD --> Z
            AE --> Z
            AF --> Z
            AG --> Z
        end
        subgraph "Cloud SQL: PostgreSQL ✅ DEPLOYED"
            N[(Database)]
            BB[(Survey Questions)]
            CC[(Survey Responses)]
            DD[(Fraud Indicators ✅ DEPLOYED)]
        end
        I --> N
        K --> N
        N --> LQ
            W --> BB
            W --> CC
            AB --> DD
    end
    
    subgraph "Static Hosting ✅ DEPLOYED"
        R[Cloud Storage Bucket]
        S[Cloud CDN]
        R --> S
    end
    
    subgraph "Integration Layer ✅ DEPLOYED"
        O[Qualtrics Integration]
        P[Decipher Integration]
        Q[Custom Webhooks]
        M --> O
        M --> P
        M --> Q
    end
    
    style A fill:#e1f5fe
    style M fill:#c8e6c9
    style N fill:#fff3e0
    style R fill:#e8f5e9
    style S fill:#e8f5e9
    style X fill:#ffeb3b
    style AA fill:#4caf50
```

## 2. Data Collection Flow

**Status**: ✅ **DEPLOYED** - All data collection mechanisms operational in production

```mermaid
graph LR
    subgraph "Behavioral Event Types Captured ✅ DEPLOYED"
        A1[Keystroke Events]
        A2[Mouse Behavior]
        A3[Scroll Events]
        A4[Focus Events]
        A5[Device Characteristics]
        A6[Timing Patterns]
    end
    
    subgraph "Text Quality Data Captured ✅ DEPLOYED"
        A7[Survey Questions]
        A8[Open-ended Responses]
        A9[Response Timing]
        A10[Question Context]
    end
    
    subgraph "Survey Metadata Captured ✅ DEPLOYED"
        A16[Question Text & Type]
        A17[Element IDs & Classes]
        A18[Page Context]
        A19[Question Timestamps]
    end
    
    subgraph "Grid/Matrix Data Captured ✅ DEPLOYED"
        A20[Grid Row/Column IDs]
        A21[Grid Response Values]
        A22[Grid Response Timing]
        A23[Pattern Detection Data]
    end
    
    subgraph "Per-Question Timing Data Captured ✅ DEPLOYED"
        A24[Question Response Times]
        A25[Speeder/Flatliner Flags]
        A26[Timing Anomalies]
        A27[Adaptive Thresholds]
    end
    
    subgraph "Fraud Detection Data Captured ✅ DEPLOYED"
        A11[IP Addresses]
        A12[Device Fingerprints]
        A13[Response Similarity]
        A14[Geolocation Data]
        A15[Response Velocity]
    end
    
    subgraph "Decisive Signal and Page Data Captured"
        A32[navigator.webdriver and user agent]
        A33[Trusted flag on clicks and key presses]
        A34[Hidden honeypot field]
        A35[Open ends filled without typing,<br/>pasting or dictation]
        A36[Time per page: qos-page]
        A37[Grid answers per page: qos-grid]
    end
    
    subgraph "Hierarchical Structure Data ✅ DEPLOYED"
        A28[Survey ID]
        A29[Platform ID]
        A30[Respondent ID]
        A31[Session ID]
    end
    
    subgraph "Collection Process ✅ DEPLOYED"
        B1[DOM Event Listeners]
        B2[Text Field Detection]
        B3[Throttling & Filtering]
        B4[Event Batching]
        B5[Real-time Transmission]
        B6[Question Capture]
        B7[Response Analysis]
        B8[Fraud Data Collection]
        B9[Grid Question Detection]
        B10[Timing Analysis]
        B11[Hierarchical Metadata]
    end
    
    A1 --> B1
    A2 --> B1
    A3 --> B1
    A4 --> B1
    A5 --> B1
    A6 --> B1
    
    A7 --> B2
    A8 --> B2
    A9 --> B2
    A10 --> B2
    
    A16 --> B6
    A17 --> B6
    A18 --> B6
    A19 --> B6
    
    A20 --> B9
    A21 --> B9
    A22 --> B9
    A23 --> B9
    
    A24 --> B10
    A25 --> B10
    A26 --> B10
    A27 --> B10
    
    A11 --> B8
    A12 --> B8
    A13 --> B8
    A14 --> B8
    A15 --> B8
    
    A28 --> B11
    A29 --> B11
    A30 --> B11
    A31 --> B11
    
    A32 --> B1
    A33 --> B1
    A34 --> B5
    A35 --> B5
    A36 --> B5
    A37 --> B5
    
    B1 --> B3
    B2 --> B6
    B6 --> B7
    B9 --> B10
    B10 --> B7
    B3 --> B4
    B4 --> B5
    B7 --> B5
    B8 --> B5
    B11 --> B5
    
    style A1 fill:#ffebee
    style A2 fill:#e8f5e8
    style A3 fill:#fff3e0
    style A4 fill:#f3e5f5
    style A5 fill:#e3f2fd
    style A6 fill:#fce4ec
    style A7 fill:#e8f5e8
    style A8 fill:#e8f5e8
    style A9 fill:#e8f5e8
    style A10 fill:#e8f5e8
    style A11 fill:#e1bee7
    style A12 fill:#e1bee7
    style A13 fill:#e1bee7
    style A14 fill:#e1bee7
    style A15 fill:#e1bee7
```

## 3. Detection Methods & Weights

**Status**: ✅ **DEPLOYED** - All detection methods operational with 100% test accuracy

```mermaid
graph TB
    subgraph "Behavioral Detection Methods ✅ DEPLOYED"
        A[Keystroke Analysis<br/>30% Weight]
        B[Mouse Analysis<br/>25% Weight]
        C[Timing Analysis<br/>20% Weight]
        D[Device Analysis<br/>15% Weight]
        E[Network Analysis<br/>0% Weight, not implemented]
    end
    
    subgraph "Decisive Signals"
        DS1[automation]
        DS2[scripted_input]
        DS3[no_input]
        DS4[honeypot]
        DS5[untyped_answers]
        DS6[One signal: score at least 0.85<br/>Two or more: at least 0.95]
    end
    
    subgraph "Text Quality Analysis ✅ DEPLOYED"
        F1[Gibberish Detection<br/>GPT-4o-mini]
        F2[Copy-Paste Detection<br/>GPT-4o-mini]
        F3[Relevance Analysis<br/>GPT-4o-mini]
        F4[Generic Answer Detection<br/>GPT-4o-mini]
        F5[Overall Quality Score<br/>GPT-4o-mini]
    end
    
    subgraph "Fraud Detection Methods ✅ DEPLOYED"
        G1[IP Address Tracking<br/>25% Weight]
        G2[Device Fingerprinting<br/>25% Weight]
        G3[Duplicate Response Detection<br/>20% Weight]
        G4[Geolocation Consistency<br/>15% Weight]
        G5[Velocity Checking<br/>15% Weight]
    end
    
    subgraph "Grid/Matrix Analysis ✅ DEPLOYED"
        H1[Straight-lining Detection<br/>80%+ identical values]
        H2[Pattern Detection<br/>Diagonal/Zigzag/Reverse]
        H3[Variance Scoring<br/>0-1 scale]
        H4[Satisficing Scoring<br/>0-1 scale]
    end
    
    subgraph "Timing Analysis ✅ DEPLOYED"
        I1[Speeder Detection<br/>< 2000ms threshold]
        I2[Flatliner Detection<br/>> 300000ms threshold]
        I3[Anomaly Detection<br/>Z-score > 2.5]
        I4[Adaptive Thresholds<br/>Question-specific norms]
    end
    
    subgraph "Composite Analysis Process ✅ DEPLOYED"
        H[Individual Method Scoring<br/>0.0 - 1.0]
        I[Behavioral Weight: 40%]
        J[Text Quality Weight: 30%]
        K[Fraud Detection Weight: 30%]
        L[Weighted Combination]
        M[Confidence Calculation]
        N[Classification Decision<br/>score >= DETECTION_THRESHOLD, default 0.7]
    end
    
    A --> H
    B --> H
    C --> H
    D --> H
    E --> H
    
    DS1 --> DS6
    DS2 --> DS6
    DS3 --> DS6
    DS4 --> DS6
    DS5 --> DS6
    DS6 --> H
    
    F1 --> H
    F2 --> H
    F3 --> H
    F4 --> H
    F5 --> H
    
    G1 --> H
    G2 --> H
    G3 --> H
    G4 --> H
    G5 --> H
    
    H1 --> H
    H2 --> H
    H3 --> H
    H4 --> H
    
    I1 --> H
    I2 --> H
    I3 --> H
    I4 --> H
    
    H --> I
    H --> J
    H --> K
    I --> L
    J --> L
    K --> L
    L --> M
    M --> N
    
    N --> O{Is Bot?}
    O -->|Yes| P[Bot Classification]
    O -->|No| Q[Human Classification]
    
    style A fill:#ffcdd2
    style B fill:#c8e6c9
    style C fill:#ffe0b2
    style D fill:#bbdefb
    style E fill:#f8bbd9
    style F1 fill:#ffeb3b
    style F2 fill:#ffeb3b
    style F3 fill:#ffeb3b
    style F4 fill:#ffeb3b
    style F5 fill:#ffeb3b
    style G1 fill:#e1bee7
    style G2 fill:#e1bee7
    style G3 fill:#e1bee7
    style G4 fill:#e1bee7
    style G5 fill:#e1bee7
    style H1 fill:#b39ddb
    style H2 fill:#b39ddb
    style H3 fill:#b39ddb
    style H4 fill:#b39ddb
    style I1 fill:#ce93d8
    style I2 fill:#ce93d8
    style I3 fill:#ce93d8
    style I4 fill:#ce93d8
    style P fill:#ffcdd2
    style Q fill:#c8e6c9
```

**How the weights are used**:
- The behaviour score is the weighted average of keystroke (0.3), mouse (0.25), timing (0.2) and device (0.15). Network analysis returns 0.0 and has no weight.
- Decisive signals are patterns people do not produce. One raises the behaviour score to at least 0.85, two or more to at least 0.95. The score before that lift is stored as `base_score`, and the signal codes as `decisive_codes`.
- A session is stored as a bot when its behaviour score is at or above `DETECTION_THRESHOLD` (Settings page, default 0.7).
- The composite score is 40% behaviour, 30% text-quality risk (1 − quality/100) and 30% fraud. The composite verdict uses the same `DETECTION_THRESHOLD`.
- Grid and per-question timing results are reported next to the composite score (and in the `QOS_` variables), but they do not change the composite number.

## 4. Fraud Detection Analysis Flow

**Status**: ✅ **DEPLOYED** - Complete fraud detection service operational with all 5 detection methods

```mermaid
graph TD
    A[Session Created] --> B[Fraud Detection Triggered]
    B --> C[IP Address Analysis]
    B --> D[Device Fingerprint Generation]
    B --> E[Response Collection]
    B --> F[Geolocation Check]
    B --> G[Velocity Calculation]
    
    C --> C1[Check IP Usage Count]
    C1 --> C2[Calculate IP Risk Score]
    C2 --> C3[Flag if High Reuse]
    
    D --> D1[Generate Device Hash]
    D1 --> D2[Check Fingerprint Reuse]
    D2 --> D3[Calculate Fingerprint Risk]
    
    E --> E1[Compare Response Texts]
    E1 --> E2[Calculate Similarity Score]
    E2 --> E3[Count Duplicate Responses]
    
    F --> F1[Extract IP Geolocation]
    F1 --> F2[Check Consistency]
    F2 --> F3[Flag Inconsistencies]
    
    G --> G1[Count Responses per Hour]
    G1 --> G2[Calculate Velocity Risk]
    G2 --> G3[Flag High Velocity]
    
    C3 --> H[Weighted Fraud Score Calculation]
    D3 --> H
    E3 --> H
    F3 --> H
    G3 --> H
    
    H --> I[Overall Fraud Score 0.0-1.0]
    I --> J[Is Duplicate?]
    J -->|Score >= 0.7| K[Mark as Duplicate]
    J -->|Score < 0.7| L[Mark as Clean]
    
    K --> DC{Data-centre, VPN<br/>or proxy IP?}
    L --> DC
    DC -->|Yes| DC1[Fraud score raised to at least 0.75<br/>reason datacenter_ip]
    DC -->|No| M[Store Fraud Indicator]
    DC1 --> M
    M --> N[Return to Composite Analysis]
    
    style A fill:#e1f5fe
    style I fill:#fff3e0
    style K fill:#ffcdd2
    style L fill:#c8e6c9
    style N fill:#4caf50
```

## 5. Text Quality Analysis Flow

**Status**: ✅ **DEPLOYED** - OpenAI GPT-4o-mini integration fully operational with 100% test accuracy

```mermaid
graph TD
    A[User Types Response] --> B[Auto-detect Text Field]
    B --> C[Capture Question Context]
    C --> D[Monitor Response Time]
    D --> E[User Submits Response]
    E --> F[Send to Text Analysis API]
    
    F --> G[OpenAI GPT-4o-mini Analysis<br/>✅ DEPLOYED]
    G --> H[Gibberish Check]
    G --> I[Copy-Paste Detection]
    G --> J[Relevance Analysis]
    G --> K[Generic Answer Check]
    G --> L[Quality Scoring]
    
    H --> M[Flag Reasons]
    I --> M
    J --> M
    K --> M
    L --> N[Quality Score 0-100]
    
    M --> O[Response Flagged?]
    N --> O
    O -->|Yes| P[Store Flagged Response]
    O -->|No| Q[Store Clean Response]
    
    P --> R[Update Session Quality Metrics]
    Q --> R
    R --> S[Return to Composite Analysis]
    
    style A fill:#e1f5fe
    style G fill:#ffeb3b
    style O fill:#fff3e0
    style P fill:#ffcdd2
    style Q fill:#c8e6c9
    style S fill:#4caf50
```

## 6. Decision Making Process

The tracker calls `composite-analyze` when the respondent submits the last page. That call stores a fresh behavioural verdict, runs the grid, timing and fraud checks, then builds the composite result. Analysis does not wait for a minimum number of events: with fewer than 5 key presses the keystroke score is 0.3, and a touch device gets a mouse score of 0.3.

```mermaid
graph TD
    A[Events arrive in batches<br/>every 5 s and on each page submit] --> D[Last page submitted:<br/>composite-analyze]
    
    D --> E[Keystroke Analysis<br/>0.3]
    D --> F[Mouse Analysis<br/>0.25]
    D --> G[Timing Analysis<br/>0.2]
    D --> H[Device Analysis<br/>0.15]
    D --> DS{Decisive signals?<br/>automation, scripted_input, no_input,<br/>honeypot, untyped_answers}
    
    E --> B1[Weighted average = base_score]
    F --> B1
    G --> B1
    H --> B1
    
    B1 --> B2[Behaviour score]
    DS -->|None| B2
    DS -->|One| B3[Raised to at least 0.85]
    DS -->|Two or more| B4[Raised to at least 0.95]
    B3 --> B2
    B4 --> B2
    
    B2 --> U{Score >= DETECTION_THRESHOLD?<br/>default 0.7}
    U -->|Yes| V[Stored verdict: BOT]
    U -->|No| W[Stored verdict: HUMAN]
    V --> X[Risk level from the score]
    W --> X
    X --> X1[Store detection result<br/>with base_score and decisive_codes]
    
    D --> J[Text Quality: average 0-100]
    D --> K[Fraud Score: 0.0-1.0]
    D --> L1[Grid Analysis]
    D --> L2[Per-question Timing]
    
    X1 --> S[Composite = 0.4 behaviour<br/>+ 0.3 x 1 - quality/100<br/>+ 0.3 fraud]
    J --> S
    K --> S
    
    S --> S1{Composite >= DETECTION_THRESHOLD?}
    S1 -->|Yes| S2[Composite verdict: BOT]
    S1 -->|No| S3[Composite verdict: HUMAN]
    S2 --> S4[Composite risk:<br/>CRITICAL >= 0.8, HIGH >= 0.6,<br/>MEDIUM >= 0.4, else LOW]
    S3 --> S4
    
    S4 --> Y[Return composite result<br/>with survey_variables QOS_]
    L1 --> Y
    L2 --> Y
    
    style V fill:#ffcdd2
    style W fill:#c8e6c9
    style S2 fill:#ffcdd2
    style S3 fill:#c8e6c9
    style X fill:#fff3e0
    style J fill:#ffeb3b
    style K fill:#e1bee7
```

The stored verdict and the composite verdict both use `DETECTION_THRESHOLD`. Changing it on the Settings page affects analyses run after the change; results already stored keep their verdict. Live Quality can judge stored results again under a survey's own rules (see section 14).

## 7. Confidence Scoring & Risk Levels

The behaviour score is a bot probability: 0.0 looks human, 1.0 looks like a bot. The verdict line is `DETECTION_THRESHOLD` (default 0.7), so the ranges below assume the default.

```mermaid
graph LR
    subgraph "Behaviour Score Ranges"
        A[0.0-0.5<br/>Looks human]
        C[0.5-0.7<br/>Uncertain]
        D[0.7-0.9<br/>Likely Bot]
        E[0.9-1.0<br/>High Confidence Bot]
    end
    
    subgraph "Stored Risk Levels"
        F[LOW<br/>score below 0.5]
        G[MEDIUM<br/>score 0.5 or more]
        H[HIGH<br/>score 0.7 or more,<br/>or judged a bot]
        I[CRITICAL<br/>score 0.9 or more]
    end
    
    A --> F
    C --> G
    D --> H
    E --> I
    
    style A fill:#c8e6c9
    style C fill:#fff3e0
    style D fill:#ffcdd2
    style E fill:#ffcdd2
    style F fill:#c8e6c9
    style G fill:#fff3e0
    style H fill:#ffcdd2
    style I fill:#ffcdd2
```

- A session judged a bot is at least HIGH, even if the threshold was set below 0.7.
- The composite result has its own risk level: CRITICAL from 0.8, HIGH from 0.6, MEDIUM from 0.4, otherwise LOW.
- Live Quality shows the behaviour risk from the stored score (HIGH from 0.7, MEDIUM from 0.5, otherwise LOW), raised to HIGH for any respondent its rules judge a bot.

## 8. Integration Flow

For Decipher, tracking is added to the survey XML on the Add tracking page (`POST /api/v1/tracking/decipher`). The file gets the tracker script as a `respview.client.js` style with `mode="after"`, Decipher's `${uuid}` as the respondent id, a hidden results page with the 21 `QOS_` variables, an optional privacy notice (`QOS_privacy`, on by default) and an optional early end on a clear bot signal (`QOS_EARLY` and `QOS_bot_term`, off by default). Removing the tracking gives back the original file byte for byte.

```mermaid
graph TB
    subgraph "Decipher XML Tracking"
        X1[Upload survey XML<br/>Add tracking page]
        X2[Check compat and delphi settings<br/>Decipher would refuse]
        X3[Add tracker, QOS_ results page,<br/>optional privacy notice and early end]
        X4[Download tracked XML or<br/>upload to Decipher, never over a live survey]
    end
    
    subgraph "Survey Platform Integration"
        A[Survey Loads]
        B[Tracker starts with the Decipher uuid<br/>as respondent id]
        C[Start Event Tracking]
        C1{Early end on and this is<br/>the chosen page break?}
        C2[Analyze behaviour so far]
        C3{Enabled decisive<br/>signal fired?}
        C4[QOS_EARLY = bot<br/>QOS_bot_term ends the survey]
        D[User Completes Survey]
        E[Last page: composite-analyze]
        F[Get Results]
        G[Fill QOS_ variables on the<br/>hidden results page]
    end
    
    subgraph "Webhook Integration"
        H[Analysis Complete]
        I[Prepare Webhook Data]
        J[Send to External System]
        K[Update User Profile]
        L[Log Results]
    end
    
    X1 --> X2
    X2 --> X3
    X3 --> X4
    X4 --> A
    A --> B
    B --> C
    C --> C1
    C1 -->|No| D
    C1 -->|Yes| C2
    C2 --> C3
    C3 -->|Yes| C4
    C3 -->|No, error or timeout| D
    D --> E
    E --> F
    F --> G
    F --> H
    H --> I
    I --> J
    J --> K
    J --> L
    
    style A fill:#e3f2fd
    style G fill:#c8e6c9
    style C4 fill:#ffcdd2
    style K fill:#c8e6c9
    style L fill:#fff3e0
```

**Early end on a clear bot signal**: when turned on, a hidden `QOS_EARLY` question goes on a page break every respondent reaches (page 2 by default). On that submit the tracker holds the page for at most 2.5 seconds, scores the behaviour so far, and writes `bot` only if one of the decisive signals chosen for the survey fired. The `QOS_bot_term` termination reads that value. A behaviour score alone, an error or a timeout leaves the respondent in the survey. If the survey has no such page break, the early check is not added and the final check still runs.

**Final check**: on the last page the tracker holds the submit for at most 3 seconds while `composite-analyze` runs, then fills `QOS_FLAG` (bot, human or unknown), `QOS_SCORE`, `QOS_RISK` and the numeric `QOS_` variables from `survey_variables`. These values reach Decipher's own data exports. They are fixed when written; per-survey rules on Live Quality do not change them.

## 9. Data Processing Pipeline

```mermaid
graph LR
    subgraph "Input Layer"
        A[Raw Events]
        B[Session Data]
        C[Device Info]
        D[Survey Questions]
        E[User Responses]
        E1[Grid Responses]
        E2[Timing Data]
        E3[Hierarchical Metadata]
    end
    
    subgraph "Processing Layer"
        F[Validation]
        G[Normalization]
        H[Enrichment]
        I[Storage]
        J[Text Analysis]
        J1[Grid Analysis]
        J2[Timing Analysis]
    end
    
    subgraph "Analysis Layer"
        K[Session Management]
        L[Analysis Triggering]
        M[Behavioral Detection Engine]
        N[Text Quality Engine]
        N1[Grid Analysis Engine]
        N2[Timing Analysis Engine]
        O[Composite Analysis]
        P[Result Generation]
    end
    
    subgraph "Output Layer"
        Q[API Response]
        R[Database Storage]
        S[Webhook Notifications]
        T[Quality Dashboard]
    end
    
    A --> F
    B --> F
    C --> F
    D --> F
    E --> F
    E1 --> F
    E2 --> F
    E3 --> F
    
    F --> G
    G --> H
    H --> I
    E --> J
    E1 --> J1
    E2 --> J2
    
    I --> K
    J --> K
    J1 --> K
    J2 --> K
    K --> L
    L --> M
    L --> N
    L --> N1
    L --> N2
    M --> O
    N --> O
    N1 --> O
    N2 --> O
    O --> P
    
    P --> Q
    P --> R
    P --> S
    N --> T
    
    style A fill:#e1f5fe
    style Q fill:#c8e6c9
    style R fill:#fff3e0
    style S fill:#f3e5f5
    style J fill:#ffeb3b
    style N fill:#ffeb3b
    style T fill:#4caf50
```

## 10. Bot vs Human Indicators

```mermaid
graph TB
    subgraph "Behavioral Bot Indicators"
        A1[Too Regular Typing<br/>std dev < 10ms within bursts]
        A2[Too Fast Typing<br/>average < 50ms, or rounded intervals]
        A3[Same-length Mouse Steps]
        A4[Perfectly Straight Mouse Path]
        A5[Clockwork Event Timing<br/>gaps vary < 0.1s, session < 10s]
        A6[Screen Size Changes or Empty Screen]
    end
    
    subgraph "Decisive Bot Signals"
        D1[automation<br/>webdriver or headless user agent]
        D2[scripted_input<br/>half or more of clicks and keys untrusted]
        D3[no_input<br/>pages answered with no mouse or keyboard]
        D4[honeypot<br/>hidden field filled in]
        D5[untyped_answers<br/>open ends with no typing, pasting or dictation]
    end
    
    subgraph "Behavioral Human Indicators"
        B1[Natural Variation<br/>std dev > 10ms]
        B2[Realistic Typing Speed<br/>pauses over 2s are ignored]
        B3[Varied Mouse Step Lengths]
        B4[Curved Movements]
        B5[Irregular Patterns]
        B6[One Stable Screen Size]
    end
    
    subgraph "Text Quality Bot Indicators"
        A7[Gibberish Text<br/>Random characters]
        A8[Copy-Paste Content<br/>Generic responses]
        A9[Irrelevant Answers<br/>Off-topic responses]
        A10[Generic Responses<br/>Low-effort answers]
        A11[Very Low Quality<br/>Score < 30]
    end
    
    subgraph "Grid/Matrix Bot Indicators ✅ DEPLOYED"
        A17[Straight-lining<br/>80%+ identical values]
        A18[Diagonal Patterns<br/>Mechanical patterns]
        A19[Low Variance<br/>No response diversity]
        A20[High Satisficing<br/>Low-effort responses]
    end
    
    subgraph "Timing Bot Indicators ✅ DEPLOYED"
        A21[Speeders<br/>Response < 2000ms]
        A22[Flatliners<br/>Response > 300000ms]
        A23[Timing Anomalies<br/>Z-score > 2.5]
        A24[Inconsistent Timing<br/>No natural variation]
    end
    
    subgraph "Fraud Detection Bot Indicators ✅ DEPLOYED"
        A12[IP Address Reuse<br/>Multiple sessions from same IP]
        A13[Device Fingerprint Reuse<br/>Same device across sessions]
        A14[Duplicate Responses<br/>High text similarity]
        A15[Geolocation Inconsistency<br/>IP location mismatch]
        A16[High Velocity<br/>Rapid response submission]
    end
    
    subgraph "Text Quality Human Indicators"
        B7[Coherent Text<br/>Meaningful responses]
        B8[Original Content<br/>Personal insights]
        B9[Relevant Answers<br/>On-topic responses]
        B10[Specific Details<br/>Thoughtful answers]
        B11[High Quality<br/>Score > 70]
    end
    
    subgraph "Analysis Methods"
        C1[Keystroke Analysis]
        C2[Mouse Analysis]
        C3[Timing Analysis]
        C4[Device Analysis]
        C5[Network Analysis<br/>not implemented]
        C6[Text Quality Analysis<br/>GPT-4o-mini]
        C14[Decisive Signal Check]
        C7[IP Address Tracking ✅ DEPLOYED]
        C8[Device Fingerprinting ✅ DEPLOYED]
        C9[Duplicate Detection ✅ DEPLOYED]
        C10[Geolocation Checking ✅ DEPLOYED]
        C11[Velocity Checking ✅ DEPLOYED]
        C12[Grid Analysis ✅ DEPLOYED]
        C13[Per-Question Timing ✅ DEPLOYED]
    end
    
    A1 --> C1
    A2 --> C1
    A3 --> C2
    A4 --> C2
    A5 --> C3
    A6 --> C4
    
    D1 --> C14
    D2 --> C14
    D3 --> C14
    D4 --> C14
    D5 --> C14
    
    B1 --> C1
    B2 --> C1
    B3 --> C2
    B4 --> C2
    B5 --> C3
    B6 --> C4
    
    A7 --> C6
    A8 --> C6
    A9 --> C6
    A10 --> C6
    A11 --> C6
    
    B7 --> C6
    B8 --> C6
    B9 --> C6
    B10 --> C6
    B11 --> C6
    
    A12 --> C7
    A13 --> C8
    A14 --> C9
    A15 --> C10
    A16 --> C11
    
    A17 --> C12
    A18 --> C12
    A19 --> C12
    A20 --> C12
    
    A21 --> C13
    A22 --> C13
    A23 --> C13
    A24 --> C13
    
    style A1 fill:#ffcdd2
    style A2 fill:#ffcdd2
    style A3 fill:#ffcdd2
    style A4 fill:#ffcdd2
    style A5 fill:#ffcdd2
    style A6 fill:#ffcdd2
    style A7 fill:#ffcdd2
    style A8 fill:#ffcdd2
    style A9 fill:#ffcdd2
    style A10 fill:#ffcdd2
    style A11 fill:#ffcdd2
    style B1 fill:#c8e6c9
    style B2 fill:#c8e6c9
    style B3 fill:#c8e6c9
    style B4 fill:#c8e6c9
    style B5 fill:#c8e6c9
    style B6 fill:#c8e6c9
    style B7 fill:#c8e6c9
    style B8 fill:#c8e6c9
    style B9 fill:#c8e6c9
    style B10 fill:#c8e6c9
    style B11 fill:#c8e6c9
    style A12 fill:#ffcdd2
    style A13 fill:#ffcdd2
    style A14 fill:#ffcdd2
    style A15 fill:#ffcdd2
    style A16 fill:#ffcdd2
    style A17 fill:#ffcdd2
    style A18 fill:#ffcdd2
    style A19 fill:#ffcdd2
    style A20 fill:#ffcdd2
    style A21 fill:#ffcdd2
    style A22 fill:#ffcdd2
    style A23 fill:#ffcdd2
    style A24 fill:#ffcdd2
    style C6 fill:#ffeb3b
    style C7 fill:#e1bee7
    style C8 fill:#e1bee7
    style C9 fill:#e1bee7
    style C10 fill:#e1bee7
    style C11 fill:#e1bee7
    style C12 fill:#b39ddb
    style C13 fill:#ce93d8
```

## 11. Grid/Matrix Analysis Flow

**Status**: ✅ **DEPLOYED** - Complete grid analysis system operational with pattern detection and satisficing scoring

```mermaid
graph TD
    A[Grid Question Detected] --> B[Collect Grid Responses]
    B --> C[Extract Row/Column Data]
    C --> D[Response Value Collection]
    D --> E[Straight-lining Detection]
    D --> F[Pattern Detection]
    D --> G[Variance Calculation]
    D --> H[Satisficing Scoring]
    
    E --> E1{80%+ Identical?}
    E1 -->|Yes| E2[Flag as Straight-lined]
    E1 -->|No| E3[No Straight-lining]
    
    F --> F1[Check Diagonal Pattern]
    F --> F2[Check Reverse Diagonal]
    F --> F3[Check Zigzag Pattern]
    F --> F4[Check Straight Line]
    F1 --> F5[Pattern Type Identified]
    F2 --> F5
    F3 --> F5
    F4 --> F5
    
    G --> G1[Calculate Response Variance]
    G1 --> G2[Variance Score 0-1]
    
    H --> H1[Combine Variance + Timing]
    H1 --> H2[Satisficing Score 0-1]
    
    E2 --> I[Store Grid Analysis Results]
    E3 --> I
    F5 --> I
    G2 --> I
    H2 --> I
    
    I --> J[Return to Composite Analysis]
    
    style A fill:#e1f5fe
    style E2 fill:#ffcdd2
    style E3 fill:#c8e6c9
    style I fill:#fff3e0
    style J fill:#4caf50
```

The number of straight-lined grids from this analysis is written to `QOS_STRAIGHTLINE`. Live Quality also reads the grid answers the tracker stores for each page (`qos-grid:`, sent for grids with 3 or more rows) and flags Straight-lining when every row of a grid has the same answer and the grid has at least the survey's `straightline_min_rows` rows (default 3), or when this analysis already flagged it.

## 12. Per-Question Timing Analysis Flow

**Status**: ✅ **DEPLOYED** - Complete timing analysis system operational with speeder/flatliner detection and anomaly scoring

```mermaid
graph TD
    A[Response Submitted] --> B[Extract Response Time]
    B --> C[Get Question Context]
    C --> D[Calculate Adaptive Threshold]
    D --> E[Speeder Detection]
    D --> F[Flatliner Detection]
    D --> G[Anomaly Detection]
    
    E --> E1{Time < 2000ms?}
    E1 -->|Yes| E2[Flag as Speeder]
    E1 -->|No| E3[Not a Speeder]
    
    F --> F1{Time > 300000ms?}
    F1 -->|Yes| F2[Flag as Flatliner]
    F1 -->|No| F3[Not a Flatliner]
    
    G --> G1[Calculate Z-Score]
    G1 --> G2{Z-Score > 2.5?}
    G2 -->|Yes| G3[Flag as Anomaly]
    G2 -->|No| G4[No Anomaly]
    
    E2 --> H[Store Timing Analysis]
    E3 --> H
    F2 --> H
    F3 --> H
    G3 --> H
    G4 --> H
    
    H --> I[Update Session Timing Metrics]
    I --> J[Return to Composite Analysis]
    
    style A fill:#e1f5fe
    style E2 fill:#ffcdd2
    style F2 fill:#ffcdd2
    style G3 fill:#ffcdd2
    style H fill:#fff3e0
    style J fill:#4caf50
```

The number of speeder answers from this analysis is written to `QOS_SPEEDER`, and flatliners show as the Flatliner flag on Live Quality. The Live Quality Speeder flag does not use per-answer times, because a quick short answer would count. It uses page times instead (see section 14).

## 13. Text Analysis Dashboard Flow

**Status**: ✅ **DEPLOYED** - Complete text analysis dashboard with filtering, pagination, and CSV export

```mermaid
graph TB
    subgraph "Text Analysis Dashboard ✅ DEPLOYED"
        A[User Access Dashboard] --> B[Load Dashboard Summary]
        B --> C[Get Aggregated Metrics]
        C --> D[Display Summary Widget]
        D --> E[Show Quality Distribution]
        E --> F[Display Flagged Responses Count]
        F --> G[Show Average Quality Score]
        G --> H[User Clicks View Details]
        H --> I[Load Respondent Analysis]
        I --> J[Apply Filters]
        J --> K[Paginate Results]
        K --> L[Display Respondent Table]
        L --> M[Show Quality Scores per Respondent]
        M --> N[Expand Flagged Responses]
        N --> O[Display Flag Reasons]
        O --> P[Export to CSV]
    end
    
    subgraph "Backend Processing ✅ DEPLOYED"
        Q[Dashboard Summary Endpoint] --> R[Query Survey Responses]
        R --> S[Calculate Quality Metrics]
        S --> T[Aggregate by Time Period]
        T --> U[Return Summary Data]
        
        V[Respondent Analysis Endpoint] --> W[Query with Pagination]
        W --> X[Apply Survey/Date Filters]
        X --> Y[Calculate Per-Respondent Metrics]
        Y --> Z[Return Paginated Results]
    end
    
    B --> Q
    I --> V
    U --> D
    Z --> L
    
    style A fill:#e1f5fe
    style D fill:#c8e6c9
    style L fill:#c8e6c9
    style P fill:#4caf50
    style Q fill:#fff3e0
    style V fill:#fff3e0
```

## 14. Live Quality Judging Flow

Live Quality (`/quality` page, `GET /api/v1/quality/results?survey_id=`) judges one survey's stored results under that survey's quality rules. Rules are applied on every read: the dashboard, the CSV export and the `LQ_` variables. Editing a rule never changes stored results or the `QOS_` values already written into Decipher. A survey with no saved rules uses the defaults.

| Rule | Default | What it does |
|------|---------|--------------|
| `bot_threshold` | 0.7 | Bot when the stored `base_score` (the behaviour score before decisive signals lifted it) is at or above this |
| `bot_signals` | all five | Decisive signals that make a respondent a bot on their own |
| `speeder_page_seconds` | 3.5 | Speeder when pages average under this many seconds |
| `speeder_median_share` | 0.5 | Speeder when total time is under this share of the median (needs 5 checked respondents with page times; 0 = off) |
| `straightline_min_rows` | 3 | Smallest grid that counts for straight-lining |
| `text_reasons` | all five | Which text-check reasons count as low-quality open ends: gibberish, generic, irrelevant, copy_paste, low_quality |
| `flag_pasted` | on | Flag answers that were pasted or appeared without typing |
| `fraud_threshold` | 0.7 | High fraud risk when the fraud score is at or above this |
| `flag_duplicates` | on | Flag respondents the fraud check marked as duplicates |
| `flag_datacenter` | on | Flag data-centre, VPN or proxy IP addresses |

```mermaid
graph TD
    A[Stored results for one survey:<br/>detection results, text, fraud, grid, timing] --> B[Read page times and grid answers<br/>from qos-page and qos-grid events]
    R[(survey_quality_rules<br/>or defaults)] --> C
    A --> C[Judge each respondent]
    B --> C
    
    C --> F1{base_score >= bot_threshold<br/>or an enabled signal fired?}
    F1 -->|Yes| G1[Bot-like behaviour]
    C --> F2{Flagged open end with<br/>a counted reason?}
    F2 -->|Yes| G2[Low-quality open ends]
    C --> F3{flag_pasted and an answer<br/>was pasted or not typed?}
    F3 -->|Yes| G3[Pasted answers]
    C --> F4{Grid with every row the same<br/>and >= straightline_min_rows rows?}
    F4 -->|Yes| G4[Straight-lining]
    C --> F5{Seconds per page < speeder_page_seconds<br/>or time < share of median?}
    F5 -->|Yes| G5[Speeder]
    C --> F6{Per-question timing<br/>found a flatliner?}
    F6 -->|Yes| G6[Flatliner]
    C --> F7{flag_duplicates and<br/>marked duplicate?}
    F7 -->|Yes| G7[Duplicate]
    C --> F8{Fraud score >= fraud_threshold?}
    F8 -->|Yes| G8[High fraud risk]
    C --> F9{flag_datacenter and<br/>datacenter_ip reason?}
    F9 -->|Yes| G9[Data-centre IP]
    
    G1 --> H[Dashboard rows, flag counts,<br/>CSV export, LQ_ variables]
    G2 --> H
    G3 --> H
    G4 --> H
    G5 --> H
    G6 --> H
    G7 --> H
    G8 --> H
    G9 --> H
    
    style G1 fill:#ffcdd2
    style R fill:#fff3e0
    style H fill:#c8e6c9
```

- Results stored before `base_score` existed are judged on their stored score.
- If a fraud score is missing, High fraud risk falls back to a stored fraud risk level of HIGH or CRITICAL.
- Respondents are `checked` once analysed, `in_progress` if active in the last 20 minutes, otherwise `dropped`. Only checked respondents get a bot or human verdict.

**Bot rate**: everywhere in the service (Overview, Sessions, survey and platform pages, `/dashboard/overview`, `/surveys`), the bot rate is distinct sessions judged bots divided by distinct sessions checked (analysed). A session analysed twice counts once. These pages use the stored verdicts; the Live Quality bot count uses the survey's rules.

## 15. Survey Data Variables

```mermaid
graph LR
    subgraph "Written into Decipher during the survey"
        A[composite-analyze result] --> B[survey_variables]
        B --> C[21 QOS_ variables on the<br/>hidden results page]
        C --> D[Decipher data exports]
    end
    
    subgraph "Added to a data file after fieldwork"
        E[Upload .sav, .csv or .xlsx<br/>POST /quality/merge] --> F[Match on QOS_SESSION,<br/>then QOS_RESPONDENT, then uuid]
        F --> G[Judge under the survey's rules]
        G --> H[Same file with LQ_ variables]
    end
    
    D --> E
```

**`QOS_` variables** (fixed when the respondent finishes): QOS_RESPONDENT, QOS_SESSION, QOS_FLAG, QOS_SCORE, QOS_RISK, QOS_STATUS (1 human, 2 suspect, 3 bot), QOS_BEHAV, QOS_OES, QOS_FRAUD, QOS_DUP, QOS_DUP_SCORE, QOS_IP_RISK, QOS_DEVICE_RISK, QOS_GEO_RISK, QOS_VELOCITY, QOS_DATACENTER, QOS_SPEEDER, QOS_STRAIGHTLINE, QOS_FLAGCOUNT, QOS_REASON, QOS_REASONS. Scores are whole numbers from 0 to 100. QOS_OES is a quality score (higher is better); the other scores are risk scores (higher is worse). A value is left blank when its check had nothing to work on. QOS_STATUS is 3 when the stored or composite verdict is bot, 2 when any reason code applies or the composite risk is MEDIUM or higher, otherwise 1.

**Reason codes** (QOS_REASONS lists all that apply; QOS_REASON is the lowest, most severe one; 0 means none):

| Code | Reason |
|------|--------|
| 1 | automation: automated or headless browser |
| 2 | scripted_input: clicks and key presses generated by script |
| 3 | no_input: pages answered with no mouse or keyboard use |
| 4 | honeypot: hidden honeypot field filled in |
| 5 | untyped_answers: open ends that appeared without typing |
| 6 | behaviour: bot-like behaviour score (only when judged a bot with no decisive signal) |
| 10 | datacenter_ip: data centre, VPN or proxy IP address |
| 11 | device_reuse: same device seen on other sessions |
| 12 | ip_reuse: same IP address used repeatedly |
| 13 | duplicate_responses: answers copied from another respondent |
| 14 | high_velocity: many surveys started in a short time |
| 15 | geolocation_inconsistency: location does not match |
| 20 | low_quality_open_ends: low-quality open-ended answers |
| 21 | straight_lining: straight-lined grid questions |
| 22 | speeder: questions answered too fast |

**`LQ_` variables** (judged under the survey's rules at upload time): LQ_MATCHED, LQ_STATUS, LQ_VERDICT, LQ_BOT_SCORE, LQ_BOT_RISK, LQ_BOT_SIGNALS, LQ_SECONDS, LQ_PAGES, LQ_SEC_PER_PAGE, LQ_TEXT_QUALITY, LQ_FRAUD_SCORE, LQ_FRAUD_RISK, one 0/1 variable per flag (LQ_F_BOT, LQ_F_TEXT, LQ_F_PASTED, LQ_F_STRAIGHT, LQ_F_SPEEDER, LQ_F_FLATLINE, LQ_F_DUPLICATE, LQ_F_FRAUD, LQ_F_DATACENTRE), LQ_NFLAGS and LQ_FLAGS. Uploading again replaces existing `LQ_` columns.