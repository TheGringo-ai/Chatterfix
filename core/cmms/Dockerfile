FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements_nexus.txt .
RUN pip install --no-cache-dir -r requirements_nexus.txt

# Copy AI Powerhouse application code
COPY chatterfix_enterprise_v3_ai_powerhouse.py .

# Expose port
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Run the AI Powerhouse application
CMD ["python", "chatterfix_enterprise_v3_ai_powerhouse.py"]