---
name: docker-service-builder
description: Use when adding services to docker-compose.yml or creating Dockerfiles
---

# Docker Service Builder

## Add Service to docker-compose.yml

```yaml
my-service:
  build:
    context: .
    dockerfile: apps/my-service/Dockerfile
  ports:
    - "8002:8002"
  environment:
    DATABASE_URL: postgresql://skillhub:skillhub@postgres:5432/skillhub
  volumes:
    - ./apps/my-service:/app/apps/my-service
    - ./libs:/app/libs
  depends_on:
    postgres:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
    interval: 5s
    timeout: 5s
    retries: 5
```

## Existing Services

| Service | Port | Dockerfile |
|---------|------|-----------|
| postgres | 5432 | image: postgres:16-alpine |
| redis | 6379 | image: redis:7-alpine |
| api | 8000 | apps/api/Dockerfile |
| mcp-server | 8001 | apps/mcp-server/Dockerfile |
| web | 5173 | apps/web/Dockerfile |

## Dockerfile Pattern (Python)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY apps/my-service/pyproject.toml .
RUN pip install -e .[dev]
COPY . .
CMD ["uvicorn", "my_service.main:app", "--host", "0.0.0.0", "--port", "8002"]
```

## References

- docker-compose.yml: project root
- API Dockerfile: `apps/api/Dockerfile`
- MCP Dockerfile: `apps/mcp-server/Dockerfile`
