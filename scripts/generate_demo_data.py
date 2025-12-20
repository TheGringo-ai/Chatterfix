#!/usr/bin/env python3
"""
Demo Data Generator for ChatterFix CMMS
Generates realistic work orders, assets, parts, and vendors for testing voice commands.

Usage:
    python scripts/generate_demo_data.py --org-id <org_id>
    python scripts/generate_demo_data.py --demo  # Uses demo organization

Examples of voice commands this data enables:
    - "What's the status of Pump 3?"
    - "Create a work order for the hydraulic press"
    - "How many bearings do we have in stock?"
    - "Show me all critical work orders"
"""

import argparse
import os
import sys
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.cloud import firestore

# ============================================================================
# DEMO DATA DEFINITIONS
# ============================================================================

# Realistic asset types with naming patterns
ASSET_TEMPLATES = [
    # Pumps
    {"name": "Hydraulic Pump 1", "type": "pump", "manufacturer": "Parker Hannifin", "model": "PV270", "location": "Building A - Floor 1", "department": "Production", "criticality": "High"},
    {"name": "Hydraulic Pump 2", "type": "pump", "manufacturer": "Parker Hannifin", "model": "PV270", "location": "Building A - Floor 1", "department": "Production", "criticality": "High"},
    {"name": "Hydraulic Pump 3", "type": "pump", "manufacturer": "Eaton Vickers", "model": "PVH131", "location": "Building A - Floor 2", "department": "Production", "criticality": "High"},
    {"name": "Coolant Pump A", "type": "pump", "manufacturer": "Grundfos", "model": "CR 32-2", "location": "Building B - Basement", "department": "Utilities", "criticality": "Medium"},
    {"name": "Coolant Pump B", "type": "pump", "manufacturer": "Grundfos", "model": "CR 32-2", "location": "Building B - Basement", "department": "Utilities", "criticality": "Medium"},

    # Motors
    {"name": "Main Drive Motor", "type": "motor", "manufacturer": "ABB", "model": "M3BP 315", "location": "Building A - Floor 1", "department": "Production", "criticality": "Critical"},
    {"name": "Conveyor Motor 1", "type": "motor", "manufacturer": "Siemens", "model": "1LE1", "location": "Building A - Floor 1", "department": "Production", "criticality": "Medium"},
    {"name": "Conveyor Motor 2", "type": "motor", "manufacturer": "Siemens", "model": "1LE1", "location": "Building A - Floor 1", "department": "Production", "criticality": "Medium"},
    {"name": "Exhaust Fan Motor", "type": "motor", "manufacturer": "Baldor", "model": "EM3770T", "location": "Building A - Roof", "department": "HVAC", "criticality": "Low"},

    # HVAC
    {"name": "AHU-1", "type": "hvac", "manufacturer": "Trane", "model": "M Series", "location": "Building A - Roof", "department": "HVAC", "criticality": "Medium"},
    {"name": "AHU-2", "type": "hvac", "manufacturer": "Trane", "model": "M Series", "location": "Building B - Roof", "department": "HVAC", "criticality": "Medium"},
    {"name": "Chiller 1", "type": "hvac", "manufacturer": "Carrier", "model": "30XA", "location": "Building A - Basement", "department": "HVAC", "criticality": "High"},
    {"name": "Boiler 1", "type": "hvac", "manufacturer": "Cleaver-Brooks", "model": "CB 200", "location": "Building A - Basement", "department": "HVAC", "criticality": "High"},

    # Conveyors
    {"name": "Main Conveyor Line", "type": "conveyor", "manufacturer": "Dorner", "model": "3200 Series", "location": "Building A - Floor 1", "department": "Production", "criticality": "Critical"},
    {"name": "Packaging Conveyor", "type": "conveyor", "manufacturer": "Hytrol", "model": "ProSort", "location": "Building A - Floor 1", "department": "Shipping", "criticality": "High"},
    {"name": "Incline Conveyor", "type": "conveyor", "manufacturer": "Dorner", "model": "2200 Series", "location": "Building A - Floor 1", "department": "Production", "criticality": "Medium"},

    # Presses & Heavy Equipment
    {"name": "Hydraulic Press 1", "type": "press", "manufacturer": "Dake", "model": "Force 50", "location": "Building A - Floor 2", "department": "Production", "criticality": "High"},
    {"name": "Hydraulic Press 2", "type": "press", "manufacturer": "Dake", "model": "Force 50", "location": "Building A - Floor 2", "department": "Production", "criticality": "High"},
    {"name": "CNC Mill", "type": "cnc", "manufacturer": "Haas", "model": "VF-2", "location": "Building B - Floor 1", "department": "Machine Shop", "criticality": "Critical"},
    {"name": "CNC Lathe", "type": "cnc", "manufacturer": "Mazak", "model": "QT-250", "location": "Building B - Floor 1", "department": "Machine Shop", "criticality": "Critical"},

    # Compressors
    {"name": "Air Compressor 1", "type": "compressor", "manufacturer": "Ingersoll Rand", "model": "R-Series 75", "location": "Building A - Utility Room", "department": "Utilities", "criticality": "High"},
    {"name": "Air Compressor 2", "type": "compressor", "manufacturer": "Atlas Copco", "model": "GA 75", "location": "Building A - Utility Room", "department": "Utilities", "criticality": "High"},

    # Electrical
    {"name": "Main Transformer", "type": "electrical", "manufacturer": "Eaton", "model": "15kVA", "location": "Building A - Electrical Room", "department": "Electrical", "criticality": "Critical"},
    {"name": "UPS System", "type": "electrical", "manufacturer": "APC", "model": "Smart-UPS", "location": "Building A - Server Room", "department": "IT", "criticality": "High"},
]

