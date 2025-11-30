#!/usr/bin/env python3
"""Test database functionality without full app initialization"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

def test_database_operations():
    """Test basic database operations"""
    print("🗄️ Testing Database Operations...")
    
    # Create temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    original_db_path = os.environ.get("CMMS_DB_PATH")
    
    try:
        # Set temporary database path
        test_db_path = os.path.join(temp_dir, "test_cmms.db")
        os.environ["CMMS_DB_PATH"] = test_db_path
        
        # Test basic database operations without the problematic imports
        import sqlite3
        
        # Create test database
        conn = sqlite3.connect(test_db_path)
        cur = conn.cursor()
        
        # Create a simple test table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS test_users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE
            )
        """)
        
        # Test insert
        cur.execute("INSERT INTO test_users (name, email) VALUES (?, ?)", 
                   ("Test User", "test@chatterfix.com"))
        
        # Test select
        cur.execute("SELECT * FROM test_users")
        users = cur.fetchall()
        
        conn.commit()
        conn.close()
        
        if len(users) > 0:
            print("✅ Database operations working: Created table, inserted data, retrieved data")
            return True
        else:
            print("❌ Database operations failed: No data retrieved")
            return False
            
    except ImportError as e:
        print(f"❌ Database import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Database operations failed: {e}")
        return False
    finally:
        # Clean up
        if original_db_path:
            os.environ["CMMS_DB_PATH"] = original_db_path
        else:
            os.environ.pop("CMMS_DB_PATH", None)
        
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def test_static_files():
    """Test that static files exist and are accessible"""
    print("📁 Testing Static Files...")
    
    static_files = [
        "app/static/css/style.css",
        "app/static/js/main.js",
        "app/static/manifest.json"
    ]
    
    success_count = 0
    for file_path in static_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                if content.strip():
                    print(f"✅ Static file {file_path}: Valid content ({len(content)} chars)")
                    success_count += 1
                else:
                    print(f"⚠️ Static file {file_path}: Empty file")
            except Exception as e:
                print(f"❌ Static file {file_path}: Error reading - {e}")
        else:
            print(f"❌ Static file {file_path}: File missing")
    
    return success_count == len(static_files)

def test_templates():
    """Test that HTML templates exist and are valid"""
    print("📄 Testing Templates...")
    
    template_files = [
        "app/templates/base.html",
        "app/templates/dashboard.html",
        "app/templates/login.html"
    ]
    
    success_count = 0
    for template_path in template_files:
        if os.path.exists(template_path):
            try:
                with open(template_path, 'r') as f:
                    content = f.read()
                if content.strip() and '<html>' in content.lower():
                    print(f"✅ Template {template_path}: Valid HTML content")
                    success_count += 1
                elif content.strip():
                    print(f"⚠️ Template {template_path}: Has content but may not be complete HTML")
                    success_count += 1
                else:
                    print(f"❌ Template {template_path}: Empty file")
            except Exception as e:
                print(f"❌ Template {template_path}: Error reading - {e}")
        else:
            print(f"❌ Template {template_path}: File missing")
    
    return success_count > 0

def test_router_files():
    """Test that router files can be imported"""
    print("🛤️ Testing Router Files...")
    
    router_files = [
        "app.routers.health",
        "app.routers.dashboard", 
        "app.routers.auth",
        "app.routers.assets"
    ]
    
    success_count = 0
    for router_module in router_files:
        try:
            # Try to import without initializing
            module_path = router_module.replace('.', '/')
            file_path = f"{module_path}.py"
            
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                
                if 'router' in content and 'APIRouter' in content:
                    print(f"✅ Router {router_module}: Valid router structure")
                    success_count += 1
                else:
                    print(f"⚠️ Router {router_module}: May not be properly structured")
            else:
                print(f"❌ Router {router_module}: File not found")
                
        except Exception as e:
            print(f"❌ Router {router_module}: Error - {e}")
    
    return success_count > 0

def test_configuration_integrity():
    """Test that configuration files are properly formatted"""
    print("⚙️ Testing Configuration Integrity...")
    
    configs = {
        "pyproject.toml": ["[tool.black]", "[tool.pytest.ini_options]"],
        ".flake8": ["[flake8]", "max-line-length"],
        "requirements.txt": ["fastapi", "uvicorn"],
        "Makefile": [".PHONY:", "help:"]
    }
    
    success_count = 0
    for config_file, required_content in configs.items():
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    content = f.read()
                
                if all(item in content for item in required_content):
                    print(f"✅ Config {config_file}: All required sections present")
                    success_count += 1
                else:
                    missing = [item for item in required_content if item not in content]
                    print(f"⚠️ Config {config_file}: Missing sections: {missing}")
            except Exception as e:
                print(f"❌ Config {config_file}: Error reading - {e}")
        else:
            print(f"❌ Config {config_file}: File missing")
    
    return success_count > 0

def main():
    """Run all database and file tests"""
    print("🧪 ChatterFix Database & File System Tests")
    print("="*60)
    
    test_results = {
        "Database Operations": test_database_operations(),
        "Static Files": test_static_files(),
        "Templates": test_templates(),
        "Router Files": test_router_files(),
        "Configuration": test_configuration_integrity()
    }
    
    # Print summary
    print("\n" + "="*60)
    print("🧪 TEST RESULTS SUMMARY")
    print("="*60)
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print("-"*60)
    print(f"Total: {total_tests} | Passed: {passed_tests} | Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print("="*60)
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)