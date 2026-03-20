FROM python:3.11-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc && \
    rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

COPY libs/python-common/pyproject.toml libs/python-common/
COPY libs/python-common/skillhub_common/ libs/python-common/skillhub_common/
COPY apps/mcp-server/pyproject.toml apps/mcp-server/

RUN pip install --no-cache-dir \
    -e libs/python-common \
    -e apps/mcp-server

COPY apps/mcp-server/ apps/mcp-server/

ENV PYTHONPATH=/app/apps/mcp-server:/app/libs/python-common

USER appuser

EXPOSE 8001

CMD ["python", "-m", "skillhub_mcp.server"]

FROM base AS production
CMD ["python", "-m", "skillhub_mcp.server"]