# Work order templates
WORK_ORDER_TEMPLATES = [
    # Preventive Maintenance
    {"title": "Quarterly PM - {asset}", "type": "Preventive", "description": "Perform quarterly preventive maintenance including inspection, lubrication, and filter replacement.", "priority": "Medium"},
    {"title": "Annual Inspection - {asset}", "type": "Preventive", "description": "Comprehensive annual inspection and testing of all components.", "priority": "High"},
    {"title": "Oil Change - {asset}", "type": "Preventive", "description": "Drain and replace hydraulic/lubricating oil. Check for metal particles.", "priority": "Medium"},
    {"title": "Belt Replacement - {asset}", "type": "Preventive", "description": "Replace drive belts per maintenance schedule.", "priority": "Low"},

    # Corrective Maintenance
    {"title": "Bearing Noise - {asset}", "type": "Corrective", "description": "Unusual bearing noise reported. Investigate and replace if necessary.", "priority": "High"},
    {"title": "Leak Repair - {asset}", "type": "Corrective", "description": "Hydraulic/coolant leak detected. Locate source and repair.", "priority": "High"},
    {"title": "Overheating Issue - {asset}", "type": "Corrective", "description": "Equipment running hot. Check cooling system and thermal protection.", "priority": "Critical"},
    {"title": "Vibration Analysis - {asset}", "type": "Corrective", "description": "Excessive vibration detected. Perform analysis and balance/align as needed.", "priority": "Medium"},
    {"title": "Electrical Fault - {asset}", "type": "Corrective", "description": "Intermittent electrical fault. Check connections and motor starter.", "priority": "High"},

    # Emergency
    {"title": "EMERGENCY: {asset} Down", "type": "Emergency", "description": "Equipment has stopped. Production impact. Immediate response required.", "priority": "Critical"},
    {"title": "Safety Shutdown - {asset}", "type": "Emergency", "description": "Safety system triggered shutdown. Do not restart until inspected.", "priority": "Critical"},
]

