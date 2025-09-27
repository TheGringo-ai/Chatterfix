# ChatterFix CMMS Enterprise - Cloud Run Dockerfile
# Optimized for API-only AI integration (no local models)

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (minimal for API-only deployment)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY auth.py .
COPY dashboard.py .
COPY reporting.py .

# Create necessary directories
RUN mkdir -p data logs static templates

# Note: static and templates directories will be created by the app if needed

# Set environment variables for Cloud Run
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV HOST=0.0.0.0

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Start command
CMD uvicorn app:app --host $HOST --port $PORT --workers 2