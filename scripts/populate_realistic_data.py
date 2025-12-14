import asyncio
import os
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

import firebase_admin
from firebase_admin import credentials, auth

# Ensure app path is in sys.path for local imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.firestore_db import FirestoreManager
from app.services.auth_service import get_permissions_for_role


# ============================================================================
# REALISTIC CMMS DATA - Proper maintenance terminology and equipment names
# ============================================================================

REALISTIC_ASSETS = [
    {"name": "CNC Milling Machine #1", "type": "CNC Machine", "manufacturer": "Haas Automation", "model": "VF-2", "location": "Machine Shop - Bay 1"},
    {"name": "CNC Milling Machine #2", "type": "CNC Machine", "manufacturer": "Haas Automation", "model": "VF-4", "location": "Machine Shop - Bay 2"},
    {"name": "Hydraulic Press 50-Ton", "type": "Press", "manufacturer": "Dake", "model": "50H", "location": "Fabrication Area"},
    {"name": "Air Compressor - Main", "type": "Compressor", "manufacturer": "Ingersoll Rand", "model": "R-Series 37kW", "location": "Utility Room"},
    {"name": "Cooling Tower #1", "type": "HVAC", "manufacturer": "Baltimore Aircoil", "model": "Series 3000", "location": "Roof - North"},
    {"name": "Chiller Unit - Primary", "type": "HVAC", "manufacturer": "Carrier", "model": "30XA-200", "location": "Mechanical Room"},
    {"name": "Conveyor Belt - Line A", "type": "Conveyor", "manufacturer": "Dorner", "model": "3200 Series", "location": "Production Line A"},
    {"name": "Conveyor Belt - Line B", "type": "Conveyor", "manufacturer": "Dorner", "model": "3200 Series", "location": "Production Line B"},
    {"name": "Forklift - Electric #1", "type": "Material Handling", "manufacturer": "Toyota", "model": "8FBE18U", "location": "Warehouse"},
    {"name": "Forklift - Electric #2", "type": "Material Handling", "manufacturer": "Crown", "model": "FC5200", "location": "Warehouse"},
    {"name": "Industrial Oven - Curing", "type": "Thermal Equipment", "manufacturer": "Grieve", "model": "NB-350", "location": "Paint Shop"},
    {"name": "Paint Booth - Main", "type": "Finishing Equipment", "manufacturer": "Global Finishing", "model": "ES-2000", "location": "Paint Shop"},
    {"name": "Boiler - Steam", "type": "Boiler", "manufacturer": "Cleaver-Brooks", "model": "CB-200", "location": "Boiler Room"},
    {"name": "Emergency Generator", "type": "Power Equipment", "manufacturer": "Caterpillar", "model": "C15", "location": "Generator Building"},
    {"name": "Electrical Panel - Main", "type": "Electrical", "manufacturer": "Schneider Electric", "model": "Masterpact", "location": "Electrical Room"},
    {"name": "Welding Station #1", "type": "Welding Equipment", "manufacturer": "Lincoln Electric", "model": "Power MIG 360MP", "location": "Weld Shop"},
    {"name": "Lathe - CNC", "type": "CNC Machine", "manufacturer": "Mazak", "model": "QT-200", "location": "Machine Shop - Bay 3"},
    {"name": "Pump - Coolant System", "type": "Pump", "manufacturer": "Grundfos", "model": "CR 32-4", "location": "Machine Shop"},
    {"name": "AHU - Production Floor", "type": "HVAC", "manufacturer": "Trane", "model": "M-Series", "location": "Mezzanine"},
    {"name": "Fire Suppression Panel", "type": "Safety Equipment", "manufacturer": "Simplex", "model": "4100ES", "location": "Main Entrance"},
]

