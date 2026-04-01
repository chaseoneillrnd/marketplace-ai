# SkillHub — Visual Architecture Companion

Reference diagrams for the technical implementation guide.
Each section number corresponds to guide references (e.g. "See Section 2").

---

## 1. System & Project Structure

### 1.1 System Context (C4)

```mermaid
C4Context
    title SkillHub — System Context

    Person(employee, "Org Employee", "Any division, any role. Browses and installs skills.")
    Person(developer, "Developer", "Uses Claude Code. Installs via CLI or MCP.")
    Person(platform, "Platform Team", "Reviews submissions. Manages skill quality.")
    Person(security, "Security Team", "Runs Gate 2 scan. Can emergency-remove skills.")

    System(skillhub, "SkillHub", "Internal AI skills marketplace — web, API, MCP server")

    System_Ext(claude_code, "Claude Code", "AI coding tool with MCP support")
    System_Ext(claude_desktop, "Claude Desktop", "AI assistant with MCP config")
    System_Ext(oauth, "OAuth Provider", "Microsoft / Google / Okta / GitHub / OIDC")
    System_Ext(bedrock, "AWS Bedrock", "Claude 3.5 Sonnet — LLM judge for Gate 2")

    Rel(employee, skillhub, "Browse, install, review, submit")
    Rel(developer, claude_code, "claude skill install <slug>")
    Rel(claude_code, skillhub, "MCP tool calls → install_skill, search_skills")
    Rel(claude_desktop, skillhub, "MCP tool calls")
    Rel(employee, oauth, "SSO login")
    Rel(skillhub, oauth, "Token validation and claim extraction")
    Rel(skillhub, bedrock, "Gate 2 LLM evaluation (feature-flagged)")
    Rel(platform, skillhub, "Review queue, featured management")
    Rel(security, skillhub, "Gate 2 manual review, emergency removal")
```

### 1.2 Container Diagram (C4)

```mermaid
C4Container
    title SkillHub — Containers

    Person(user, "User / Developer")

    Container(web, "Web SPA", "React 18 + Vite + TypeScript", "All UI views. No direct DB access.")
    Container(api, "API", "Flask/APIFlask + Python 3.12 + gunicorn", "All business logic, auth, data.")
    Container(mcp, "MCP Server", "Python + mcp SDK", "Exposes 9 MCP tools. Delegates to API.")
    ContainerDb(pg, "PostgreSQL 16", "Primary datastore", "15 tables. Alembic migrations.")

    Rel(user, web, "HTTPS", "Browser")
    Rel(user, mcp, "MCP Protocol", "Claude Code / Desktop")
    Rel(web, api, "HTTPS REST", "/api/v1/*")
    Rel(mcp, api, "HTTP", "Internal REST — never direct DB")
    Rel(api, pg, "SQLAlchemy ORM", "Port 5432")
```

### 1.3 NX Project Dependency Graph

```mermaid
flowchart TB
    subgraph apps
        web["apps/web\nReact + Vite + TS"]
        api["apps/api\nFlask/APIFlask"]
        mcp["apps/mcp-server\nPython MCP"]
    end
    subgraph libs
        ui["libs/ui\n@skillhub/ui"]
        types["libs/shared-types\n@skillhub/shared-types"]
        pycommon["libs/python-common\nskillhub-common"]
        db["libs/db\nskillhub-db"]
    end

    web --> ui
    web --> types
    api --> db
    api --> pycommon
    mcp --> pycommon
    db --> pycommon

    style apps fill:#0c1825,stroke:#1e3248,color:#ddeaf7
    style libs fill:#07111f,stroke:#152030,color:#517898
```

---

## 2. Data Models

### 2.1 Identity Domain ERD

```mermaid
erDiagram
    users {
        uuid id PK
        varchar email UK
        varchar username UK
        varchar name
        varchar division FK
        varchar role
        varchar oauth_provider
        varchar oauth_sub
        boolean is_platform_team
        boolean is_security_team
        boolean is_active
        timestamptz created_at
        timestamptz last_login_at
    }
    divisions {
        varchar slug PK
        varchar name
        varchar color
    }
    oauth_sessions {
        uuid id PK
        uuid user_id FK
        varchar provider
        text access_token_hash
        timestamptz expires_at
        timestamptz created_at
    }
    users }o--|| divisions : "belongs to"
    users ||--o{ oauth_sessions : "has sessions"
```

