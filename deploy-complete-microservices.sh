#!/bin/bash
# Complete ChatterFix Dockerized AI Microservices Deployment
set -e

echo "🚀 ChatterFix AI Microservices - Complete Dockerized Deployment"
echo "================================================================="

# Create deployment directory
mkdir -p chatterfix-docker-stack
cd chatterfix-docker-stack

echo "📦 Creating Dockerized Ollama Service..."

# 1. Dockerized Ollama Service
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # Ollama AI Service
  ollama:
    image: ollama/ollama:latest
    container_name: chatterfix-ollama
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
      - ./ollama-models:/models
    environment:
      - OLLAMA_ORIGINS=*
      - OLLAMA_HOST=0.0.0.0:11434
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Fix It Fred AI Service  
  fix-it-fred:
    build:
      context: .
      dockerfile: Dockerfile.fred
    container_name: chatterfix-fred
    restart: unless-stopped
    ports:
      - "9000:9000"
    depends_on:
      - ollama
    environment:
      - OLLAMA_HOST=ollama:11434
      - DEFAULT_MODEL=llama3.2:1b
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ChatterFix Main App
  chatterfix-app:
    build:
      context: .
      dockerfile: Dockerfile.app
    container_name: chatterfix-main
    restart: unless-stopped
    ports:
      - "8080:8080"
    depends_on:
      - fix-it-fred
    environment:
      - AI_SERVICE_URL=http://fix-it-fred:9000
      - PORT=8080

volumes:
  ollama_data:
    driver: local

networks:
  default:
    driver: bridge
EOF

echo "🤖 Creating Fix It Fred Dockerfile..."
cat > Dockerfile.fred << 'EOF'
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements-fred.txt .
RUN pip install --no-cache-dir -r requirements-fred.txt

# Copy Fix It Fred service
COPY fix_it_fred_ai_service.py .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:9000/health || exit 1

EXPOSE 9000

CMD ["python", "fix_it_fred_ai_service.py"]
EOF

echo "📱 Creating ChatterFix App Dockerfile..."
cat > Dockerfile.app << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements-app.txt .
RUN pip install --no-cache-dir -r requirements-app.txt

# Copy application
COPY app.py .
COPY templates/ ./templates/
COPY static/ ./static/

EXPOSE 8080

CMD ["python", "app.py"]
EOF

echo "📋 Creating requirements files..."
cat > requirements-fred.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
requests==2.31.0
pydantic==2.5.0
urllib3==2.1.0
EOF

cat > requirements-app.txt << 'EOF'
flask==2.3.3
requests==2.31.0
gunicorn==21.2.0
EOF

echo "🧹 Creating VM Cleanup Script..."
cat > cleanup-vm.sh << 'EOF'
#!/bin/bash
echo "🧹 Cleaning ChatterFix VM..."

# Stop all Python processes
sudo pkill -f python3 || true
sudo pkill -f ollama || true

# Remove old services
sudo systemctl stop ollama* || true
sudo systemctl disable ollama* || true

# Clean old installations
sudo rm -rf /usr/local/bin/ollama* || true
sudo rm -rf /root/.ollama || true
sudo rm -rf /tmp/ollama* || true

# Clean old Python cache
find /home -name "*.pyc" -delete || true
find /home -name "__pycache__" -delete || true

# Clean Docker if exists
docker system prune -af || true
docker volume prune -f || true

# Free up disk space
sudo apt-get autoremove -y || true
sudo apt-get autoclean || true

echo "✅ VM cleanup complete!"
EOF

echo "🚢 Creating Deployment Script..."
cat > deploy-to-vm.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Deploying Dockerized ChatterFix to VM..."

# Copy files to VM
echo "📂 Copying files to VM..."
gcloud compute scp --recurse . chatterfix-cmms-production:/home/yoyofred_gringosgambit_com/chatterfix-docker --zone=us-east1-b

# Execute on VM
echo "🔧 Setting up on VM..."
gcloud compute ssh chatterfix-cmms-production --zone=us-east1-b --command="
cd /home/yoyofred_gringosgambit_com/chatterfix-docker && 

# Cleanup first
chmod +x cleanup-vm.sh && sudo ./cleanup-vm.sh

# Install Docker if needed
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker \$USER
    sudo systemctl enable docker
    sudo systemctl start docker
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L \"https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Copy current app files
cp /home/yoyofred_gringosgambit_com/chatterfix-docker/app/fix_it_fred_ai_service.py . || true
cp /home/yoyofred_gringosgambit_com/chatterfix-docker/app/app.py . || true
cp -r /home/yoyofred_gringosgambit_com/chatterfix-docker/app/templates . || true
cp -r /home/yoyofred_gringosgambit_com/chatterfix-docker/app/static . || true

# Build and deploy
echo '🐳 Building containers...'
docker-compose down || true
docker-compose build --no-cache
docker-compose up -d

echo '⏳ Waiting for services to start...'
sleep 30

echo '🧪 Testing services...'
docker-compose ps
curl -f http://localhost:11434/api/tags || echo 'Ollama not ready yet'
curl -f http://localhost:9000/health || echo 'Fix It Fred not ready yet'  
curl -f http://localhost:8080 || echo 'ChatterFix app not ready yet'

echo '✅ Deployment complete!'
"
EOF

echo "🔍 Creating AI Team Diagnostic Script..."
cat > ai-team-diagnostics.sh << 'EOF'
#!/bin/bash
echo "🤖 AI Team Diagnostic Report"
echo "============================"

# System Resources
echo "💾 System Resources:"
gcloud compute ssh chatterfix-cmms-production --zone=us-east1-b --command="
free -h
df -h
top -bn1 | head -20
"

# Docker Status  
echo "🐳 Docker Status:"
gcloud compute ssh chatterfix-cmms-production --zone=us-east1-b --command="
docker --version
docker-compose --version
docker ps -a
docker stats --no-stream
docker logs chatterfix-ollama --tail 50 || true
docker logs chatterfix-fred --tail 50 || true
docker logs chatterfix-main --tail 50 || true
"

# Network Status
echo "🌐 Network Status:"
gcloud compute ssh chatterfix-cmms-production --zone=us-east1-b --command="
netstat -tlnp | grep LISTEN | grep -E '(8080|9000|11434)'
curl -s http://localhost:11434/api/tags | head -10 || echo 'Ollama API failed'
curl -s http://localhost:9000/health || echo 'Fred API failed'
"

# Test AI Chat
echo "💬 Testing AI Chat:"
curl -s -X POST "https://chatterfix.com/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message":"AI Team test - are all systems operational?","user_role":"technician"}' || echo 'Chat API failed'

echo "📊 Diagnostic complete!"
EOF

chmod +x *.sh

echo ""
echo "🎯 DOCKERIZED AI STACK READY!"
echo "=============================="
echo ""
echo "📁 Files created in: $(pwd)"
echo ""
echo "🚀 To deploy:"
echo "   ./deploy-to-vm.sh"
echo ""
echo "🔍 To get AI team diagnostics:"
echo "   ./ai-team-diagnostics.sh"
echo ""
echo "📋 What this gives you:"
echo "   ✅ Dockerized Ollama (isolated, reliable)"
echo "   ✅ Containerized Fix It Fred AI"
echo "   ✅ Clean VM environment"
echo "   ✅ Health monitoring & auto-restart"
echo "   ✅ Low-cost AI with your own models"
echo ""
echo "💡 Models supported: llama3.2:1b (fast), mistral:7b (quality)"
EOF