REALISTIC_PARTS = [
    {"name": "Bearing - Deep Groove", "part_number": "BRG-6205-2RS", "description": "Deep groove ball bearing, 25x52x15mm, sealed", "unit_cost": 15.75, "category": "Bearings"},
    {"name": "V-Belt - Industrial", "part_number": "BLT-A68", "description": "A-section V-belt, 68 inch length", "unit_cost": 12.50, "category": "Belts"},
    {"name": "Hydraulic Filter Element", "part_number": "HYD-FLT-10M", "description": "10 micron hydraulic filter, 6x12 inch", "unit_cost": 45.00, "category": "Filters"},
    {"name": "Contactor - 3 Pole", "part_number": "CONT-3P-40A", "description": "40A 3-pole contactor, 120V coil", "unit_cost": 78.50, "category": "Electrical"},
    {"name": "Fuse - Industrial", "part_number": "FUSE-30A-600V", "description": "30A 600V time-delay fuse", "unit_cost": 8.25, "category": "Electrical"},
    {"name": "Pneumatic Cylinder Seal Kit", "part_number": "CYL-SK-2IN", "description": "Seal kit for 2-inch bore pneumatic cylinder", "unit_cost": 35.00, "category": "Pneumatics"},
    {"name": "Motor - 5HP 3-Phase", "part_number": "MTR-5HP-1800", "description": "5HP 1800RPM 3-phase motor, TEFC", "unit_cost": 485.00, "category": "Motors"},
    {"name": "Coupling - Flexible", "part_number": "COUP-FLEX-1.5", "description": "1.5 inch flexible jaw coupling", "unit_cost": 95.25, "category": "Power Transmission"},
    {"name": "Oil - Hydraulic AW46", "part_number": "OIL-HYD-AW46", "description": "5 gallon hydraulic oil AW46", "unit_cost": 65.00, "category": "Lubricants"},
    {"name": "Grease - Multi-Purpose", "part_number": "GRS-MP-14OZ", "description": "14oz cartridge multi-purpose grease", "unit_cost": 8.50, "category": "Lubricants"},
    {"name": "Air Filter - Compressor", "part_number": "AF-COMP-IR37", "description": "Replacement air filter for IR 37kW compressor", "unit_cost": 125.00, "category": "Filters"},
    {"name": "Limit Switch", "part_number": "LS-HD-SPDT", "description": "Heavy duty limit switch SPDT", "unit_cost": 42.00, "category": "Sensors"},
    {"name": "Proximity Sensor - Inductive", "part_number": "PROX-IND-8MM", "description": "8mm inductive proximity sensor, NPN", "unit_cost": 55.00, "category": "Sensors"},
    {"name": "Solenoid Valve - 24VDC", "part_number": "SOL-24V-1/4", "description": "1/4 inch 24VDC solenoid valve", "unit_cost": 68.00, "category": "Valves"},
    {"name": "Pressure Gauge", "part_number": "PG-0-100PSI", "description": "0-100 PSI pressure gauge, 2.5 inch dial", "unit_cost": 28.00, "category": "Instrumentation"},
    {"name": "Chain - Roller #60", "part_number": "CHAIN-60-10FT", "description": "10 feet of #60 roller chain", "unit_cost": 45.75, "category": "Power Transmission"},
    {"name": "Sprocket - #60 24T", "part_number": "SPRKT-60-24", "description": "#60 chain sprocket, 24 teeth", "unit_cost": 32.50, "category": "Power Transmission"},
    {"name": "Pilot Light - LED Green", "part_number": "PLT-LED-GRN", "description": "22mm LED pilot light, green, 24V", "unit_cost": 12.75, "category": "Electrical"},
    {"name": "Push Button - Emergency Stop", "part_number": "PB-ESTOP-40", "description": "40mm mushroom head E-stop, NC", "unit_cost": 35.00, "category": "Electrical"},
    {"name": "Thermostat - Industrial", "part_number": "THERM-IND-F", "description": "Industrial thermostat, 40-110F range", "unit_cost": 85.00, "category": "HVAC"},
]