### 2.2 Skill Core ERD

```mermaid
erDiagram
    skills {
        uuid id PK
        varchar slug UK
        varchar name
        varchar short_desc
        varchar category FK
        uuid author_id FK
        enum author_type
        varchar current_version
        enum install_method
        enum data_sensitivity
        boolean external_calls
        boolean verified
        boolean featured
        int featured_order
        enum status
        int install_count
        int fork_count
        int favorite_count
        int view_count
        int review_count
        numeric avg_rating
        numeric trending_score
        timestamptz published_at
    }
    skill_versions {
        uuid id PK
        uuid skill_id FK
        varchar version
        text content
        jsonb frontmatter
        text changelog
        varchar content_hash
        timestamptz published_at
    }
    skill_divisions {
        uuid skill_id FK
        varchar division_slug FK
    }
    skill_tags {
        uuid skill_id FK
        varchar tag
    }
    trigger_phrases {
        uuid id PK
        uuid skill_id FK
        varchar phrase
    }
    categories {
        varchar slug PK
        varchar name
        int sort_order
    }
    skills ||--o{ skill_versions : "versioned by"
    skills ||--o{ skill_divisions : "authorized for"
    skills ||--o{ skill_tags : "tagged with"
    skills ||--o{ trigger_phrases : "triggered by"
    skills }o--|| categories : "belongs to"
```

### 2.3 Social Domain ERD

```mermaid
erDiagram
    installs {
        uuid id PK
        uuid skill_id FK
        uuid user_id FK
        varchar version
        enum method
        timestamptz installed_at
        timestamptz uninstalled_at
    }
    forks {
        uuid id PK
        uuid original_skill_id FK
        uuid forked_skill_id FK
        uuid forked_by FK
        varchar upstream_version_at_fork
    }
    favorites {
        uuid user_id FK
        uuid skill_id FK
        timestamptz created_at
    }
    follows {
        uuid follower_id FK
        uuid followed_user_id FK
        timestamptz created_at
    }
    reviews {
        uuid id PK
        uuid skill_id FK
        uuid user_id FK
        smallint rating
        text body
        int helpful_count
        int unhelpful_count
    }
    review_votes {
        uuid review_id FK
        uuid user_id FK
        enum vote
    }
    comments {
        uuid id PK
        uuid skill_id FK
        uuid user_id FK
        text body
        int upvote_count
        timestamptz deleted_at
    }
    replies {
        uuid id PK
        uuid comment_id FK
        uuid user_id FK
        text body
        timestamptz deleted_at
    }
    skills ||--o{ installs : "installed via"
    skills ||--o{ forks : "forked as"
    skills ||--o{ favorites : "favorited by"
    skills ||--o{ reviews : "reviewed in"
    skills ||--o{ comments : "discussed in"
    reviews ||--o{ review_votes : "voted on"
    comments ||--o{ replies : "has replies"
```

### 2.4 Submission Domain ERD

```mermaid
erDiagram
    submissions {
        uuid id PK
        varchar display_id UK
        uuid submitted_by FK
        varchar name
        varchar category
        text content
        jsonb declared_divisions
        text division_justification
        enum status
        timestamptz submitted_at
    }
    submission_gate_results {
        uuid id PK
        uuid submission_id FK
        smallint gate
        enum result
        jsonb findings
        numeric score
        uuid reviewer_id FK
        timestamptz completed_at
    }
    division_access_requests {
        uuid id PK
        uuid skill_id FK
        uuid requested_by FK
        varchar user_division
        text reason
        enum status
    }
    submissions ||--o{ submission_gate_results : "evaluated by"
```

### 2.5 Platform Domain ERD

