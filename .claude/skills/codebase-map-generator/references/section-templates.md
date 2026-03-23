# Section Templates — Domain-Aware Markdown

Markdown templates that adapt to detected tech stack and project structure.

## TypeScript Monorepo Template (Nx, pnpm, Lerna)

### Directory Tree
```markdown
## File Tree

\`\`\`
[project-name]/
├── apps/              # Application shells
│   ├── [app1]/        # [Brief purpose]
│   └── [app2]/        # [Brief purpose]
├── libs/
│   ├── [domain1]/feature/   # Business logic
│   ├── [domain2]/feature/   # Business logic
│   └── shared/
│       ├── data-access/     # Infrastructure (DB, cache, encryption)
│       ├── util/            # Pure utilities
│       └── ui/              # Shared components
├── packages/          # Cross-boundary types + shared constants
├── infrastructure/    # AWS CDK or Terraform
├── prisma/            # Database schema (or embedded in libs/shared/data-access/)
└── docs/              # Documentation
\`\`\`
```

### Domain Section
```markdown
## [Domain Name]

\`\`\`
libs/[domain]/feature/src/
├── services/          # Core business logic
├── types/             # Type definitions, interfaces
├── guards/            # (if auth-related)
├── middleware/        # (if applicable)
├── repositories/      # (if data access)
└── index.ts           # Public API barrel
\`\`\`

**Key files**:
- `[service].ts` — [1-line purpose]
- `[service].ts` — [1-line purpose]
- `types.ts` — [type exports, 1 line]

**Relationships**: Depends on [list domains], exposes [brief API summary]
```

---

## Go Microservice Template

### Directory Tree
```markdown
## File Tree

\`\`\`
[service-name]/
├── cmd/               # CLI entry points
│   └── [service]/     # Main application
├── internal/          # Private packages
│   ├── handler/       # HTTP handlers
│   ├── service/       # Business logic
│   ├── repository/    # Data access
│   └── config/        # Configuration
├── pkg/               # Public packages (if library-like)
├── migrations/        # Database migrations
├── docker/            # Docker configuration
└── README.md
\`\`\`
```

### Domain Section
```markdown
## [Service/Package Name]

\`\`\`
internal/[domain]/
├── handler.go         # HTTP/gRPC handlers
├── service.go         # Business logic
├── repository.go      # Data access layer
└── types.go           # Type definitions
\`\`\`

**Key files**:
- `handler.go` — [HTTP routes or RPC methods]
- `service.go` — [Core business logic]
- `repository.go` — [Database operations]

**Relationships**: Depends on [list services], exposes [API summary]
```

---

## Python Django/FastAPI Template

### Directory Tree
```markdown
## File Tree

\`\`\`
[project-name]/
├── manage.py          # Django management
├── [app1]/            # Django app
│   ├── models.py      # Database models
│   ├── views.py       # View logic
│   ├── urls.py        # URL routing
│   └── serializers.py # Request/response schemas
├── [app2]/            # Django app
├── migrations/        # Database migrations
├── config/            # Project settings
└── static/            # Static files
\`\`\`
```

### Domain Section
```markdown
## [App Name]

\`\`\`
[app_name]/
├── models.py          # Database models
├── views.py           # Business logic + HTTP handlers
├── serializers.py     # Request/response serialization
├── urls.py            # Route definitions
└── tests.py           # Tests
\`\`\`

**Key files**:
- `models.py` — [Model definitions]
- `views.py` — [View functions or viewsets]
- `serializers.py` — [Data serialization]

**Relationships**: Depends on [list apps], exposes [API endpoints]
```

---

## Single-Repo TypeScript Template

### Directory Tree
```markdown
## File Tree

\`\`\`
[project-name]/
├── src/
│   ├── handlers/      # HTTP handlers / Lambda functions
│   ├── services/      # Business logic
│   ├── middleware/    # Middleware
│   ├── lib/           # Utilities
│   ├── types/         # Type definitions
│   └── index.ts       # Entry point
├── tests/             # Test files
├── config/            # Configuration
└── prisma/            # Database schema
\`\`\`
```

### Domain Section
```markdown
## [Module Name]

\`\`\`
src/[module]/
├── index.ts           # Public API
├── [service].ts       # Implementation
└── types.ts           # Types
\`\`\`

**Key files**:
- `[service].ts` — [1-line purpose]
- `types.ts` — [exported types]

**Relationships**: [Brief dependency note]
```

