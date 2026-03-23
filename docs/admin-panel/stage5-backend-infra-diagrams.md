# Stage 5: Backend Infrastructure — Visual Architecture Companion

This file is the diagram companion to `stage5-backend-infra-guide.md`.
All diagrams use Mermaid syntax and are renderable in GitHub, GitLab, and most Markdown viewers.

---

## Diagram 1 — Full Data Pipeline Overview

End-to-end view from user action to admin dashboard read, showing every component introduced in Stage 5.

```mermaid
flowchart TD
    subgraph users["User Actions (any hour)"]
        UA[Install / Fork / Submit / Review]
    end

    subgraph api["FastAPI API  :8000"]
        EP[Existing endpoints\nskills / installs / submissions]
        ALog[(audit_log\nappend-only)]
        EP -->|writes| ALog
    end

    subgraph pg["PostgreSQL 16  :5432"]
        T_installs[(installs)]
        T_submissions[(submissions)]
        T_users[(users)]
        T_audit[(audit_log)]
        T_metrics[(daily_metrics\nPK: date + division_slug)]
        T_exports[(export_jobs)]
    end

    subgraph redis["Redis 7  :6379"]
        R_summary["analytics:summary:{div}  TTL 5 min"]
        R_ts["analytics:timeseries:{div}:{days}  TTL 1 hr"]
        R_funnel["analytics:funnel:{div}:{days}  TTL 2 hr"]
        R_top["analytics:top_skills:{n}  TTL 30 min"]
        ARQ_queue[("ARQ job queue")]
    end

    subgraph worker["ARQ Worker  (arq-worker container)"]
        CRON1["02:00 UTC\naggregate_daily_metrics"]
        CRON2["02:30 UTC\nrecalculate_trending"]
        CRON3["03:00 UTC\nclean_expired_exports"]
        JOB1["generate_export\n(enqueued on demand)"]
    end

    subgraph analytics_api["Analytics Router  /api/v1/admin/analytics"]
        A_sum[GET /summary]
        A_ts[GET /time-series]
        A_fun[GET /submission-funnel]
        A_top[GET /top-skills]
    end

    subgraph export_api["Exports Router  /api/v1/admin/exports"]
        E_post[POST /exports]
        E_get[GET /exports/{id}]
        E_dl[GET /exports/{id}/download]
    end

    subgraph exports_fs["export-staging volume  /exports"]
        CSV["{job_id}.csv"]
        JSON["{job_id}.json"]
    end

    UA -->|HTTP| EP
    EP -->|INSERT| T_installs
    EP -->|INSERT| T_submissions
    EP -->|INSERT| T_users
    EP -->|INSERT| T_audit

    CRON1 -->|SELECT| T_installs
    CRON1 -->|SELECT| T_submissions
    CRON1 -->|SELECT| T_users
    CRON1 -->|SELECT| T_audit
    CRON1 -->|UPSERT| T_metrics
    CRON1 -->|DEL analytics:summary:*| redis

    CRON2 -->|UPDATE skills.trending_score| pg
    CRON2 -->|DEL analytics:top_skills:*| redis

    CRON3 -->|rm old files| exports_fs

    JOB1 -->|SELECT| pg
    JOB1 -->|write file| exports_fs
    JOB1 -->|UPDATE status| T_exports

    A_sum -->|GET| R_summary
    A_sum -.->|cache miss: SELECT| T_metrics
    A_ts -->|GET| R_ts
    A_ts -.->|cache miss: SELECT| T_metrics
    A_fun -->|GET| R_funnel
    A_fun -.->|cache miss: SELECT| T_metrics
    A_top -->|SELECT| pg

    E_post -->|INSERT| T_exports
    E_post -->|ENQUEUE| ARQ_queue
    ARQ_queue -->|dequeue| JOB1
    E_get -->|SELECT| T_exports
    E_dl -->|read| exports_fs
```

---

## Diagram 2 — Nightly Aggregation Sequence

Detailed sequence for the 02:00 UTC `aggregate_daily_metrics` job.

