#!/bin/bash
# Fix It Fred Repository Cleanup Script

echo "🧹 Fix It Fred: Repository Cleanup"
echo "=================================="

# 1. Remove duplicate files (files ending with " 2", " 3", " 4", etc.)
echo "🗂️ Removing duplicate files..."
find . -name "* 2*" -type f -delete
find . -name "* 3*" -type f -delete  
find . -name "* 4*" -type f -delete
find . -name "* 5*" -type f -delete

# 2. Remove database temporary files  
echo "🗄️ Cleaning database temp files..."
find . -name "*.db-shm" -delete
find . -name "*.db-wal" -delete

# 3. Remove common temporary/cache files
echo "🧽 Removing temp files..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name ".DS_Store" -delete 2>/dev/null || true
find . -name "*.log" -delete 2>/dev/null || true

# 4. Update .gitignore to prevent future issues
echo "📝 Updating .gitignore..."
cat >> .gitignore << 'EOF'

# Fix It Fred Cleanup Rules
*.db-shm
*.db-wal
*~ 
* 2*
* 3*
* 4*
* 5*
*.pyc
__pycache__/
.DS_Store
*.log
node_modules/
.env
*.tmp
*.temp
EOF

echo "✅ Cleanup complete!"

# Show current status
echo "📊 Repository status after cleanup:"
echo "  Untracked files: $(git status --porcelain | grep -c '^??')"
echo "  Modified files: $(git status --porcelain | grep -c '^ M')"
echo "  Total issues: $(git status --porcelain | wc -l)"

echo ""
echo "🎯 Ready for clean development!"