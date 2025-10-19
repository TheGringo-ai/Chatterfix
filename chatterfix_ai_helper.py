#!/usr/bin/env python3
"""
ChatterFix AI Helper - Integration Demo
Shows how ChatterFix CMMS integrates with Fix It Fred Universal AI Assistant
"""

import requests
import json
from datetime import datetime

class ChatterFixAIHelper:
    def __init__(self, fred_base_url="http://localhost:8011", cmms_work_orders_url="http://localhost:8013"):
        self.fred_url = fred_base_url
        self.work_orders_url = cmms_work_orders_url
        self.app_id = "chatterfix-cmms"
    
    def ask_ai(self, question, conversation_id=None):
        """Ask the ChatterFix-specific AI assistant a question"""
        data = {
            "message": question,
            "provider": "anthropic"
        }
        if conversation_id:
            data["conversation_id"] = conversation_id
            
        try:
            response = requests.post(f"{self.fred_url}/api/apps/{self.app_id}/chat", json=data)
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_work_orders(self):
        """Get current work orders from CMMS"""
        try:
            response = requests.get(f"{self.work_orders_url}/api/work_orders")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def create_work_order(self, title, description, priority="medium", technician=None):
        """Create a new work order"""
        data = {
            "title": title,
            "description": description,
            "priority": priority,
            "status": "open"
        }
        if technician:
            data["technician"] = technician
            
        try:
            response = requests.post(f"{self.work_orders_url}/api/work_orders", json=data)
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def demo_integration(self):
        """Demonstrate the integration between Fix It Fred AI and ChatterFix CMMS"""
        print("🤖 ChatterFix AI Helper - Integration Demo")
        print("=" * 50)
        
        # 1. Get current work orders
        print("\n📋 Current Work Orders:")
        work_orders = self.get_work_orders()
        if work_orders.get("success"):
            for wo in work_orders.get("work_orders", []):
                print(f"  #{wo['id']}: {wo['title']} - {wo['status']} ({wo['priority']})")
        
        # 2. Ask AI about work order management
        print("\n🤖 AI Assistant Response:")
        ai_response = self.ask_ai("How should I prioritize work orders for optimal maintenance efficiency?")
        if ai_response.get("success"):
            print(f"  AI: {ai_response['response']}")
        else:
            print(f"  AI Error: {ai_response.get('response', 'Unknown error')}")
        
        # 3. Create a new work order with AI guidance
        print("\n➕ Creating New Work Order:")
        new_wo = self.create_work_order(
            "Replace HVAC filters in East Wing",
            "Scheduled monthly maintenance for HVAC system filters",
            "medium",
            "Mike Johnson"
        )
        if new_wo.get("success"):
            print(f"  ✅ Work order created successfully")
        else:
            print(f"  ❌ Error: {new_wo.get('error', 'Unknown error')}")
        
        # 4. Show updated work orders
        print("\n📋 Updated Work Orders:")
        work_orders = self.get_work_orders()
        if work_orders.get("success"):
            for wo in work_orders.get("work_orders", []):
                print(f"  #{wo['id']}: {wo['title']} - {wo['status']} ({wo['priority']})")
        
        print("\n✅ Integration demo complete!")

if __name__ == "__main__":
    helper = ChatterFixAIHelper()
    helper.demo_integration()