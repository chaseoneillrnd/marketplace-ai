# Phase 2: Auth Endpoints + Async Sync Conversion — Diagrams

Companion diagrams for `phase2-auth-async-guide.md`.

---

## 1. Auth Flow Sequence — Flask `before_request` Hook

Shows how every request flows through the authentication middleware and how
public endpoints, protected endpoints, and stub auth interact.

```mermaid
sequenceDiagram
    participant C as Client
    participant F as Flask before_request
    participant PE as PUBLIC_ENDPOINTS
    participant JWT as jwt.decode()
    participant G as g.current_user
    participant V as View Function

    C->>F: HTTP Request
    F->>PE: Is request.endpoint in PUBLIC_ENDPOINTS?

    alt Endpoint is public
        PE-->>F: Yes
        F->>V: Pass through (no auth)
        V-->>C: Response
    else Endpoint is protected
        PE-->>F: No
        F->>F: Extract Authorization header

        alt No token / missing Bearer prefix
            F-->>C: 401 {"detail": "Missing or invalid token"}
        else Has Bearer token
            F->>JWT: decode(token, secret, algorithms=[HS256])

            alt Token valid
                JWT-->>F: payload dict
                F->>G: g.current_user = payload
                F->>V: Continue to view function
                V-->>C: Response (200/4xx/5xx)
            else Token expired
                JWT-->>F: ExpiredSignatureError
                F-->>C: 401 {"detail": "Token expired"}
            else Invalid token (wrong secret, bad format, wrong algorithm)
                JWT-->>F: InvalidTokenError
                F-->>C: 401 {"detail": "Invalid token"}
            end
        end
    end
```

---

## 2. Stub Auth Conditional Registration Flow

Shows how the Flask app factory decides whether to register the stub auth
blueprint and how `PUBLIC_ENDPOINTS` grows accordingly.

```mermaid
flowchart TD
    A[create_app called] --> B[Load AppConfig]
    B --> C{config.stub_auth_enabled?}

    C -->|True| D[Import stub_auth_bp from blueprints.stub_auth]
    D --> E[Register stub_auth_bp on app]
    E --> F[Add stub_auth endpoints to PUBLIC_ENDPOINTS]
    F --> G[PUBLIC_ENDPOINTS includes:<br/>health.health_check<br/>auth.oauth_redirect<br/>auth.oauth_callback<br/>stub_auth.login<br/>stub_auth.list_dev_users]

    C -->|False| H[Do NOT import stub_auth module]
    H --> I[PUBLIC_ENDPOINTS stays minimal:<br/>health.health_check<br/>auth.oauth_redirect<br/>auth.oauth_callback]

    G --> J[Store PUBLIC_ENDPOINTS on app.config]
    I --> J

    J --> K[Always register auth_bp]
    K --> L[Register remaining blueprints]
    L --> M[App ready]

    style D fill:#ffd,stroke:#aa0
    style H fill:#dfd,stroke:#0a0
    style F fill:#ffd,stroke:#aa0
```

### Security Invariants

```mermaid
flowchart LR
    subgraph Production [stub_auth_enabled = False]
        P1[stub_auth.py never imported]
        P2[/auth/token returns 404]
        P3[/auth/dev-users returns 404]
        P1 --> P2
        P1 --> P3
    end

    subgraph Development [stub_auth_enabled = True]
        D1[stub_auth.py imported + registered]
        D2[/auth/token returns 200]
        D3[/auth/dev-users returns 200]
        D1 --> D2
        D1 --> D3
    end

    style Production fill:#dfd,stroke:#0a0
    style Development fill:#ffd,stroke:#aa0
```

---

## 3. Async-to-Sync Conversion Chain

Shows the dependency chain that dictates conversion order and the exact
changes at each level.

```mermaid
flowchart TB
    subgraph Tier1 ["Tier 1: Root Cause (convert first)"]
        LJ["llm_judge.py<br/>LLMJudgeService.evaluate()"]
        LJ_BEFORE["BEFORE:<br/>async def evaluate()<br/>async with httpx.AsyncClient()<br/>response = await client.post()"]
        LJ_AFTER["AFTER:<br/>def evaluate()<br/>with httpx.Client()<br/>response = client.post()"]
        LJ_BEFORE -->|"~20 lines"| LJ_AFTER
    end

    subgraph Tier2 ["Tier 2: Cascading (convert after Tier 1)"]
        SUB["submissions.py<br/>run_gate2_scan()"]
        SUB_BEFORE["BEFORE:<br/>async def run_gate2_scan()<br/>verdict = await judge.evaluate()"]
        SUB_AFTER["AFTER:<br/>def run_gate2_scan()<br/>verdict = judge.evaluate()"]
        SUB_BEFORE -->|"remove async/await"| SUB_AFTER

        RTR["routers/submissions.py<br/>scan_submission()"]
        RTR_BEFORE["BEFORE:<br/>async def scan_submission()<br/>result = await run_gate2_scan()"]
        RTR_AFTER["AFTER:<br/>def scan_submission()<br/>result = run_gate2_scan()"]
        RTR_BEFORE -->|"remove async/await"| RTR_AFTER
    end

    subgraph Tier3 ["Tier 3: Independent (convert anytime)"]
        CACHE["cache.py<br/>get_redis / cache_get / cache_set"]
        CACHE_BEFORE["BEFORE:<br/>async def cache_get()<br/>raw = await redis.get()<br/>async def cache_set()<br/>await redis.setex()"]
        CACHE_AFTER["AFTER:<br/>def cache_get()<br/>raw = redis.get()<br/>def cache_set()<br/>redis.setex()"]
        CACHE_BEFORE -->|"remove async/await"| CACHE_AFTER
    end

    subgraph NoChange ["Tier 4: Do NOT Convert"]
        WORKER["worker.py<br/>aggregate_daily_metrics()<br/>recalculate_trending()<br/>clean_expired_exports()"]
        WORKER_NOTE["Stays async<br/>ARQ requires async<br/>Per ADR-001"]
    end

    LJ_AFTER -->|"unblocks"| SUB_BEFORE
    SUB_AFTER -->|"unblocks"| RTR_BEFORE

    style NoChange fill:#f5f5f5,stroke:#999
    style WORKER_NOTE fill:#f5f5f5,stroke:#999
```