---

## Database Schema Section Template

```markdown
## Database Schema

**ORM/Framework**: [Prisma | SQLAlchemy | TypeORM | Raw SQL]

**Key models/tables**:
- `User` — Authentication & profile
- `Organization` — Multi-tenancy container
- `Plan` — Insurance plan documents
- `[Model]` — [Purpose]

**Relationships**:
- User ← Membership → Organization (many-to-many)
- Organization → Subscription (one-to-many)
- [Table A] → [Table B] (relationship type)

**Notes**: [Special constraints, e.g., PHI encryption, tiered retention, pgvector usage]
```

---

## Infrastructure Section Template

```markdown
## Infrastructure (AWS CDK / Terraform)

**Stack structure**:
- **API Stack**: Lambda functions (handlers), API Gateway, WebSocket
- **Data Stack**: RDS (PostgreSQL), DynamoDB, S3 buckets
- **Auth Stack**: Cognito user pool, custom authorizers
- **Processing Stack**: Step Functions, SQS, Lambda workers
- **Monitoring Stack**: CloudWatch, X-Ray, EventBridge

**Key resources**:
- [Resource Type] `[resource-name]` — [Purpose]
- [Resource Type] `[resource-name]` — [Purpose]

**Deployment**: [Env strategy, e.g., dev/stage/prod]
```

---

## Architectural Relationships Section Template

### Arrow Notation (for linear flows)
```markdown
## Architectural Relationships

\`\`\`
User Request → API (apps/api)
  ↓
Auth Guard (libs/auth/feature)
  ↓
Handler (apps/api/src/handlers/[handler])
  ↓
Service (libs/[domain]/feature/src/services/)
  ↓
Repository (libs/shared/data-access/prisma/)
  ↓
Database (Aurora PostgreSQL or DSQL)
\`\`\`
```

### Dependency Table (for complex graphs)
```markdown
## Architectural Relationships

| Domain | Depends On | Exposes |
|--------|-----------|---------|
| API | Auth, [Domain 1], [Domain 2] | REST endpoints |
| [Domain 1] | Data Access, Shared Utils | Service interfaces |
| [Domain 2] | [Domain 1], Data Access | Service interfaces |
| Shared Utils | (none) | Logger, encryption, validators |
```

### Bullet List (for high-level overview)
```markdown
## Architectural Relationships

- **API** orchestrates Auth, Chat, Plan, and Billing services
- **Chat** depends on Plan (RAG context), Auth (user context), Billing (feature gates)
- **Plan** depends on Data Access (Prisma), Shared Utils (encryption, S3)
- **Billing** verifies subscription status, enforces plan limits
- **Data Access** abstracts Prisma, DynamoDB, cache, encryption
```

---

## Optional Configuration Section Template

```markdown
## Key Configuration

**Feature flags**: [Storage + evaluation logic, e.g., "DynamoDB-backed, evaluated per user/org/tier"]

**Model selection**: [If LLM-heavy, e.g., "Llama 4 Maverick/Scout, configurable via BEDROCK_MODEL env"]

**Rate limits**: [Per-endpoint strategy, e.g., "DynamoDB-backed counters, 100 req/min default"]

**Plan tiers**: [Billing model, e.g., "Free (1 org), Lite (3 orgs), Pro/Enterprise (unlimited)"]

**Key environment variables**:
- `[VAR_NAME]` — [Purpose + example value]
- `[VAR_NAME]` — [Purpose + example value]
```

---

## Template Selection Logic

Choose template based on detected structure:

| Detection Signal | Template |
|------------------|----------|
| `pnpm-workspace.yaml` + `apps/` + `libs/` | TypeScript Monorepo |
| `nx.json` + `libs/[domain]/feature/` | TypeScript Monorepo |
| `go.mod` + `cmd/` + `internal/` | Go Microservice |
| `go.mod` + `pkg/` (no `cmd/`) | Go Library |
| `pyproject.toml` + `manage.py` + `[app]/models.py` | Python Django |
| `pyproject.toml` + `main.py` / `asgi.py` | Python FastAPI |
| Single `package.json` (no workspace) + `src/` | Single-Repo TypeScript |
| Single `go.mod` (no workspace) + `src/` or flat | Single-Repo Go |

Hybrid projects: Combine templates (e.g., TypeScript monorepo + Python data pipeline).
