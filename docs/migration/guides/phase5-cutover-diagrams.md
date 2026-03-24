# Phase 5: Cutover Diagrams

Companion diagrams for `phase5-cutover-guide.md`. Render with any Mermaid-compatible viewer.

---

## 1. Cleanup Dependency Graph

Shows which cleanup tasks depend on each other. Execute sequentially top-to-bottom.

```mermaid
graph TD
    A[Remove FastAPI<br/>from docker-compose] --> B[Remove canary<br/>infrastructure]
    B --> C[mise.toml rename<br/>drop :flask suffix]
    C --> D[Delete apps/fast-api/]
    C --> E[Update CLAUDE.md]
    D --> F[Remove FastAPI<br/>dependencies from pyproject.toml]
    F --> G[Remove openapi<br/>baseline]
    G --> H[Final quality gate]
    E --> H

    style A fill:#369,color:#fff
    style B fill:#369,color:#fff
    style C fill:#693,color:#fff
    style D fill:#693,color:#fff
    style E fill:#693,color:#fff
    style F fill:#693,color:#fff
    style G fill:#693,color:#fff
    style H fill:#963,color:#fff
```

---

## 2. File Changes Summary

Overview of which files are modified or deleted during cleanup.

```mermaid
graph LR
    subgraph "Modified"
        M1[mise.toml]
        M2[docker-compose.yml]
        M3[docker-compose.prod.yml]
        M4[CLAUDE.md]
        M5[.env / .env.example]
        M6[apps/api/pyproject.toml]
    end

    subgraph "Deleted"
        D1[apps/fast-api/]
        D2[specs/openapi-baseline.json]
        D3[nginx canary template]
    end
```