```mermaid
sequenceDiagram
    participant Scheduler as ARQ Scheduler
    participant Job as aggregate_daily_metrics
    participant DB as PostgreSQL
    participant Redis as Redis

    Scheduler->>Job: trigger at 02:00 UTC
    activate Job

    Job->>DB: SELECT slug FROM divisions
    DB-->>Job: ["eng", "sales", "ops", ...]

    loop For each division slug
        Job->>DB: SELECT COUNT installs WHERE division=slug AND date=yesterday
        Job->>DB: SELECT COUNT active installs WHERE division=slug
        Job->>DB: SELECT COUNT uninstalls WHERE division=slug AND date=yesterday
        Job->>DB: SELECT COUNT users WHERE division=slug AND date=yesterday
        Job->>DB: SELECT COUNT submissions WHERE division=slug AND date=yesterday
        Job->>DB: SELECT COUNT DISTINCT actor_id FROM audit_log WHERE division=slug AND date=yesterday
        Job->>DB: SELECT status, COUNT FROM submissions WHERE division=slug AND date=yesterday
        Job->>DB: INSERT INTO daily_metrics ON CONFLICT DO UPDATE
    end

    Note over Job,DB: Platform-wide '__all__' row

    Job->>DB: SELECT COUNT installs WHERE date=yesterday (all divisions)
    Job->>DB: SELECT COUNT DISTINCT actor_id FROM audit_log WHERE date=yesterday (no division filter)
    Job->>DB: PERCENTILE_CONT(0.5) gate3 wait time
    Job->>DB: INSERT INTO daily_metrics ('__all__') ON CONFLICT DO UPDATE

    Job->>DB: COMMIT

    Job->>Redis: DEL analytics:summary:*
    Redis-->>Job: N keys deleted

    deactivate Job
    Job-->>Scheduler: "aggregated N rows for YYYY-MM-DD"
```

---

## Diagram 3 — Analytics API Cache Flow

Shows the exact decision path for a GET /summary request, illustrating the "read-only cache path" principle.

```mermaid
flowchart TD
    REQ[GET /api/v1/admin/analytics/summary\n?division=__all__]
    AUTH{require_platform_team\npasses?}
    REDIS_GET[Redis GET\nanalytics:summary:__all__]
    CACHE_HIT{cache hit?}
    DB_QUERY[get_summary\nSELECT daily_metrics\nWHERE division_slug='__all__'\nAND metric_date = yesterday]
    RETURN_CACHED[Return cached JSON\n200 OK]
    RETURN_LIVE[Return live DB result\n200 OK]
    NO_WRITE["No cache write here.\nNext write: nightly cron\nat 02:00 UTC"]

    REQ --> AUTH
    AUTH -->|403| FORBIDDEN[403 Forbidden]
    AUTH -->|OK| REDIS_GET
    REDIS_GET --> CACHE_HIT
    CACHE_HIT -->|yes| RETURN_CACHED
    CACHE_HIT -->|no| DB_QUERY
    DB_QUERY --> RETURN_LIVE
    RETURN_LIVE --> NO_WRITE

    style NO_WRITE fill:#fff3cd,stroke:#ffc107,color:#333
    style RETURN_CACHED fill:#d4edda,stroke:#28a745,color:#333
    style RETURN_LIVE fill:#d1ecf1,stroke:#17a2b8,color:#333
```

---

## Diagram 4 — daily_metrics Table Schema

Entity-relationship style view of the new tables and their relationships to existing tables.

