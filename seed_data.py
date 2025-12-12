#!/usr/bin/env python3
"""
SEED DATA SCRIPT FOR CHATTERFIX CMMS
Populates the database with essential team members and equipment
"""

import requests
import json
from datetime import datetime

# ChatterFix API Base URL
BASE_URL = "https://chatterfix-cmms-650169261019.us-central1.run.app"

class ChatterFixSeeder:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'ChatterFix-Seeder/1.0'
        })
    
    def create_team_members(self):
        """Create the core team members"""
        print("🔧 CREATING TEAM MEMBERS...")
        
        team_members = [
            {
                "username": "commander",
                "name": "Commander",
                "email": "commander@chatterfix.com",
                "password": "ChatterFix2025!",
                "role": "Maintenance Manager",
                "department": "Maintenance",
                "skills": ["Management", "Leadership", "Strategic Planning"],
                "phone": "555-0101",
                "active": True,
                "admin": True
            },
            {
                "username": "alpha",
                "name": "Alpha",
                "email": "alpha@chatterfix.com",
                "password": "ChatterFix2025!",
                "role": "Senior Technician",
                "department": "Maintenance",
                "skills": ["Electrical", "HVAC", "Leadership"],
                "phone": "555-0102",
                "active": True
            },
            {
                "username": "bravo",
                "name": "Bravo",
                "email": "bravo@chatterfix.com",
                "password": "ChatterFix2025!",
                "role": "Maintenance Technician",
                "department": "Maintenance",
                "skills": ["Mechanical", "Welding", "Hydraulics"],
                "phone": "555-0103",
                "active": True
            },
            {
                "username": "charlie",
                "name": "Charlie",
                "email": "charlie@chatterfix.com",
                "password": "ChatterFix2025!",
                "role": "Maintenance Technician",
                "department": "Maintenance", 
                "skills": ["Plumbing", "Electrical", "Troubleshooting"],
                "phone": "555-0104",
                "active": True
            },
            {
                "username": "delta",
                "name": "Delta",
                "email": "delta@chatterfix.com",
                "password": "ChatterFix2025!",
                "role": "Equipment Specialist",
                "department": "Maintenance",
                "skills": ["Heavy Equipment", "Diagnostics", "Preventive Maintenance"],
                "phone": "555-0105",
                "active": True
            },
            {
                "username": "echo",
                "name": "Echo",
                "email": "echo@chatterfix.com",
                "password": "ChatterFix2025!",
                "role": "Safety Technician",
                "department": "Maintenance",
                "skills": ["Safety Protocols", "OSHA Compliance", "Emergency Response"],
                "phone": "555-0106",
                "active": True
            }
        ]
        
        created_users = []
        
        for member in team_members:
            try:
                response = self.session.post(f"{BASE_URL}/settings/users/add", json=member, timeout=30)
                if response.status_code in [200, 201]:
                    print(f"✅ Created user: {member['name']}")
                    created_users.append(member['name'])
                else:
                    print(f"❌ Failed to create user {member['name']}: {response.status_code}")
                    print(f"   Response: {response.text}")
            except Exception as e:
                print(f"❌ Error creating user {member['name']}: {str(e)}")
        
        return created_users
    
    def create_assets(self):
        """Create essential assets including Douglas Washer"""
        print("\n🏭 CREATING ASSETS...")
        
        assets = [
            {
                "name": "Douglas Washer",
                "type": "Washing Equipment",
                "manufacturer": "Douglas Manufacturing",
                "model": "2024 Industrial",
                "serial_number": "DW-998877",
                "location": "Laundry Facility - Bay 1",
                "status": "Active",
                "purchase_date": "2024-01-15",
                "warranty_expiry": "2027-01-15",
                "criticality": "High",
                "description": "Industrial washing machine for heavy-duty cleaning operations - 2024 model with enhanced features",
                "specifications": {
                    "capacity": "50 lbs",
                    "voltage": "480V",
                    "water_pressure": "40-80 PSI",
                    "dimensions": "36\"W x 42\"D x 54\"H"
                }
            },
            {
                "name": "Honeywell Fire System",
                "type": "Fire Safety System",
                "manufacturer": "Honeywell", 
                "model": "Notifier NFS2-3030",
                "serial_number": "HW-2024-FSS",
                "location": "Building Central - Main Panel",
                "status": "Active",
                "purchase_date": "2024-02-10",
                "warranty_expiry": "2027-02-10", 
                "criticality": "Critical",
                "description": "Advanced fire detection and suppression system with integrated monitoring"
            }
        ]
        
        created_assets = []
        
        for asset in assets:
            try:
                response = self.session.post(f"{BASE_URL}/assets/", json=asset, timeout=30)
                if response.status_code in [200, 201]:
                    print(f"✅ Created asset: {asset['name']}")
                    created_assets.append(asset['name'])
                else:
                    print(f"❌ Failed to create asset {asset['name']}: {response.status_code}")
                    print(f"   Response: {response.text}")
            except Exception as e:
                print(f"❌ Error creating asset {asset['name']}: {str(e)}")
        
        return created_assets
    
    def create_work_orders(self, users, assets):
        """Create sample work orders"""
        print("\n📝 CREATING SAMPLE WORK ORDERS...")
        
        if not users or not assets:
            print("⚠️  Skipping work orders - missing users or assets")
            return []
        
        work_orders = [
            {
                "title": "Douglas Washer - Weekly Inspection",
                "description": "Perform weekly inspection and maintenance on Douglas Washer including filter cleaning and calibration check",
                "asset_name": "Douglas Washer",
                "assigned_to": "Bravo",
                "priority": "Medium",
                "status": "Open",
                "created_date": datetime.now().strftime("%Y-%m-%d"),
                "due_date": "2024-12-19",
                "estimated_hours": 2,
                "work_type": "Preventive Maintenance"
            },
            {
                "title": "Fire System Inspection",
                "description": "Quarterly inspection of Honeywell fire detection system - check sensors and test alarm functionality",
                "asset_name": "Honeywell Fire System", 
                "assigned_to": "Alpha",
                "priority": "High",
                "status": "Open",
                "created_date": datetime.now().strftime("%Y-%m-%d"),
                "due_date": "2024-12-20",
                "estimated_hours": 3,
                "work_type": "Preventive Maintenance"
            }
        ]
        
        created_orders = []
        
        for order in work_orders:
            try:
                response = self.session.post(f"{BASE_URL}/work-orders", json=order, timeout=30)
                if response.status_code in [200, 201]:
                    print(f"✅ Created work order: {order['title']}")
                    created_orders.append(order['title'])
                else:
                    print(f"❌ Failed to create work order {order['title']}: {response.status_code}")
                    print(f"   Response: {response.text}")
            except Exception as e:
                print(f"❌ Error creating work order {order['title']}: {str(e)}")
        
        return created_orders
    
    def verify_seeded_data(self):
        """Verify that seeded data was created successfully"""
        print("\n🔍 VERIFYING SEEDED DATA...")
        
        verification_results = {
            "users": 0,
            "assets": 0,
            "douglas_washer": False,
            "team_members": []
        }
        
        # Verify users
        try:
            response = self.session.get(f"{BASE_URL}/api/users", timeout=30)
            if response.status_code == 200:
                users = response.json()
                verification_results["users"] = len(users)
                
                target_team = ["Commander", "Alpha", "Bravo", "Charlie", "Delta", "Echo"]
                for user in users:
                    if isinstance(user, dict) and 'name' in user:
                        for target in target_team:
                            if target.lower() in user['name'].lower():
                                verification_results["team_members"].append(target)
                
                print(f"✅ Users found: {verification_results['users']}")
                print(f"✅ Team members found: {verification_results['team_members']}")
            
        except Exception as e:
            print(f"❌ Error verifying users: {str(e)}")
        
        # Verify assets
        try:
            response = self.session.get(f"{BASE_URL}/api/assets", timeout=30)
            if response.status_code == 200:
                assets = response.json()
                verification_results["assets"] = len(assets)
                
                for asset in assets:
                    if isinstance(asset, dict) and 'name' in asset:
                        if 'douglas' in asset['name'].lower() and 'washer' in asset['name'].lower():
                            verification_results["douglas_washer"] = True
                            break
                
                print(f"✅ Assets found: {verification_results['assets']}")
                print(f"✅ Douglas Washer found: {verification_results['douglas_washer']}")
            
        except Exception as e:
            print(f"❌ Error verifying assets: {str(e)}")
        
        return verification_results
    
    def run_seed_process(self):
        """Execute the complete seeding process"""
        print("🚀 CHATTERFIX CMMS SEED DATA PROCESS")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target URL: {BASE_URL}")
        print("="*60)
        
        # Create team members
        created_users = self.create_team_members()
        
        # Create assets
        created_assets = self.create_assets()
        
        # Create work orders
        created_orders = self.create_work_orders(created_users, created_assets)
        
        # Verify data
        verification = self.verify_seeded_data()
        
        # Final report
        print("\n" + "="*60)
        print("  SEED DATA SUMMARY REPORT")
        print("="*60)
        print(f"Users Created: {len(created_users)}")
        print(f"Assets Created: {len(created_assets)}")
        print(f"Work Orders Created: {len(created_orders)}")
        print(f"\nVerification Results:")
        print(f"  Total Users in DB: {verification['users']}")
        print(f"  Total Assets in DB: {verification['assets']}")
        print(f"  Douglas Washer: {'✅ FOUND' if verification['douglas_washer'] else '❌ NOT FOUND'}")
        print(f"  Team Members: {verification['team_members']}")
        
        success = (
            len(created_users) >= 3 and 
            len(created_assets) >= 1 and
            verification['douglas_washer']
        )
        
        status = "✅ SEED DATA PROCESS COMPLETED SUCCESSFULLY" if success else "⚠️  SEED DATA PROCESS COMPLETED WITH ISSUES"
        print(f"\n🎯 {status}")
        
        return success

def main():
    """Main execution function"""
    seeder = ChatterFixSeeder()
    success = seeder.run_seed_process()
    
    if success:
        print("\n🎉 Your ChatterFix CMMS is now populated with essential data!")
        print("   - Team members are ready to be assigned work")
        print("   - Douglas Washer and other assets are in the system") 
        print("   - Sample work orders have been created")
        print("\n🔧 Next steps:")
        print("   1. Run the smoke test again to verify everything passes")
        print("   2. Log into ChatterFix and review the seeded data")
        print("   3. Customize the data as needed for your organization")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)