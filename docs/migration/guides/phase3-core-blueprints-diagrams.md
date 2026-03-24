# Phase 3: Core Domain Blueprints — Architecture Diagrams

**Companion to:** `phase3-core-blueprints-guide.md`
**Purpose:** Visual reference for agents implementing Phase 3 blueprints

---

## Diagram 1: Blueprint Registration Flow

How the app factory discovers and registers all 7 Phase 3 blueprints at startup.

```mermaid
flowchart TD
    A["create_app(config)"] --> B["Create APIFlask instance"]
    B --> C["Register extensions<br/>(db, settings, error handlers)"]
    C --> D["Register auth before_request"]
    D --> E["Register Phase 1/2 blueprints<br/>(health, auth, stub_auth)"]
    E --> F["Register Phase 3 blueprints"]

    F --> G["skills_bp<br/>prefix: /api/v1/skills"]
    F --> H["users_bp<br/>prefix: /api/v1/users"]
    F --> I["social_bp<br/>prefix: /api/v1/skills"]
    F --> J["submissions_bp<br/>(mixed prefixes)"]
    F --> K["flags_bp<br/>prefix: /api/v1"]
    F --> L["feedback_bp<br/>(mixed prefixes)"]
    F --> M["roadmap_bp<br/>(mixed prefixes)"]

    G --> N["app ready"]
    H --> N
    I --> N
    J --> N
    K --> N
    L --> N
    M --> N

    style A fill:#4a9eff,color:#fff
    style N fill:#22c55e,color:#fff
    style F fill:#f59e0b,color:#fff
```

---

## Diagram 2: Request Lifecycle — Authenticated Endpoint

Complete request flow from HTTP request to JSON response for an authenticated endpoint (e.g., POST /api/v1/skills/{slug}/install).

```mermaid
sequenceDiagram
    participant C as FlaskClient
    participant W as WSGI Layer
    participant BR as before_request
    participant PE as PUBLIC_ENDPOINTS
    participant BP as Blueprint Route
    participant V as validated_body()
    participant S as Service Layer
    participant DB as Database
    participant TR as teardown_appcontext

    C->>W: POST /api/v1/skills/my-skill/install<br/>Authorization: Bearer <jwt>
    W->>BR: Dispatch to before_request hook

    BR->>PE: Is "social.post_install" in PUBLIC_ENDPOINTS?
    PE-->>BR: No

    BR->>BR: Decode JWT from Authorization header
    alt JWT valid
        BR->>BR: Store decoded claims in g.current_user
        BR-->>W: Continue to route handler
    else JWT missing/invalid/expired
        BR-->>C: 401 {"detail": "..."}
    end

    W->>BP: Route to social.post_install(slug="my-skill")
    BP->>V: @validated_body(InstallRequest)
    V->>V: Parse request.get_json()
    alt Validation passes
        V-->>BP: body=InstallRequest(method="cli", version="1.0")
    else Validation fails
        V-->>C: 422 {"detail": [...errors...]}
    end

    BP->>BP: user_id = UUID(g.current_user["user_id"])
    BP->>BP: db = get_db()
    BP->>S: install_skill(db, slug, user_id, division, method, version)
    S->>DB: Query Skill, check divisions, insert Install
    S->>DB: db.commit()
    DB-->>S: Return result dict

    alt Success
        S-->>BP: result dict
        BP->>BP: InstallResponse(**result).model_dump(mode="json")
        BP-->>C: 201 {"skill_id": "...", "method": "cli", ...}
    else ValueError (not found)
        S-->>BP: raise ValueError
        BP-->>C: 404 {"detail": "Skill not found"}
    else PermissionError (division)
        S-->>BP: raise PermissionError
        BP-->>C: 403 {"detail": {"error": "division_restricted"}}
    end

    W->>TR: teardown_appcontext
    TR->>DB: session.remove()
```

---

## Diagram 3: Request Lifecycle — Public Endpoint

Flow for a public endpoint (e.g., GET /api/v1/skills). Note that `before_request` still runs but skips auth enforcement.

```mermaid
sequenceDiagram
    participant C as FlaskClient
    participant BR as before_request
    participant PE as PUBLIC_ENDPOINTS
    participant BP as Blueprint Route
    participant V as validated_query()
    participant S as Service Layer

    C->>BR: GET /api/v1/skills?q=review&page=1<br/>(no Authorization header)

    BR->>PE: Is "skills.list_skills" in PUBLIC_ENDPOINTS?
    PE-->>BR: Yes — skip auth enforcement

    BR->>BR: Attempt JWT decode (optional)
    alt JWT present and valid
        BR->>BR: Store in g.current_user (for optional user features)
    else No JWT or invalid
        BR->>BR: g.current_user = None (OK for public endpoint)
    end

    BR-->>BP: Continue to route handler

    BP->>V: @validated_query(SkillsQueryParams)
    V->>V: request.args.to_dict(flat=False)
    V->>V: Normalize + validate with Pydantic
    V-->>BP: query=SkillsQueryParams(q="review", page=1, ...)

    BP->>BP: Extract optional user from g.get("current_user")
    BP->>S: browse_skills(db, q="review", page=1, ...)
    S-->>BP: (items, total)
    BP-->>C: 200 {"items": [...], "total": 42, "page": 1, ...}
```

