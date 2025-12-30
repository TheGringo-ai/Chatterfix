# Fix It Fred Git Integration - Troubleshooting Guide

## 🔧 Common Issues and Solutions

This guide helps resolve common issues with the Fix It Fred Git Integration system.

---

## 🚨 Port Conflicts

### **Issue**: Service fails to start on port 9002
```
Error: [Errno 98] Address already in use
```

**Solution**:
```bash
# 1. Check what's using port 9002
sudo netstat -tulpn | grep 9002
sudo lsof -i :9002

# 2. Kill existing processes
sudo pkill -f "fix_it_fred_git_integration_service.py"
sudo pkill -f ":9002"

# 3. Wait and restart
sleep 5
sudo systemctl restart fix-it-fred-git.service

# 4. Verify service is running
sudo systemctl status fix-it-fred-git.service
curl http://localhost:9002/health
```

### **Issue**: Fix It Fred AI service not accessible on port 9000
```
Connection refused to localhost:9000
```

**Solution**:
```bash
# 1. Check if AI service is running
ps aux | grep "fix_it_fred_ai_service"
curl http://localhost:9000/health

# 2. Start Fix It Fred AI service if needed
cd /home/yoyofred_gringosgambit_com/chatterfix-docker
nohup python3 fix_it_fred_ai_service.py > /tmp/fred_ai.log 2>&1 &

# 3. Verify both services
curl http://localhost:9000/health  # AI service
curl http://localhost:9002/health  # Git integration
```

---

## 🔐 Authentication Issues

### **Issue**: Git operations fail with permission denied
```
Permission denied (publickey)
```

**Solution**:
```bash
# 1. Run the credentials setup script
cd /home/yoyofred_gringosgambit_com/chatterfix-docker
./setup_git_credentials.sh

# 2. Choose SSH authentication (recommended)
# Follow prompts to generate SSH key

# 3. Add public key to GitHub/GitLab
cat ~/.ssh/fix_it_fred_git.pub

# 4. Test authentication
./setup_git_credentials.sh test git@github.com:your-username/your-repo.git
```

### **Issue**: Token authentication not working
```
remote: Invalid username or password
```

**Solution**:
```bash
# 1. Generate new personal access token
# GitHub: Settings → Developer Settings → Personal Access Tokens
# Permissions needed: repo, write:repo_hook

# 2. Update credentials
./setup_git_credentials.sh token your-username your-new-token

# 3. Test connection
git ls-remote https://github.com/your-username/your-repo.git
```

---

## 🤖 GitHub Actions Issues

### **Issue**: Workflow fails with GCP authentication error
```
Error: google-github-actions/auth failed
```

**Solution**:
1. **Check GitHub Secrets**:
   - Go to repository → Settings → Secrets
   - Verify `GCP_SA_KEY` secret exists
   - Ensure it contains valid JSON service account key

2. **Regenerate Service Account Key**:
   ```bash
   # Create new service account key
   gcloud iam service-accounts keys create github-actions-key.json \
     --iam-account=github-actions@fredfix.iam.gserviceaccount.com
   
   # Copy contents to GitHub secret
   cat github-actions-key.json
   ```

3. **Verify Permissions**:
   ```bash
   # Check service account permissions
   gcloud projects get-iam-policy fredfix \
     --flatten="bindings[].members" \
     --filter="bindings.members:github-actions@fredfix.iam.gserviceaccount.com"
   ```

### **Issue**: Git integration deployment fails
```
gcloud compute scp failed
```

**Solution**:
```bash
# 1. Verify VM is running
gcloud compute instances list --filter="name=chatterfix-cmms-production"

# 2. Check VM SSH access
gcloud compute ssh chatterfix-cmms-production --zone=us-east1-b --command="echo 'VM accessible'"

# 3. Manually trigger Git integration deployment
gh workflow run deploy-fix-it-fred-git-integration.yml
```

---

## 📊 Service Health Issues

### **Issue**: Git Integration Service unhealthy
```
curl: (7) Failed to connect to localhost port 9002
```