# Parts inventory
PARTS_TEMPLATES = [
    # Bearings
    {"name": "6205-2RS Ball Bearing", "part_number": "BRG-6205-2RS", "category": "Bearings", "description": "Deep groove ball bearing, sealed", "unit_cost": 12.50, "min_stock": 10, "max_stock": 50},
    {"name": "6310-2RS Ball Bearing", "part_number": "BRG-6310-2RS", "category": "Bearings", "description": "Deep groove ball bearing, sealed, heavy duty", "unit_cost": 35.00, "min_stock": 5, "max_stock": 20},
    {"name": "32210 Tapered Roller Bearing", "part_number": "BRG-32210", "category": "Bearings", "description": "Tapered roller bearing for heavy loads", "unit_cost": 45.00, "min_stock": 4, "max_stock": 15},
    {"name": "Pillow Block Bearing UCP205", "part_number": "BRG-UCP205", "category": "Bearings", "description": "Pillow block with insert bearing", "unit_cost": 28.00, "min_stock": 8, "max_stock": 30},

    # Seals & Gaskets
    {"name": "Hydraulic Cylinder Seal Kit", "part_number": "SEAL-HYD-001", "category": "Seals", "description": "Complete seal kit for Parker cylinders", "unit_cost": 85.00, "min_stock": 3, "max_stock": 10},
    {"name": "Pump Shaft Seal", "part_number": "SEAL-PMP-001", "category": "Seals", "description": "Mechanical shaft seal for hydraulic pumps", "unit_cost": 120.00, "min_stock": 2, "max_stock": 8},
    {"name": "O-Ring Kit - Metric", "part_number": "SEAL-ORING-M", "category": "Seals", "description": "Assorted metric O-rings, 400 pieces", "unit_cost": 45.00, "min_stock": 2, "max_stock": 5},
    {"name": "Gasket Sheet - 1/16\"", "part_number": "GASK-SHEET-116", "category": "Seals", "description": "Compressed non-asbestos gasket material", "unit_cost": 35.00, "min_stock": 5, "max_stock": 15},

    # Filters
    {"name": "Hydraulic Filter Element", "part_number": "FILT-HYD-001", "category": "Filters", "description": "10 micron hydraulic filter", "unit_cost": 55.00, "min_stock": 6, "max_stock": 20},
    {"name": "Air Compressor Filter", "part_number": "FILT-AIR-001", "category": "Filters", "description": "Intake air filter for IR compressors", "unit_cost": 28.00, "min_stock": 4, "max_stock": 12},
    {"name": "Oil Filter - Spin On", "part_number": "FILT-OIL-001", "category": "Filters", "description": "Standard spin-on oil filter", "unit_cost": 15.00, "min_stock": 10, "max_stock": 40},
    {"name": "HVAC Air Filter 20x20x2", "part_number": "FILT-HVAC-20", "category": "Filters", "description": "Pleated HVAC filter, MERV 11", "unit_cost": 8.50, "min_stock": 20, "max_stock": 100},

    # Belts
    {"name": "V-Belt A68", "part_number": "BELT-A68", "category": "Belts", "description": "Classical V-belt, A section", "unit_cost": 12.00, "min_stock": 4, "max_stock": 15},
    {"name": "V-Belt B75", "part_number": "BELT-B75", "category": "Belts", "description": "Classical V-belt, B section", "unit_cost": 18.00, "min_stock": 4, "max_stock": 15},
    {"name": "Timing Belt HTD-8M", "part_number": "BELT-HTD8M-1200", "category": "Belts", "description": "HTD timing belt, 8mm pitch, 1200mm", "unit_cost": 65.00, "min_stock": 2, "max_stock": 8},
    {"name": "Conveyor Belt Splice Kit", "part_number": "BELT-SPLICE-01", "category": "Belts", "description": "Mechanical splice kit for conveyor belts", "unit_cost": 125.00, "min_stock": 2, "max_stock": 6},

    # Lubricants
    {"name": "Hydraulic Oil ISO 46", "part_number": "OIL-HYD-46", "category": "Lubricants", "description": "Premium hydraulic oil, 5 gallon pail", "unit_cost": 85.00, "min_stock": 4, "max_stock": 12},
    {"name": "Gear Oil ISO 220", "part_number": "OIL-GEAR-220", "category": "Lubricants", "description": "EP gear oil, 5 gallon pail", "unit_cost": 95.00, "min_stock": 2, "max_stock": 8},
    {"name": "Multi-Purpose Grease", "part_number": "GREASE-MP", "category": "Lubricants", "description": "NLGI #2 lithium grease, 14oz cartridge", "unit_cost": 8.00, "min_stock": 20, "max_stock": 60},
    {"name": "Food Grade Lubricant", "part_number": "OIL-FOOD-32", "category": "Lubricants", "description": "NSF H1 food grade oil", "unit_cost": 120.00, "min_stock": 2, "max_stock": 6},

    # Electrical
    {"name": "Motor Starter 30A", "part_number": "ELEC-MS-30A", "category": "Electrical", "description": "NEMA size 1 motor starter", "unit_cost": 185.00, "min_stock": 2, "max_stock": 6},
    {"name": "Contactor 40A", "part_number": "ELEC-CONT-40A", "category": "Electrical", "description": "3-pole contactor, 40A, 120V coil", "unit_cost": 75.00, "min_stock": 3, "max_stock": 10},
    {"name": "Overload Relay 25-32A", "part_number": "ELEC-OL-32A", "category": "Electrical", "description": "Thermal overload relay", "unit_cost": 45.00, "min_stock": 4, "max_stock": 12},
    {"name": "Proximity Sensor", "part_number": "ELEC-PROX-01", "category": "Electrical", "description": "Inductive proximity sensor, 18mm, NPN", "unit_cost": 55.00, "min_stock": 5, "max_stock": 15},
    {"name": "Fuse 30A 600V", "part_number": "ELEC-FUSE-30A", "category": "Electrical", "description": "Class J time-delay fuse", "unit_cost": 18.00, "min_stock": 10, "max_stock": 30},

    # Hardware
    {"name": "Coupling Spider - L100", "part_number": "COUP-L100-SPD", "category": "Couplings", "description": "Urethane spider for L100 jaw coupling", "unit_cost": 22.00, "min_stock": 4, "max_stock": 12},
    {"name": "Sprocket #40 - 20T", "part_number": "SPRK-40-20T", "category": "Chain/Sprocket", "description": "#40 chain sprocket, 20 tooth", "unit_cost": 28.00, "min_stock": 3, "max_stock": 10},
    {"name": "Roller Chain #40", "part_number": "CHAIN-40-10FT", "category": "Chain/Sprocket", "description": "#40 roller chain, 10ft box", "unit_cost": 45.00, "min_stock": 3, "max_stock": 10},
]