---

## Diagram 4: DivisionRestrictedError Handling Flow

How division enforcement works for the install endpoint, from service layer exception to structured 403 response.

```mermaid
flowchart TD
    A["POST /api/v1/skills/{slug}/install"] --> B["Extract user_division<br/>from g.current_user"]
    B --> C["Call install_skill(db, slug,<br/>user_id, user_division, ...)"]
    C --> D{"Service: Is user_division<br/>in skill.divisions?"}

    D -->|Yes| E["Create Install record"]
    E --> F["db.commit()"]
    F --> G["Return result dict"]
    G --> H["201 + InstallResponse JSON"]

    D -->|No| I["raise PermissionError()"]
    I --> J["Blueprint catches PermissionError"]
    J --> K["Return 403 with structured body"]
    K --> L["403 Response"]

    L --> M["Response Body:<br/>{<br/>  'detail': {<br/>    'error': 'division_restricted'<br/>  }<br/>}"]

    style H fill:#22c55e,color:#fff
    style L fill:#ef4444,color:#fff
    style M fill:#fef3c7,color:#000
```

### Key Detail: Dict-typed detail

The 403 response for division restriction uses a **dict** as the detail value, not a string. This is intentional and matches the FastAPI behavior where `HTTPException(detail={"error": "division_restricted"})` serializes the dict directly. The Flask equivalent:

```python
except PermissionError:
    return jsonify({"detail": {"error": "division_restricted"}}), 403
```

Frontend code checks `response.json().detail.error === "division_restricted"` to show the division access request dialog.

---

## Diagram 5: Background Task Session Pattern

How background tasks (view count increment, Gate 2 scan) create their own database sessions to avoid using the request-scoped session after the request completes.

```mermaid
sequenceDiagram
    participant R as Request Thread
    participant BP as Blueprint Route
    participant DB1 as Scoped Session<br/>(request-bound)
    participant T as Background Thread
    participant DB2 as Fresh SessionLocal()<br/>(thread-owned)
    participant TD as teardown_appcontext

    R->>BP: GET /api/v1/skills/{slug}
    BP->>DB1: get_skill_detail(db, slug)
    DB1-->>BP: result dict (includes skill_id)

    BP->>T: Thread(target=_bg_increment, args=(skill_id,)).start()
    Note over T: Thread starts independently

    BP-->>R: Return 200 response immediately

    R->>TD: teardown_appcontext fires
    TD->>DB1: session.remove()
    Note over DB1: Request session is now closed

    Note over T: Thread may still be running...
    T->>DB2: bg_db = SessionLocal()
    T->>DB2: increment_view_count(bg_db, skill_id)
    T->>DB2: bg_db.commit()
    T->>DB2: bg_db.close()
    Note over T: Thread exits cleanly

    style DB1 fill:#ef4444,color:#fff
    style DB2 fill:#22c55e,color:#fff
```

### Rules for Background Sessions

1. **NEVER** use `get_db()` (the scoped session proxy) in a background thread
2. **ALWAYS** create a fresh `SessionLocal()` at the start of the thread function
3. **ALWAYS** close the session in a `finally` block
4. **ALWAYS** set `daemon=True` on the thread so it does not block shutdown
5. **ALWAYS** wrap the thread body in try/except to log errors (otherwise they vanish silently)

```python
def _bg_increment_view(skill_id: UUID) -> None:
    """Background: increment view count with its own session."""
    from skillhub_db.session import SessionLocal
    bg_db = SessionLocal()
    try:
        increment_view_count(bg_db, skill_id)
    except Exception:
        logger.exception("Failed to increment view count for %s", skill_id)
    finally:
        bg_db.close()

# In route handler:
threading.Thread(target=_bg_increment_view, args=(skill_id,), daemon=True).start()
```

---

## Diagram 6: Admin Route Auth Enforcement

How platform-team and security-team checks work with the two-tier `before_request` pattern.

