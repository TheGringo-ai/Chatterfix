# ULTRA-OPTIMIZED Production Dockerfile for ChatterFix CMMS
# AI Team Enhanced - UV for 10-100x faster builds
FROM python:3.14-slim AS python-base

# Optimized environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    DEBIAN_FRONTEND=noninteractive \
    UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1

# Builder stage for dependencies - UV POWERED (10-100x faster)
FROM python-base AS builder
WORKDIR /app

# Install UV package manager (blazingly fast) and build deps in one layer
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libc6-dev curl build-essential \
    libssl-dev libffi-dev libxml2-dev libxslt1-dev \
    zlib1g-dev libjpeg-dev libpng-dev \
    && apt-get clean \
    && pip install uv --quiet

# Copy core requirements (fast builds, heavy ML deps in separate services)
COPY requirements-core.txt requirements.txt

# Install Python dependencies with UV (10-100x faster than pip)
# UV uses parallel downloads and smart caching
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system \
    -r requirements.txt

# Production stage - MINIMAL SIZE
FROM python-base AS production
WORKDIR /app

# Install minimal runtime dependencies in one layer
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create non-root user for security (single layer)
RUN useradd -m -u 1001 -s /bin/bash appuser \
    && mkdir -p /app/logs \
    && chown -R appuser:appuser /app

# Copy Python packages from builder (UV installs to system)
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code efficiently
COPY --chown=1001:1001 main.py .
COPY --chown=1001:1001 app/ app/

# Switch to non-root user
USER appuser

# Optimized environment variables for production
ENV PATH=/usr/local/bin:$PATH \
    PORT=8080 \
    ENVIRONMENT=production \
    WORKERS=1 \
    TIMEOUT=300 \
    KEEP_ALIVE=2 \
    MAX_REQUESTS=1000 \
    MAX_REQUESTS_JITTER=100

# Enhanced health check with better timeout handling
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f --max-time 3 http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Production-optimized startup with proper signal handling
CMD ["python", "-m", "uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--workers", "1", \
     "--timeout-keep-alive", "2", \
     "--access-log", \
     "--no-use-colors"]