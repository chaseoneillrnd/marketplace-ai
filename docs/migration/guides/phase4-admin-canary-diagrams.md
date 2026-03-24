# Phase 4: Admin, Analytics, Exports — Visual Architecture Companion

Visual companion to `phase4-admin-canary-guide.md`. All diagrams use Mermaid syntax.

---

## 1. Admin Blueprint Auth Flow

Shows how the admin blueprint's `before_request` hook enforces access control before any route logic executes. The key distinction: most endpoints require `platform_team`, but `DELETE /skills/{slug}` requires `security_team`.

```mermaid
flowchart TD
    A[Incoming Request to /api/v1/admin/*] --> B{App-level before_request:<br/>JWT valid?}
    B -->|No token / invalid| C[401 Unauthorized]
    B -->|Valid JWT| D[g.current_user = decoded payload]
    D --> E{Admin blueprint before_request}
    E --> F{Is endpoint in<br/>SECURITY_TEAM_ENDPOINTS?}

    F -->|Yes: DELETE /skills/slug| G{user.is_security_team?}
    G -->|True| H[Proceed to route handler]
    G -->|False| I[403: Security team access required]

    F -->|No: all other admin routes| J{user.is_platform_team?}
    J -->|True| H
    J -->|False| K[403: Platform team access required]

    H --> L{Route handler executes}
    L --> M[Service layer call]
    M --> N[200/201 Response]
    M -->|ValueError| O[404 Not Found]
    M -->|PermissionError| P[403 Forbidden]

    style C fill:#f66,color:#fff
    style I fill:#f66,color:#fff
    style K fill:#f66,color:#fff
    style O fill:#f96,color:#fff
    style P fill:#f66,color:#fff
    style N fill:#6f6,color:#000
```

### Endpoint-to-Gate Mapping

```mermaid
graph LR
    subgraph "platform_team gate"
        A1[POST /skills/slug/feature]
        A2[POST /skills/slug/deprecate]
        A3[POST /recalculate-trending]
        A4[GET /audit-log]
        A5[GET /users]
        A6[PATCH /users/user_id]
        A7[GET /analytics/*]
        A8[POST /exports]
        A9[GET /exports/job_id]
        A10[GET /review-queue]
        A11[POST /review-queue/*/claim]
        A12[POST /review-queue/*/decision]
    end

    subgraph "security_team gate"
        B1[DELETE /skills/slug]
    end

    style A1 fill:#36f,color:#fff
    style A2 fill:#36f,color:#fff
    style A3 fill:#36f,color:#fff
    style A4 fill:#36f,color:#fff
    style A5 fill:#36f,color:#fff
    style A6 fill:#36f,color:#fff
    style A7 fill:#36f,color:#fff
    style A8 fill:#36f,color:#fff
    style A9 fill:#36f,color:#fff
    style A10 fill:#36f,color:#fff
    style A11 fill:#36f,color:#fff
    style A12 fill:#36f,color:#fff
    style B1 fill:#c33,color:#fff
```

---

## 2. Export Polling Sequence

Shows the client-server interaction for the export workflow, including the 3 bug fixes applied in the Flask port.

```mermaid
sequenceDiagram
    participant Client as Web Client
    participant Flask as Flask API
    participant DB as PostgreSQL
    participant Worker as ARQ Worker

    Note over Client,Worker: BUG FIX #1: JSON body, not query params

    Client->>+Flask: POST /api/v1/admin/exports<br/>{"scope":"installs","format":"csv",<br/>"start_date":"2026-01-01","end_date":"2026-03-01"}
    Flask->>Flask: validated_body(ExportRequest)<br/>Wire start_date/end_date into filters
    Flask->>DB: INSERT ExportJob<br/>status="queued", filters={start_date, end_date}
    DB-->>Flask: job record

    Note over Flask,Client: BUG FIX #3: Return "pending" not "queued"

    Flask-->>-Client: 200 {"id":"abc","status":"pending","scope":"installs"}

    Note over Worker,DB: Background processing

    Worker->>DB: SELECT ExportJob WHERE status="queued"
    Worker->>Worker: Generate CSV with date filters
    Worker->>DB: UPDATE status="done", file_path="/exports/abc.csv"

    loop Poll every 5 seconds
        Client->>+Flask: GET /api/v1/admin/exports/abc
        Flask->>DB: SELECT ExportJob WHERE id=abc
        DB-->>Flask: job record

        alt Still processing
            Note over Flask,Client: Status map: queued->pending, processing->processing
            Flask-->>Client: 200 {"status":"processing"}
        else Complete
            Note over Flask,Client: BUG FIX #2: Return download_url not file_path
            Flask-->>-Client: 200 {"status":"complete","download_url":"/exports/abc.csv"}
        end
    end

    Client->>Flask: GET /exports/abc.csv
    Flask-->>Client: 200 CSV file download
```

