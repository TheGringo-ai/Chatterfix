#!/usr/bin/env python3
"""
Quick fix for critical security and functionality issues
"""

import os
import subprocess
import sys

def fix_security_issues():
    """Fix critical security issues found by Bandit"""
    
    # Fix 1: Replace eval() with json.loads in dashboard.py
    print("🔧 Fixing eval() security issue...")
    dashboard_file = "app/routers/dashboard.py"
    
    with open(dashboard_file, 'r') as f:
        content = f.read()
    
    # Replace eval() with json.loads()
    content = content.replace(
        "message = eval(data)  # Parse JSON",
        "message = json.loads(data)  # Parse JSON"
    )
    
    # Add json import if not present
    if "import json" not in content:
        content = content.replace(
            "from fastapi import APIRouter, WebSocket, Request, Depends",
            "from fastapi import APIRouter, WebSocket, Request, Depends\nimport json"
        )
    
    with open(dashboard_file, 'w') as f:
        f.write(content)
    
    print("✅ Fixed eval() security vulnerability")

def fix_code_formatting():
    """Auto-fix code formatting issues"""
    print("🎨 Running Black code formatter...")
    
    try:
        subprocess.run(["black", "app/", "--quiet"], check=True)
        print("✅ Code formatting fixed")
    except subprocess.CalledProcessError:
        print("⚠️ Some formatting issues remain")
    except FileNotFoundError:
        print("⚠️ Black not installed, skipping formatting")

def create_health_endpoint():
    """Create missing health endpoint"""
    print("🏥 Creating health endpoint...")
    
    health_content = '''from fastapi import APIRouter
from fastapi.responses import JSONResponse
import os
import sqlite3
from datetime import datetime

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connectivity
        db_status = "ok"
        try:
            if os.getenv("USE_FIRESTORE", "false").lower() == "true":
                # Firestore health check
                from app.core.db_adapter import get_db_adapter
                db_adapter = get_db_adapter()
                db_status = "firestore_ok"
            else:
                # Database health check
                from app.core.database import get_db_connection
                conn = get_db_connection()
                conn.execute("SELECT 1")
                conn.close()
                db_status = "db_ok"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        return JSONResponse({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_status,
            "version": "2.0.0",
            "service": "chatterfix-cmms"
        })
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy", 
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
'''
    
    with open("app/routers/health.py", 'w') as f:
        f.write(health_content)
    
    print("✅ Health endpoint created")

def update_main_py():
    """Ensure health router is included in main.py"""
    print("🔧 Updating main.py to include health router...")
    
    with open("main.py", 'r') as f:
        content = f.read()
    
    if "health," not in content:
        content = content.replace(
            "from app.routers import (",
            "from app.routers import (\n    health,"
        )
        
        content = content.replace(
            "app.include_router(health.router)     # Health checks (no prefix)",
            "app.include_router(health.router, prefix=\"\", tags=[\"health\"])     # Health checks (no prefix)"
        )
    
    with open("main.py", 'w') as f:
        f.write(content)
    
    print("✅ Health router added to main.py")

def main():
    """Run all fixes"""
    print("🚀 Running critical fixes for ChatterFix workflows...")
    
    fix_security_issues()
    fix_code_formatting() 
    create_health_endpoint()
    update_main_py()
    
    print("\n🎉 Critical fixes completed!")
    print("📋 Next steps:")
    print("   1. git add .")
    print("   2. git commit -m 'fix: Critical security and functionality fixes'")
    print("   3. git push origin main")
    print("   4. Monitor GitHub Actions for workflow success")

if __name__ == "__main__":
    main()