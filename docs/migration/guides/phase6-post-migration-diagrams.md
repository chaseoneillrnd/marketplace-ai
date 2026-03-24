# SkillHub Phase 6 — Post-Migration Enhancements: Architecture Diagrams

## Companion to phase6-post-migration-guide.md

Reference these diagrams by section number when executing prompts from the guide.

---

## Table of Contents

1. [Revision State Machine](#section-1)
2. [Submission Pipeline with Revision Loops](#section-2)
3. [VitePress Architecture](#section-3)
4. [Component Hierarchy — Submission Page & Admin Queue](#section-4)
5. [Audit Log Data Flow](#section-5)
6. [Version Selector UX Flow](#section-6)
7. [Database Schema Changes ERD](#section-7)

---

## Section 1 — Revision State Machine

> Referenced by: Prompts A.2.1, A.2.2

This diagram shows the complete lifecycle of a submission including revision loops.
REJECTED is terminal. CHANGES_REQUESTED leads to revision. The revision_number
increments on each resubmit cycle.

```mermaid
stateDiagram-v2
    [*] --> SUBMITTED : author submits\n(revision_number=1)

    SUBMITTED --> GATE1_PASSED : Gate 1 passes\n(frontmatter + slug check)
    SUBMITTED --> GATE1_FAILED : Gate 1 fails\n(terminal for this attempt)

    GATE1_PASSED --> GATE2_PASSED : Gate 2 passes\n(LLM judge score >= threshold)
    GATE1_PASSED --> GATE2_FLAGGED : Gate 2 flags\n(score borderline)
    GATE1_PASSED --> GATE2_FAILED : Gate 2 fails\n(score below threshold)

    GATE2_PASSED --> GATE3_HITL : enters human review queue
    GATE2_FLAGGED --> GATE3_HITL : enters human review queue\n(with flag context)

    GATE3_HITL --> APPROVED : reviewer approves
    GATE3_HITL --> REJECTED : reviewer rejects\n(terminal)
    GATE3_HITL --> CHANGES_REQUESTED : reviewer requests changes\n(flags + notes recorded)

    CHANGES_REQUESTED --> REVISION_PENDING : author acknowledges\n(begins editing)

    REVISION_PENDING --> SUBMITTED : author resubmits\n(revision_number++,\ncontent overwritten,\ndiff stored)

    APPROVED --> PUBLISHED : skill created/updated\n(or version created)

    note right of REJECTED
        Terminal state.
        No appeal by default.
        (SKILLHUB_ALLOW_APPEAL flag
        can enable one appeal)
    end note

    note right of CHANGES_REQUESTED
        State transition records:
        - change_request_flags[]
        - notes (free text)
        - reviewer_id
    end note

    note left of SUBMITTED
        On resubmit:
        - Same Submission row mutated
        - content_hash recomputed
        - Gate 1 always re-runs
        - Gate 2 skips if content_hash unchanged
        - Gate 3 always fresh
    end note

    note right of REVISION_PENDING
        At revision_number >= 3:
        escalation_recommended = true
        in transition metadata
    end note
```

---

## Section 2 — Submission Pipeline with Revision Loops

> Referenced by: Prompts A.2.1, A.6.1, C.3.1

This sequence diagram shows the full flow including the revision loop and the
optimization where Gate 2 can be skipped if the content hash has not changed.

```mermaid
sequenceDiagram
    participant Author
    participant API as Flask API
    participant G1 as Gate 1<br/>(Structural)
    participant G2 as Gate 2<br/>(LLM Judge)
    participant G3 as Gate 3<br/>(HITL Queue)
    participant DB as Database

    Note over Author,DB: Initial Submission
    Author->>API: POST /api/v1/submissions
    API->>DB: Create Submission (status=SUBMITTED, revision=1)
    API->>DB: Record state_transition (action=submit)
    API->>G1: Run Gate 1 (frontmatter, slug)
    G1-->>API: PASSED
    API->>DB: Update status=GATE1_PASSED
    API->>DB: Record state_transition (action=gate1_pass)
    API->>G2: Queue Gate 2 (async)
    API-->>Author: 201 { display_id, status, gate1_result }

    G2->>DB: Store content_hash
    G2->>G2: LLM evaluation
    G2-->>DB: Update status=GATE2_PASSED, store score
    DB->>DB: Record state_transition (action=gate2_pass)

    Note over Author,DB: Human Review
    G3->>DB: Admin fetches queue
    G3->>API: PATCH review decision=changes_requested
    API->>DB: Update status=CHANGES_REQUESTED
    API->>DB: Record state_transition (action=request_changes,<br/>flags=[...], notes="...")
    API-->>G3: 200

    Note over Author,DB: Revision Loop
    Author->>API: POST /submissions/{id}/resubmit
    API->>DB: Compute diff(old_content, new_content)
    API->>DB: Mutate Submission (content, revision++, hash, status=SUBMITTED)
    API->>DB: Record state_transition (action=resubmit, diff_hunks=[...])
    API->>G1: Run Gate 1 (always)
    G1-->>API: PASSED
    API->>DB: Record state_transition (action=gate1_pass)

    alt content_hash changed
        API->>G2: Queue Gate 2
        G2->>G2: Full LLM evaluation
    else content_hash unchanged
        API->>DB: Gate 2 result=passed (no_change skip)
        DB->>DB: Record state_transition (action=gate2_skip)
    end

    API-->>Author: 200 { updated submission }

    Note over Author,DB: Final Approval
    G3->>API: PATCH review decision=approved
    API->>DB: Update status=APPROVED
    API->>DB: Record state_transition (action=approve)
    API->>DB: Create Skill + SkillVersion
    API->>DB: Update status=PUBLISHED
    API->>DB: Record state_transition (action=publish)
```

---

## Section 3 — VitePress Architecture

> Referenced by: Prompts B.1.1, B.1.2

```mermaid
graph TB
    subgraph "Browser"
        USER[User]
    end

    subgraph "Nginx Reverse Proxy"
        NGINX[nginx]
    end

    subgraph "Static Assets"
        REACT[React SPA<br/>apps/web/dist/]
        VPRESS[VitePress<br/>apps/docs/.vitepress/dist/]
    end

    subgraph "NX Monorepo"
        direction TB
        subgraph "apps/docs/"
            VP_CFG[".vitepress/config.ts<br/>base: '/docs/'"]
            VP_THEME[".vitepress/theme/index.ts"]
            VP_PAGES["Markdown Pages<br/>(10 pages)"]
            VP_PUBLIC["public/<br/>(static assets)"]
        end

        subgraph "apps/web/"
            NAV["Nav.tsx<br/>(has Docs link)"]
        end
    end

    USER -->|"/*"| NGINX
    NGINX -->|"location /"| REACT
    NGINX -->|"location /docs/"| VPRESS

    NAV -->|"<a href='/docs/'>"| NGINX

    VP_CFG --> VPRESS
    VP_PAGES --> VPRESS

    style NGINX fill:#4a9,stroke:#fff,color:#fff
    style REACT fill:#61dafb,stroke:#fff,color:#000
    style VPRESS fill:#42b883,stroke:#fff,color:#fff
```

### Nginx Configuration Layout

```mermaid
graph LR
    subgraph "nginx.conf"
        A["location / "] -->|"try_files"| B["React SPA<br/>/usr/share/nginx/html/"]
        C["location /docs/"] -->|"try_files"| D["VitePress<br/>/usr/share/nginx/html/docs/"]
        E["location /api/"] -->|"proxy_pass"| F["Flask API<br/>:5000"]
    end
```

### Docker Multi-Stage Build

```mermaid
graph TD
    S1["Stage 1: Build React<br/>npm run build"] --> S3
    S2["Stage 2: Build VitePress<br/>npx vitepress build"] --> S3
    S3["Stage 3: nginx:alpine"]

    S1 -->|"COPY dist/"| S3
    S2 -->|"COPY .vitepress/dist/"| S3

    S3 -->|"React at /"| OUT["/usr/share/nginx/html/"]
    S3 -->|"Docs at /docs/"| OUT2["/usr/share/nginx/html/docs/"]
```

### Documentation Site Map

```mermaid
graph TD
    HOME["/ (Index)"]
    HOME --> GS["Getting Started"]
    HOME --> INTRO["Introduction to Skills"]
    HOME --> USES["Uses for Skills"]
    HOME --> DISC["Skill Discovery"]
    HOME --> SOC["Social Features"]
    HOME --> ADV["Advanced Usage"]
    HOME --> SUB["Submitting a Skill"]
    HOME --> FR["Feature Requests"]
    HOME --> FAQ["FAQ"]
    HOME --> RES["Resources"]

    GS --> GS_CLI["CLI Install"]
    GS --> GS_CLINE["Cline Install"]
    GS --> GS_MCP["MCP Connect"]
    GS --> GS_MAN["Manual Install"]

    style HOME fill:#42b883,stroke:#fff,color:#fff
```

---

## Section 4 — Component Hierarchy: Submission Page & Admin Queue

> Referenced by: Prompts A.3.1-A.3.3, A.4.1-A.4.2, A.5.1, C.1.1-C.3.3

### Skill Submission Page Hierarchy

```mermaid
graph TD
    SP["SubmitSkillPage<br/>/submit"]
    SP --> MS["ModeSelector<br/>(tabs)"]
    SP --> ACTIVE["Active Mode Component"]
    SP --> FMV["FrontMatterValidator<br/>(shared)"]
    SP --> SPP["SkillPreviewPanel<br/>(shared, live)"]
    SP --> HINTS["Judge Hints<br/>(useJudgeHints)"]
    SP --> SB["SubmitButton"]
    SP --> SST["SubmissionStatusTracker<br/>(after submit)"]

    MS --> TAB1["Form Builder"]
    MS --> TAB2["File Upload"]
    MS --> TAB3["MCP Sync<br/>(Advanced)"]

    ACTIVE -->|"mode=form"| FBM["FormBuilderMode"]
    ACTIVE -->|"mode=upload"| FUM["FileUploadMode"]
    ACTIVE -->|"mode=mcp"| MCM["MCPSyncMode"]

    FBM --> STEP1["Step 1: Basics"]
    FBM --> STEP2["Step 2: Config"]
    FBM --> STEP3["Step 3: Content"]
    FBM --> STEP4["Step 4: Preview"]

    FUM --> DZ["Drop Zone"]
    FUM --> ED["Editable Textarea"]

    MCM --> URL["URL Input"]
    MCM --> TOOLS["Tool List"]
    MCM --> GEN["Generated Content"]

    subgraph "Shared Data Flow"
        direction LR
        CONTENT["content: string"] --> FMV
        CONTENT --> SPP
        CONTENT --> HINTS
    end

    style SP fill:#6366f1,stroke:#fff,color:#fff
    style FMV fill:#f59e0b,stroke:#fff,color:#000
    style SPP fill:#10b981,stroke:#fff,color:#fff
    style HINTS fill:#f97316,stroke:#fff,color:#fff
```

### Admin Queue Component Hierarchy

```mermaid
graph TD
    AQV["AdminQueueView"]
    AQV --> SCL["SubmissionCard List"]
    AQV --> MODALS["Modal State Manager"]

    SCL --> SC1["SubmissionCard"]
    SC1 --> RB["RevisionBadge"]
    SC1 --> UI["User Info<br/>(name, division, avatar)"]
    SC1 --> AB["Action Buttons<br/>(Approve/Changes/Reject)"]

    MODALS --> MS_SHELL["ModalShell<br/>(shared chrome)"]
    MODALS --> ACD["AdminConfirmDialog<br/>(approve)"]
    MODALS --> RCM["RequestChangesModal"]
    MODALS --> RJM["RejectModal"]

    ACD --> MS_SHELL
    RCM --> MS_SHELL
    RJM --> MS_SHELL

    RCM --> FLAGS["Flag Checkboxes<br/>(6 options)"]
    RCM --> NOTES1["Notes Textarea"]

    RJM --> CAT["Category Dropdown<br/>(6 options)"]
    RJM --> NOTES2["Notes Textarea<br/>(required for 'other')"]

    AQV --> ALP["AuditLogPanel<br/>(on card expand)"]
    ALP --> TL["Timeline Entries"]
    ALP --> DV["Diff Viewer<br/>(expandable)"]

    style AQV fill:#6366f1,stroke:#fff,color:#fff
    style MS_SHELL fill:#94a3b8,stroke:#fff,color:#fff
    style RCM fill:#f59e0b,stroke:#fff,color:#000
    style RJM fill:#ef4444,stroke:#fff,color:#fff
```

### ModalShell Extraction Pattern

```mermaid
graph TD
    subgraph "Before (Current)"
        ACD_OLD["AdminConfirmDialog<br/>- backdrop<br/>- blur<br/>- focus trap<br/>- card<br/>- gradient bar<br/>- title<br/>- message<br/>- buttons"]
    end

    subgraph "After (Refactored)"
        MS["ModalShell<br/>- backdrop<br/>- blur<br/>- focus trap<br/>- card<br/>- gradient bar<br/>- title<br/>- children slot"]

        ACD_NEW["AdminConfirmDialog<br/>= ModalShell + message + buttons"]
        RCM_NEW["RequestChangesModal<br/>= ModalShell + flags + notes + button"]
        RJM_NEW["RejectModal<br/>= ModalShell + dropdown + notes + button"]

        MS --> ACD_NEW
        MS --> RCM_NEW
        MS --> RJM_NEW
    end

    ACD_OLD -.->|"extract"| MS

    style MS fill:#94a3b8,stroke:#fff,color:#fff
```

---

## Section 5 — Audit Log Data Flow

> Referenced by: Prompts A.2.2, A.5.1

```mermaid
sequenceDiagram
    participant Client as AuditLogPanel
    participant API as Flask API
    participant SST as submission_state_transitions
    participant AL as audit_log (existing)

    Client->>API: GET /api/v1/submissions/{display_id}/audit-log?page=1
    API->>SST: SELECT * WHERE submission_id = ? ORDER BY created_at ASC
    SST-->>API: state_transition rows

    Note over API: Merge and sort by timestamp
    API->>API: Build unified timeline

    API-->>Client: { items: [...], total, page, per_page }

    Note over Client: Render Timeline
    Client->>Client: Map each item to timeline entry
    Client->>Client: Color-code by action type
    Client->>Client: Render diff viewer (collapsed)
```

### Audit Log Entry Types and Colors

```mermaid
graph LR
    subgraph "Timeline Entry Colors"
        SUBMIT["submit / resubmit<br/>BLUE #3b82f6"]
        GATE["gate1_pass / gate2_pass<br/>GRAY #94a3b8"]
        APPROVE["approve<br/>GREEN #22c55e"]
        CHANGES["request_changes<br/>AMBER #f59e0b"]
        REJECT["reject<br/>RED #ef4444"]
        PUBLISH["publish<br/>PURPLE #a855f7"]
    end

    style SUBMIT fill:#3b82f6,stroke:#fff,color:#fff
    style GATE fill:#94a3b8,stroke:#fff,color:#fff
    style APPROVE fill:#22c55e,stroke:#fff,color:#fff
    style CHANGES fill:#f59e0b,stroke:#fff,color:#000
    style REJECT fill:#ef4444,stroke:#fff,color:#fff
    style PUBLISH fill:#a855f7,stroke:#fff,color:#fff
```

### State Transition Record Structure

```mermaid
classDiagram
    class SubmissionStateTransition {
        +UUID id
        +UUID submission_id
        +String from_status (nullable)
        +String to_status
        +String action
        +UUID actor_id
        +String notes (nullable)
        +JSON diff_hunks (nullable)
        +JSON change_request_flags (nullable)
        +String rejection_category (nullable)
        +JSON metadata_ (nullable)
        +DateTime created_at
    }

    class TimelineEntry {
        +String action
        +String actor_name
        +String relative_time
        +String state_before
        +String state_after
        +String notes
        +String[] flags
        +String category
        +DiffHunk[] diffs
        +String dot_color
    }

    SubmissionStateTransition --> TimelineEntry : API transforms to
```

---

## Section 6 — Version Selector UX Flow

> Referenced by: Prompts A.6.1, A.6.2

### Browse Grid to Version Detail Flow

```mermaid
graph TD
    BG["Browse Grid"]
    BG -->|"click card"| SD["Skill Detail View"]

    subgraph "Browse Grid Card"
        CARD["SkillCard"]
        BADGE["v1.3 badge"]
        VCOUNT["4 versions"]
        CARD --> BADGE
        CARD --> VCOUNT
    end

    subgraph "Skill Detail View"
        HEADER["Skill Header"]
        VS["VersionSelector dropdown"]
        CONTENT["Skill Content<br/>(version-specific)"]
        BANNER["Historical Version Banner<br/>(conditional)"]
        CMP["Compare with Current button"]

        HEADER --> VS
        VS --> CONTENT
        VS -->|"non-current selected"| BANNER
        BANNER --> CMP
        CMP --> VDV["VersionDiffView"]
    end

    style BANNER fill:#fbbf24,stroke:#000,color:#000
    style VS fill:#6366f1,stroke:#fff,color:#fff
```

### Version Selector State Machine

```mermaid
stateDiagram-v2
    [*] --> CurrentVersion : page loads

    CurrentVersion --> Loading : user opens dropdown
    Loading --> VersionList : versions fetched
    VersionList --> SelectedVersion : user picks version

    SelectedVersion --> ShowBanner : version != current
    SelectedVersion --> CurrentVersion : version == current

    ShowBanner --> DiffView : "Compare with current" clicked
    ShowBanner --> CurrentVersion : "View current" clicked
    DiffView --> ShowBanner : close diff

    note right of ShowBanner
        Yellow banner:
        "Viewing v1.2.0.
        Current is v1.3.0."
    end note
```

### Version Comparison Diff View

```mermaid
graph LR
    subgraph "VersionDiffView"
        TOGGLE["View Toggle"]
        UNIFIED["Unified View"]
        SIDEBY["Side-by-Side View"]

        TOGGLE -->|"unified"| UNIFIED
        TOGGLE -->|"split"| SIDEBY

        subgraph "Unified"
            UL["- removed lines (red)"]
            UA["+ added lines (green)"]
            UC["  unchanged lines"]
        end

        subgraph "Side-by-Side"
            LEFT["Left: From Version"]
            RIGHT["Right: To Version"]
        end
    end
```

---

## Section 7 — Database Schema Changes ERD

> Referenced by: Prompts A.1.1, A.1.2, A.6.1

### New and Modified Tables

```mermaid
erDiagram
    submissions {
        uuid id PK
        string display_id UK
        uuid skill_id FK "nullable"
        uuid submitted_by FK
        string name
        string short_desc
        string category
        text content
        json declared_divisions
        text division_justification
        enum status
        uuid gate3_reviewer_id FK "nullable"
        datetime gate3_reviewed_at "nullable"
        text gate3_notes "nullable"
        int revision_number "NEW - default 1"
        varchar content_hash "NEW - SHA-256, indexed"
        varchar rejection_category "NEW - nullable"
        json change_request_flags "NEW - nullable"
        uuid parent_submission_id FK "NEW - self-ref, nullable"
        uuid target_skill_id FK "NEW - for version updates, nullable"
        datetime created_at
        datetime updated_at
    }

    submission_state_transitions {
        uuid id PK
        uuid submission_id FK "indexed"
        varchar from_status "nullable"
        varchar to_status
        varchar action
        uuid actor_id FK
        text notes "nullable"
        json diff_hunks "nullable"
        json change_request_flags "nullable"
        varchar rejection_category "nullable"
        json metadata_ "nullable"
        datetime created_at "server_default=now()"
    }

    skill_versions {
        uuid id PK
        uuid skill_id FK
        string version
        text content
        json frontmatter "nullable"
        text changelog "nullable"
        string content_hash
        datetime published_at
        uuid submission_id FK "NEW - nullable"
    }

    skills {
        uuid id PK
        string slug UK
        string name
        string short_desc
        string category FK
        uuid author_id FK
        string current_version
        string status
        datetime created_at
        datetime updated_at
    }

    users {
        uuid id PK
        string display_name
        string email
        string division
        string avatar_url
    }

    submissions ||--o{ submission_state_transitions : "has many"
    submissions }o--|| users : "submitted_by"
    submissions }o--o| skills : "target_skill_id"
    submissions }o--o| submissions : "parent_submission_id"
    submission_state_transitions }o--|| users : "actor_id"
    skill_versions }o--|| skills : "skill_id"
    skill_versions }o--o| submissions : "submission_id"
    skills }o--|| users : "author_id"
```

### New Indexes

```mermaid
graph TD
    subgraph "submission_state_transitions indexes"
        IDX1["ix_sst_submission_created<br/>(submission_id, created_at)"]
        IDX2["ix_sst_actor<br/>(actor_id)"]
    end

    subgraph "submissions new indexes"
        IDX3["ix_submissions_content_hash<br/>(content_hash)"]
        IDX4["ix_submissions_target_skill<br/>(target_skill_id)"]
        IDX5["ix_submissions_parent<br/>(parent_submission_id)"]
    end

    style IDX1 fill:#3b82f6,stroke:#fff,color:#fff
    style IDX3 fill:#22c55e,stroke:#fff,color:#fff
```

### Enum Changes

```mermaid
graph TD
    subgraph "SubmissionStatus Enum (Updated)"
        S1["SUBMITTED"]
        S2["GATE1_PASSED"]
        S3["GATE1_FAILED"]
        S4["GATE2_PASSED"]
        S5["GATE2_FLAGGED"]
        S6["GATE2_FAILED"]
        S7["GATE3_CHANGES_REQUESTED<br/>(legacy alias)"]
        S8["APPROVED"]
        S9["REJECTED"]
        S10["PUBLISHED"]
        S11["CHANGES_REQUESTED<br/>(NEW)"]
        S12["REVISION_PENDING<br/>(NEW)"]

        style S11 fill:#f59e0b,stroke:#fff,color:#000
        style S12 fill:#f59e0b,stroke:#fff,color:#000
    end
```

---

## Cross-Cutting: Full System Topology with Phase 6 Additions

```mermaid
graph TB
    subgraph "Client Layer"
        BROWSER["Browser"]
    end

    subgraph "Reverse Proxy"
        NGINX["nginx"]
    end

    subgraph "Frontend Apps"
        REACT["React SPA<br/>apps/web"]
        VITEPRESS["VitePress Docs<br/>apps/docs<br/>(NEW)"]
    end

    subgraph "API Layer"
        FLASK["Flask API<br/>apps/api<br/>63+ paths"]
        MCP["MCP Server<br/>apps/mcp-server"]
    end

    subgraph "Data Layer"
        PG["PostgreSQL 16"]
        REDIS["Redis 7"]
    end

    subgraph "External"
        LLM["LLM Provider<br/>(judge + hints)"]
        MCP_EXT["External MCP Servers<br/>(introspection)"]
    end

    BROWSER --> NGINX
    NGINX -->|"/"| REACT
    NGINX -->|"/docs/"| VITEPRESS
    NGINX -->|"/api/"| FLASK

    REACT -->|"API calls"| FLASK
    FLASK --> PG
    FLASK --> REDIS
    FLASK -->|"Gate 2 + hints"| LLM
    FLASK -->|"MCP introspect"| MCP_EXT
    MCP --> FLASK

    style VITEPRESS fill:#42b883,stroke:#fff,color:#fff
    style FLASK fill:#f97316,stroke:#fff,color:#fff
    style REACT fill:#61dafb,stroke:#fff,color:#000
```