**Diagnosis**:
```bash
# 1. Check service status
sudo systemctl status fix-it-fred-git.service

# 2. Check service logs
sudo journalctl -u fix-it-fred-git.service -f

# 3. Check process
ps aux | grep fix_it_fred_git_integration_service
```

**Solution**:
```bash
# 1. Restart service
sudo systemctl restart fix-it-fred-git.service

# 2. If service fails to start, check dependencies
pip3 list | grep -E "(fastapi|watchdog|cryptography)"

# 3. Install missing dependencies
pip3 install --user -r requirements_git.txt

# 4. Check file permissions
ls -la fix_it_fred_git_integration_service.py
chmod +x fix_it_fred_git_integration_service.py

# 5. Manual start for debugging
cd /home/yoyofred_gringosgambit_com/chatterfix-docker
python3 fix_it_fred_git_integration_service.py
```

### **Issue**: File monitoring not working
```
No file changes detected
```

**Solution**:
```bash
# 1. Check inotify limits
cat /proc/sys/fs/inotify/max_user_watches

# 2. Increase limits if needed
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# 3. Test file monitoring
touch test_file.py
# Should appear in service logs

# 4. Check service logs for file events
tail -f /tmp/fix_it_fred_git.log
```

---

## 🧠 AI Integration Issues

### **Issue**: AI analysis not working
```
AI analysis error: Connection refused
```

**Solution**:
```bash
# 1. Verify Fix It Fred AI service
curl -X POST http://localhost:9000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "provider": "ollama"}'

# 2. Check Ollama service
curl http://localhost:11434/api/tags

# 3. Restart Ollama if needed
sudo systemctl restart ollama

# 4. Check Git integration AI configuration
curl http://localhost:9002/api/git/config
```

### **Issue**: Commit messages not generated
```
Using fallback commit message
```

**Solution**:
```bash
# 1. Test AI service directly
curl -X POST http://localhost:9000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Generate commit message for: app.py modified", "provider": "ollama"}'

# 2. Check AI provider configuration
# Ensure Ollama models are installed
curl http://localhost:11434/api/tags

# 3. Pull missing models
docker exec ollama ollama pull mistral:7b
```

---

## 🔄 Git Repository Issues

### **Issue**: Repository not initialized
```
fatal: not a git repository
```

**Solution**:
```bash
# 1. Initialize repository
cd /home/yoyofred_gringosgambit_com/chatterfix-docker
git init

# 2. Configure git user
git config user.name "Fix It Fred AI"
git config user.email "fix-it-fred@chatterfix.com"

# 3. Create initial commit
git add .
git commit -m "Initial commit: ChatterFix CMMS with Fix It Fred Git Integration"

# 4. Add remote if needed
git remote add origin git@github.com:your-username/your-repo.git
```

### **Issue**: Remote repository not configured
```
fatal: No configured push destination
```

**Solution**:
```bash
# 1. Add remote repository
git remote add origin git@github.com:your-username/your-repo.git

# 2. Verify remote
git remote -v

# 3. Test push
git push -u origin main
```

---

## 📋 Systematic Debugging

### **Complete Health Check Script**
```bash
#!/bin/bash
# Fix It Fred Git Integration Health Check

echo "🔍 Fix It Fred Git Integration Health Check"
echo "==========================================="

# Check services
echo "📊 Service Status:"
curl -s http://localhost:9000/health | jq '.' 2>/dev/null || echo "❌ AI Service (9000) not responding"
curl -s http://localhost:9002/health | jq '.' 2>/dev/null || echo "❌ Git Service (9002) not responding"

# Check processes
echo ""
echo "🔄 Running Processes:"
ps aux | grep -E "(fix_it_fred|ollama)" | grep -v grep

# Check systemd services
echo ""
echo "⚙️ Systemd Services:"
sudo systemctl is-active fix-it-fred-git.service 2>/dev/null || echo "❌ Git service not active"
sudo systemctl is-active ollama 2>/dev/null || echo "❌ Ollama service not active"

# Check git status
echo ""
echo "📝 Git Status:"
cd /home/yoyofred_gringosgambit_com/chatterfix-docker
git status --short 2>/dev/null || echo "❌ Not a git repository"

# Check recent logs
echo ""
echo "📜 Recent Logs:"
tail -5 /tmp/fix_it_fred_git.log 2>/dev/null || echo "❌ No git service logs"

echo ""
echo "✅ Health check complete"
```

