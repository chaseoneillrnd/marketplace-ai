# Phase 1: Flask Skeleton — Visual Architecture Companion

**Companion to:** `phase1-flask-skeleton-guide.md`
**Notation:** All diagrams use Mermaid syntax

---

## 1. System Overview — Before and After Phase 1

### Before Phase 1 (Current State)

```mermaid
graph TB
    subgraph "Monorepo"
        subgraph "apps/api (FastAPI)"
            FA_MAIN["skillhub/main.py<br/>create_app()"]
            FA_DEPS["skillhub/dependencies.py<br/>get_current_user, get_db"]
            FA_ROUTERS["skillhub/routers/<br/>13 router modules"]
            FA_SERVICES["skillhub/services/<br/>11 service modules"]
            FA_CONFIG["skillhub/config.py<br/>Settings (pydantic-settings)"]
            FA_TRACING["skillhub/tracing.py<br/>OTel setup"]
        end

        subgraph "libs/db"
            DB_SESSION["skillhub_db/session.py<br/>SessionLocal, engine"]
            DB_MODELS["skillhub_db/models/<br/>8 model modules"]
        end

        subgraph "libs/python-common"
            COMMON["skillhub_common/<br/>__init__.py (empty)"]
        end

        subgraph "apps/web (React)"
            WEB["React + Vite"]
        end
    end

    WEB -->|HTTP| FA_MAIN
    FA_MAIN --> FA_ROUTERS
    FA_ROUTERS --> FA_DEPS
    FA_ROUTERS --> FA_SERVICES
    FA_DEPS --> DB_SESSION
    FA_SERVICES --> DB_SESSION
    FA_SERVICES --> DB_MODELS
    FA_MAIN --> FA_CONFIG
    FA_MAIN --> FA_TRACING

    style FA_MAIN fill:#e74c3c,color:#fff
    style FA_DEPS fill:#e74c3c,color:#fff
    style FA_ROUTERS fill:#e74c3c,color:#fff
```

### After Phase 1

```mermaid
graph TB
    subgraph "Monorepo"
        subgraph "apps/fast-api (Preserved)"
            FA_MAIN["skillhub/main.py<br/>(untouched)"]
            FA_ALL["... all FastAPI code ..."]
        end

        subgraph "apps/api (New Flask)"
            FL_APP["skillhub_flask/app.py<br/>create_app()"]
            FL_AUTH["skillhub_flask/auth.py<br/>before_request hook"]
            FL_DB["skillhub_flask/db.py<br/>scoped_session + teardown"]
            FL_VAL["skillhub_flask/validation.py<br/>validated_query, validated_body"]
            FL_CONFIG["skillhub_flask/config.py<br/>AppConfig + Settings"]
            FL_TRACE["skillhub_flask/tracing.py<br/>FlaskInstrumentor"]
            FL_HEALTH["blueprints/health.py<br/>GET /health"]
            FL_TESTS["tests/<br/>conftest + 5 test files"]
        end

        subgraph "libs/db"
            DB_SESSION["skillhub_db/session.py<br/>SessionLocal, engine"]
            DB_MODELS["skillhub_db/models/<br/>8 model modules"]
        end

        subgraph "libs/python-common"
            COMMON_AUDIT["skillhub_common/audit.py<br/>audit_log_append()"]
        end

        subgraph "apps/web (React)"
            WEB["React + Vite"]
        end
    end

    WEB -->|HTTP| FL_APP
    FL_APP --> FL_AUTH
    FL_APP --> FL_DB
    FL_APP --> FL_HEALTH
    FL_APP --> FL_CONFIG
    FL_APP --> FL_TRACE
    FL_DB --> DB_SESSION
    FL_HEALTH -.->|"future"| DB_MODELS

    FA_MAIN -.->|"reference only"| FA_ALL
    COMMON_AUDIT --> DB_MODELS

    style FL_APP fill:#27ae60,color:#fff
    style FL_AUTH fill:#27ae60,color:#fff
    style FL_DB fill:#27ae60,color:#fff
    style FL_VAL fill:#27ae60,color:#fff
    style FL_CONFIG fill:#27ae60,color:#fff
    style FL_HEALTH fill:#27ae60,color:#fff
    style FA_MAIN fill:#95a5a6,color:#fff
    style FA_ALL fill:#95a5a6,color:#fff
```