```mermaid
erDiagram
    DIVISIONS {
        string slug PK
        string name
        string color
    }

    USERS {
        uuid id PK
        string email
        string username
        string division FK
        string role
        bool is_platform_team
        bool is_security_team
        json admin_scopes
        datetime last_login_at
        datetime created_at
    }

    INSTALLS {
        uuid id PK
        uuid skill_id FK
        uuid user_id FK
        string version
        string method
        datetime installed_at
        datetime uninstalled_at
    }

    SUBMISSIONS {
        uuid id PK
        string display_id
        uuid submitted_by FK
        string status
        datetime created_at
    }

    AUDIT_LOG {
        uuid id PK
        string event_type
        uuid actor_id
        datetime created_at
    }

    DAILY_METRICS {
        date metric_date PK
        string division_slug PK
        int new_installs
        int active_installs
        int uninstalls
        int dau
        int new_users
        int new_submissions
        int published_skills
        int new_reviews
        int funnel_submitted
        int funnel_g1_pass
        int funnel_g2_pass
        int funnel_approved
        int funnel_published
        bigint gate3_median_wait
        datetime computed_at
    }

    EXPORT_JOBS {
        uuid id PK
        uuid requested_by FK
        string scope
        string format
        jsonb filters
        string status
        int row_count
        text file_path
        text error
        datetime created_at
        datetime completed_at
    }

    DIVISIONS ||--o{ USERS : "has"
    USERS ||--o{ INSTALLS : "installs"
    USERS ||--o{ SUBMISSIONS : "submits"
    USERS ||--o{ EXPORT_JOBS : "requests"
    INSTALLS }o--|| USERS : "belongs to"
    AUDIT_LOG }o--o| USERS : "actor"
```

Note: `DAILY_METRICS.division_slug` has no FK constraint on `DIVISIONS.slug` — this is intentional to allow the `'__all__'` sentinel without violating referential integrity.

---

## Diagram 5 — ARQ Worker Architecture

Shows the relationship between the API process, the ARQ worker process, and shared infrastructure.

```mermaid
flowchart LR
    subgraph compose["docker-compose network"]
        subgraph api_svc["api container  :8000"]
            FA[FastAPI app]
            ARQ_POOL["app.state.arq\nARQ connection pool"]
            REDIS_POOL["app.state.redis\nRedis pool  max_connections=20"]
            FA --> ARQ_POOL
            FA --> REDIS_POOL
        end

        subgraph worker_svc["arq-worker container"]
            WS[WorkerSettings]
            CRON_AGG["cron: aggregate_daily_metrics\n02:00 UTC"]
            CRON_TREND["cron: recalculate_trending\n02:30 UTC"]
            CRON_CLEAN["cron: clean_expired_exports\n03:00 UTC"]
            FN_EXP["function: generate_export\n(enqueued on demand)"]
            WS --> CRON_AGG
            WS --> CRON_TREND
            WS --> CRON_CLEAN
            WS --> FN_EXP
        end

        PG[(PostgreSQL 16\n:5432)]
        RDS[(Redis 7\n:6379)]

        subgraph vol["export-staging volume"]
            FILES["/exports/*.csv\n/exports/*.json"]
        end

        ARQ_POOL -->|enqueue_job| RDS
        REDIS_POOL -->|GET/SETEX/DEL| RDS
        worker_svc -->|dequeue jobs| RDS
        worker_svc -->|SELECT/UPSERT| PG
        FA -->|SELECT/INSERT| PG
        FN_EXP -->|write| FILES
        FA -->|StreamingResponse| FILES
    end
```

---

## Diagram 6 — Export Job Lifecycle

State machine showing all status transitions for an `ExportJob`.

```mermaid
stateDiagram-v2
    [*] --> queued : POST /admin/exports\n(rate limit OK)

    queued --> running : ARQ worker dequeues\ngenerate_export(job_id)

    running --> completed : File written\nrow_count set\nfile_path set\ncompleted_at set

    running --> failed : Exception caught\nerror message stored\ncompleted_at set

    completed --> [*] : GET /exports/{id}/download\nStreamingResponse

    failed --> [*] : Admin reviews error\nRe-request if needed

    note right of queued
        status = 'queued'
        file_path = NULL
        row_count = NULL
    end note

    note right of completed
        status = 'completed'
        file_path = '/exports/{id}.{fmt}'
        row_count = N
    end note

    note right of failed
        status = 'failed'
        error = exception message
        file_path = NULL
    end note
```

---

## Diagram 7 — Redis Key Taxonomy

```mermaid
mindmap
  root((Redis))
    analytics
      summary
        "analytics:summary:__all__"
          TTL 300s
        "analytics:summary:{division_slug}"
          TTL 300s
      timeseries
        "analytics:timeseries:__all__:{days}"
          TTL 3600s
        "analytics:timeseries:{division}:{days}"
          TTL 3600s
      funnel
        "analytics:funnel:__all__:{days}"
          TTL 7200s
        "analytics:funnel:{division}:{days}"
          TTL 7200s
      top_skills
        "analytics:top_skills:{limit}"
          TTL 1800s
    arq
      "arq:job:{job_id}"
        ARQ managed
      "arq:result:{job_id}"
        ARQ managed
```

