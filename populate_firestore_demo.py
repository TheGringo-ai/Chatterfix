#!/usr/bin/env python3
"""
Populate Firestore with demo data for ChatterFix CMMS
This script is designed to run in the Cloud Run environment with Firestore access
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
from google.cloud import firestore
import bcrypt
import json

# Add the app directory to the path
sys.path.append("/app")


def get_firestore_client():
    """Initialize Firestore client for Cloud Run environment"""
    try:
        # For GCP deployment with default credentials
        return firestore.Client()
    except Exception as e:
        print(f"❌ Failed to initialize Firestore: {e}")
        return None


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def populate_demo_data():
    """Populate Firestore with comprehensive demo data"""
    db = get_firestore_client()
    if not db:
        print("❌ Could not connect to Firestore")
        return False

    try:
        # Check if data already exists
        users_ref = db.collection("users")
        existing_users = list(users_ref.limit(1).stream())
        if existing_users:
            print("✅ Demo data already exists, skipping population")
            return True

        print("🔄 Starting Firestore demo data population...")

        # 1. Create Users
        users_data = [
            {
                "id": "user_001",
                "email": "manager@evfactory.com",
                "password_hash": hash_password("demo123"),
                "full_name": "Sarah Johnson",
                "role": "Plant Manager",
                "department": "Operations",
                "phone": "+1-555-0101",
                "is_active": True,
                "created_at": datetime.now(),
                "last_login": datetime.now() - timedelta(hours=2),
            },
            {
                "id": "user_002",
                "email": "tech@evfactory.com",
                "password_hash": hash_password("demo123"),
                "full_name": "Mike Rodriguez",
                "role": "Senior Technician",
                "department": "Maintenance",
                "phone": "+1-555-0102",
                "is_active": True,
                "created_at": datetime.now() - timedelta(days=30),
                "last_login": datetime.now() - timedelta(hours=1),
            },
            {
                "id": "user_003",
                "email": "supervisor@evfactory.com",
                "password_hash": hash_password("demo123"),
                "full_name": "Jessica Chen",
                "role": "Maintenance Supervisor",
                "department": "Maintenance",
                "phone": "+1-555-0103",
                "is_active": True,
                "created_at": datetime.now() - timedelta(days=45),
                "last_login": datetime.now() - timedelta(hours=3),
            },
            {
                "id": "user_004",
                "email": "engineer@evfactory.com",
                "password_hash": hash_password("demo123"),
                "full_name": "David Park",
                "role": "Maintenance Engineer",
                "department": "Engineering",
                "phone": "+1-555-0104",
                "is_active": True,
                "created_at": datetime.now() - timedelta(days=60),
                "last_login": datetime.now() - timedelta(hours=5),
            },
            {
                "id": "user_005",
                "email": "operator@evfactory.com",
                "password_hash": hash_password("demo123"),
                "full_name": "Lisa Wang",
                "role": "Production Operator",
                "department": "Production",
                "phone": "+1-555-0105",
                "is_active": True,
                "created_at": datetime.now() - timedelta(days=20),
                "last_login": datetime.now() - timedelta(minutes=30),
            },
            {
                "id": "user_006",
                "email": "quality@evfactory.com",
                "password_hash": hash_password("demo123"),
                "full_name": "Robert Kim",
                "role": "Quality Inspector",
                "department": "Quality",
                "phone": "+1-555-0106",
                "is_active": True,
                "created_at": datetime.now() - timedelta(days=90),
                "last_login": datetime.now() - timedelta(hours=8),
            },
            {
                "id": "user_007",
                "email": "admin@evfactory.com",
                "password_hash": hash_password("admin123"),
                "full_name": "Alex Thompson",
                "role": "System Administrator",
                "department": "IT",
                "phone": "+1-555-0107",
                "is_active": True,
                "created_at": datetime.now() - timedelta(days=100),
                "last_login": datetime.now() - timedelta(minutes=15),
            },
        ]

        # Populate users
        for user_data in users_data:
            user_id = user_data.pop("id")
            db.collection("users").document(user_id).set(user_data)
        print(f"✅ Created {len(users_data)} users")

        # 2. Create Assets
        assets_data = [
            {
                "id": "asset_001",
                "name": "Battery Pack Assembly Line",
                "asset_number": "BPA-001",
                "category": "Production Equipment",
                "location": "Building A - Floor 1",
                "status": "Operational",
                "manufacturer": "AutoTech Systems",
                "model": "BPA-2000X",
                "serial_number": "BPA2000X-2023-001",
                "purchase_date": "2023-01-15",
                "warranty_expiry": "2026-01-15",
                "condition": "Good",
                "criticality": "High",
                "description": "Automated battery pack assembly line for EV production",
                "specifications": {
                    "voltage": "480V",
                    "capacity": "500 units/hour",
                    "power": "50kW",
                },
                "created_at": datetime.now() - timedelta(days=300),
                "updated_at": datetime.now() - timedelta(days=10),
            },
            {
                "id": "asset_002",
                "name": "Motor Winding Station",
                "asset_number": "MWS-002",
                "category": "Production Equipment",
                "location": "Building A - Floor 2",
                "status": "Operational",
                "manufacturer": "ElectroWind Pro",
                "model": "EWP-1500",
                "serial_number": "EWP1500-2023-002",
                "purchase_date": "2023-02-20",
                "warranty_expiry": "2026-02-20",
                "condition": "Excellent",
                "criticality": "High",
                "description": "Precision motor winding station for electric motors",
                "specifications": {
                    "precision": "±0.001mm",
                    "speed": "200 RPM",
                    "power": "25kW",
                },
                "created_at": datetime.now() - timedelta(days=280),
                "updated_at": datetime.now() - timedelta(days=5),
            },
            {
                "id": "asset_003",
                "name": "Quality Testing Station",
                "asset_number": "QTS-003",
                "category": "Quality Equipment",
                "location": "Building B - Floor 1",
                "status": "Operational",
                "manufacturer": "QualityMax",
                "model": "QM-500",
                "serial_number": "QM500-2023-003",
                "purchase_date": "2023-03-10",
                "warranty_expiry": "2026-03-10",
                "condition": "Good",
                "criticality": "Medium",
                "description": "Automated quality testing for battery components",
                "specifications": {
                    "test_capacity": "100 units/hour",
                    "accuracy": "99.9%",
                    "power": "15kW",
                },
                "created_at": datetime.now() - timedelta(days=260),
                "updated_at": datetime.now() - timedelta(days=2),
            },
        ]

        # Populate assets
        for asset_data in assets_data:
            asset_id = asset_data.pop("id")
            db.collection("assets").document(asset_id).set(asset_data)
        print(f"✅ Created {len(assets_data)} assets")

        # 3. Create Work Orders
        work_orders_data = [
            {
                "id": "wo_001",
                "title": "Battery Assembly Line Calibration",
                "description": "Perform routine calibration on battery pack assembly line sensors",
                "asset_id": "asset_001",
                "asset_name": "Battery Pack Assembly Line",
                "priority": "Medium",
                "status": "In Progress",
                "type": "Preventive Maintenance",
                "assigned_to": "user_002",
                "assigned_to_name": "Mike Rodriguez",
                "created_by": "user_001",
                "created_by_name": "Sarah Johnson",
                "estimated_hours": 4.0,
                "actual_hours": 2.5,
                "due_date": datetime.now() + timedelta(days=2),
                "created_at": datetime.now() - timedelta(days=1),
                "updated_at": datetime.now() - timedelta(hours=3),
            },
            {
                "id": "wo_002",
                "title": "Motor Winding Station Inspection",
                "description": "Monthly inspection and lubrication of motor winding equipment",
                "asset_id": "asset_002",
                "asset_name": "Motor Winding Station",
                "priority": "High",
                "status": "Completed",
                "type": "Preventive Maintenance",
                "assigned_to": "user_003",
                "assigned_to_name": "Jessica Chen",
                "created_by": "user_001",
                "created_by_name": "Sarah Johnson",
                "estimated_hours": 3.0,
                "actual_hours": 3.5,
                "due_date": datetime.now() - timedelta(days=5),
                "completed_at": datetime.now() - timedelta(days=2),
                "created_at": datetime.now() - timedelta(days=7),
                "updated_at": datetime.now() - timedelta(days=2),
            },
        ]

        # Populate work orders
        for wo_data in work_orders_data:
            wo_id = wo_data.pop("id")
            db.collection("work_orders").document(wo_id).set(wo_data)
        print(f"✅ Created {len(work_orders_data)} work orders")

        # 4. Create Inventory Items
        inventory_data = [
            {
                "id": "inv_001",
                "name": "Lithium Battery Cells",
                "part_number": "LBC-18650-3200",
                "category": "Battery Components",
                "description": "High-capacity lithium-ion battery cells for EV batteries",
                "unit": "pieces",
                "quantity_on_hand": 15000,
                "minimum_stock": 5000,
                "maximum_stock": 25000,
                "unit_cost": 12.50,
                "supplier": "BatteryTech Corp",
                "location": "Warehouse A - Rack A1",
                "status": "Active",
                "created_at": datetime.now() - timedelta(days=100),
                "updated_at": datetime.now() - timedelta(days=5),
            },
            {
                "id": "inv_002",
                "name": "Motor Magnets",
                "part_number": "MM-NEO-N42",
                "category": "Motor Components",
                "description": "Neodymium magnets for electric motor rotors",
                "unit": "pieces",
                "quantity_on_hand": 2500,
                "minimum_stock": 1000,
                "maximum_stock": 5000,
                "unit_cost": 8.75,
                "supplier": "MagnetPro Industries",
                "location": "Warehouse A - Rack B2",
                "status": "Active",
                "created_at": datetime.now() - timedelta(days=85),
                "updated_at": datetime.now() - timedelta(days=3),
            },
        ]

        # Populate inventory
        for inv_data in inventory_data:
            inv_id = inv_data.pop("id")
            db.collection("inventory").document(inv_id).set(inv_data)
        print(f"✅ Created {len(inventory_data)} inventory items")

        print("🎉 Demo data population completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error populating demo data: {e}")
        return False


if __name__ == "__main__":
    success = populate_demo_data()
    if success:
        print("✅ Firestore demo data population completed")
        sys.exit(0)
    else:
        print("❌ Firestore demo data population failed")
        sys.exit(1)