### **Quick Fix Script**
```bash
#!/bin/bash
# Quick Fix for Common Issues

echo "🔧 Quick Fix for Fix It Fred Git Integration"
echo "==========================================="

# Kill any conflicting processes
echo "🛑 Stopping conflicting processes..."
sudo pkill -f "fix_it_fred_git_integration_service.py" || true
sudo pkill -f ":9002" || true

# Wait for cleanup
sleep 5

# Restart services
echo "🔄 Restarting services..."
sudo systemctl restart fix-it-fred-git.service
sleep 10

# Check health
echo "🩺 Checking health..."
if curl -s http://localhost:9002/health | grep -q "healthy"; then
    echo "✅ Git Integration Service is healthy"
else
    echo "❌ Git Integration Service needs attention"
    echo "Check logs: sudo journalctl -u fix-it-fred-git.service -n 20"
fi

echo "✅ Quick fix complete"
```

---

## 🆘 Emergency Procedures

### **Complete Reset**
```bash
#!/bin/bash
# Emergency Reset - Use only if everything is broken

echo "🚨 Emergency Reset of Fix It Fred Git Integration"
echo "================================================"

# Stop all services
sudo systemctl stop fix-it-fred-git.service
sudo pkill -f fix_it_fred

# Clean up
rm -f /tmp/fix_it_fred_git*.log
rm -f /tmp/fix_it_fred_git.db

# Reinstall dependencies
pip3 install --user --force-reinstall -r requirements_git.txt

# Restart service
sudo systemctl start fix-it-fred-git.service

# Wait and test
sleep 15
curl http://localhost:9002/health

echo "🔄 Emergency reset complete"
```

### **Backup and Restore**
```bash
# Create backup
tar czf fix_it_fred_backup_$(date +%s).tar.gz \
  fix_it_fred_git*.py \
  git_integration_config.json \
  requirements_git.txt \
  ~/.ssh/fix_it_fred_git* \
  ~/.git-credentials

# Restore from backup
tar xzf fix_it_fred_backup_*.tar.gz
chmod +x *.py *.sh
sudo systemctl restart fix-it-fred-git.service
```

---

## 📞 Getting Help

### **Log Collection**
```bash
# Collect all relevant logs for support
mkdir -p /tmp/fix_it_fred_debug
cp /tmp/fix_it_fred_git*.log /tmp/fix_it_fred_debug/
sudo journalctl -u fix-it-fred-git.service > /tmp/fix_it_fred_debug/systemd.log
ps aux | grep fix_it_fred > /tmp/fix_it_fred_debug/processes.txt
git status > /tmp/fix_it_fred_debug/git_status.txt 2>&1
curl http://localhost:9002/health > /tmp/fix_it_fred_debug/health.json 2>&1

tar czf fix_it_fred_debug_$(date +%s).tar.gz -C /tmp fix_it_fred_debug
echo "Debug package created: fix_it_fred_debug_*.tar.gz"
```

### **Support Checklist**
- [ ] Service status: `sudo systemctl status fix-it-fred-git.service`
- [ ] Health check: `curl http://localhost:9002/health`
- [ ] Recent logs: `sudo journalctl -u fix-it-fred-git.service -n 50`
- [ ] Git status: `git status` in repository directory
- [ ] Port availability: `netstat -tulpn | grep 9002`
- [ ] Dependencies: `pip3 list | grep -E "(fastapi|watchdog|cryptography)"`

---

**Remember**: Most issues can be resolved by restarting the service and checking logs. Always start with the basics before attempting complex solutions.