---

## 2. App Factory Sequence Diagram

```mermaid
sequenceDiagram
    participant Caller as Caller (gunicorn / test)
    participant Factory as create_app()
    participant Config as AppConfig
    participant Flask as APIFlask
    participant CORS as flask_cors.CORS
    participant DB as init_db()
    participant Trace as setup_tracing()
    participant Auth as register_auth()
    participant BP as Blueprint Registration

    Caller->>Factory: create_app(config?)

    alt config is None
        Factory->>Config: AppConfig() with defaults
        Config-->>Factory: config
    end

    Factory->>Flask: APIFlask(__name__, title, version)
    Flask-->>Factory: app

    Factory->>Factory: app.extensions["config"] = config

    Factory->>CORS: CORS(app, origins, credentials)
    CORS-->>Factory: configured

    Factory->>DB: init_db(app, session_factory)

    alt session_factory provided (test mode)
        DB->>DB: app.extensions["db"] = session_factory
    else session_factory is None (production)
        DB->>DB: from skillhub_db.session import SessionLocal
        DB->>DB: scoped_session(SessionLocal)
        DB->>DB: app.extensions["db"] = scoped_session
    end

    DB->>DB: Register @app.teardown_appcontext
    DB-->>Factory: db_session

    Factory->>Trace: setup_tracing(settings)

    alt otel_traces_enabled
        Trace->>Trace: Configure TracerProvider + OTLP exporter
        Trace->>Trace: FlaskInstrumentor.instrument_app(app)
    else disabled
        Trace->>Trace: NoOp tracer (log "tracing disabled")
    end

    Trace-->>Factory: configured

    Factory->>Auth: register_auth(app)
    Auth->>Auth: Register @app.before_request
    Auth-->>Factory: configured

    Factory->>BP: app.register_blueprint(health_bp)
    BP-->>Factory: registered

    Factory-->>Caller: app (APIFlask)
```

---

## 3. Authentication Flow — `before_request` Hook

```mermaid
flowchart TD
    REQ[Incoming Request] --> BR["@app.before_request<br/>authenticate_request()"]

    BR --> IS_PUBLIC{endpoint in<br/>PUBLIC_ENDPOINTS?}

    IS_PUBLIC -->|Yes| PASS_PUBLIC[Return None<br/>Request proceeds]

    IS_PUBLIC -->|No| IS_OPTIONS{method == OPTIONS?}

    IS_OPTIONS -->|Yes| PASS_CORS[Return None<br/>CORS preflight]

    IS_OPTIONS -->|No| HAS_HEADER{Authorization<br/>header present?}

    HAS_HEADER -->|No| REJECT_401A["401: Missing or<br/>invalid token"]

    HAS_HEADER -->|Yes| HAS_BEARER{Starts with<br/>'Bearer '?}

    HAS_BEARER -->|No| REJECT_401B["401: Missing or<br/>invalid token"]

    HAS_BEARER -->|Yes| DECODE["jwt.decode(token,<br/>secret, algorithms)"]

    DECODE -->|ExpiredSignatureError| REJECT_401C["401: Token expired"]
    DECODE -->|InvalidTokenError| REJECT_401D["401: Invalid token"]
    DECODE -->|Success| SET_G["g.current_user = payload"]

    SET_G --> PASS_AUTH[Return None<br/>Request proceeds]

    PASS_PUBLIC --> ROUTE[Route handler executes]
    PASS_CORS --> ROUTE
    PASS_AUTH --> ROUTE

    style REJECT_401A fill:#e74c3c,color:#fff
    style REJECT_401B fill:#e74c3c,color:#fff
    style REJECT_401C fill:#e74c3c,color:#fff
    style REJECT_401D fill:#e74c3c,color:#fff
    style PASS_PUBLIC fill:#27ae60,color:#fff
    style PASS_CORS fill:#27ae60,color:#fff
    style PASS_AUTH fill:#27ae60,color:#fff
```

