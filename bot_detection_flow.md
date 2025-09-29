# Bot Detection Methodology - Mermaid Diagrams

## 1. Overall System Architecture

```mermaid
graph TB
    subgraph "Client Side (Survey Respondent)"
        A[User Takes Survey] --> B[JavaScript SDK]
        B --> C[Event Listeners]
        C --> D[Data Collection]
        D --> E[Event Batching]
        E --> F[Network Transmission]
    end
    
    subgraph "Server Side (GCP)"
        subgraph "Cloud Run: FastAPI Backend"
            F --> G[Event Ingestion]
            G --> H[Data Validation]
            H --> I[Session Management]
            I --> J[Analysis Triggering]
            J --> K[Detection Engine]
            K --> L[Result Generation]
            L --> M[Response to Client]
        end
        subgraph "Cloud SQL: PostgreSQL"
            N[(Database)]
        end
        I --> N
        K --> N
    end
    
    subgraph "Static Hosting"
        R[Cloud Storage Bucket]
        S[Cloud CDN]
        R --> S
    end
    
    subgraph "Integration Layer"
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
```

## 2. Data Collection Flow

```mermaid
graph LR
    subgraph "Event Types Captured"
        A1[Keystroke Events]
        A2[Mouse Behavior]
        A3[Scroll Events]
        A4[Focus Events]
        A5[Device Characteristics]
        A6[Timing Patterns]
    end
    
    subgraph "Collection Process"
        B1[DOM Event Listeners]
        B2[Throttling & Filtering]
        B3[Event Batching]
        B4[Real-time Transmission]
    end
    
    A1 --> B1
    A2 --> B1
    A3 --> B1
    A4 --> B1
    A5 --> B1
    A6 --> B1
    
    B1 --> B2
    B2 --> B3
    B3 --> B4
    
    style A1 fill:#ffebee
    style A2 fill:#e8f5e8
    style A3 fill:#fff3e0
    style A4 fill:#f3e5f5
    style A5 fill:#e3f2fd
    style A6 fill:#fce4ec
```

## 3. Detection Methods & Weights

```mermaid
graph TB
    subgraph "Detection Methods"
        A[Keystroke Analysis<br/>30% Weight]
        B[Mouse Analysis<br/>25% Weight]
        C[Timing Analysis<br/>20% Weight]
        D[Device Analysis<br/>15% Weight]
        E[Network Analysis<br/>10% Weight]
    end
    
    subgraph "Analysis Process"
        F[Individual Method Scoring<br/>0.0 - 1.0]
        G[Weighted Combination]
        H[Confidence Calculation]
        I[Classification Decision]
    end
    
    A --> F
    B --> F
    C --> F
    D --> F
    E --> F
    
    F --> G
    G --> H
    H --> I
    
    I --> J{Is Bot?}
    J -->|Yes| K[Bot Classification]
    J -->|No| L[Human Classification]
    
    style A fill:#ffcdd2
    style B fill:#c8e6c9
    style C fill:#ffe0b2
    style D fill:#bbdefb
    style E fill:#f8bbd9
    style K fill:#ffcdd2
    style L fill:#c8e6c9
```

## 4. Decision Making Process

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
    
    E --> J[Score: 0.0-1.0]
    F --> K[Score: 0.0-1.0]
    G --> L[Score: 0.0-1.0]
    H --> M[Score: 0.0-1.0]
    I --> N[Score: 0.0-1.0]
    
    J --> O[Weighted Average<br/>Calculation]
    K --> O
    L --> O
    M --> O
    N --> O
    
    O --> P[Confidence Score]
    P --> Q{Confidence > 0.7?}
    Q -->|Yes| R[Classified as BOT]
    Q -->|No| S[Classified as HUMAN]
    
    R --> T[Risk Level Assessment]
    S --> T
    T --> U[Return Result]
    
    style R fill:#ffcdd2
    style S fill:#c8e6c9
    style T fill:#fff3e0
```

## 5. Confidence Scoring & Risk Levels

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

## 6. Integration Flow

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

## 7. Data Processing Pipeline

```mermaid
graph LR
    subgraph "Input Layer"
        A[Raw Events]
        B[Session Data]
        C[Device Info]
    end
    
    subgraph "Processing Layer"
        D[Validation]
        E[Normalization]
        F[Enrichment]
        G[Storage]
    end
    
    subgraph "Analysis Layer"
        H[Session Management]
        I[Analysis Triggering]
        J[Detection Engine]
        K[Result Generation]
    end
    
    subgraph "Output Layer"
        L[API Response]
        M[Database Storage]
        N[Webhook Notifications]
    end
    
    A --> D
    B --> D
    C --> D
    
    D --> E
    E --> F
    F --> G
    
    G --> H
    H --> I
    I --> J
    J --> K
    
    K --> L
    K --> M
    K --> N
    
    style A fill:#e1f5fe
    style L fill:#c8e6c9
    style M fill:#fff3e0
    style N fill:#f3e5f5
```

## 8. Bot vs Human Indicators

```mermaid
graph TB
    subgraph "Bot Indicators"
        A1[Too Regular Timing<br/>std dev < 10ms]
        A2[Too Fast/Slow<br/>< 50ms or > 2000ms]
        A3[Perfect Precision<br/>> 99% accuracy]
        A4[Straight-line Movements]
        A5[Consistent Patterns]
        A6[Common Bot Screen Sizes]
    end
    
    subgraph "Human Indicators"
        B1[Natural Variation<br/>std dev > 10ms]
        B2[Realistic Timing<br/>50-2000ms intervals]
        B3[Variable Precision<br/>< 99% accuracy]
        B4[Curved Movements]
        B5[Irregular Patterns]
        B6[Unique Device Characteristics]
    end
    
    subgraph "Analysis Methods"
        C1[Keystroke Analysis]
        C2[Mouse Analysis]
        C3[Timing Analysis]
        C4[Device Analysis]
        C5[Network Analysis]
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
    
    style A1 fill:#ffcdd2
    style A2 fill:#ffcdd2
    style A3 fill:#ffcdd2
    style A4 fill:#ffcdd2
    style A5 fill:#ffcdd2
    style A6 fill:#ffcdd2
    style B1 fill:#c8e6c9
    style B2 fill:#c8e6c9
    style B3 fill:#c8e6c9
    style B4 fill:#c8e6c9
    style B5 fill:#c8e6c9
    style B6 fill:#c8e6c9
``` 