# Vendors
VENDORS_TEMPLATES = [
    {"name": "Motion Industries", "contact_name": "John Smith", "email": "jsmith@motion.com", "phone": "555-0101", "address": "123 Industrial Blvd", "category": "Bearings, Power Transmission"},
    {"name": "Grainger", "contact_name": "Sarah Johnson", "email": "sjohnson@grainger.com", "phone": "555-0102", "address": "456 Supply Way", "category": "General MRO"},
    {"name": "McMaster-Carr", "contact_name": "Online Orders", "email": "orders@mcmaster.com", "phone": "555-0103", "address": "Online Supplier", "category": "General MRO, Hardware"},
    {"name": "Parker Hannifin", "contact_name": "Mike Davis", "email": "mdavis@parker.com", "phone": "555-0104", "address": "789 Hydraulic Ave", "category": "Hydraulics, Pneumatics"},
    {"name": "Trane Commercial", "contact_name": "Lisa Chen", "email": "lchen@trane.com", "phone": "555-0105", "address": "321 Climate Dr", "category": "HVAC"},
    {"name": "Electrical Supply Co", "contact_name": "Bob Wilson", "email": "bwilson@elec-supply.com", "phone": "555-0106", "address": "654 Voltage St", "category": "Electrical"},
]

# Technician names for assignments
TECHNICIANS = [
    {"name": "Mike Johnson", "uid": "tech_mike"},
    {"name": "Sarah Chen", "uid": "tech_sarah"},
    {"name": "Carlos Rodriguez", "uid": "tech_carlos"},
    {"name": "Emily Watson", "uid": "tech_emily"},
    {"name": "James Brown", "uid": "tech_james"},
]

# ============================================================================
# DATA GENERATION FUNCTIONS
# ============================================================================

def generate_asset_tag(asset_type: str, index: int) -> str:
    """Generate a realistic asset tag"""
    prefixes = {
        "pump": "PMP",
        "motor": "MTR",
        "hvac": "HVAC",
        "conveyor": "CNV",
        "press": "PRS",
        "cnc": "CNC",
        "compressor": "CMP",
        "electrical": "ELEC",
    }
    prefix = prefixes.get(asset_type, "EQP")
    return f"{prefix}-{str(index).zfill(4)}"


def generate_serial_number() -> str:
    """Generate a realistic serial number"""
    letters = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=2))
    numbers = "".join(random.choices("0123456789", k=8))
    return f"{letters}{numbers}"