WORK_ORDER_TEMPLATES = [
    # Preventive Maintenance
    {"title": "PM - Monthly Lubrication", "type": "Preventive", "description": "Perform monthly lubrication on all grease points per PM schedule. Check oil levels and top off as needed."},
    {"title": "PM - Quarterly Inspection", "type": "Preventive", "description": "Complete quarterly inspection checklist. Check belt tension, bearing condition, and general equipment condition."},
    {"title": "PM - Annual Overhaul", "type": "Preventive", "description": "Annual preventive maintenance overhaul. Replace wear parts, clean thoroughly, and verify calibration."},
    {"title": "PM - Filter Replacement", "type": "Preventive", "description": "Replace all air and oil filters per maintenance schedule. Document filter condition."},
    {"title": "PM - Belt Inspection and Tensioning", "type": "Preventive", "description": "Inspect all drive belts for wear, cracks, and proper tension. Adjust or replace as needed."},

    # Corrective Maintenance
    {"title": "Repair - Unusual Vibration", "type": "Corrective", "description": "Equipment exhibiting unusual vibration. Investigate root cause and repair. Check bearings and alignment."},
    {"title": "Repair - Overheating Issue", "type": "Corrective", "description": "Equipment running hot. Check cooling system, clean heat exchangers, and verify proper airflow."},
    {"title": "Repair - Hydraulic Leak", "type": "Corrective", "description": "Hydraulic oil leak detected. Locate source of leak, replace seals/fittings as needed."},
    {"title": "Repair - Electrical Fault", "type": "Corrective", "description": "Intermittent electrical fault reported. Troubleshoot electrical system and repair."},
    {"title": "Repair - Abnormal Noise", "type": "Corrective", "description": "Operator reported abnormal noise during operation. Investigate and correct."},
    {"title": "Repair - Pressure Drop", "type": "Corrective", "description": "System pressure not reaching setpoint. Check for leaks, worn pump, or clogged filters."},
    {"title": "Repair - Motor Not Starting", "type": "Corrective", "description": "Motor fails to start. Check electrical connections, overloads, and motor windings."},

    # Emergency
    {"title": "Emergency - Equipment Down", "type": "Emergency", "description": "URGENT: Equipment completely down, halting production. Immediate response required."},
    {"title": "Emergency - Safety Concern", "type": "Emergency", "description": "URGENT: Safety issue identified. Equipment locked out until repairs complete."},

    # Inspection
    {"title": "Inspection - Safety Systems", "type": "Inspection", "description": "Inspect all safety systems including E-stops, guards, and interlocks. Document findings."},
    {"title": "Inspection - Pre-Shift Check", "type": "Inspection", "description": "Complete pre-shift inspection checklist. Verify fluid levels, guards in place, and general condition."},
]

TECHNICIAN_NAMES = [
    "Mike Rodriguez",
    "Sarah Chen",
    "James Wilson",
    "Maria Garcia",
    "David Thompson",
    "Jennifer Martinez",
    "Robert Johnson",
    "Emily Davis",
]

USERS_TO_CREATE = [
    {"email": "mike.rodriguez@company.com", "display_name": "Mike Rodriguez", "role": "technician"},
    {"email": "sarah.chen@company.com", "display_name": "Sarah Chen", "role": "technician"},
    {"email": "james.wilson@company.com", "display_name": "James Wilson", "role": "technician"},
    {"email": "maria.garcia@company.com", "display_name": "Maria Garcia", "role": "supervisor"},
    {"email": "david.thompson@company.com", "display_name": "David Thompson", "role": "manager"},
    {"email": "jennifer.martinez@company.com", "display_name": "Jennifer Martinez", "role": "planner"},
    {"email": "robert.johnson@company.com", "display_name": "Robert Johnson", "role": "parts_manager"},
    {"email": "emily.davis@company.com", "display_name": "Emily Davis", "role": "requestor"},
]


def initialize_firebase_app():
    if not firebase_admin._apps:
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize Firebase Admin SDK: {e}")
            sys.exit(1)


async def clear_collection(firestore_manager, collection_name: str):
    """Delete all documents in a collection."""
    try:
        docs = await firestore_manager.get_collection(collection_name, limit=500)
        for doc in docs:
            if 'id' in doc:
                await firestore_manager.delete_document(collection_name, doc['id'])
        print(f"  Cleared {len(docs)} documents from '{collection_name}'")
    except Exception as e:
        print(f"  Warning: Could not clear {collection_name}: {e}")