### Export Request Schema Comparison

```mermaid
graph LR
    subgraph "FastAPI (Bug)"
        FA[ExportRequest]
        FA --> F1[scope: str]
        FA --> F2[format: str]
        FA -.->|missing| F3[start_date]
        FA -.->|missing| F4[end_date]
    end

    subgraph "Flask (Fixed)"
        FL[ExportRequest]
        FL --> L1[scope: str]
        FL --> L2[format: str]
        FL --> L3[start_date: str?]
        FL --> L4[end_date: str?]
    end

    style F3 fill:#f66,color:#fff,stroke-dasharray: 5 5
    style F4 fill:#f66,color:#fff,stroke-dasharray: 5 5
    style L3 fill:#6f6,color:#000
    style L4 fill:#6f6,color:#000
```

---

## 3. Review Queue State Machine

Shows the submission lifecycle through the HITL review process, including the event_type strings written to the audit log at each transition.

```mermaid
stateDiagram-v2
    [*] --> gate2_passed: Gate 2 auto-scan passes
    [*] --> gate2_flagged: Gate 2 auto-scan flags issues

    gate2_passed --> claimed: Reviewer claims<br/>audit: submission.claimed
    gate2_flagged --> claimed: Reviewer claims<br/>audit: submission.claimed

    claimed --> approved: Decision: approve<br/>audit: submission.approved
    claimed --> rejected: Decision: reject<br/>audit: submission.rejected
    claimed --> gate3_changes_requested: Decision: request_changes<br/>audit: submission.changes_requested

    approved --> [*]: Published to marketplace
    rejected --> [*]: Removed from queue
    gate3_changes_requested --> gate2_passed: Author resubmits

    note right of claimed
        Self-approval prevention:
        submitted_by == reviewer_id
        raises PermissionError -> 403
    end note
```

### Event Type Bug Fix Detail

```mermaid
flowchart TD
    A[decision = "reject"] --> B{Which implementation?}

    B -->|"FastAPI (Bug)"| C["f'submission.{decision}d'"<br/>= "submission.rejectd"]
    B -->|"Flask (Fixed)"| D["_event_map[decision]"<br/>= "submission.rejected"]

    C --> E[AuditLog.event_type = "submission.rejectd"]
    D --> F[AuditLog.event_type = "submission.rejected"]

    style C fill:#f66,color:#fff
    style E fill:#f66,color:#fff
    style D fill:#6f6,color:#000
    style F fill:#6f6,color:#000
```

### Audit Log Entries per Review Action

```mermaid
graph TD
    subgraph "Claim Action"
        C1[POST /review-queue/id/claim]
        C1 --> C2[AuditLog]
        C2 --> C3["event_type: submission.claimed<br/>actor_id: reviewer_id<br/>target_type: submission<br/>target_id: submission.id"]
    end

    subgraph "Decision Action"
        D1[POST /review-queue/id/decision]
        D1 --> D2[AuditLog]
        D2 --> D3["event_type: submission.{approved|rejected|changes_requested}<br/>actor_id: reviewer_id<br/>target_type: submission<br/>target_id: submission.id"]
        D1 --> D4[SubmissionGateResult]
        D4 --> D5["gate: 3<br/>result: passed|failed<br/>findings: {decision, notes, score}"]
    end

    style C3 fill:#36f,color:#fff
    style D3 fill:#36f,color:#fff
    style D5 fill:#369,color:#fff
```

---

## 4. Test Migration Flow

Shows how existing FastAPI test files are converted to Flask test files, highlighting the mechanical transformation pattern and the distinction between portable (framework-agnostic) and framework-dependent tests.

