FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Pure Firestore - no local database needed
# RUN mkdir -p /app/data

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Set environment variables
ENV PORT=8080
ENV USE_FIRESTORE=true
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8080

# Remove health check that might be causing issues
# HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
#   CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Simple uvicorn command for Cloud Run
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