**Cache write ownership:**
- `analytics:summary:*` — written by `aggregate_daily_metrics` cron, busted on each run
- `analytics:timeseries:*` — written by `aggregate_daily_metrics` cron
- `analytics:funnel:*` — written by `aggregate_daily_metrics` cron
- `analytics:top_skills:*` — written by `recalculate_trending` cron, busted on each run
- `arq:*` — managed entirely by the ARQ library; do not touch

---

## Diagram 8 — Submission Funnel Visualization

How the five funnel columns in `daily_metrics` map to the submission pipeline states.

```mermaid
flowchart LR
    S1["SUBMITTED\nfunnel_submitted"] -->|Gate 1 LLM| S2["GATE1_PASSED\nfunnel_g1_pass"]
    S1 -->|Gate 1 reject| X1["GATE1_FAILED\n(not counted in funnel)"]
    S2 -->|Gate 2 security| S3["GATE2_PASSED\nfunnel_g2_pass"]
    S2 -->|Gate 2 issues| X2["GATE2_FLAGGED / FAILED\n(not counted)"]
    S3 -->|Gate 3 human review| S4["APPROVED\nfunnel_approved"]
    S3 -->|Changes requested| X3["GATE3_CHANGES_REQUESTED\n(not counted until re-submitted)"]
    S4 -->|Publish| S5["PUBLISHED\nfunnel_published"]
    S4 -->|Rejected| X4["REJECTED\n(not counted)"]

    style S1 fill:#e3f2fd,stroke:#2196f3
    style S2 fill:#e8f5e9,stroke:#4caf50
    style S3 fill:#fff9c4,stroke:#ffc107
    style S4 fill:#f3e5f5,stroke:#9c27b0
    style S5 fill:#e0f2f1,stroke:#009688
    style X1 fill:#ffebee,stroke:#f44336
    style X2 fill:#ffebee,stroke:#f44336
    style X3 fill:#fff3e0,stroke:#ff9800
    style X4 fill:#ffebee,stroke:#f44336
```

Conversion rates returned by `/admin/analytics/submission-funnel`:
- `submitted_to_g1` = funnel_g1_pass / funnel_submitted
- `g1_to_g2` = funnel_g2_pass / funnel_g1_pass
- `g2_to_approved` = funnel_approved / funnel_g2_pass
- `approved_to_published` = funnel_published / funnel_approved
- `end_to_end` = funnel_published / funnel_submitted

---

## Diagram 9 — DAU Calculation Strategy

Why the `'__all__'` row re-derives DAU instead of summing division DAUs.

```mermaid
flowchart TD
    subgraph scenario["Scenario: User Alice in 'eng', takes actions in two contexts"]
        A1["audit_log row 1:\nactor_id=alice\nevent_type=skill.install"]
        A2["audit_log row 2:\nactor_id=alice\nevent_type=submission.create"]
    end

    subgraph wrong["WRONG: Sum division DAUs"]
        W1["DAU eng = 1 (Alice counted)"]
        W2["DAU sales = 0"]
        WSUM["Sum = 1\n(Correct here, but would double-count\nif Alice appeared in multiple divisions)"]
    end

    subgraph right["CORRECT: Re-derive from audit_log"]
        R1["SELECT COUNT DISTINCT actor_id\nFROM audit_log\nWHERE date = target_date\n(no division filter)"]
        R2["DAU __all__ = 1\n(Alice counted exactly once)"]
    end

    scenario --> wrong
    scenario --> right

    style wrong fill:#ffebee,stroke:#f44336
    style right fill:#e8f5e9,stroke:#4caf50
```

The division filter joins `audit_log` to `users` on `actor_id`. A user belongs to exactly one division at any moment in time. However, if division membership changes between events (unlikely but possible), summing division DAUs could overcount. Re-deriving from audit_log is always correct.

---