```mermaid
flowchart TD
    subgraph "FastAPI Tests (apps/api/tests/)"
        FA1[test_division_enforcement.py<br/>385 lines - SECURITY CRITICAL]
        FA2[test_auth_multi_identity.py]
        FA3[test_regression_fixes.py]
        FA4[test_reviews_router.py]
        FA5[test_reviews_comprehensive.py]
        FA6[test_fix_social_users_router.py]
        FA7[test_seed_data_integrity.py]
        FA8[test_dependencies.py]
        FA9[test_security_migration_gate.py<br/>326 tests, 8 classes]
    end

    subgraph "Conversion Pattern"
        CP[Replace TestClient with test_client<br/>Replace dependency_overrides with session_factory<br/>Replace response.json with response.get_json<br/>Keep ALL assertions identical]
    end

    subgraph "Flask Tests (apps/flask-api/tests/)"
        FL1[test_division_enforcement.py]
        FL2[test_auth_multi_identity.py]
        FL3[test_regression_fixes.py]
        FL4[test_reviews_router.py]
        FL5[test_reviews_comprehensive.py]
        FL6[test_fix_social_users_router.py]
        FL7[test_seed_data_integrity.py]
        FL8[test_dependencies.py]
        FL9[test_security_migration_gate.py]
    end

    FA1 --> CP --> FL1
    FA2 --> CP --> FL2
    FA3 --> CP --> FL3
    FA4 --> CP --> FL4
    FA5 --> CP --> FL5
    FA6 --> CP --> FL6
    FA7 --> CP --> FL7
    FA8 --> CP --> FL8
    FA9 --> CP --> FL9

    style FA1 fill:#c33,color:#fff
    style FA9 fill:#c33,color:#fff
    style FL1 fill:#363,color:#fff
    style FL9 fill:#363,color:#fff
```

### Portable vs Framework-Dependent Tests

```mermaid
graph TB
    subgraph "Portable (No Changes Needed)"
        P1[test_skills_service.py]
        P2[test_social_service.py]
        P3[test_reviews_service.py]
        P4[test_users_service.py]
        P5[test_skill_schemas.py]
    end

    subgraph "Framework-Dependent (Must Convert)"
        F1[test_division_enforcement.py]
        F2[test_auth_multi_identity.py]
        F3[test_regression_fixes.py]
        F4[test_security_migration_gate.py]
        F5[test_admin.py]
        F6[test_exports.py]
        F7[test_review_queue.py]
        F8[test_analytics.py]
    end

    P1 --- Note1[Pure service layer tests.<br/>Call service functions with mock db.<br/>No HTTP client involved.]
    F1 --- Note2[Use HTTP test client.<br/>Test routes, auth, status codes.<br/>Must convert client + DI pattern.]

    style P1 fill:#363,color:#fff
    style P2 fill:#363,color:#fff
    style P3 fill:#363,color:#fff
    style P4 fill:#363,color:#fff
    style P5 fill:#363,color:#fff
    style F1 fill:#936,color:#fff
    style F2 fill:#936,color:#fff
    style F3 fill:#936,color:#fff
    style F4 fill:#936,color:#fff
    style F5 fill:#936,color:#fff
    style F6 fill:#936,color:#fff
    style F7 fill:#936,color:#fff
    style F8 fill:#936,color:#fff
```

### Test Conversion Diff

```mermaid
graph LR
    subgraph "FastAPI Pattern"
        A1["from fastapi.testclient import TestClient"]
        A2["from skillhub.dependencies import get_db"]
        A3["app = create_app(settings=settings)"]
        A4["app.dependency_overrides[get_db] = lambda: db"]
        A5["client = TestClient(app)"]
        A6["response.json()"]
    end

    subgraph "Flask Pattern"
        B1["# no import needed"]
        B2["from skillhub.app import create_app, AppConfig"]
        B3["app = create_app(config=AppConfig(<br/>session_factory=lambda: db))"]
        B4["# no override needed"]
        B5["client = app.test_client()"]
        B6["response.get_json()"]
    end

    A1 -->|replace| B1
    A2 -->|replace| B2
    A3 -->|replace| B3
    A4 -->|remove| B4
    A5 -->|replace| B5
    A6 -->|replace| B6

    style A1 fill:#933,color:#fff
    style A2 fill:#933,color:#fff
    style A3 fill:#933,color:#fff
    style A4 fill:#933,color:#fff
    style A5 fill:#933,color:#fff
    style A6 fill:#933,color:#fff
    style B1 fill:#363,color:#fff
    style B2 fill:#363,color:#fff
    style B3 fill:#363,color:#fff
    style B4 fill:#363,color:#fff
    style B5 fill:#363,color:#fff
    style B6 fill:#363,color:#fff
```

### Security Gate Test Classes (326 Total)

```mermaid
pie title Security Migration Gate — 326 Tests by Class
    "1. AuthenticationEnforcement (~40)" : 40
    "2. JWTValidation (~30)" : 30
    "3. DivisionIsolation (~60)" : 60
    "4. RoleEscalation (~25)" : 25
    "5. AdminBoundary (~35)" : 35
    "6. AuditLogIntegrity (~20)" : 20
    "7. InputValidation (~50)" : 50
    "8. ReviewQueueWorkflow (~66)" : 66
```
