# ChatterFix CMMS - Real-Time Sync Workflow Guide

## 🔄 Three-Way Synchronization Setup

Your ChatterFix CMMS project now has **real-time synchronization** between:
- 🖥️ **Local Development** (Your machine)
- 🌐 **GitHub Repository** (https://github.com/TheGringo-ai/Chatterfix.git)
- ☁️ **Production VM** (35.237.149.25:8080)

## 🚀 Quick Sync Commands

### Option 1: One-Command Sync (Recommended)
```bash
./sync-and-deploy.sh
```
This will:
- ✅ Commit all local changes
- ✅ Push to GitHub
- ✅ Deploy to VM
- ✅ Restart all services
- ✅ Verify deployment

### Option 2: Manual Git Workflow
```bash
git add .
git commit -m "Your commit message"
git push origin main-clean
```
- Auto-pushes to GitHub (via git hook)
- Manual VM deployment needed

### Option 3: GitHub Actions (Automatic)
- Triggers on push to `main-clean` or `main` branch
- Automatically deploys to VM
- Includes verification tests

## 📁 File Structure

```
core/cmms/
├── sync-and-deploy.sh              # One-command sync script
├── .github/workflows/
│   └── auto-deploy-to-vm.yml      # GitHub Actions workflow
├── .git/hooks/
│   └── post-commit                 # Auto-push git hook
└── [microservices files...]
```

## 🔧 Service URLs

### Production VM
- **Main App**: http://35.237.149.25:8080
- **Work Orders**: http://35.237.149.25:8080/work-orders
- **Assets**: http://35.237.149.25:8080/assets
- **Parts**: http://35.237.149.25:8080/parts
- **Health Check**: http://35.237.149.25:8080/health

### Local Development
- **Main App**: http://localhost:8000
- **Database Service**: http://localhost:8001
- **Work Orders Service**: http://localhost:8002
- **Assets Service**: http://localhost:8003
- **Parts Service**: http://localhost:8004
- **Fix It Fred AI**: http://localhost:8005

## 🔄 Workflow Examples

### Daily Development Workflow
1. Make changes to your code locally
2. Test locally: `python3 app.py`
3. Sync everything: `./sync-and-deploy.sh`
4. Verify on VM: http://35.237.149.25:8080

### Quick Fix Workflow
1. Edit file (e.g., `work_orders_service.py`)
2. Run: `./sync-and-deploy.sh`
3. Changes are live in ~30 seconds

### Collaborative Development
1. Pull latest: `git pull origin main-clean`
2. Make changes
3. Sync: `./sync-and-deploy.sh`
4. Team sees changes on VM immediately

## ⚙️ Microservices Architecture

Each sync deploys these services to the VM:
- `database_service.py` → Port 8001
- `work_orders_service.py` → Port 8002
- `assets_service.py` → Port 8003
- `parts_service.py` → Port 8004
- `grok_connector.py` → Port 8006
- `document_intelligence_service.py` → Port 8008
- `enterprise_security_service.py` → Port 8007
- `app.py` (main gateway) → Port 8080

## 🚨 Troubleshooting

### If Sync Fails
```bash
# Check git status
git status

# Check VM connectivity
ping 35.237.149.25

# Check service status
curl http://35.237.149.25:8080/health
```

### If Services Don't Start
```bash
# SSH into VM and check logs
ssh yoyofred_gringosgambit_com@35.237.149.25
cd /opt/chatterfix-cmms/current
tail -f logs/*.log
```

### Reset Everything
```bash
# Local: Force sync
git reset --hard origin/main-clean
./sync-and-deploy.sh

# VM: Manual restart
ssh yoyofred_gringosgambit_com@35.237.149.25
cd /opt/chatterfix-cmms/current
./deploy-clean-microservices-to-vm.sh
```

## 📊 Monitoring

- **GitHub**: Track commits and actions at https://github.com/TheGringo-ai/Chatterfix.git
- **VM Health**: http://35.237.149.25:8080/health
- **Logs**: Available in VM at `/opt/chatterfix-cmms/current/logs/`

## 🎯 Benefits

✅ **Real-time sync** - Changes go live in seconds
✅ **Automatic backups** - Everything versioned in GitHub
✅ **Reliable deployments** - Tested deployment scripts
✅ **Multi-environment** - Local testing, GitHub storage, VM production
✅ **Team collaboration** - Shared GitHub repository
✅ **Rollback capability** - Git history for easy rollbacks

---

**Remember**: Use `./sync-and-deploy.sh` for the fastest local-to-production workflow!