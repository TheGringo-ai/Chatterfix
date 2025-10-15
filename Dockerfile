FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY cloud_ai_service.py .

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "cloud_ai_service.py"]
