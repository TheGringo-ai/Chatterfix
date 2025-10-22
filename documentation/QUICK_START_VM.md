# ⚡ Quick Start - ChatterFix Docker on VM

## 🎯 One-Line Setup

### Step 1: Open SSH to Your VM
Click here: **[Open VM SSH in Browser](https://console.cloud.google.com/compute/instances?project=fredfix)**

Then click the **SSH** button next to `chatterfix-cmms-production`

### Step 2: Run This Command
```bash
curl -fsSL https://raw.githubusercontent.com/docker/docker-install/master/install.sh | sudo sh && \
sudo apt-get install -y docker-compose-plugin && \
mkdir -p ~/chatterfix && cd ~/chatterfix && \
curl -o setup.sh https://metadata.google.internal/computeMetadata/v1/instance/attributes/startup-script -H "Metadata-Flavor: Google" && \
chmod +x setup.sh && ./setup.sh
```

### Step 3: Add Your API Keys
```bash
cd ~/chatterfix-docker
nano .env
```

**Add these lines (replace with your actual keys):**
```
OPENAI_API_KEY=sk-proj-YOUR-OPENAI-KEY-HERE
XAI_API_KEY=xai-YOUR-GROK-KEY-HERE
```

Save: `Ctrl+X`, `Y`, `Enter`

### Step 4: Start ChatterFix
```bash
sudo docker compose up -d
sudo docker compose logs -f
```

### Step 5: Access Your App
**URL:** http://35.237.149.25:8080

---

## 🔑 Where to Get API Keys

### OpenAI API Key
1. Go to: https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key (starts with `sk-proj-...`)
4. Add to .env: `OPENAI_API_KEY=sk-proj-...`

### Grok (xAI) API Key
1. Go to: https://console.x.ai/
2. Get your API key
3. Add to .env: `XAI_API_KEY=xai-...`

---

## 📊 Check Status

```bash
# Check running containers
sudo docker compose ps

# View logs
sudo docker compose logs -f

# Test health
curl http://localhost:8080/health

# Check Ollama models
sudo docker exec chatterfix-ollama ollama list
```

---

## 🚀 Your VM Info
- **Name:** chatterfix-cmms-production
- **Zone:** us-east1-b
- **External IP:** 35.237.149.25
- **App URL:** http://35.237.149.25:8080
- **SSH:** [Console SSH](https://console.cloud.google.com/compute/instances?project=fredfix)

---

## ⚡ Common Commands

```bash
# Start
sudo docker compose up -d

# Stop
sudo docker compose down

# Restart
sudo docker compose restart

# View logs
sudo docker compose logs -f

# Rebuild
sudo docker compose up -d --build
```

---

## 🆘 Troubleshooting

**Can't connect to VM?**
- Use browser SSH from GCP Console
- Link: https://console.cloud.google.com/compute/instances?project=fredfix

**Docker not found?**
```bash
curl -fsSL https://get.docker.com | sudo sh
```

**Port 8080 blocked?**
```bash
# Already open! Should work at http://35.237.149.25:8080
```

**Need to restart everything?**
```bash
cd ~/chatterfix-docker
sudo docker compose down
sudo docker compose up -d
```

---

## ✅ Success Checklist

- [ ] Connected to VM via SSH
- [ ] Docker installed
- [ ] Created ~/chatterfix-docker directory
- [ ] Added OpenAI API key to .env
- [ ] Added Grok/xAI API key to .env
- [ ] Started containers with `docker compose up -d`
- [ ] Can access http://35.237.149.25:8080
- [ ] Ollama models downloaded (mistral:7b, llama3:8b)

---

## 🎉 You're All Set!

Your ChatterFix CMMS is now running with:
- ✅ Docker containerization
- ✅ Ollama local AI (Mistral 7B, Llama3 8B)
- ✅ OpenAI GPT integration
- ✅ Grok/xAI integration
- ✅ Auto-restart on failure
- ✅ Persistent data volumes

**Access it now:** http://35.237.149.25:8080
