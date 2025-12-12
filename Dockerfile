# EMERGENCY DOCKERFILE - Optimized for fast Cloud Run startup
FROM python:3.12-slim

WORKDIR /app

# Install only essential system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy minimal requirements first
COPY requirements.txt .

# Install Python packages with cache
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create app user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Use emergency main file with critical routers including analytics and user management  
CMD ["python", "-m", "uvicorn", "main_emergency:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]