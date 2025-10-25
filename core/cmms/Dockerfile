# ChatterFix CMMS - Unified Services Dockerfile
# Supports multiple service modes based on environment variables

FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy all service files
COPY app.py .
COPY backend_unified_service.py .
COPY ai_unified_service.py .
COPY database_utils.py .

# Copy any additional files needed
COPY templates/ templates/
COPY static/ static/

# Expose port
EXPOSE 8080

# Use environment variable to determine which service to run
CMD ["sh", "-c", "if [ \"$SERVICE_MODE\" = \"unified_backend\" ]; then python backend_unified_service.py; elif [ \"$SERVICE_MODE\" = \"unified_ai\" ]; then python ai_unified_service.py; else python app.py; fi"]