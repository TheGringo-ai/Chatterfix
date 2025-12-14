import asyncio
import os
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

import firebase_admin
from firebase_admin import credentials, auth
from faker import Faker

# Ensure app path is in sys.path for local imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.firestore_db import FirestoreManager
from app.services.auth_service import get_permissions_for_role


# Initialize Firebase Admin SDK (similar to auth_service.py)
def initialize_firebase_app():
    if not firebase_admin._apps:
        try:
            # The SDK will automatically use the GOOGLE_APPLICATION_CREDENTIALS env var
            # if it's set and valid.
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)
            print("✅ Firebase Admin SDK initialized successfully.")
        except Exception as e:
            print(f"❌ Failed to initialize Firebase Admin SDK: {e}")
            print(
                "Please ensure the GOOGLE_APPLICATION_CREDENTIALS environment variable is set "
                "correctly to a valid service account JSON file."
            )
            sys.exit(1)

async def populate_firestore():
    initialize_firebase_app()
    firestore_manager = FirestoreManager()
    fake = Faker()

    print("\n🚀 Starting Firestore Database Population...")
    print("-------------------------------------------\
")

    # --- 1. Create Users (in Firebase Auth and Firestore) ---
    print("👤 Creating Users...")
    user_roles = ["manager", "supervisor", "planner", "parts_manager", "technician", "requestor"]
    users_to_create: List[Dict[str, Any]] = []

    # Create one user for each role + a few extra technicians
    for i, role in enumerate(user_roles):
        email = f"{role}@{fake.domain_name()}"
        password = "password123" # Secure password for demo
        display_name = f"{fake.first_name()} {fake.last_name()}"
        
        users_to_create.append({
            "email": email,
            "password": password,
            "display_name": display_name,
            "role": role
        })

    # Add a couple more technicians
    for _ in range(2):
        email = f"tech{_ + 1}@{fake.domain_name()}"
        password = "password123"
        display_name = f"{fake.first_name()} {fake.last_name()}"
        users_to_create.append({
            "email": email,
            "password": password,
            "display_name": display_name,
            "role": "technician"
        })
    
    # Store created Firebase users to link with Firestore documents
    firebase_users = {}
    firestore_users = []

    for user_data in users_to_create:
        try:
            # Create user in Firebase Authentication
            user_record = auth.create_user(
                email=user_data["email"],
                password=user_data["password"],
                display_name=user_data["display_name"]
            )
            firebase_users[user_data["role"]] = user_record
            print(f"  ✅ Created Firebase Auth user: {user_data['display_name']} ({user_data['role']})")

            # Create user document in Firestore (keyed by UID)
            user_doc_data = {
                "email": user_data["email"],
                "full_name": user_data["display_name"],
                "role": user_data["role"],
                "disabled": False,
                "created_at": datetime.now(timezone.utc),
                "last_login": datetime.now(timezone.utc),
                "permissions": get_permissions_for_role(user_data["role"]) # Add permissions to user document
            }
            await firestore_manager.create_document("users", user_doc_data, doc_id=user_record.uid)
            firestore_users.append({"uid": user_record.uid, "email": user_data["email"], "role": user_data["role"], "full_name": user_data["display_name"]})
            print(f"    ✅ Created Firestore user document for UID: {user_record.uid}")

        except Exception as e:
            print(f"  ❌ Failed to create user {user_data['email']}: {e}")

    # Ensure we have at least one manager and technician for relationships
    manager_uid = next((u["uid"] for u in firestore_users if u["role"] == "manager"), None)
    technician_uids = [u["uid"] for u in firestore_users if u["role"] == "technician"]
    if not manager_uid or not technician_uids:
        print("⚠️ Not enough users created. Please ensure Firebase Auth setup is correct.")
        return

    # --- 2. Create Assets ---
    print("\n🏭 Creating Assets...")
    assets_to_create = []
    for _ in range(10):
        asset_type = random.choice(["Pump", "Motor", "HVAC Unit", "Conveyor Belt", "Sensor Array"])
        status = random.choice(["Operational", "Maintenance", "Offline", "Retired"])
        assets_to_create.append({
            "name": f"{fake.word().capitalize()} {asset_type} {fake.random_int(1, 100)}",
            "type": asset_type,
            "manufacturer": fake.company(),
            "model": fake.bothify(text="???-###"),
            "serial_number": fake.uuid4(),
            "location": fake.address(),
            "status": status,
            "criticality": random.choice(["Low", "Medium", "High", "Critical"]),
            "purchase_date": fake.date_this_decade().isoformat(),
            "last_maintenance_date": fake.date_this_year().isoformat(),
            "next_maintenance_date": (fake.date_this_year() + timedelta(days=random.randint(30, 365))).isoformat(),
            "image_url": fake.image_url()
        })
    
    created_assets = []
    for asset_data in assets_to_create:
        try:
            asset_id = await firestore_manager.create_document("assets", asset_data)
            created_assets.append({"id": asset_id, "name": asset_data["name"]})
            print(f"  ✅ Created asset: {asset_data['name']} (ID: {asset_id})")
        except Exception as e:
            print(f"  ❌ Failed to create asset {asset_data['name']}: {e}")

    # --- 3. Create Parts Inventory ---
    print("\n📦 Creating Parts Inventory...")
    parts_to_create = []
    for _ in range(15):
        parts_to_create.append({
            "name": f"{fake.word().capitalize()} {fake.word().capitalize()} Bearing",
            "part_number": fake.bothify(text="PN-###-???"),
            "description": fake.sentence(),
            "current_stock": fake.random_int(5, 50),
            "minimum_stock": fake.random_int(1, 10),
            "unit_cost": round(random.uniform(10.0, 500.0), 2),
            "supplier": fake.company(),
            "location": fake.word().capitalize() + " Warehouse",
        })

    created_parts = []
    for part_data in parts_to_create:
        try:
            part_id = await firestore_manager.create_document("parts", part_data)
            created_parts.append({"id": part_id, "name": part_data["name"]})
            print(f"  ✅ Created part: {part_data['name']} (ID: {part_id})")
        except Exception as e:
            print(f"  ❌ Failed to create part {part_data['name']}: {e}")


    # --- 4. Create Work Orders ---
    print("\n📝 Creating Work Orders...")
    if not created_assets or not firestore_users:
        print("  ⚠️ Skipping work order creation: No assets or users available.")
    else:
        for _ in range(20):
            asset = random.choice(created_assets)
            assigned_tech = random.choice(technician_uids)
            priority = random.choice(["Low", "Medium", "High", "Critical"])
            status = random.choice(["Open", "In Progress", "Completed", "On Hold"])
            created_at = fake.date_this_year()
            due_date = created_at + timedelta(days=random.randint(1, 30))

            work_order_data = {
                "title": f"Inspect {asset['name']} - {fake.catch_phrase()}",
                "description": fake.paragraph(),
                "asset_id": asset["id"],
                "asset_name": asset["name"],
                "assigned_to_uid": assigned_tech,
                "assigned_to_name": next((u["full_name"] for u in firestore_users if u["uid"] == assigned_tech), "Unknown Technician"),
                "priority": priority,
                "status": status,
                "created_date": created_at.isoformat(),
                "due_date": due_date.isoformat(),
                "estimated_hours": round(random.uniform(1.0, 8.0), 1),
                "work_order_type": random.choice(["Preventive", "Corrective", "Predictive", "Emergency"])
            }
            if status == "Completed":
                work_order_data["completed_date"] = (due_date - timedelta(days=random.randint(0,2))).isoformat()
                work_order_data["actual_hours"] = work_order_data["estimated_hours"] - round(random.uniform(-1,1), 1)

            try:
                wo_id = await firestore_manager.create_document("work_orders", work_order_data)
                print(f"  ✅ Created work order: {work_order_data['title']} (ID: {wo_id})")
            except Exception as e:
                print(f"  ❌ Failed to create work order {work_order_data['title']}: {e}")

    # --- 5. Create Training Modules ---
    print("\n📚 Creating Training Modules...")
    training_modules_to_create = []
    for _ in range(5):
        asset_type = random.choice(["Pump", "Motor", "HVAC Unit"])
        skill_category = random.choice(["Electrical", "Mechanical", "Safety", "Hydraulics"])
        training_modules_to_create.append({
            "title": f"{fake.word().capitalize()} {skill_category} Module for {asset_type}",
            "description": fake.text(),
            "asset_type": asset_type,
            "skill_category": skill_category,
            "estimated_duration_minutes": fake.random_int(15, 120),
            "difficulty_level": random.randint(1, 5),
            "ai_generated": True,
            "content_path": "{\"sections\": [{\"title\": \"Intro\", \"body\": \"...\"}]}" # Mock JSON content
        })
    
    created_training_modules = []
    for module_data in training_modules_to_create:
        try:
            module_id = await firestore_manager.create_document("training_modules", module_data)
            created_training_modules.append({"id": module_id, "title": module_data["title"]})
            print(f"  ✅ Created training module: {module_data['title']} (ID: {module_id})")
        except Exception as e:
            print(f"  ❌ Failed to create training module {module_data['title']}: {e}")

    # --- 6. Assign User Training ---
    print("\n🧑‍🎓 Assigning User Training...")
    if not created_training_modules or not firestore_users:
        print("  ⚠️ Skipping user training assignment: No training modules or users available.")
    else:
        for user_item in firestore_users:
            if user_item["role"] == "technician":
                for _ in range(random.randint(1, 3)): # Assign 1-3 modules per technician
                    module = random.choice(created_training_modules)
                    status = random.choice(["assigned", "in_progress", "completed"])
                    
                    training_assignment_data = {
                        "user_id": user_item["uid"],
                        "training_module_id": module["id"],
                        "status": status,
                        "assigned_date": fake.date_this_year().isoformat(),
                    }
                    if status in ["in_progress", "completed"]:
                        training_assignment_data["started_date"] = (fake.date_this_year() + timedelta(days=random.randint(1, 10))).isoformat()
                    if status == "completed":
                        training_assignment_data["completed_date"] = (training_assignment_data["started_date"] + timedelta(days=random.randint(1, 5))).isoformat()
                        training_assignment_data["score"] = random.randint(70, 100)
                    
                    try:
                        assignment_id = await firestore_manager.create_document("user_training", training_assignment_data)
                        print(f"  ✅ Assigned '{module['title']}' to {user_item['full_name']} (Status: {status})")
                    except Exception as e:
                        print(f"  ❌ Failed to assign training {module['title']} to {user_item['full_name']}: {e}")


    print("\n--- Population Complete ---")
    print(f"  Users created in Firebase Auth: {len(firebase_users)}")
    print(f"  User documents created in Firestore: {len(firestore_users)}")
    print(f"  Assets created: {len(created_assets)}")
    print(f"  Parts created: {len(created_parts)}")
    print(f"  Training modules created: {len(created_training_modules)}")
    print("-------------------------------------------\
")


if __name__ == "__main__":
    asyncio.run(populate_firestore())
