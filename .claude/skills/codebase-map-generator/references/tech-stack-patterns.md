# Tech Stack Patterns — Glob Discovery Guide

Reference glob patterns for detecting languages, frameworks, package managers, databases, and infrastructure.

## JavaScript/TypeScript Ecosystems

### Monorepo Detection
```
pnpm-workspace.yaml         → pnpm monorepo
lerna.json                  → Lerna monorepo
nx.json                     → Nx monorepo
turbo.json                  → Turborepo
yarn.lock (workspaces:)     → Yarn workspaces
```

### Framework Detection
```
next.config.js              → Next.js
vite.config.ts              → Vite
webpack.config.js           → Webpack
svelte.config.js            → SvelteKit
```

### TypeScript + Config
```
tsconfig.json               → TypeScript (extract paths, references)
tsconfig.*.json             → Workspace tsconfigs (monorepos)
tsc --listFiles              → Understand compilation order
```

### Dependencies & Entry Points
```
package.json                → Scripts, dependencies, version
apps/*/package.json         → App-specific config (monorepos)
libs/*/package.json         → Lib-specific config (monorepos)
src/main.ts, src/index.ts   → Entry points
apps/api/src/index.ts       → Handler entry points
```

### Testing
```
jest.config.js              → Jest configuration
jest.preset.cjs             → Jest preset (monorepos)
**/*.test.ts                → Test files
**/*.spec.ts                → Spec files
```

## Go Ecosystems

### Module & Project Structure
```
go.mod                      → Go module (version, dependencies)
go.sum                      → Dependency hashes
cmd/                        → Command entry points
internal/                   → Private packages
pkg/                        → Public packages
```

### Framework Detection
```
go.mod (github.com/labstack/echo)  → Echo web framework
go.mod (github.com/gin-gonic/gin)  → Gin framework
```

### Configuration
```
.env                        → Environment variables
config/                     → Config files
docker-compose.yml          → Local dev setup
```

## Python Ecosystems

### Project Management
```
pyproject.toml              → Modern Python project
setup.py                    → Legacy Python project
requirements.txt            → Pinned dependencies
requirements-dev.txt        → Dev dependencies
poetry.lock / pipenv.lock   → Lock files
```

### Framework Detection
```
manage.py                   → Django project
wsgi.py                     → WSGI app entry point
asgi.py                     → ASGI app entry point
```

### Project Structure
```
[app_name]/                 → App directories
tests/ or test/             → Test directories
migrations/                 → Database migrations
```

## Database & ORM

### Prisma
```
schema.prisma               → Prisma schema (models, relationships)
.env.local, .env            → Database URL
prisma/migrations/          → Migration history
```

### SQL-Based
```
**/*.sql                    → Raw SQL files
migrations/, db/            → Migration directories
schema.sql                  → Initial schema
```

### Other ORMs
```
sequelize-config.json       → Sequelize (Node)
ormconfig.json              → TypeORM (Node)
alembic/                    → SQLAlchemy migrations (Python)
```

## Infrastructure & DevOps

### AWS CDK
```
infrastructure/             → CDK source code
cdk.json                    → CDK config
cdk.out/                    → CDK build output
*.stack.ts                  → Stack definitions
```

### Terraform
```
terraform/                  → Terraform code
*.tf                        → Terraform files
terraform.tfstate           → State (don't glob, but note existence)
```

### Docker & Containerization
```
Dockerfile                  → Container image
docker-compose.yml          → Local dev compose
.dockerignore               → Excluded files
```

### CI/CD
```
.github/workflows/          → GitHub Actions
.gitlab-ci.yml              → GitLab CI
.circleci/                  → CircleCI
Jenkinsfile                 → Jenkins
```

## Project Configuration & Metadata

### Agent Configurations
```
.claude/                    → Claude Code plugin config
.cursor/                    → Cursor AI config
.ruler/                     → Ruler agent instructions
.kiro/specs/                → Kiro specifications
```

### Documentation
```
README.md                   → Project overview
docs/                       → Documentation
docs/ai-agent-context/      → Architecture docs
CLAUDE.md                   → Project memory for Claude Code
constitution.md             → Immutable project rules
```

### Linting & Code Quality
```
.eslintrc.js                → ESLint config
.prettierrc                 → Prettier config
tsconfig.json               → TypeScript strictness
.editorconfig               → Editor config
```

### Environment
```
.env.example                → Env template
.env.local                  → Local overrides
.nvmrc                      → Node version
.python-version             → Python version
```

## Recommended Glob Sequence

Run in order to avoid noise and build understanding:

1. **Language/Framework Detection** (package.json, go.mod, pyproject.toml, tsconfig.json)
2. **Project Structure** (apps/, libs/, src/, cmd/, internal/)
3. **Config & Metadata** (infrastructure/, cdk.json, docker-compose.yml, .env*, Dockerfile)
4. **Database** (schema.prisma, migrations/, *.sql)
5. **Agent Configs** (.claude/, .ruler/, .kiro/)
6. **Documentation** (README.md, docs/, CLAUDE.md, constitution.md)

This order builds context progressively without overwhelming results.