```mermaid
erDiagram
    feature_flags {
        varchar key PK
        boolean enabled
        text description
        jsonb division_overrides
        timestamptz updated_at
    }
    audit_log {
        uuid id PK
        varchar event_type
        uuid actor_id FK
        varchar target_type
        uuid target_id
        jsonb metadata
        inet ip_address
        timestamptz created_at
    }
```

---

## 3. Sequence Diagrams

### 3.1 Stub Auth Flow (Development)

```mermaid
sequenceDiagram
    participant SPA as React SPA
    participant API as Flask API /auth
    participant JWT as JWT Library

    SPA->>API: POST /auth/token\n{username: test, password: user}
    API->>API: check STUB_AUTH_ENABLED=true
    API->>API: validate credentials vs STUB_CREDENTIALS
    API->>JWT: encode(STUB_USER + exp)
    JWT-->>API: signed JWT
    API-->>SPA: {access_token, token_type, expires_in, user}
    SPA->>SPA: store token in memory
    SPA->>SPA: decode claims → set auth state
    Note over SPA: All subsequent requests include\nAuthorization: Bearer {token}
```

### 3.2 Production OAuth Flow

```mermaid
sequenceDiagram
    participant Browser as Browser
    participant SPA as React SPA
    participant API as Flask API /auth
    participant Provider as OAuth Provider
    participant DB as PostgreSQL

    SPA->>API: GET /auth/oauth/microsoft
    API-->>SPA: {redirect_url, state}
    SPA->>Browser: redirect to provider
    Browser->>Provider: login + consent
    Provider->>Browser: redirect to /auth/oauth/microsoft/callback?code=...&state=...
    Browser->>API: GET /auth/oauth/microsoft/callback
    API->>Provider: POST token exchange (code → access_token)
    Provider-->>API: access_token + id_token
    API->>Provider: GET userinfo (email, name, division claim)
    Provider-->>API: user profile
    API->>DB: UPSERT users ON CONFLICT(email) DO UPDATE
    DB-->>API: user row
    API->>API: encode SkillHub JWT with user claims
    API-->>SPA: {access_token, user}
```

### 3.3 MCP Skill Install

```mermaid
sequenceDiagram
    participant CC as Claude Code CLI
    participant MCP as MCP Server :8001
    participant API as Flask API :8000
    participant DB as PostgreSQL
    participant FS as ~/.local/share/claude/skills/

    CC->>MCP: install_skill("pr-review-assistant")
    MCP->>API: GET /api/v1/skills/pr-review-assistant/versions/latest\nAuthorization: Bearer {JWT}
    API->>DB: SELECT skill + latest version content
    DB-->>API: SkillVersion {content, frontmatter, version}
    API-->>MCP: SkillVersionResponse
    MCP->>MCP: check user.division in skill.divisions
    alt Division authorized
        MCP->>FS: write pr-review-assistant/SKILL.md
        MCP->>API: POST /api/v1/skills/pr-review-assistant/install\n{method: "mcp", version: "2.3.1"}
        API->>DB: INSERT installs + UPDATE install_count
        API->>DB: INSERT audit_log {event: skill.installed}
        MCP-->>CC: {success: true, version: "2.3.1", path: "..."}
    else Division not authorized
        MCP-->>CC: {success: false, error: "division_restricted"}
    end
```

---

## 4. Submission State Machine

```mermaid
stateDiagram-v2
    direction TB
    [*] --> submitted: POST /submissions

    submitted --> gate1_running: Gate 1 starts (sync)
    gate1_running --> gate1_passed: Schema valid
    gate1_running --> gate1_failed: Schema invalid

    gate1_passed --> gate2_running: Gate 2 triggered (async)
    gate2_running --> gate2_passed: score≥70, no critical
    gate2_running --> gate2_flagged: score≥70, has findings
    gate2_running --> gate2_failed: score<70 or critical

    gate2_passed --> gate3_pending: Enters review queue
    gate2_flagged --> gate3_pending: Enters with findings

    gate3_pending --> gate3_changes_requested: Reviewer requests changes
    gate3_pending --> gate3_approved: Reviewer approves
    gate3_pending --> rejected: Reviewer rejects

    gate3_changes_requested --> submitted: Submitter resubmits

    gate3_approved --> published: Skill created
    gate1_failed --> [*]
    gate2_failed --> [*]
    rejected --> [*]
    published --> [*]
```