```mermaid
flowchart TD
    A["Incoming Request"] --> B["Global before_request"]
    B --> C{"Endpoint in<br/>PUBLIC_ENDPOINTS?"}
    C -->|Yes| D["Skip auth, continue"]
    C -->|No| E{"Valid JWT?"}
    E -->|No| F["401 Unauthorized"]
    E -->|Yes| G["g.current_user = decoded JWT"]
    G --> H{"Route is /api/v1/admin/*?"}

    H -->|No| D
    H -->|Yes| I["Admin before_request"]
    I --> J{"g.current_user<br/>.is_platform_team?"}
    J -->|Yes| K["Continue to route handler"]
    J -->|No| L["403 Forbidden"]

    K --> M{"Route is DELETE<br/>/admin/platform-updates/*?"}
    M -->|No| N["Execute handler"]
    M -->|Yes| O{"g.current_user<br/>.is_security_team?"}
    O -->|Yes| N
    O -->|No| P["403 Forbidden<br/>(security team required)"]

    style F fill:#ef4444,color:#fff
    style L fill:#ef4444,color:#fff
    style P fill:#ef4444,color:#fff
    style N fill:#22c55e,color:#fff
    style D fill:#22c55e,color:#fff
```

### Auth Level Summary

| Level | Check | Applied To |
|-------|-------|-----------|
| Public | In `PUBLIC_ENDPOINTS` frozenset | 5 endpoints (skills browse/categories/detail, flags list, changelog) |
| Authenticated | Valid JWT in `g.current_user` | 29 endpoints (users, social, feedback submit/upvote, submissions create/view, access-request) |
| Platform Team | `g.current_user["is_platform_team"]` | 14 endpoints (admin submissions, admin flags, admin feedback, admin roadmap) |
| Security Team | `g.current_user["is_security_team"]` | 1 endpoint (DELETE platform-updates) |

---

## Diagram 7: Test Injection Pattern — FastAPI vs Flask

Side-by-side comparison of how test database injection works in FastAPI vs Flask.

```mermaid
flowchart LR
    subgraph FastAPI["FastAPI (before migration)"]
        direction TB
        A1["app = create_app()"] --> A2["app.dependency_overrides[get_db] = lambda: mock_db"]
        A2 --> A3["client = TestClient(app)"]
        A3 --> A4["client.get('/api/v1/skills')"]
        A4 --> A5["FastAPI DI resolves get_db<br/>→ returns mock_db"]
    end

    subgraph Flask["Flask (after migration)"]
        direction TB
        B1["app = create_app(<br/>  session_factory=lambda: mock_db<br/>)"] --> B2["client = app.test_client()"]
        B2 --> B3["client.get('/api/v1/skills')"]
        B3 --> B4["current_app.extensions['db']()<br/>→ returns mock_db"]
    end

    style FastAPI fill:#fee2e2,color:#000
    style Flask fill:#dcfce7,color:#000
```

### Test Setup Comparison

```python
# BEFORE (FastAPI)
def test_list_skills(client, mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    with patch("skillhub.services.skills.browse_skills") as mock:
        mock.return_value = ([skill_dict], 1)
        resp = client.get("/api/v1/skills")
    assert resp.status_code == 200

# AFTER (Flask)
def test_list_skills(client, auth_headers, mock_db):
    with patch("skillhub.services.skills.browse_skills") as mock:
        mock.return_value = ([skill_dict], 1)
        resp = client.get("/api/v1/skills")
    assert resp.status_code == 200
```

Key differences:
1. Session factory is injected via `create_app()` constructor, not monkey-patched
2. Auth token must be passed in headers (no `dependency_overrides` for auth either)
3. `client.get()` / `client.post()` API is identical between TestClient and FlaskClient
4. Response `.json` is a method in Flask (`resp.get_json()`) vs property in FastAPI (`resp.json()`) — but many test helpers normalize this

---

## Diagram 8: Complete Phase 3 Blueprint Map

All 49 routes across 7 blueprints, organized by auth level.