### PUBLIC_ENDPOINTS Registry

```mermaid
graph LR
    subgraph "PUBLIC_ENDPOINTS (frozenset)"
        E1["health.health_check"]
        E2["openapi.spec"]
        E3["static"]
    end

    subgraph "Authenticated by Default"
        A1["All blueprint routes"]
        A2["All app-level routes"]
        A3["Future: skills, submissions, etc."]
    end

    style E1 fill:#27ae60,color:#fff
    style E2 fill:#27ae60,color:#fff
    style E3 fill:#27ae60,color:#fff
    style A1 fill:#e67e22,color:#fff
    style A2 fill:#e67e22,color:#fff
    style A3 fill:#e67e22,color:#fff
```

---

## 4. Database Session Lifecycle

```mermaid
sequenceDiagram
    participant Client as HTTP Client
    participant Flask as Flask App
    participant Auth as before_request
    participant Route as Route Handler
    participant Service as Service Function
    participant Session as scoped_session
    participant TD as teardown_appcontext

    Client->>Flask: GET /api/skills

    Flask->>Auth: before_request()
    Auth->>Auth: Decode JWT, set g.current_user
    Auth-->>Flask: None (proceed)

    Flask->>Route: route_handler()
    Route->>Session: app.extensions["db"]()
    Note over Session: scoped_session returns<br/>thread-local Session
    Session-->>Route: db (Session)

    Route->>Service: some_service(db, ...)
    Service->>Session: db.query(...) / db.add(...)
    Service->>Session: db.commit()
    Service-->>Route: result

    Route-->>Flask: jsonify(response)

    Flask->>TD: teardown_appcontext(exception?)

    alt exception is not None
        TD->>Session: session.rollback()
    end

    TD->>Session: session.remove()
    Note over Session: Session returned to pool

    Flask-->>Client: HTTP Response
```

### Test Mode vs Production Mode

```mermaid
graph TB
    subgraph "Production"
        P_FACTORY["create_app()"] -->|"session_factory=None"| P_INIT["init_db()"]
        P_INIT -->|"import"| P_SL["skillhub_db.session.SessionLocal"]
        P_SL --> P_SCOPED["scoped_session(SessionLocal)"]
        P_SCOPED --> P_EXT["app.extensions['db']"]
    end

    subgraph "Test"
        T_FACTORY["create_app(config)"] -->|"session_factory=mock"| T_INIT["init_db()"]
        T_INIT --> T_MOCK["MagicMock()"]
        T_MOCK --> T_EXT["app.extensions['db']"]
    end

    style P_SL fill:#3498db,color:#fff
    style T_MOCK fill:#e67e22,color:#fff
```

---

## 5. Request Validation Flow

### `validated_query()` Decorator

```mermaid
flowchart TD
    REQ["Incoming Request<br/>GET /skills?page=2&q=flask"] --> RAW["request.args.to_dict(flat=False)<br/>{'page': ['2'], 'q': ['flask']}"]

    RAW --> INSPECT["Inspect model_fields<br/>for each key"]

    INSPECT --> UNWRAP{"Field annotation<br/>is list-like?"}

    UNWRAP -->|"Yes (list[str])"| KEEP["Keep as list<br/>{'divisions': ['a', 'b']}"]
    UNWRAP -->|"No (int, str, etc.)"| SINGLE["Unwrap single element<br/>{'page': '2', 'q': 'flask'}"]

    KEEP --> MERGE[Merge into normalized dict]
    SINGLE --> MERGE

    MERGE --> VALIDATE["model_cls.model_validate(normalized)"]

    VALIDATE -->|ValidationError| ERR["Return jsonify({'detail': errors}), 422"]
    VALIDATE -->|Success| CALL["Call fn(*args, query=params, **kwargs)"]

    style ERR fill:#e74c3c,color:#fff
    style CALL fill:#27ae60,color:#fff
```

### `validated_body()` Decorator

