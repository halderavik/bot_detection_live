# Bot Detection Flow - Mermaid Diagrams

## Production Status (January 2026)
✅ **DEPLOYED & OPERATIONAL** - All core systems verified and working in production

### Production URLs
- **Backend API**: `https://bot-backend-i56xopdg6q-pd.a.run.app` (Google Cloud Run) ✅ **DEPLOYED**
- **Health Check**: `https://bot-backend-i56xopdg6q-pd.a.run.app/health` ✅ **OPERATIONAL**
- **Metrics**: `https://bot-backend-i56xopdg6q-pd.a.run.app/metrics` ✅ **OPERATIONAL**
- **Frontend Dashboard**: `https://storage.googleapis.com/bot-detection-frontend-20251208/index.html` (Cloud Storage + CDN) ✅ **DEPLOYED**

### Deployed Features
- **Behavioral Bot Detection**: Rule-based analysis with composite scoring ✅ **DEPLOYED**
- **OpenAI Text Quality Analysis**: GPT-4o-mini integration with 100% test accuracy ✅ **DEPLOYED**
- **Hierarchical API (V2)**: Survey → Platform → Respondent → Session structure ✅ **DEPLOYED**
- **Database**: Cloud SQL PostgreSQL with `platform_id` column and composite indexes ✅ **DEPLOYED**
- **VPC Networking**: VPC Connector with optimized egress routing (`private-ranges-only`) ✅ **DEPLOYED**
- **Secrets Management**: Secret Manager with sanitized API keys (CRLF/whitespace stripping) ✅ **DEPLOYED**
- **Text Analysis Dashboard**: Real-time monitoring with filtering and pagination ✅ **DEPLOYED**
- **Enhanced Reporting**: Text quality metrics integrated into all reports ✅ **DEPLOYED**
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
        end
        subgraph "Cloud SQL: PostgreSQL ✅ DEPLOYED"
            N[(Database)]
            BB[(Survey Questions)]
            CC[(Survey Responses)]
        end
        I --> N
        K --> N
        W --> BB
        W --> CC
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
    
    subgraph "Collection Process ✅ DEPLOYED"
        B1[DOM Event Listeners]
        B2[Text Field Detection]
        B3[Throttling & Filtering]
        B4[Event Batching]
        B5[Real-time Transmission]
        B6[Question Capture]
        B7[Response Analysis]
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
    
    B1 --> B3
    B2 --> B6
    B6 --> B7
    B3 --> B4
    B4 --> B5
    B7 --> B5
    
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
    
    subgraph "Composite Analysis Process ✅ DEPLOYED"
        G[Individual Method Scoring<br/>0.0 - 1.0]
        H[Behavioral Weight: 60%]
        I[Text Quality Weight: 40%]
        J[Weighted Combination]
        K[Confidence Calculation]
        L[Classification Decision]
    end
    
    A --> G
    B --> G
    C --> G
    D --> G
    E --> G
    
    F1 --> G
    F2 --> G
    F3 --> G
    F4 --> G
    F5 --> G
    
    G --> H
    G --> I
    H --> J
    I --> J
    J --> K
    K --> L
    
    L --> M{Is Bot?}
    M -->|Yes| N[Bot Classification]
    M -->|No| O[Human Classification]
    
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
    style N fill:#ffcdd2
    style O fill:#c8e6c9
```

## 4. Text Quality Analysis Flow

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

## 5. Decision Making Process

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
    
    E --> K[Score: 0.0-1.0]
    F --> L[Score: 0.0-1.0]
    G --> M[Score: 0.0-1.0]
    H --> N[Score: 0.0-1.0]
    I --> O[Score: 0.0-1.0]
    J --> P[Quality Score: 0-100]
    
    K --> Q[Behavioral Weighted Average<br/>60% Weight]
    L --> Q
    M --> Q
    N --> Q
    O --> Q
    
    P --> R[Text Quality Normalized<br/>40% Weight]
    
    Q --> S[Composite Score Calculation]
    R --> S
    
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
```

## 6. Confidence Scoring & Risk Levels

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

## 7. Integration Flow

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

## 8. Data Processing Pipeline

```mermaid
graph LR
    subgraph "Input Layer"
        A[Raw Events]
        B[Session Data]
        C[Device Info]
        D[Survey Questions]
        E[User Responses]
    end
    
    subgraph "Processing Layer"
        F[Validation]
        G[Normalization]
        H[Enrichment]
        I[Storage]
        J[Text Analysis]
    end
    
    subgraph "Analysis Layer"
        K[Session Management]
        L[Analysis Triggering]
        M[Behavioral Detection Engine]
        N[Text Quality Engine]
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
    
    F --> G
    G --> H
    H --> I
    E --> J
    
    I --> K
    J --> K
    K --> L
    L --> M
    L --> N
    M --> O
    N --> O
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

## 9. Bot vs Human Indicators

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
    style C6 fill:#ffeb3b
```

## 10. Text Analysis Dashboard Flow

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