### Conversion Order with Test File Mapping

```mermaid
flowchart LR
    subgraph Step1 ["Step 1: llm_judge.py"]
        S1[Convert evaluate to sync]
        T1["Update tests:<br/>test_llm_judge.py (5 tests)<br/>- Remove @pytest.mark.asyncio<br/>- AsyncMock -> MagicMock<br/>- AsyncClient -> Client"]
    end

    subgraph Step2 ["Step 2: submissions.py"]
        S2[Convert run_gate2_scan to sync]
        T2["Update tests:<br/>test_submission_pipeline_fixes.py (8)<br/>test_submissions_service.py (2)<br/>- Remove @pytest.mark.asyncio<br/>- Remove await"]
    end

    subgraph Step3 ["Step 3: routers/submissions.py"]
        S3[Convert scan_submission to sync]
        T3["No dedicated test changes<br/>(covered by Step 2 tests)"]
    end

    subgraph Step4 ["Step 4: cache.py"]
        S4[Convert cache functions to sync]
        T4["Update tests:<br/>test_cache.py (5 tests)<br/>- Remove @pytest.mark.asyncio<br/>- AsyncMock -> MagicMock"]
    end

    Step1 --> Step2 --> Step3
    Step4 -.->|"independent"| Step1

    style Step1 fill:#fee,stroke:#c00
    style Step2 fill:#ffe,stroke:#aa0
    style Step3 fill:#efe,stroke:#0a0
    style Step4 fill:#eef,stroke:#00a
```

---

## 4. Blueprint Registration and PUBLIC_ENDPOINTS Overview

Shows all blueprints and their endpoint-to-visibility mapping after Phase 2.

```mermaid
flowchart TD
    subgraph App ["Flask App (create_app)"]
        subgraph AlwaysRegistered ["Always Registered"]
            HBP["health_bp<br/>/health"]
            ABP["auth_bp<br/>/auth/me<br/>/auth/oauth/&lt;provider&gt;<br/>/auth/oauth/&lt;provider&gt;/callback"]
        end

        subgraph ConditionalRegistered ["Conditional (stub_auth_enabled=True only)"]
            SABP["stub_auth_bp<br/>/auth/token<br/>/auth/dev-users"]
        end
    end

    subgraph PubEndpoints ["PUBLIC_ENDPOINTS (frozenset)"]
        PE1["health.health_check"]
        PE2["auth.oauth_redirect"]
        PE3["auth.oauth_callback"]
        PE4["stub_auth.login *"]
        PE5["stub_auth.list_dev_users *"]
    end

    HBP --> PE1
    ABP -->|"oauth_redirect"| PE2
    ABP -->|"oauth_callback"| PE3
    SABP -->|"login"| PE4
    SABP -->|"list_dev_users"| PE5

    ABP -->|"get_me"| PROT["PROTECTED<br/>(requires JWT)"]

    PE4 -.-|"* Only when stub_auth_enabled"| SABP
    PE5 -.-|"* Only when stub_auth_enabled"| SABP

    style ConditionalRegistered fill:#ffd,stroke:#aa0
    style PROT fill:#fdd,stroke:#c00
```

---

## 5. Test Coverage Map

Shows which test files cover which source files after Phase 2.

```mermaid
flowchart LR
    subgraph Tests ["Test Files"]
        TA["test_auth_flask.py<br/>(new — Flask client)"]
        TL["test_llm_judge.py<br/>(modified — sync)"]
        TS["test_submission_pipeline_fixes.py<br/>(modified — sync)"]
        TSS["test_submissions_service.py<br/>(modified — sync)"]
        TC["test_cache.py<br/>(modified — sync)"]
        TSG["test_security_migration_gate.py<br/>(Classes 2 & 4)"]
    end

    subgraph Source ["Source Files"]
        BA["blueprints/auth.py"]
        BSA["blueprints/stub_auth.py"]
        SLJ["services/llm_judge.py"]
        SSB["services/submissions.py"]
        RSB["routers/submissions.py"]
        CAC["cache.py"]
        APP["app.py"]
    end

    TA --> BA
    TA --> BSA
    TA --> APP
    TL --> SLJ
    TS --> SSB
    TSS --> SSB
    TS --> RSB
    TC --> CAC
    TSG --> BA
    TSG --> BSA
    TSG --> APP
```