```mermaid
graph LR
    subgraph Public["PUBLIC (5 routes)"]
        P1["GET /skills"]
        P2["GET /skills/categories"]
        P3["GET /skills/{slug}"]
        P4["GET /flags"]
        P5["GET /changelog"]
    end

    subgraph Auth["AUTHENTICATED (29 routes)"]
        direction TB
        subgraph Skills_Auth["Skills (3)"]
            SA1["GET /{slug}/versions"]
            SA2["GET /{slug}/versions/latest"]
            SA3["GET /{slug}/versions/{v}"]
        end
        subgraph Users_Auth["Users (5)"]
            UA1["GET /me"]
            UA2["GET /me/installs"]
            UA3["GET /me/favorites"]
            UA4["GET /me/forks"]
            UA5["GET /me/submissions"]
        end
        subgraph Social_Auth["Social (16)"]
            SO1["POST /{slug}/install"]
            SO2["DELETE /{slug}/install"]
            SO3["POST+DELETE /{slug}/favorite"]
            SO4["POST /{slug}/fork"]
            SO5["POST+DELETE /{slug}/follow"]
            SO6["GET+POST /{slug}/reviews"]
            SO7["PATCH /{slug}/reviews/{id}"]
            SO8["POST /{slug}/reviews/{id}/vote"]
            SO9["GET+POST /{slug}/comments"]
            SO10["DELETE /{slug}/comments/{id}"]
            SO11["POST /{slug}/comments/{id}/replies"]
            SO12["POST /{slug}/comments/{id}/vote"]
        end
        subgraph Other_Auth["Other (5)"]
            OA1["POST /submissions"]
            OA2["GET /submissions/{id}"]
            OA3["POST /{slug}/access-request"]
            OA4["POST /feedback"]
            OA5["POST /feedback/{id}/upvote"]
        end
    end

    subgraph Admin["PLATFORM TEAM (14 routes)"]
        AD1["POST /admin/submissions/{id}/scan"]
        AD2["GET /admin/submissions"]
        AD3["POST /admin/submissions/{id}/review"]
        AD4["GET /admin/access-requests"]
        AD5["POST /admin/access-requests/{id}/review"]
        AD6["POST /admin/flags"]
        AD7["PATCH /admin/flags/{key}"]
        AD8["DELETE /admin/flags/{key}"]
        AD9["GET /admin/feedback"]
        AD10["PATCH /admin/feedback/{id}/status"]
        AD11["GET /admin/platform-updates"]
        AD12["POST /admin/platform-updates"]
        AD13["PATCH /admin/platform-updates/{id}"]
        AD14["POST /admin/platform-updates/{id}/ship"]
    end

    subgraph Security["SECURITY TEAM (1 route)"]
        SEC1["DELETE /admin/platform-updates/{id}"]
    end

    style Public fill:#22c55e,color:#fff
    style Auth fill:#3b82f6,color:#fff
    style Admin fill:#f59e0b,color:#fff
    style Security fill:#ef4444,color:#fff
```

---

## Diagram 9: Bug #5 Fix — Feedback JOIN

Before and after the `list_feedback()` query fix.

```mermaid
flowchart LR
    subgraph Before["BEFORE (Bug #5)"]
        direction TB
        Q1["SELECT * FROM skill_feedback<br/>WHERE ..."] --> R1["Result: {<br/>  id, user_id, skill_id,<br/>  category, body, status,<br/>  upvote_count<br/>}"]
        R1 --> R1a["user_display_name: MISSING<br/>skill_name: MISSING"]
    end

    subgraph After["AFTER (Fix)"]
        direction TB
        Q2["SELECT sf.*, u.display_name, s.name<br/>FROM skill_feedback sf<br/>LEFT JOIN users u ON sf.user_id = u.id<br/>LEFT JOIN skills s ON sf.skill_id = s.id<br/>WHERE ..."] --> R2["Result: {<br/>  id, user_id, skill_id,<br/>  category, body, status,<br/>  upvote_count,<br/>  user_display_name: 'Jane Doe',<br/>  skill_name: 'PR Review Assistant'<br/>}"]
    end

    style Before fill:#fee2e2,color:#000
    style After fill:#dcfce7,color:#000
```

---

## Diagram 10: Bug #6 Fix — Roadmap version_tag

Before and after the `PlatformUpdateResponse` and changelog fix.

```mermaid
flowchart TD
    subgraph Before["BEFORE (Bug #6)"]
        direction TB
        B1["ship_update() returns {<br/>  ..., version_tag: 'v1.2.0', ...<br/>}"]
        B1 --> B2["PlatformUpdateResponse schema<br/>has NO version_tag field"]
        B2 --> B3["version_tag silently dropped"]

        B4["GET /changelog handler"]
        B4 --> B5["ChangelogEntry(<br/>  version_tag=None  # hardcoded!<br/>)"]
    end

    subgraph After["AFTER (Fix)"]
        direction TB
        A1["ship_update() returns {<br/>  ..., version_tag: 'v1.2.0', ...<br/>}"]
        A1 --> A2["PlatformUpdateResponse schema<br/>version_tag: str | None = None"]
        A2 --> A3["version_tag preserved in response"]

        A4["GET /changelog handler"]
        A4 --> A5["ChangelogEntry(<br/>  version_tag=item['version_tag']<br/>)"]
        A5 --> A6["Changelog shows 'v1.2.0'"]
    end

    style Before fill:#fee2e2,color:#000
    style After fill:#dcfce7,color:#000
```