async def populate_realistic_data():
    initialize_firebase_app()
    firestore_manager = FirestoreManager()

    print("\n" + "="*60)
    print("   POPULATING REALISTIC CMMS DATA")
    print("="*60 + "\n")

    # --- Clear existing data ---
    print("Clearing existing data...")
    await clear_collection(firestore_manager, "work_orders")
    await clear_collection(firestore_manager, "assets")
    await clear_collection(firestore_manager, "parts")
    print()

    # --- 1. Create Assets ---
    print("Creating realistic assets...")
    created_assets = []

    for asset_data in REALISTIC_ASSETS:
        full_asset = {
            **asset_data,
            "serial_number": f"SN-{random.randint(100000, 999999)}",
            "status": random.choice(["Operational", "Operational", "Operational", "Maintenance"]),  # Most operational
            "criticality": random.choice(["Low", "Medium", "High", "Critical"]),
            "purchase_date": (datetime.now() - timedelta(days=random.randint(365, 2000))).strftime("%Y-%m-%d"),
            "last_maintenance_date": (datetime.now() - timedelta(days=random.randint(7, 90))).strftime("%Y-%m-%d"),
            "next_maintenance_date": (datetime.now() + timedelta(days=random.randint(7, 90))).strftime("%Y-%m-%d"),
            "condition_rating": random.randint(6, 10),
        }

        try:
            asset_id = await firestore_manager.create_document("assets", full_asset)
            created_assets.append({"id": asset_id, "name": asset_data["name"], "type": asset_data["type"]})
            print(f"  + {asset_data['name']}")
        except Exception as e:
            print(f"  ! Failed: {asset_data['name']} - {e}")

    print(f"\n  Total assets created: {len(created_assets)}\n")

    # --- 2. Create Parts ---
    print("Creating realistic parts inventory...")
    created_parts = []

    for part_data in REALISTIC_PARTS:
        full_part = {
            **part_data,
            "current_stock": random.randint(5, 50),
            "minimum_stock": random.randint(2, 10),
            "supplier": random.choice(["Grainger", "McMaster-Carr", "MSC Industrial", "Fastenal", "Motion Industries"]),
            "location": random.choice(["Parts Room A", "Parts Room B", "Electrical Cabinet", "MRO Storage"]),
        }

        try:
            part_id = await firestore_manager.create_document("parts", full_part)
            created_parts.append({"id": part_id, "name": part_data["name"]})
            print(f"  + {part_data['name']}")
        except Exception as e:
            print(f"  ! Failed: {part_data['name']} - {e}")

    print(f"\n  Total parts created: {len(created_parts)}\n")

    # --- 3. Create Work Orders ---
    print("Creating realistic work orders...")
    work_orders_created = 0

    for i in range(25):
        asset = random.choice(created_assets)
        template = random.choice(WORK_ORDER_TEMPLATES)
        technician = random.choice(TECHNICIAN_NAMES)

        # Determine dates
        if template["type"] == "Emergency":
            created_date = datetime.now() - timedelta(hours=random.randint(1, 24))
            due_date = datetime.now() + timedelta(hours=random.randint(1, 8))
            priority = "Critical"
            status = random.choice(["Open", "In Progress"])
        elif template["type"] == "Corrective":
            created_date = datetime.now() - timedelta(days=random.randint(1, 7))
            due_date = datetime.now() + timedelta(days=random.randint(1, 5))
            priority = random.choice(["Medium", "High", "High"])
            status = random.choice(["Open", "Open", "In Progress", "Completed"])
        else:  # Preventive or Inspection
            created_date = datetime.now() - timedelta(days=random.randint(1, 30))
            due_date = datetime.now() + timedelta(days=random.randint(1, 14))
            priority = random.choice(["Low", "Medium", "Medium"])
            status = random.choice(["Open", "In Progress", "Completed", "Completed"])

        work_order_data = {
            "title": f"{template['title']} - {asset['name']}",
            "description": template["description"],
            "asset_id": asset["id"],
            "asset_name": asset["name"],
            "assigned_to": technician,
            "assigned_to_name": technician,
            "priority": priority,
            "status": status,
            "created_date": created_date.strftime("%Y-%m-%d"),
            "due_date": due_date.strftime("%Y-%m-%d"),
            "estimated_hours": round(random.uniform(1.0, 6.0), 1),
            "work_order_type": template["type"],
        }

        if status == "Completed":
            completed_date = created_date + timedelta(days=random.randint(1, 5))
            work_order_data["completed_date"] = completed_date.strftime("%Y-%m-%d")
            work_order_data["actual_hours"] = round(work_order_data["estimated_hours"] + random.uniform(-1, 2), 1)
            work_order_data["work_summary"] = f"Completed {template['type'].lower()} maintenance. All issues addressed and equipment returned to service."

        try:
            wo_id = await firestore_manager.create_document("work_orders", work_order_data)
            work_orders_created += 1
            status_icon = "✓" if status == "Completed" else "●" if status == "In Progress" else "○"
            print(f"  {status_icon} [{priority}] {work_order_data['title'][:50]}...")
        except Exception as e:
            print(f"  ! Failed to create work order: {e}")

    print(f"\n  Total work orders created: {work_orders_created}\n")

    # --- Summary ---
    print("="*60)
    print("   POPULATION COMPLETE")
    print("="*60)
    print(f"  Assets:      {len(created_assets)}")
    print(f"  Parts:       {len(created_parts)}")
    print(f"  Work Orders: {work_orders_created}")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(populate_realistic_data())
