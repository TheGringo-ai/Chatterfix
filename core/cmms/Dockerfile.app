# ChatterFix CMMS Main Application Dockerfile
# Optimized for Cloud Run deployment

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY app_microservice_requirements.txt .
RUN pip install --no-cache-dir -r app_microservice_requirements.txt

# Copy application files
COPY database_client.py .
COPY app_microservice.py .

# Create static directory (if needed)
RUN mkdir -p /app/static

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Run the main application
CMD ["python", "app_microservice.py"]