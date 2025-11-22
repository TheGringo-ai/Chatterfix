"""
Mock Data Service
Generate demo/sample data for new users and guest mode
"""

import sqlite3
from datetime import datetime, timedelta
import random

DATABASE_PATH = "./data/cmms.db"


def create_demo_data(user_id: int):
    """
    Create demo data for a new user
    
    Args:
        user_id: ID of the user to create data for
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create sample assets
    assets = [
        ("Hydraulic Press #1", "Main production hydraulic press", "Production Floor", "Hydraulic Equipment", "Active"),
        ("Conveyor Belt System", "Material transport conveyor", "Warehouse", "Conveyor Systems", "Active"),
        ("Air Compressor Unit", "Central air supply compressor", "Utility Room", "HVAC Equipment", "Active"),
        ("CNC Machine #3", "Computer numerical control machine", "Production Floor", "Machining Equipment", "Active"),
        ("Forklift #7", "Material handling forklift", "Warehouse", "Material Handling", "Active"),
    ]
    
    asset_ids = []
    for name, desc, location, category, status in assets:
        cursor.execute("""
            INSERT INTO assets (name, description, location, category, status, condition_rating)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, desc, location, category, status, random.randint(7, 10)))
        asset_ids.append(cursor.lastrowid)
    
    # Create sample parts
    parts = [
        ("Hydraulic Seal Kit", "HSK-2025-001", "Seals", 25, 10, 45.99, "Warehouse A-12"),
        ("V-Belt Drive", "VBD-500", "Belts", 15, 5, 28.50, "Warehouse A-15"),
        ("Air Filter Element", "AFE-100", "Filters", 30, 15, 12.99, "Warehouse B-03"),
        ("Bearing Assembly", "BA-2000", "Bearings", 20, 8, 67.50, "Warehouse A-08"),
        ("Lubricating Oil", "LO-SAE30", "Lubricants", 50, 20, 15.75, "Warehouse C-01"),
        ("Safety Valve", "SV-150PSI", "Valves", 12, 5, 89.99, "Warehouse A-10"),
        ("Pressure Gauge", "PG-0-200", "Gauges", 18, 10, 34.50, "Warehouse B-05"),
        ("Hydraulic Hose", "HH-3/4-20FT", "Hoses", 22, 10, 42.00, "Warehouse A-14"),
    ]
    
    for name, part_num, category, stock, min_stock, cost, location in parts:
        cursor.execute("""
            INSERT INTO parts (name, part_number, category, current_stock, minimum_stock, unit_cost, location)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, part_num, category, stock, min_stock, cost, location))
    
    # Create sample work orders
    work_orders = [
        ("Hydraulic Press Maintenance", "Routine maintenance on hydraulic press", "Medium", "Open", asset_ids[0]),
        ("Conveyor Belt Inspection", "Weekly inspection of conveyor system", "Low", "Open", asset_ids[1]),
        ("Air Compressor Filter Change", "Replace air filters", "High", "In Progress", asset_ids[2]),
        ("CNC Calibration", "Calibrate CNC machine axes", "Medium", "Open", asset_ids[3]),
        ("Forklift Safety Check", "Monthly safety inspection", "High", "Open", asset_ids[4]),
        ("Hydraulic Seal Replacement", "Replace worn seals on press", "High", "Completed", asset_ids[0]),
        ("Belt Tension Adjustment", "Adjust conveyor belt tension", "Low", "Completed", asset_ids[1]),
    ]
    
    for title, desc, priority, status, asset_id in work_orders:
        due_date = datetime.now() + timedelta(days=random.randint(1, 14))
        cursor.execute("""
            INSERT INTO work_orders (title, description, priority, status, asset_id, due_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (title, desc, priority, status, asset_id, due_date.isoformat()))
    
    conn.commit()
    conn.close()


def get_mock_data():
    """
    Get mock data for guest users (read-only)
    
    Returns:
        dict: Mock data for display
    """
    return {
        "assets": [
            {"id": "demo-1", "name": "Demo Hydraulic Press", "status": "Active", "location": "Production Floor"},
            {"id": "demo-2", "name": "Demo Conveyor System", "status": "Active", "location": "Warehouse"},
            {"id": "demo-3", "name": "Demo Air Compressor", "status": "Maintenance", "location": "Utility Room"},
        ],
        "parts": [
            {"id": "demo-1", "name": "Demo Seal Kit", "stock": 25, "location": "Warehouse A"},
            {"id": "demo-2", "name": "Demo V-Belt", "stock": 15, "location": "Warehouse B"},
            {"id": "demo-3", "name": "Demo Air Filter", "stock": 30, "location": "Warehouse C"},
        ],
        "work_orders": [
            {"id": "demo-1", "title": "Demo Maintenance Task", "priority": "Medium", "status": "Open"},
            {"id": "demo-2", "title": "Demo Inspection", "priority": "Low", "status": "In Progress"},
            {"id": "demo-3", "title": "Demo Repair", "priority": "High", "status": "Open"},
        ]
    }
