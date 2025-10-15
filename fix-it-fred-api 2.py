#!/usr/bin/env python3
"""
Fix It Fred Live Editing Interface
Simplified API for making live code changes
"""

import os
import requests
import json
from typing import Optional

class FixItFredEditor:
    def __init__(self, vm_ip: str = "35.237.149.25"):
        self.base_url = f"http://{vm_ip}:8001"
        self.main_app_url = f"http://{vm_ip}:8080"
    
    def test_connection(self) -> bool:
        """Test if live editor is accessible"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_file_content(self, filename: str) -> Optional[str]:
        """Get current content of a file"""
        try:
            response = requests.get(f"{self.base_url}/files/{filename}")
            if response.status_code == 200:
                return response.json()["content"]
            return None
        except:
            return None
    
    def edit_file(self, filename: str, old_content: str, new_content: str, description: str) -> dict:
        """Make a live edit to a file"""
        data = {
            "file_path": filename,
            "old_content": old_content,
            "new_content": new_content,
            "description": description
        }
        
        try:
            response = requests.post(f"{self.base_url}/edit/{filename}", json=data)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def quick_fix(self, issue_description: str, file_section: str, new_code: str) -> dict:
        """Quick fix for common issues"""
        # For now, assume we're editing app.py
        filename = "app.py"
        
        result = self.edit_file(
            filename=filename,
            old_content=file_section,
            new_content=new_code,
            description=f"Fix It Fred: {issue_description}"
        )
        
        return result
    
    def add_new_endpoint(self, endpoint_code: str, description: str) -> dict:
        """Add a new API endpoint"""
        filename = "app.py"
        current_content = self.get_file_content(filename)
        
        if not current_content:
            return {"success": False, "error": "Could not read app.py"}
        
        # Insert before the main block
        insertion_point = 'if __name__ == "__main__":'
        if insertion_point in current_content:
            new_content = current_content.replace(
                insertion_point,
                f"{endpoint_code}\n\n{insertion_point}"
            )
            
            return self.edit_file(
                filename=filename,
                old_content=current_content,
                new_content=new_content,
                description=f"Add endpoint: {description}"
            )
        
        return {"success": False, "error": "Could not find insertion point"}
    
    def update_feature(self, feature_name: str, old_implementation: str, new_implementation: str) -> dict:
        """Update an existing feature"""
        return self.edit_file(
            filename="app.py",
            old_content=old_implementation,
            new_content=new_implementation,
            description=f"Update feature: {feature_name}"
        )
    
    def test_change(self) -> dict:
        """Test if the main app is still responding after changes"""
        try:
            response = requests.get(f"{self.main_app_url}/health", timeout=10)
            return {
                "healthy": response.status_code == 200,
                "response": response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}

# Example usage for Fix It Fred
def example_usage():
    """Example of how Fix It Fred can use this"""
    editor = FixItFredEditor()
    
    # Test connection
    if not editor.test_connection():
        print("❌ Live editor not available")
        return
    
    print("✅ Live editor connected")
    
    # Example: Add a new endpoint
    new_endpoint = '''
@app.get("/fix-it-fred-test")
async def fix_it_fred_test():
    """Test endpoint added by Fix It Fred"""
    return {
        "message": "Fix It Fred live editing works!",
        "timestamp": datetime.now().isoformat(),
        "status": "success"
    }'''
    
    result = editor.add_new_endpoint(new_endpoint, "Test endpoint")
    print(f"Add endpoint result: {result}")
    
    # Test the change
    test_result = editor.test_change()
    print(f"Health check after change: {test_result}")

if __name__ == "__main__":
    example_usage()