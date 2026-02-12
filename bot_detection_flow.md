# Bot Detection Flow - Mermaid Diagrams

## Production Status (February 2026)
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
- **Backend API**: `https://bot-backend-i56xopdg6q-pd.a.run.app` (Google Cloud Run) ✅ **DEPLOYED**
- **Health Check**: `https://bot-backend-i56xopdg6q-pd.a.run.app/health` ✅ **OPERATIONAL**
- **Metrics**: `https://bot-backend-i56xopdg6q-pd.a.run.app/metrics` ✅ **OPERATIONAL**
- **Frontend Dashboard**: `https://storage.googleapis.com/bot-detection-frontend-20251208/index.html` (Cloud Storage + CDN) ✅ **DEPLOYED**

### Deployed Features
- **Behavioral Bot Detection**: Rule-based analysis with composite scoring ✅ **DEPLOYED**
- **OpenAI Text Quality Analysis**: GPT-4o-mini integration with 100% test accuracy ✅ **DEPLOYED**
- **Hierarchical API (V2)**: Survey → Platform → Respondent → Session structure ✅ **DEPLOYED**

### Completed Features (Ready to Deploy)
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
            K --> L[Result Generation]
            L --> M[Response to Client]
            V --> W[Text Quality Analysis]
            W --> X[OpenAI GPT-4o-mini]
            X --> Y[Quality Scoring]
            Y --> Z[Composite Analysis]
            Z --> AA[Unified Bot Detection]
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
        E[Network Analysis<br/>10% Weight]
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
        N[Classification Decision]
    end
    
    A --> H
    B --> H
    C --> H
    D --> H
    E --> H
    
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
    
    K --> M[Store Fraud Indicator]
    L --> M
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

```mermaid
graph TD
    A[Session Data Collected] --> B{Sufficient Data?<br/>>5 keystrokes, >3 mouse events}
    B -->|No| C[Wait for More Data]
    C --> A
    B -->|Yes| D[Trigger Analysis]
    
    D --> E[Keystroke Analysis]
    D --> F[Mouse Analysis]
    D --> G[Timing Analysis]
    D --> H[Device Analysis]
    D --> I[Network Analysis]
    D --> J[Text Quality Analysis]
    D --> K1[IP Address Tracking]
    D --> K2[Device Fingerprinting]
    D --> K3[Duplicate Response Detection]
    D --> K4[Geolocation Checking]
    D --> K5[Velocity Checking]
    D --> L1[Grid Analysis]
    D --> L2[Timing Analysis]
    
    E --> L1[Score: 0.0-1.0]
    F --> L2[Score: 0.0-1.0]
    G --> L3[Score: 0.0-1.0]
    H --> L4[Score: 0.0-1.0]
    I --> L5[Score: 0.0-1.0]
    J --> L6[Quality Score: 0-100]
    
    K1 --> L7[Fraud Score: 0.0-1.0]
    K2 --> L8[Fraud Score: 0.0-1.0]
    K3 --> L9[Fraud Score: 0.0-1.0]
    K4 --> L10[Fraud Score: 0.0-1.0]
    K5 --> L11[Fraud Score: 0.0-1.0]
    
    L1 --> L12[Grid Score: 0.0-1.0]
    L2 --> L13[Timing Score: 0.0-1.0]
    
    L1 --> M1[Behavioral Weighted Average<br/>40% Weight]
    L2 --> M1
    L3 --> M1
    L4 --> M1
    L5 --> M1
    
    L6 --> M2[Text Quality Normalized<br/>30% Weight]
    
    L7 --> M3[Fraud Detection Weighted Average<br/>30% Weight]
    L8 --> M3
    L9 --> M3
    L10 --> M3
    L11 --> M3
    
    L12 --> M4[Grid Analysis Results<br/>Flagged Patterns]
    L13 --> M5[Timing Analysis Results<br/>Speeder/Flatliner Flags]
    
    M1 --> S[Composite Score Calculation]
    M2 --> S
    M3 --> S
    M4 --> S
    M5 --> S
    
    S --> T[Confidence Score]
    T --> U{Confidence > 0.7?}
    U -->|Yes| V[Classified as BOT]
    U -->|No| W[Classified as HUMAN]
    
    V --> X[Risk Level Assessment]
    W --> X
    X --> Y[Return Composite Result]
    
    style V fill:#ffcdd2
    style W fill:#c8e6c9
    style X fill:#fff3e0
    style J fill:#ffeb3b
    style K1 fill:#e1bee7
    style K2 fill:#e1bee7
    style K3 fill:#e1bee7
    style K4 fill:#e1bee7
    style K5 fill:#e1bee7
    style M3 fill:#e1bee7
    style K fill:#e1bee7
    style P fill:#e1bee7
```

## 7. Confidence Scoring & Risk Levels

```mermaid
graph LR
    subgraph "Confidence Score Ranges"
        A[0.0-0.3<br/>High Confidence Human]
        B[0.3-0.5<br/>Likely Human]
        C[0.5-0.7<br/>Uncertain]
        D[0.7-0.9<br/>Likely Bot]
        E[0.9-1.0<br/>High Confidence Bot]
    end
    
    subgraph "Risk Levels"
        F[LOW<br/>High confidence human<br/>Natural patterns]
        G[MEDIUM<br/>Mixed signals<br/>Manual review needed]
        H[HIGH<br/>Strong bot indicators<br/>Automated patterns]
        I[CRITICAL<br/>Very high confidence bot<br/>Clear automated patterns]
    end
    
    A --> F
    B --> F
    C --> G
    D --> H
    E --> I
    
    style A fill:#c8e6c9
    style B fill:#c8e6c9
    style C fill:#fff3e0
    style D fill:#ffcdd2
    style E fill:#ffcdd2
    style F fill:#c8e6c9
    style G fill:#fff3e0
    style H fill:#ffcdd2
    style I fill:#ffcdd2
```

## 8. Integration Flow

```mermaid
graph TB
    subgraph "Survey Platform Integration"
        A[Survey Loads]
        B[Initialize Bot Detection SDK]
        C[Start Event Tracking]
        D[User Completes Survey]
        E[Trigger Analysis]
        F[Get Results]
        G[Store Results in Survey Data]
    end
    
    subgraph "Webhook Integration"
        H[Analysis Complete]
        I[Prepare Webhook Data]
        J[Send to External System]
        K[Update User Profile]
        L[Log Results]
    end
    
    A --> B
    B --> C
    C --> D
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
    style K fill:#c8e6c9
    style L fill:#fff3e0
```

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
        A1[Too Regular Timing<br/>std dev < 10ms]
        A2[Too Fast/Slow<br/>< 50ms or > 2000ms]
        A3[Perfect Precision<br/>> 99% accuracy]
        A4[Straight-line Movements]
        A5[Consistent Patterns]
        A6[Common Bot Screen Sizes]
    end
    
    subgraph "Behavioral Human Indicators"
        B1[Natural Variation<br/>std dev > 10ms]
        B2[Realistic Timing<br/>50-2000ms intervals]
        B3[Variable Precision<br/>< 99% accuracy]
        B4[Curved Movements]
        B5[Irregular Patterns]
        B6[Unique Device Characteristics]
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
        C5[Network Analysis]
        C6[Text Quality Analysis<br/>GPT-4o-mini]
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