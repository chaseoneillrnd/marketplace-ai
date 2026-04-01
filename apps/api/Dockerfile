FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for layer caching
COPY libs/python-common/ libs/python-common/
COPY libs/db/ libs/db/
COPY apps/api/ apps/api/

# Install Python packages
RUN pip install --no-cache-dir \
    -e libs/python-common \
    -e libs/db \
    -e apps/api

ENV PYTHONPATH="apps/api:libs/db:libs/python-common"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "skillhub_flask.app:create_app()"]
