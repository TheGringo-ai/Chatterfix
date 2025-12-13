# Codebase Cleanup Workflow

Clean up redundant files, old Docker instances, and maintain project organization.

## CEO Directive

> "Keep this clean and organized. Do not make redundant or duplicated files. Shutdown old Docker instances that are interfering. Only one deploy script."

## Docker Cleanup

### Stop and Remove Old Containers
```bash
# List all containers
docker ps -a

# Stop running containers
docker stop $(docker ps -q)

# Remove stopped containers
docker container prune -f

# Remove unused images
docker image prune -a -f

# Remove unused volumes
docker volume prune -f

# Full system cleanup
docker system prune -a -f --volumes
```

### Verify Single Instance
```bash
# Ensure only one ChatterFix container running
docker ps | grep chatterfix
```

## File Cleanup

### Check for Duplicates
```bash
# Find duplicate Python files
find . -name "*.py" -type f | xargs md5 | sort | uniq -d -w 32

# Find backup files that should be removed
find . -name "*.bak" -o -name "*.backup" -o -name "*~"

# Find old deployment configs
ls -la deployment/ cloudbuild*.yaml
```

### Verify Single Deploy Script
```bash
# Should only be scripts/deploy.sh
ls -la scripts/deploy*.sh
ls -la deploy*.sh
```

## Git Cleanup

### Remove Deleted Files from Git Status
Based on current status, these files are marked for deletion:
- `.env.example`
- `.github/workflows/backup/*`
- `cloudbuild-*.yaml` (except production)
- `deployment/*.yaml` (consolidate)
- `requirements_optimized.txt`
- `test_simple.py`

```bash
# Stage all deletions
git add -A

# Verify what will be committed
git status

# Commit cleanup
git commit -m "Cleanup: Remove redundant files and consolidate deployment configs"
```

## Requirements Consolidation

Ensure single source of truth:
- `requirements.txt` - Main dependencies
- Remove `requirements_optimized.txt` if redundant

## Workflow Consolidation

Keep only active workflows:
- `.github/workflows/ci-cd.yml` - Main CI/CD
- `.github/workflows/production-ci-cd.yml` - Production
- `.github/workflows/workflow-maintenance.yml` - Health

Remove backup workflows in `.github/workflows/backup/`

## Post-Cleanup Verification

```bash
# Verify project structure is clean
tree -L 2 -I '__pycache__|node_modules|.git|venv'

# Verify no orphaned files
git status

# Verify single Docker instance
docker ps
```