```mermaid
flowchart TD
    REQ["Incoming Request<br/>POST /skills"] --> PARSE["request.get_json(force=True)"]

    PARSE -->|None| EMPTY["Use empty dict {}"]
    PARSE -->|dict| BODY["JSON body dict"]

    EMPTY --> VALIDATE["model_cls.model_validate(data)"]
    BODY --> VALIDATE

    VALIDATE -->|ValidationError| ERR["Return jsonify({'detail': errors}), 422"]
    VALIDATE -->|Success| CALL["Call fn(*args, body=model, **kwargs)"]

    style ERR fill:#e74c3c,color:#fff
    style CALL fill:#27ae60,color:#fff
```

### Error Response Format (FastAPI Parity)

```mermaid
graph LR
    subgraph "422 Response Body"
        direction TB
        D["detail: ["]
        E1["  {"]
        E1A["    type: 'greater_than_equal'"]
        E1B["    loc: ['page']"]
        E1C["    msg: 'Input should be >= 1'"]
        E1D["  },"]
        E2["  ..."]
        D2["]"]
    end
```

---

## 6. File Dependency Graph — Phase 1 Modules

```mermaid
graph TD
    subgraph "skillhub_flask/"
        APP["app.py<br/>create_app()"]
        CONFIG["config.py<br/>AppConfig, Settings"]
        AUTH["auth.py<br/>register_auth()"]
        DB["db.py<br/>init_db()"]
        TRACE["tracing.py<br/>setup_tracing()"]
        VAL["validation.py<br/>validated_query()<br/>validated_body()"]
        HEALTH["blueprints/health.py<br/>GET /health"]
    end

    subgraph "libs/"
        DB_SESSION["libs/db<br/>skillhub_db.session"]
        DB_MODELS["libs/db<br/>skillhub_db.models"]
        AUDIT["libs/python-common<br/>skillhub_common.audit"]
    end

    subgraph "External"
        APIFLASK["apiflask"]
        FLASK_CORS["flask_cors"]
        PYJWT["PyJWT"]
        PYDANTIC["pydantic v2"]
        OTEL["opentelemetry"]
    end

    APP --> CONFIG
    APP --> DB
    APP --> AUTH
    APP --> TRACE
    APP --> HEALTH
    APP --> APIFLASK
    APP --> FLASK_CORS

    AUTH --> PYJWT
    AUTH --> CONFIG

    DB --> DB_SESSION

    TRACE --> OTEL

    VAL --> PYDANTIC

    HEALTH --> CONFIG

    AUDIT --> DB_MODELS

    style APP fill:#2ecc71,color:#fff
    style CONFIG fill:#3498db,color:#fff
    style AUTH fill:#e67e22,color:#fff
    style DB fill:#9b59b6,color:#fff
    style TRACE fill:#1abc9c,color:#fff
    style VAL fill:#e74c3c,color:#fff
    style HEALTH fill:#f1c40f,color:#000
```

---

## 7. Prompt Execution Dependency Graph

```mermaid
graph TD
    P1["Prompt 1<br/>Rename apps/api → apps/fast-api<br/>⏱ 5-10 min"]
    P2["Prompt 2<br/>Scaffold Flask directory<br/>⏱ 10 min"]
    P3["Prompt 3<br/>App factory + config + db + tracing<br/>⏱ 30-40 min"]
    P4["Prompt 4<br/>before_request auth<br/>⏱ 30-40 min"]
    P5["Prompt 5<br/>Health blueprint<br/>⏱ 10-15 min"]
    P6["Prompt 6<br/>Validation helpers<br/>⏱ 30-40 min"]
    P7["Prompt 7<br/>Test infrastructure (conftest)<br/>⏱ 20-30 min"]
    P8["Prompt 8<br/>Extract audit_log_append<br/>⏱ 15-20 min"]

    P1 --> P2
    P2 --> P3
    P3 --> P4
    P3 --> P5
    P3 --> P6
    P4 --> P7
    P5 --> P7
    P6 --> P7

    P1 --> P8

    style P1 fill:#3498db,color:#fff
    style P2 fill:#3498db,color:#fff
    style P3 fill:#e74c3c,color:#fff
    style P4 fill:#e67e22,color:#fff
    style P5 fill:#27ae60,color:#fff
    style P6 fill:#e67e22,color:#fff
    style P7 fill:#9b59b6,color:#fff
    style P8 fill:#1abc9c,color:#fff
```

