# 🚀 ChatterFix Docker Setup on GCP VM

## VM Information
- **Name:** chatterfix-cmms-production
- **Zone:** us-east1-b
- **External IP:** 35.237.149.25
- **URL:** http://35.237.149.25:8080

## Option 1: Automated Setup (Recommended)

I've uploaded a deployment script to your VM. To run it:

### Step 1: Connect to VM via GCP Console
1. Go to: https://console.cloud.google.com/compute/instances?project=fredfix
2. Find `chatterfix-cmms-production`
3. Click **SSH** button (opens browser SSH)

### Step 2: Run the Setup Script
```bash
# Download and run the setup script
curl -o setup.sh https://metadata.google.internal/computeMetadata/v1/instance/attributes/startup-script -H "Metadata-Flavor: Google"
chmod +x setup.sh
./setup.sh
```

### Step 3: Add Your API Keys
```bash
# Edit the .env file
cd /home/$USER/chatterfix-docker
nano .env
```

**Replace these values:**
```bash
OPENAI_API_KEY=sk-your-actual-openai-key-here
XAI_API_KEY=REDACTED_XAI_KEY
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here  # Optional
```

Save with: `Ctrl+X`, then `Y`, then `Enter`

### Step 4: Start ChatterFix
```bash
cd /home/$USER/chatterfix-docker
sudo docker compose up -d
```

### Step 5: Monitor Progress
```bash
# Watch the logs
sudo docker compose logs -f

# Check status
sudo docker compose ps

# Test health
curl http://localhost:8080/health
```

---

## Option 2: Manual Setup (If automated script fails)

### Step 1: Connect via SSH (Browser)
https://console.cloud.google.com/compute/instances?project=fredfix

### Step 2: Install Docker
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt-get update
sudo apt-get install -y docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

### Step 3: Create Project Directory
```bash
mkdir -p ~/chatterfix-docker/app
cd ~/chatterfix-docker
```

### Step 4: Create docker-compose.yml
```bash
cat > docker-compose.yml << 'EOF'
services:
  chatterfix:
    build:
      context: ./app
      dockerfile: Dockerfile
    container_name: chatterfix-cmms
    ports:
      - "8080:8080"
    environment:
      - SERVICE_MODE=default
      - PORT=8080
      - OLLAMA_HOST=http://ollama:11434
      - OLLAMA_BASE_URL=http://ollama:11434
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - XAI_API_KEY=${XAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GCLOUD_PROJECT=fredfix
    volumes:
      - chatterfix-data:/app/data
    depends_on:
      - ollama
    networks:
      - chatterfix-network
    restart: unless-stopped

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
      sleep 10
      ollama pull mistral:7b
      ollama pull llama3:8b
      wait \$\$SERVER_PID
      "

networks:
  chatterfix-network:
    driver: bridge

volumes:
  ollama-data:
  chatterfix-data:
EOF
```

### Step 5: Create .env File
```bash
cat > .env << 'EOF'
# Replace with your actual API keys
OPENAI_API_KEY=sk-your-openai-key
XAI_API_KEY=xai-your-grok-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GCLOUD_PROJECT=fredfix
DATABASE_URL=sqlite:///./chatterfix.db
SERVICE_MODE=default
PORT=8080
EOF

# Edit and add your real keys
nano .env
```

### Step 6: Copy Application Code
```bash
# If you have existing code in /opt/chatterfix
cp -r /opt/chatterfix/core/cmms/* app/

# OR download from GitHub
# git clone https://github.com/your-repo/chatterfix.git app/
```

### Step 7: Start Services
```bash
# Make sure you're in the right directory
cd ~/chatterfix-docker

# Start everything
sudo docker compose up -d

# Watch logs
sudo docker compose logs -f
```

---

## 🔍 Verification & Testing

### Check Service Status
```bash
cd ~/chatterfix-docker
sudo docker compose ps
```

Expected output:
```
NAME                 STATUS              PORTS
chatterfix-cmms      Up 2 minutes        0.0.0.0:8080->8080/tcp
chatterfix-ollama    Up 2 minutes        0.0.0.0:11434->11434/tcp
```

### Test Endpoints
```bash
# Health check
curl http://localhost:8080/health

# Ollama models
curl http://localhost:11434/api/tags

# From your local machine
curl http://35.237.149.25:8080/health
```

### View Logs
```bash
# All services
sudo docker compose logs -f

# Just ChatterFix
sudo docker compose logs -f chatterfix

# Just Ollama
sudo docker compose logs -f ollama
```

---

## 🔧 Common Commands

```bash
# Start services
sudo docker compose up -d

# Stop services
sudo docker compose down

# Restart a service
sudo docker compose restart chatterfix

# Rebuild after code changes
sudo docker compose up -d --build

# View resource usage
sudo docker stats

# Clean up old containers
sudo docker system prune -a
```

---

## 🔥 Firewall Rules

Make sure ports are open:
```bash
# Allow port 8080 (ChatterFix)
gcloud compute firewall-rules create allow-chatterfix \
  --project=fredfix \
  --allow=tcp:8080 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=http-server

# Allow port 11434 (Ollama) - optional, only if you want external access
gcloud compute firewall-rules create allow-ollama \
  --project=fredfix \
  --allow=tcp:11434 \
  --source-ranges=0.0.0.0/0
```

---

## 📊 Monitoring

### Check Ollama Model Downloads
```bash
# Ollama downloads large models (4-5GB each)
# Watch progress:
sudo docker compose logs -f ollama

# Check available models:
sudo docker exec chatterfix-ollama ollama list
```

### Resource Usage
```bash
# Check disk space
df -h

# Check memory
free -h

# Docker stats
sudo docker stats
```

---

## 🚨 Troubleshooting

### Service won't start
```bash
# Check logs
sudo docker compose logs chatterfix

# Check if port is in use
sudo lsof -i :8080

# Restart Docker
sudo systemctl restart docker
```

### Ollama models not downloading
```bash
# Manual pull
sudo docker exec chatterfix-ollama ollama pull mistral:7b
sudo docker exec chatterfix-ollama ollama pull llama3:8b
```

### Out of disk space
```bash
# Check space
df -h

# Clean Docker
sudo docker system prune -a --volumes
```

### API keys not working
```bash
# Verify .env file
cat .env

# Make sure no spaces around = sign
# Correct: OPENAI_API_KEY=sk-123
# Wrong: OPENAI_API_KEY = sk-123

# Restart to reload env
sudo docker compose restart
```

---

## 🎯 Access Your Application

**After successful startup:**
- **Main App:** http://35.237.149.25:8080
- **Health Check:** http://35.237.149.25:8080/health
- **Ollama API:** http://35.237.149.25:11434 (if firewall open)

---

## 📝 Next Steps

1. ✅ Connect to VM via GCP Console SSH
2. ✅ Run setup script or manual setup
3. ✅ Add your OpenAI and Grok API keys to .env
4. ✅ Start Docker Compose
5. ✅ Access http://35.237.149.25:8080
6. ✅ Test AI features

---

## 🆘 Support Commands

```bash
# Get VM external IP
gcloud compute instances describe chatterfix-cmms-production \
  --zone=us-east1-b \
  --format="value(networkInterfaces[0].accessConfigs[0].natIP)"

# SSH via browser
gcloud compute ssh chatterfix-cmms-production \
  --zone=us-east1-b

# Check VM status
gcloud compute instances list --filter="name:chatterfix"
```
