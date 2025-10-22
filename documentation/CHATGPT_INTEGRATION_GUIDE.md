# ChatGPT Integration Guide - Fix It Fred DevOps API

🤖 **Complete setup for ChatGPT to control your VM through Fix It Fred**

## 🚀 API Access Information

**Base URL:** `http://35.237.149.25:9004`  
**API Key:** `pjRALvKOpKwrvr796ywpPA2Y2kc9OU7m`  
**Documentation:** `http://35.237.149.25:9004/docs`

## 🔐 Authentication

All API requests require Bearer token authentication:

```bash
Authorization: Bearer pjRALvKOpKwrvr796ywpPA2Y2kc9OU7m
```

## 📋 Available Endpoints for ChatGPT

### 1. Health Check & System Status
```http
GET /health
Authorization: Bearer pjRALvKOpKwrvr796ywpPA2Y2kc9OU7m

Returns: VM status, services, system resources, git status
```

### 2. Execute VM Commands
```http
POST /command
Authorization: Bearer pjRALvKOpKwrvr796ywpPA2Y2kc9OU7m
Content-Type: application/json

{
  "command": "ls -la",
  "description": "List directory contents",
  "working_directory": "/optional/path"
}
```

### 3. Manage Services
```http
POST /service
Authorization: Bearer pjRALvKOpKwrvr796ywpPA2Y2kc9OU7m
Content-Type: application/json

{
  "service_name": "nginx",
  "action": "restart"
}

Actions: start, stop, restart, status, enable, disable
```

### 4. Deploy Updates
```http
POST /deploy
Authorization: Bearer pjRALvKOpKwrvr796ywpPA2Y2kc9OU7m
Content-Type: application/json

{
  "branch": "main-clean",
  "force": false,
  "notify_completion": true
}
```

### 5. Git Operations
```http
GET /git/status
Authorization: Bearer pjRALvKOpKwrvr796ywpPA2Y2kc9OU7m

Returns: git status, current branch, last commit
```

### 6. Service List & Status
```http
GET /services
Authorization: Bearer pjRALvKOpKwrvr796ywpPA2Y2kc9OU7m

Returns: Status of all Fix It Fred services
```

### 7. Get Service Logs
```http
GET /logs/{service_name}?lines=50
Authorization: Bearer pjRALvKOpKwrvr796ywpPA2Y2kc9OU7m

Example: GET /logs/nginx?lines=20
```

### 8. Control Fix It Fred Daemon
```http
POST /fred/signal
Authorization: Bearer pjRALvKOpKwrvr796ywpPA2Y2kc9OU7m
Content-Type: application/json

{
  "signal": "health_check"
}
```

## 🧪 Example ChatGPT Commands

### Check VM Health
```bash
curl -H "Authorization: Bearer pjRALvKOpKwrvr796ywpPA2Y2kc9OU7m" \
  http://35.237.149.25:9004/health
```

### Restart Nginx
```bash
curl -X POST \
  -H "Authorization: Bearer pjRALvKOpKwrvr796ywpPA2Y2kc9OU7m" \
  -H "Content-Type: application/json" \
  -d '{"service_name":"nginx","action":"restart"}' \
  http://35.237.149.25:9004/service
```

### Deploy Latest Code
```bash
curl -X POST \
  -H "Authorization: Bearer pjRALvKOpKwrvr796ywpPA2Y2kc9OU7m" \
  -H "Content-Type: application/json" \
  -d '{"branch":"main-clean","force":false}' \
  http://35.237.149.25:9004/deploy
```

### Execute Command
```bash
curl -X POST \
  -H "Authorization: Bearer pjRALvKOpKwrvr796ywpPA2Y2kc9OU7m" \
  -H "Content-Type: application/json" \
  -d '{"command":"uptime","description":"Check system uptime"}' \
  http://35.237.149.25:9004/command
```

## 🔒 Security Features

- **API Key Authentication**: 32-character secure token
- **Command Filtering**: Dangerous commands blocked
- **CORS Enabled**: For web-based access
- **Structured Logging**: All actions logged with JSON format
- **Service Isolation**: API runs as dedicated service
- **Firewall Protected**: Port 9004 specifically opened

## 🎯 What ChatGPT Can Do

✅ **VM Management:**
- Check system health and resources
- Monitor service status
- View system logs
- Execute safe commands

✅ **Service Control:**
- Start/stop/restart services
- Check service status
- Enable/disable services
- View service logs

✅ **Deployment:**
- Deploy latest code from GitHub
- Force deployments
- Monitor deployment status
- Check git repository status

✅ **Fix It Fred Control:**
- Trigger health checks
- Monitor autonomous operations
- View Fix It Fred logs
- Control daemon signals

## 🚨 Limitations & Safety

❌ **Blocked Commands:**
- `rm -rf` (destructive deletion)
- `mkfs` (filesystem formatting)
- `dd if=` (disk operations)
- `sudo passwd` (password changes)
- Fork bombs and malicious scripts

✅ **Safe Operations:**
- File listing and reading
- Service management
- Git operations
- System monitoring
- Application deployment

## 🔧 Troubleshooting

### API Not Responding
```bash
# Check API service status
gcloud compute ssh chatterfix-cmms-production --zone=us-east1-b \
  --command="sudo systemctl status fix-it-fred-devops-api"

# View API logs
gcloud compute ssh chatterfix-cmms-production --zone=us-east1-b \
  --command="sudo journalctl -u fix-it-fred-devops-api -f"
```

### Restart API Service
```bash
gcloud compute ssh chatterfix-cmms-production --zone=us-east1-b \
  --command="sudo systemctl restart fix-it-fred-devops-api"
```

### Check Firewall
```bash
gcloud compute firewall-rules describe allow-fred-api
```

## 📊 Monitoring

- **API Logs:** `sudo journalctl -u fix-it-fred-devops-api -f`
- **Service Status:** `sudo systemctl status fix-it-fred-devops-api`
- **API Documentation:** `http://35.237.149.25:9004/docs`
- **Health Endpoint:** `http://35.237.149.25:9004/health`

## 🎉 Integration Complete

ChatGPT now has secure, controlled access to your VM through Fix It Fred's DevOps API. The system provides:

- **Autonomous VM management** via API calls
- **Secure authentication** with API keys
- **Comprehensive logging** of all operations
- **Safety controls** to prevent destructive actions
- **Real-time monitoring** and health checks

Your VM is now ready for ChatGPT-powered autonomous management! 🤖