def generate_assets(org_id: str) -> List[Dict[str, Any]]:
    """Generate asset documents"""
    assets = []
    now = datetime.now(timezone.utc)

    for i, template in enumerate(ASSET_TEMPLATES, 1):
        asset = {
            "organization_id": org_id,
            "name": template["name"],
            "description": f"{template['manufacturer']} {template['model']} - {template['type'].title()}",
            "asset_tag": generate_asset_tag(template["type"], i),
            "serial_number": generate_serial_number(),
            "model": template["model"],
            "manufacturer": template["manufacturer"],
            "location": template["location"],
            "department": template["department"],
            "asset_type": template["type"],
            "status": random.choice(["operational", "operational", "operational", "warning", "critical"]),
            "criticality": template["criticality"],
            "purchase_date": (now - timedelta(days=random.randint(365, 2000))).isoformat(),
            "warranty_expiry": (now + timedelta(days=random.randint(-365, 730))).isoformat(),
            "purchase_cost": round(random.uniform(5000, 150000), 2),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        assets.append(asset)

    return assets


def generate_work_orders(org_id: str, assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate work order documents"""
    work_orders = []
    now = datetime.now(timezone.utc)
    statuses = ["Open", "In Progress", "On Hold", "Completed", "Completed"]

    # Generate work orders for random assets
    for i in range(30):  # Generate 30 work orders
        asset = random.choice(assets)
        template = random.choice(WORK_ORDER_TEMPLATES)
        tech = random.choice(TECHNICIANS)

        status = random.choice(statuses)
        created_date = now - timedelta(days=random.randint(0, 60))
        due_date = created_date + timedelta(days=random.randint(1, 14))

        work_order = {
            "organization_id": org_id,
            "title": template["title"].format(asset=asset["name"]),
            "description": template["description"],
            "priority": template["priority"],
            "status": status,
            "work_order_type": template["type"],
            "asset_id": asset.get("id", ""),  # Will be filled after asset creation
            "asset_name": asset["name"],
            "assigned_to_uid": tech["uid"],
            "assigned_to_name": tech["name"],
            "created_date": created_date.isoformat(),
            "due_date": due_date.isoformat(),
            "estimated_hours": round(random.uniform(0.5, 8), 1),
        }

        # Add completion data for completed work orders
        if status == "Completed":
            work_order["completed_date"] = (due_date - timedelta(days=random.randint(0, 3))).isoformat()
            work_order["actual_hours"] = round(work_order["estimated_hours"] * random.uniform(0.7, 1.5), 1)
            work_order["work_summary"] = f"Completed {template['type'].lower()} maintenance. All issues resolved."

        work_orders.append(work_order)

    return work_orders


def generate_parts(org_id: str) -> List[Dict[str, Any]]:
    """Generate parts inventory documents"""
    parts = []
    now = datetime.now(timezone.utc)
    locations = ["Storeroom A", "Storeroom B", "Tool Crib", "Maintenance Shop"]

    for template in PARTS_TEMPLATES:
        # Randomize stock levels
        min_stock = template["min_stock"]
        max_stock = template["max_stock"]
        current_stock = random.randint(
            max(0, min_stock - 3),  # Sometimes below minimum
            max_stock + 5  # Sometimes overstocked
        )

        part = {
            "organization_id": org_id,
            "name": template["name"],
            "part_number": template["part_number"],
            "category": template["category"],
            "description": template["description"],
            "current_stock": current_stock,
            "minimum_stock": min_stock,
            "maximum_stock": max_stock,
            "unit_cost": template["unit_cost"],
            "total_value": round(current_stock * template["unit_cost"], 2),
            "location": random.choice(locations),
            "supplier": random.choice(["Motion Industries", "Grainger", "McMaster-Carr"]),
            "reorder_point": min_stock,
            "lead_time_days": random.randint(1, 7),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        # Flag low stock items
        if current_stock < min_stock:
            part["low_stock_alert"] = True

        parts.append(part)

    return parts


def generate_vendors(org_id: str) -> List[Dict[str, Any]]:
    """Generate vendor documents"""
    vendors = []
    now = datetime.now(timezone.utc)

    for template in VENDORS_TEMPLATES:
        vendor = {
            "organization_id": org_id,
            "name": template["name"],
            "contact_name": template["contact_name"],
            "contact_email": template["email"],
            "contact_phone": template["phone"],
            "address": template["address"],
            "category": template["category"],
            "status": "Active",
            "payment_terms": random.choice(["Net 30", "Net 45", "Net 60", "COD"]),
            "rating": random.randint(3, 5),
            "notes": f"Preferred vendor for {template['category']}",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        vendors.append(vendor)

    return vendors


# ============================================================================
# FIRESTORE OPERATIONS
# ============================================================================

def get_firestore_client():
    """Initialize Firestore client"""
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path and os.path.exists(creds_path):
        return firestore.Client.from_service_account_json(creds_path)
    return firestore.Client()


def upload_to_firestore(db, collection: str, documents: List[Dict[str, Any]]) -> List[str]:
    """Upload documents to Firestore and return document IDs"""
    doc_ids = []
    batch = db.batch()
    batch_count = 0

    for doc in documents:
        doc_ref = db.collection(collection).document()
        doc["id"] = doc_ref.id
        batch.set(doc_ref, doc)
        doc_ids.append(doc_ref.id)
        batch_count += 1

        # Firestore batch limit is 500
        if batch_count >= 400:
            batch.commit()
            batch = db.batch()
            batch_count = 0

    if batch_count > 0:
        batch.commit()

    return doc_ids


def main():
    parser = argparse.ArgumentParser(description="Generate demo data for ChatterFix CMMS")
    parser.add_argument("--org-id", help="Organization ID to populate")
    parser.add_argument("--demo", action="store_true", help="Use demo organization")
    parser.add_argument("--dry-run", action="store_true", help="Print data without uploading")
    args = parser.parse_args()

    # Determine organization ID
    org_id = args.org_id or ("demo_org" if args.demo else None)
    if not org_id:
        print("Error: Please specify --org-id or --demo")
        sys.exit(1)

    print(f"{'='*60}")
    print(f"ChatterFix Demo Data Generator")
    print(f"{'='*60}")
    print(f"Organization: {org_id}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE UPLOAD'}")
    print()

    # Generate data
    print("Generating assets...")
    assets = generate_assets(org_id)
    print(f"  Created {len(assets)} assets")

    print("Generating work orders...")
    work_orders = generate_work_orders(org_id, assets)
    print(f"  Created {len(work_orders)} work orders")

    print("Generating parts inventory...")
    parts = generate_parts(org_id)
    print(f"  Created {len(parts)} parts")

    print("Generating vendors...")
    vendors = generate_vendors(org_id)
    print(f"  Created {len(vendors)} vendors")

    if args.dry_run:
        print("\n" + "="*60)
        print("DRY RUN - Data not uploaded")
        print("="*60)
        print("\nSample Asset:")
        print(f"  {assets[0]['name']} ({assets[0]['asset_tag']})")
        print(f"  Location: {assets[0]['location']}")
        print(f"  Status: {assets[0]['status']}")

        print("\nSample Work Order:")
        print(f"  {work_orders[0]['title']}")
        print(f"  Priority: {work_orders[0]['priority']}, Status: {work_orders[0]['status']}")

        print("\nSample Part:")
        print(f"  {parts[0]['name']} ({parts[0]['part_number']})")
        print(f"  Stock: {parts[0]['current_stock']} / Min: {parts[0]['minimum_stock']}")

        return

    # Upload to Firestore
    print("\nConnecting to Firestore...")
    db = get_firestore_client()

    print("Uploading assets...")
    asset_ids = upload_to_firestore(db, "assets", assets)
    print(f"  Uploaded {len(asset_ids)} assets")

    # Update work orders with asset IDs
    asset_id_map = {a["name"]: a["id"] for a in assets}
    for wo in work_orders:
        wo["asset_id"] = asset_id_map.get(wo["asset_name"], "")

    print("Uploading work orders...")
    wo_ids = upload_to_firestore(db, "work_orders", work_orders)
    print(f"  Uploaded {len(wo_ids)} work orders")

    print("Uploading parts...")
    part_ids = upload_to_firestore(db, "parts", parts)
    print(f"  Uploaded {len(part_ids)} parts")

    print("Uploading vendors...")
    vendor_ids = upload_to_firestore(db, "vendors", vendors)
    print(f"  Uploaded {len(vendor_ids)} vendors")

    print("\n" + "="*60)
    print("Demo data generation complete!")
    print("="*60)
    print(f"\nTotal records created:")
    print(f"  Assets:      {len(assets)}")
    print(f"  Work Orders: {len(work_orders)}")
    print(f"  Parts:       {len(parts)}")
    print(f"  Vendors:     {len(vendors)}")
    print(f"\nVoice command examples:")
    print(f'  "What\'s the status of {assets[0]["name"]}?"')
    print(f'  "Show me all critical work orders"')
    print(f'  "How many {parts[0]["name"].split()[0].lower()}s do we have?"')
    print(f'  "Create a work order for the {assets[5]["name"]}"')


if __name__ == "__main__":
    main()