---

## 5. LLM Judge Flow

```mermaid
flowchart TD
    A[Gate 1 passes] --> B{llm_judge_enabled\nfeature flag?}
    B -- false --> C[Return: pass=true, score=85, skipped]
    B -- true --> D{LLM_ROUTER_URL\nconfigured?}
    D -- false --> C
    D -- true --> E[Build judge prompt\nsystem + skill content]
    E --> F[POST /v1/chat/completions\nto LiteLLM router]
    F --> G[LiteLLM → AWS Bedrock\nClaude 3.5 Sonnet]
    G --> H{HTTP success?}
    H -- timeout/error --> I[Return: pass=false, score=0\njudge_unavailable finding]
    H -- 200 --> J[Parse JSON verdict]
    J --> K{Any CRITICAL\nfinding?}
    K -- yes --> L[gate2_failed]
    K -- no --> M{score >= 70?}
    M -- no --> L
    M -- yes --> N{Any findings?}
    N -- yes --> O[gate2_flagged\nEnters Gate 3 with flags]
    N -- no --> P[gate2_passed]

    style L fill:#2a0a0d,stroke:#ef5060,color:#ef5060
    style O fill:#2a1a00,stroke:#f2a020,color:#f2a020
    style P fill:#0a2a1a,stroke:#1fd49e,color:#1fd49e
```

---

## 6. CI/CD Pipeline

```mermaid
flowchart LR
    subgraph trigger[Trigger]
        push[git push]
        mr[Merge Request]
    end

    subgraph lint[Stage: lint]
        l1[lint:python\nruff check + format]
        l2[lint:typescript\neslint + prettier]
    end

    subgraph test[Stage: test]
        t1[test:api\npytest ≥80% cov]
        t2[test:web\nVitest ≥80% cov]
        t3[test:mcp\npytest]
        t4[test:migrations\nalembic check]
        t5[typecheck:api\nmypy --strict]
        t6[typecheck:web\ntsc --noEmit]
    end

    subgraph build[Stage: build]
        b1[build:web\nnpx nx build web]
        b2[build:docker\ndocker compose build]
    end

    subgraph security[Stage: security]
        s1[SAST\nGitLab template]
        s2[openapi:freshness\nspec matches routes]
    end

    subgraph deploy[Stage: deploy]
        d1[deploy:staging\nauto on main]
        d2[deploy:production\nmanual trigger]
    end

    push --> lint
    mr --> lint
    lint --> test
    test --> build
    build --> security
    security --> deploy

    style lint fill:#07111f,stroke:#1e3248
    style test fill:#07111f,stroke:#1e3248
    style build fill:#07111f,stroke:#1e3248
    style security fill:#07111f,stroke:#1e3248
    style deploy fill:#07111f,stroke:#1e3248
```

---

## Quick Reference: All Diagrams

| Section | Diagram | Type | Used By Prompt |
|---------|---------|------|----------------|
| 1.1 | System Context | C4 Context | 0.1.1 |
| 1.2 | Container Diagram | C4 Container | 0.1.2 |
| 1.3 | NX Project Graph | Flowchart | 0.1.2 |
| 2.1 | Identity Domain ERD | ER Diagram | 1.1.1 |
| 2.2 | Skill Core ERD | ER Diagram | 1.1.2 |
| 2.3 | Social Domain ERD | ER Diagram | 1.1.3 |
| 2.4 | Submission Domain ERD | ER Diagram | 6.1.1 |
| 2.5 | Platform Domain ERD | ER Diagram | 9.1.1 |
| 3.1 | Stub Auth Flow | Sequence | 2.2.1 |
| 3.2 | Production OAuth Flow | Sequence | 4.1.1 |
| 3.3 | MCP Skill Install | Sequence | 7.1.1 |
| 4.0 | Submission State Machine | State | 6.1.1 |
| 5.0 | LLM Judge Flow | Flowchart | 6.1.2 |
| 6.0 | CI/CD Pipeline | Flowchart | 0.2.3 |
