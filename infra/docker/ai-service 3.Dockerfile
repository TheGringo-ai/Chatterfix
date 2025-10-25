
# Fix It Fred AI Service
FROM python:3.11-slim

WORKDIR /app

# Install dependencies for AI service
COPY requirements-ai.txt .
RUN pip install --no-cache-dir -r requirements-ai.txt

# Copy AI service code
COPY fix_it_fred_ai_service.py .
COPY ai_team_enterprise_meeting.py .

# Create non-root user
RUN useradd --create-home --shell /bin/bash aiservice
USER aiservice

EXPOSE 9001

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9001/health || exit 1

CMD ["python", "fix_it_fred_ai_service.py"]
