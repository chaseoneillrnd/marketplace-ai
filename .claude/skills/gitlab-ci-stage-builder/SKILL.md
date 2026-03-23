---
name: gitlab-ci-stage-builder
description: Use when adding CI pipeline stages to .gitlab-ci.yml
---

# GitLab CI Stage Builder

## Existing Stages

lint → test → typecheck → build → security

## Add Python Job

```yaml
my_job:
  stage: test
  extends: .python_base
  services:
    - postgres:16-alpine
    - redis:7-alpine
  variables:
    DATABASE_URL: "postgresql://skillhub:skillhub@postgres:5432/skillhub"
    PYTHONPATH: "apps/api:libs/db:libs/python-common"
  script:
    - python -m pytest apps/my-service/tests/ -v --cov-fail-under=80
```

## Add Node Job

```yaml
my_node_job:
  stage: lint
  extends: .node_base
  script:
    - npx eslint apps/web/src/
```

## Base Templates

- `.python_base` — Python 3.11-slim, pip install all packages
- `.node_base` — Node 22-alpine, npm ci

## References

- CI config: `.gitlab-ci.yml`
- Mise equivalent: `mise.toml` (quality-gate task)
