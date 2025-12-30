#!/usr/bin/env python3
"""
ChatterFix Frontend URL Migration Script
Automatically updates all frontend files to use the new consolidated CMMS service
"""

import os
import re
import glob

# New consolidated service URL
CONSOLIDATED_URL = "https://chatterfix-consolidated-cmms-650169261019.us-central1.run.app"

# URL mappings for migration
URL_REPLACEMENTS = {
    # Work Orders
    r'https://chatterfix-work-orders-[^"\']+': f'{CONSOLIDATED_URL}/work_orders',
    r'WORK_ORDERS_URL["\'].*?["\']': f'WORK_ORDERS_URL", "{CONSOLIDATED_URL}/work_orders"',
    
    # Assets  
    r'https://chatterfix-assets-[^"\']+': f'{CONSOLIDATED_URL}/assets',
    r'ASSETS_URL["\'].*?["\']': f'ASSETS_URL", "{CONSOLIDATED_URL}/assets"',
    
    # Parts
    r'https://chatterfix-parts-[^"\']+': f'{CONSOLIDATED_URL}/parts', 
    r'PARTS_URL["\'].*?["\']': f'PARTS_URL", "{CONSOLIDATED_URL}/parts"',
    
    # Deprecated services - redirect to appropriate CMMS endpoints
    r'https://chatterfix-customer-success-[^"\']+': f'{CONSOLIDATED_URL}/work_orders',
    r'https://chatterfix-revenue-intelligence-[^"\']+': f'{CONSOLIDATED_URL}/assets',
    r'https://chatterfix-data-room-[^"\']+': f'{CONSOLIDATED_URL}/parts',
}

def update_file(file_path):
    """Update a single file with new URLs"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        updated = False
        
        for pattern, replacement in URL_REPLACEMENTS.items():
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                content = new_content
                updated = True
        
        if updated:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"✅ Updated: {file_path}")
            return True
        else:
            print(f"⏭️  No changes needed: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def main():
    """Main migration function"""
    print("🔄 ChatterFix Frontend URL Migration")
    print("=" * 50)
    print(f"🌐 Migrating to consolidated service: {CONSOLIDATED_URL}")
    print()
    
    # Find all Python files in frontend directory
    frontend_files = []
    for pattern in ['./frontend/**/*.py', './frontend/*.py', './*gateway*.py', './*unified*.py']:
        frontend_files.extend(glob.glob(pattern, recursive=True))
    
    # Remove duplicates
    frontend_files = list(set(frontend_files))
    
    updated_count = 0
    total_count = len(frontend_files)
    
    print(f"📁 Found {total_count} files to check...")
    print()
    
    for file_path in frontend_files:
        if update_file(file_path):
            updated_count += 1
    
    print()
    print("=" * 50)
    print(f"✅ Migration complete!")
    print(f"📊 Updated {updated_count} out of {total_count} files")
    
    if updated_count > 0:
        print()
        print("🚀 Next steps:")
        print("1. Test your frontend with the new URLs")
        print("2. Deploy your updated frontend")
        print("3. Verify all CMMS functionality works")
        print()
        print("🌐 New endpoints:")
        print(f"   - Work Orders: {CONSOLIDATED_URL}/work_orders")
        print(f"   - Assets: {CONSOLIDATED_URL}/assets") 
        print(f"   - Parts: {CONSOLIDATED_URL}/parts")
        print(f"   - Health: {CONSOLIDATED_URL}/health")

if __name__ == "__main__":
    main()