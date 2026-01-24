# System Workflows

## Core Asynchronous Workflows
This document outlines the detailed sequence of operations for the primary AI capabilities: **Legal Drafting** and **Hearing Preparation**. These flows rely on the Celery Async Layer to ensure responsiveness and proper version control via Object Storage.

### 1. Legal Drafting & Versioning Workflow
This flow demonstrates how a user requests a document to be drafted, how the system processes it asynchronously, and how it versions the output in S3.

```mermaid
sequenceDiagram
    autonumber
    participant U as Lawyer (User)
    participant FE as Frontend (Next.js)
    participant API as Backend (FastAPI)
    participant Q as Redis Queue
    participant W as Celery Worker
    participant LLM as OpenRouter / AI
    participant DB as Postgres DB
    participant S3 as Object Storage (S3)

    note over U, S3: Scenario: Drafting a New Legal Document

    U->>FE: Inputs requirements & Clicks "Generate Draft"
    FE->>API: POST /api/v1/ai-tasks/draft
    
    activate API
    API->>DB: Create Task Record (Status: PENDING)
    API->>Q: Enqueue "Drafting Task"
    API-->>FE: Return Task ID (202 Accepted)
    deactivate API
    
    FE-->>U: Show "Drafting in Progress" Spinner

    activate W
    Q->>W: Worker Consumes Task
    W->>DB: Fetch Case Context, Parties, Precedents
    
    note right of W: Construct Prompt with RAG Context
    
    W->>LLM: Send Prompt (Draft Contract)
    activate LLM
    LLM-->>W: Stream/Return Generated Text
    deactivate LLM

    note right of W: Generate .DOCX / .PDF Artifact

    W->>S3: Upload File "Matter-123/Drafts/Lease_v1.docx"
    activate S3
    S3-->>W: Return S3 URL / Key
    deactivate S3

    W->>DB: Create "DocumentVersion" Record (v1)
    W->>DB: Update Task Status -> COMPLETED
    deactivate W

    FE->>API: GET /tasks/{id}/status
    API-->>FE: Status: COMPLETED, ArtifactUrl: ...
    FE-->>U: Display "Draft Ready" & Enable Download
```

### 3. High-Level Process Flowchart
This flowchart visualizes the decision logic and data movement across the system components.

```mermaid
graph TD
    %% Styling
    classDef user fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef frontend fill:#fff3e0,stroke:#ff6f00,stroke-width:2px;
    classDef backend fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef async fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,stroke-dasharray: 5 5;
    classDef storage fill:#eceff1,stroke:#455a64,stroke-width:2px;
    classDef external fill:#ffebee,stroke:#c62828,stroke-width:2px;

    Start((Start)) --> UserInput[User Inputs Requirements]
    UserInput -->|Click Generate| UI[Frontend UI]
    
    subgraph "Synchronous API"
        UI -->|POST /draft| API[FastAPI Endpoint]
        API -->|Create Task| DB[(Database)]
        API -->|Enqueue Job| Redis[Redis Queue]
        API -->|202 Accepted| UI
    end

    subgraph "Asynchronous Worker Layer"
        Redis -->|Consume| Worker[Celery Worker]
        
        Worker -->|Step 1: Context| RAG{Need Context?}
        RAG -- Yes --> VectorDB[(ChromaDB)]
        VectorDB -->|Retrieved Docs| Worker
        RAG -- No --> Prompt

        Worker -->|Step 2: Generate| Prompt[Build LLM Prompt]
        Prompt --> LLM[OpenRouter / GPT-4]
        LLM -->|Stream Text| Worker
        
        Worker -->|Step 3: Format| DocGen[Generate .DOCX/.PDF]
    end

    subgraph "Persistence & Versioning"
        DocGen -->|Upload| S3[(S3 Object Storage)]
        S3 -->|Return URL| Worker
        Worker -->|Save Version info| DB
    end

    Worker -->|Task Complete| Notify[Update UI / Send Notification]
    Notify --> End((End))

    %% Apply Styles
    class Start,UserInput,End user;
    class UI frontend;
    class API,DB backend;
    class Redis,Worker,RAG,Prompt,DocGen,Notify async;
    class VectorDB,S3 storage;
    class LLM external;
```


### 2. Hearing Preparation & Argument Analysis
This flow shows the complex analysis of existing evidence to prepare a hearing strategy bundle.

```mermaid
sequenceDiagram
    autonumber
    participant U as Lawyer
    participant FE as UI
    participant Q as Redis
    participant W as Analyzer Worker
    participant VB as Vector DB (Chroma)
    participant S3 as S3 Storage

    U->>FE: Select "Prepare Hearing Strategy"
    FE->>Q: Push Job: ANALYZE_HEARING_STRATEGY
    
    Q->>W: Pick up Job
    
    rect rgb(20, 20, 20)
        note right of W: 1. Gather Evidence
        W->>VB: Query Relevant Facts & Contradictions
        VB-->>W: Retail list of embedding matches
    end
    
    rect rgb(30, 30, 30)
        note right of W: 2. Synthesize Arguments
        W->>W: Generate Strengths/Weaknesses Matrix
        W->>W: Predict Opposing Counsel Arguments
    end

    W->>S3: Save "Hearing_Bundle_v1.pdf"
    W->>S3: Save "Cross_Exam_Questions_v1.docx"
    
    W->>FE: Notify: "Hearing Prep Pack Generated"
```