## Diagram 10 — Connection Pool Layout

Database connection pool topology under steady-state load.

```mermaid
flowchart TD
    subgraph api_process["API process (uvicorn, N workers)"]
        W1[Uvicorn worker 1]
        W2[Uvicorn worker 2]
        WN[Uvicorn worker N...]
    end

    subgraph pool["SQLAlchemy Engine pool\npool_size=10, max_overflow=20\npool_timeout=30s, pool_recycle=1800s\npool_pre_ping=True"]
        P1[Connection 1]
        P2[Connection 2]
        P3[Connection 3 ... 10]
        O1[Overflow 1 ... 20]
    end

    subgraph pg["PostgreSQL 16\nmax_connections=100 (default)"]
        DB[(skillhub DB)]
    end

    W1 -->|checkout| pool
    W2 -->|checkout| pool
    WN -->|checkout| pool

    P1 -->|TCP| DB
    P2 -->|TCP| DB
    P3 -->|TCP| DB
    O1 -.->|burst only| DB

    subgraph worker_process["ARQ worker process"]
        WK[Worker job]
        WK_SESSION["SessionLocal()\nSEPARATE pool instance"]
    end

    WK --> WK_SESSION
    WK_SESSION -->|TCP| DB
```

The ARQ worker process creates its own `create_engine()` instance with the same pool parameters. The two processes share the PostgreSQL server but maintain independent connection pools. PostgreSQL max_connections of 100 easily accommodates api (30 max) + worker (30 max) + headroom.

---

## Diagram 11 — Backfill Script Flow

```mermaid
flowchart TD
    START([mise run db:aggregate:backfill])
    Q1[SELECT MIN installed_at\nFROM installs]
    EMPTY{earliest_dt\nis NULL?}
    SET_RANGE[start_date = earliest.date\nend_date = today - 1]
    LOOP{current <= end_date?}
    AGG[run_daily_aggregation\ndb, current]
    COMMIT[db.commit inside\naggregation function]
    ADVANCE[current += 1 day]
    LOG_ERR[log exception\ncontinue to next day]
    DONE([Backfill complete\nN days processed])

    START --> Q1
    Q1 --> EMPTY
    EMPTY -->|yes| DONE
    EMPTY -->|no| SET_RANGE
    SET_RANGE --> LOOP
    LOOP -->|yes| AGG
    AGG -->|success| COMMIT
    AGG -->|exception| LOG_ERR
    COMMIT --> ADVANCE
    LOG_ERR --> ADVANCE
    ADVANCE --> LOOP
    LOOP -->|no| DONE
```

Each day commits independently. A failure on one day is logged and skipped — the script continues to the next day. Re-running the script is safe because `run_daily_aggregation` is idempotent (INSERT ON CONFLICT DO UPDATE).

---

## Diagram 12 — Docker Compose Service Graph (Post Stage 5)

```mermaid
flowchart TD
    subgraph infra["Infrastructure"]
        PG[(postgres\n:5433)]
        RDS[(redis\n:6379)]
        JAE[jaeger\n:16686 / :4317]
    end

    subgraph apps["Applications"]
        API[api\n:8000]
        WORKER[arq-worker\npython -m skillhub.worker]
        MCP[mcp-server\n:8001]
        WEB[web\n:5173]
    end

    subgraph volumes["Named Volumes"]
        PGDATA[(pgdata)]
        EXPORTS[(export-staging\n/exports)]
    end

    PG -->|healthcheck| API
    PG -->|healthcheck| WORKER
    RDS -->|healthcheck| API
    RDS -->|healthcheck| WORKER
    JAE --> API
    JAE --> WORKER
    JAE --> MCP

    API --> MCP
    API --> WEB

    API --- EXPORTS
    WORKER --- EXPORTS

    PG --- PGDATA

    style WORKER fill:#e8f5e9,stroke:#4caf50
    style EXPORTS fill:#fff9c4,stroke:#ffc107
```

The `arq-worker` service shares the same Docker image as `api` (built from `apps/api/Dockerfile`) but runs a different command. The `export-staging` volume is the only shared filesystem state between the two containers — the API reads export files for download; the worker writes them.
