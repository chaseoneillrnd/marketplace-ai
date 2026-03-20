FROM python:3.11-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

COPY libs/python-common/pyproject.toml libs/python-common/
COPY libs/python-common/skillhub_common/ libs/python-common/skillhub_common/
COPY libs/db/pyproject.toml libs/db/
COPY libs/db/skillhub_db/ libs/db/skillhub_db/
COPY apps/api/pyproject.toml apps/api/

RUN pip install --no-cache-dir \
    -e libs/python-common \
    -e libs/db \
    -e apps/api

COPY apps/api/ apps/api/

ENV PYTHONPATH=/app/apps/api:/app/libs/db:/app/libs/python-common

USER appuser

EXPOSE 8000

CMD ["uvicorn", "skillhub.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS production
CMD ["uvicorn", "skillhub.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
