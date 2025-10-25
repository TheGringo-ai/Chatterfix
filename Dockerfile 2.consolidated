FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including curl for health check
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY consolidated_requirements.txt .
RUN pip install --no-cache-dir -r consolidated_requirements.txt

# Copy application code
COPY consolidated_cmms_service.py .
COPY modules/ ./modules/

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "consolidated_cmms_service.py"]