**Legend:**
- Blue: Setup / scaffolding
- Red: Core infrastructure (longest prompt)
- Orange: Medium complexity
- Green: Simple implementation
- Purple: Integration / verification
- Teal: Independent extraction

---

## 8. FastAPI-to-Flask Concept Mapping

```mermaid
graph LR
    subgraph "FastAPI Concepts"
        FA1["FastAPI()"]
        FA2["Depends(get_current_user)"]
        FA3["Depends(get_db)"]
        FA4["dependency_overrides"]
        FA5["APIRouter"]
        FA6["HTTPException(status_code=...)"]
        FA7["request.app.state.settings"]
        FA8["app.openapi()"]
        FA9["TestClient(app)"]
    end

    subgraph "Flask Equivalents"
        FL1["APIFlask()"]
        FL2["before_request + g.current_user"]
        FL3["app.extensions['db']"]
        FL4["AppConfig(session_factory=...)"]
        FL5["Blueprint"]
        FL6["jsonify({...}), status_code"]
        FL7["current_app.extensions['config']"]
        FL8["app.spec"]
        FL9["app.test_client()"]
    end

    FA1 -.-> FL1
    FA2 -.-> FL2
    FA3 -.-> FL3
    FA4 -.-> FL4
    FA5 -.-> FL5
    FA6 -.-> FL6
    FA7 -.-> FL7
    FA8 -.-> FL8
    FA9 -.-> FL9
```

---

## 9. Security Model — Fail-Closed vs Fail-Open

### FastAPI (Fail-Open — Current)

```mermaid
flowchart TD
    NEW["Developer adds new route"] --> FORGOT{"Remembered to add<br/>@Depends(get_current_user)?"}
    FORGOT -->|"Yes"| SAFE["Route is protected ✓"]
    FORGOT -->|"No (human error)"| EXPOSED["Route is PUBLIC ✗<br/>Silent security hole"]

    style EXPOSED fill:#e74c3c,color:#fff
    style SAFE fill:#27ae60,color:#fff
```

### Flask (Fail-Closed — Phase 1)

```mermaid
flowchart TD
    NEW["Developer adds new route"] --> HOOK["before_request fires<br/>automatically"]
    HOOK --> IN_PUBLIC{"endpoint in<br/>PUBLIC_ENDPOINTS?"}
    IN_PUBLIC -->|"Yes (explicitly added)"| PUBLIC["Route is public<br/>(intentional)"]
    IN_PUBLIC -->|"No (default)"| PROTECTED["Route requires JWT ✓<br/>Auth enforced automatically"]

    style PROTECTED fill:#27ae60,color:#fff
    style PUBLIC fill:#3498db,color:#fff
```

---

## 10. Migration Timeline — Phase 1 in Context

```mermaid
gantt
    title SkillHub Migration — Phase 1 Detail
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d

    section Phase 1 - Flask Skeleton
    Prompt 1 - Rename apps/api         :p1, 2026-03-24, 1d
    Prompt 2 - Scaffold Flask           :p2, after p1, 1d
    Prompt 3 - App Factory              :p3, after p2, 1d
    Prompt 4 - Auth Hook                :p4, after p3, 1d
    Prompt 5 - Health Blueprint         :p5, after p3, 1d
    Prompt 6 - Validation Helpers       :p6, after p3, 1d
    Prompt 7 - Test Infrastructure      :p7, after p4, 1d
    Prompt 8 - Audit Extract            :p8, after p1, 1d
    Phase 1 Verification                :milestone, after p7, 0d

    section Phase 2 - Service Port (Future)
    Port service layer                  :p2start, after p7, 5d

    section Phase 3 - Route Port (Future)
    Port all routes                     :p3start, after p2start, 7d
```
