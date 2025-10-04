FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for monitoring
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    httpx==0.25.2 \
    pydantic==2.5.0 \
    psutil==5.9.6

# Copy self-healing monitor
COPY ai_self_healing_monitor.py .

# Create non-root user
RUN useradd --create-home --shell /bin/bash aiuser
RUN chown -R aiuser:aiuser /app
USER aiuser

EXPOSE 8010
ENV PORT=8010

CMD ["python", "ai_self_healing_monitor.py"]