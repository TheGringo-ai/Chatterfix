# ULTRA-OPTIMIZED Production Dockerfile for ChatterFix CMMS
# AI Team Enhanced - Fast Build, Small Size, Enhanced Security
FROM python:3.12-slim as python-base

# Optimized environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_PROGRESS_BAR=off \
    PYTHONPATH=/app \
    DEBIAN_FRONTEND=noninteractive

# Builder stage for dependencies - OPTIMIZED FOR SPEED
FROM python-base as builder
WORKDIR /app

# Use BuildKit for faster builds with cache mounting
# Install ALL build dependencies in one layer
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libc6-dev curl build-essential \
    libssl-dev libffi-dev libxml2-dev libxslt1-dev \
    zlib1g-dev libjpeg-dev libpng-dev \
    && apt-get clean

# Pre-install wheel and setuptools for faster pip installs
RUN pip install --user --no-deps wheel setuptools packaging

# Copy requirements and install with optimizations
COPY requirements.txt .

# Install Python dependencies with cache mounting
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --user --no-warn-script-location \
    --find-links /root/.local/lib/python3.12/site-packages \
    -r requirements.txt

# Production stage - MINIMAL SIZE
FROM python-base as production
WORKDIR /app

# Copy only essential Python packages from builder
COPY --from=builder /root/.local /root/.local

# Install minimal runtime dependencies in one layer
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy application code efficiently
COPY --chown=1001:1001 main.py .
COPY --chown=1001:1001 app/ app/

# Create non-root user for security (single layer)
RUN useradd -m -u 1001 -s /bin/bash appuser \
    && mkdir -p /app/logs \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Optimized environment variables for production
ENV PATH=/root/.local/bin:$PATH \
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