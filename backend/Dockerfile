# syntax=docker/dockerfile:1

FROM python:3.11-slim as base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

# System deps (build essentials for some libs)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps separately for better caching
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy application code
COPY . .

# Expose default port (Cloud Run sets $PORT)
EXPOSE 8080

# Healthcheck (optional) - hits /health when container runs locally
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://127.0.0.1:${PORT:-8080}/health || exit 1

# Run the app with uvicorn; Cloud Run provides $PORT
CMD ["/bin/sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]


