#!/bin/bash
set -e

echo "🚀 ChatterFix Docker Deployment Script"
echo "======================================="

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "✅ Docker installed"
else
    echo "✅ Docker already installed"
fi

# Install Docker Compose if not present
if ! command -v docker compose &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    sudo apt-get update
    sudo apt-get install -y docker-compose-plugin
    echo "✅ Docker Compose installed"
else
    echo "✅ Docker Compose already installed"
fi

# Create app directory
APP_DIR="/home/$USER/chatterfix-docker"
mkdir -p $APP_DIR
cd $APP_DIR

echo "📁 Working directory: $APP_DIR"

# Create docker-compose.yml
echo "📝 Creating docker-compose.yml..."
cat > docker-compose.yml << 'COMPOSE_EOF'
services:
  # ChatterFix CMMS Application
  chatterfix:
    build:
      context: ./app
      dockerfile: Dockerfile
    container_name: chatterfix-cmms
    ports:
      - "8080:8080"
    environment:
      # Service Configuration
      - SERVICE_MODE=default
      - PORT=8080

      # Ollama Configuration
      - OLLAMA_HOST=http://ollama:11434
      - OLLAMA_BASE_URL=http://ollama:11434

      # AI API Keys (loaded from .env)
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - XAI_API_KEY=${XAI_API_KEY:-}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}

      # GCP Configuration
      - GCLOUD_PROJECT=${GCLOUD_PROJECT:-fredfix}
      - GCP_PROJECT_ID=${GCLOUD_PROJECT:-fredfix}

      # Database
      - DATABASE_URL=${DATABASE_URL:-sqlite:///./chatterfix.db}

    volumes:
      - chatterfix-data:/app/data
    depends_on:
      - ollama
    networks:
      - chatterfix-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  # Ollama Service for Local LLM
  ollama:
    image: ollama/ollama:latest
    container_name: chatterfix-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    networks:
      - chatterfix-network
    restart: unless-stopped
    entrypoint: /bin/sh
    command: >
      -c "
      ollama serve &
      SERVER_PID=\$\$!
      echo 'Waiting for Ollama server to start...'
      sleep 10
      echo 'Pulling Mistral 7B model...'
      ollama pull mistral:7b || echo 'Mistral pull failed, continuing...'
      echo 'Pulling Llama3 8B model...'
      ollama pull llama3:8b || echo 'Llama3 pull failed, continuing...'
      echo 'Models ready!'
      wait \$\$SERVER_PID
      "
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 120s

networks:
  chatterfix-network:
    driver: bridge

volumes:
  ollama-data:
    driver: local
  chatterfix-data:
    driver: local
COMPOSE_EOF

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << 'ENV_EOF'
# ChatterFix CMMS Environment Configuration

# AI API Keys - REPLACE WITH YOUR ACTUAL KEYS
OPENAI_API_KEY=your_openai_api_key_here
XAI_API_KEY=your_grok_xai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# GCP Configuration
GCLOUD_PROJECT=fredfix
GCP_PROJECT_ID=fredfix

# Database Configuration
DATABASE_URL=sqlite:///./chatterfix.db

# Service Mode
SERVICE_MODE=default
PORT=8080
ENV_EOF
    echo "⚠️  IMPORTANT: Edit .env file and add your API keys!"
    echo "   Run: nano .env"
fi

# Create app directory structure
mkdir -p app/templates app/static

# Clone the repository or copy files
echo "📦 Fetching application code..."
if [ -d "/opt/chatterfix" ]; then
    echo "Copying from /opt/chatterfix..."
    cp -r /opt/chatterfix/core/cmms/* app/ 2>/dev/null || true
else
    echo "Creating minimal app structure..."
    # Create a basic Dockerfile if not exists
    if [ ! -f app/Dockerfile ]; then
        cat > app/Dockerfile << 'DOCKERFILE_EOF'
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "app.py"]
DOCKERFILE_EOF
    fi

    # Create minimal requirements.txt
    if [ ! -f app/requirements.txt ]; then
        cat > app/requirements.txt << 'REQUIREMENTS_EOF'
fastapi
uvicorn[standard]
httpx
python-multipart
jinja2
requests
REQUIREMENTS_EOF
    fi
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Edit API keys: nano .env"
echo "2. Add your OpenAI key: OPENAI_API_KEY=sk-..."
echo "3. Add your Grok/xAI key: XAI_API_KEY=xai-..."
echo "4. Start services: sudo docker compose up -d"
echo "5. View logs: sudo docker compose logs -f"
echo "6. Access app: http://$(curl -s ifconfig.me):8080"
echo ""
echo "🔧 Useful Commands:"
echo "  - Check status: sudo docker compose ps"
echo "  - View logs: sudo docker compose logs -f"
echo "  - Restart: sudo docker compose restart"
echo "  - Stop: sudo docker compose down"
echo ""
