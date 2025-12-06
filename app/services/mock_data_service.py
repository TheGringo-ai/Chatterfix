"""
Mock Data Service
Generate demo/sample data for new users and guest mode
"""

from datetime import datetime, timedelta
import random

from app.core.firestore_db import get_db_connection

# # from app.core.database import get_db_connection


def create_demo_data(user_id: int):
    """
    Create demo data for a new user

    Args:
        user_id: ID of the user to create data for
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Update user avatar
    cursor.execute(
        "UPDATE users SET avatar_url = ? WHERE id = ?",
        ("https://placehold.co/200x200?text=User", user_id),
    )

    # Create sample assets
    assets = [
        (
            "Hydraulic Press #1",
            "Main production hydraulic press",
            "Production Floor",
            "Hydraulic Equipment",
            "Active",
            "https://placehold.co/600x400?text=Hydraulic+Press",
        ),
        (
            "Conveyor Belt System",
            "Material transport conveyor",
            "Warehouse",
            "Conveyor Systems",
            "Active",
            "https://placehold.co/600x400?text=Conveyor",
        ),
        (
            "Air Compressor Unit",
            "Central air supply compressor",
            "Utility Room",
            "HVAC Equipment",
            "Active",
            "https://placehold.co/600x400?text=Compressor",
        ),
        (
            "CNC Machine #3",
            "Computer numerical control machine",
            "Production Floor",
            "Machining Equipment",
            "Active",
            "https://placehold.co/600x400?text=CNC+Machine",
        ),
        (
            "Forklift #7",
            "Material handling forklift",
            "Warehouse",
            "Material Handling",
            "Active",
            "https://placehold.co/600x400?text=Forklift",
        ),
    ]

    asset_ids = []
    for name, desc, location, category, status, image_url in assets:
        cursor.execute(
            """
            INSERT INTO assets (name, description, location, category, status, condition_rating, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (name, desc, location, category, status, random.randint(7, 10), image_url),
        )
        asset_ids.append(cursor.lastrowid)

    # Create sample parts
    parts = [
        (
            "Hydraulic Seal Kit",
            "HSK-2025-001",
            "Seals",
            25,
            10,
            45.99,
            "Warehouse A-12",
            "https://placehold.co/400x400?text=Seal+Kit",
        ),
        (
            "V-Belt Drive",
            "VBD-500",
            "Belts",
            15,
            5,
            28.50,
            "Warehouse A-15",
            "https://placehold.co/400x400?text=V-Belt",
        ),
        (
            "Air Filter Element",
            "AFE-100",
            "Filters",
            30,
            15,
            12.99,
            "Warehouse B-03",
            "https://placehold.co/400x400?text=Air+Filter",
        ),
        (
            "Bearing Assembly",
            "BA-2000",
            "Bearings",
            20,
            8,
            67.50,
            "Warehouse A-08",
            "https://placehold.co/400x400?text=Bearing",
        ),
        (
            "Lubricating Oil",
            "LO-SAE30",
            "Lubricants",
            50,
            20,
            15.75,
            "Warehouse C-01",
            "https://placehold.co/400x400?text=Oil",
        ),
        (
            "Safety Valve",
            "SV-150PSI",
            "Valves",
            12,
            5,
            89.99,
            "Warehouse A-10",
            "https://placehold.co/400x400?text=Valve",
        ),
        (
            "Pressure Gauge",
            "PG-0-200",
            "Gauges",
            18,
            10,
            34.50,
            "Warehouse B-05",
            "https://placehold.co/400x400?text=Gauge",
        ),
        (
            "Hydraulic Hose",
            "HH-3/4-20FT",
            "Hoses",
            22,
            10,
            42.00,
            "Warehouse A-14",
            "https://placehold.co/400x400?text=Hose",
        ),
    ]

    for name, part_num, category, stock, min_stock, cost, location, image_url in parts:
        cursor.execute(
            """
            INSERT INTO parts (name, part_number, category, current_stock, minimum_stock, unit_cost, location, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (name, part_num, category, stock, min_stock, cost, location, image_url),
        )

    # Create sample work orders
    work_orders = [
        (
            "Hydraulic Press Maintenance",
            "Routine maintenance on hydraulic press",
            "Medium",
            "Open",
            asset_ids[0],
        ),
        (
            "Conveyor Belt Inspection",
            "Weekly inspection of conveyor system",
            "Low",
            "Open",
            asset_ids[1],
        ),
        (
            "Air Compressor Filter Change",
            "Replace air filters",
            "High",
            "In Progress",
            asset_ids[2],
        ),
        (
            "CNC Calibration",
            "Calibrate CNC machine axes",
            "Medium",
            "Open",
            asset_ids[3],
        ),
        (
            "Forklift Safety Check",
            "Monthly safety inspection",
            "High",
            "Open",
            asset_ids[4],
        ),
        (
            "Hydraulic Seal Replacement",
            "Replace worn seals on press",
            "High",
            "Completed",
            asset_ids[0],
        ),
        (
            "Belt Tension Adjustment",
            "Adjust conveyor belt tension",
            "Low",
            "Completed",
            asset_ids[1],
        ),
    ]

    for title, desc, priority, status, asset_id in work_orders:
        due_date = datetime.now() + timedelta(days=random.randint(1, 14))
        cursor.execute(
            """
            INSERT INTO work_orders (title, description, priority, status, asset_id, due_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (title, desc, priority, status, asset_id, due_date.isoformat()),
        )

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
            {
                "id": "demo-1",
                "name": "Demo Hydraulic Press",
                "status": "Active",
                "location": "Production Floor",
                "image_url": "https://placehold.co/600x400?text=Hydraulic+Press",
            },
            {
                "id": "demo-2",
                "name": "Demo Conveyor System",
                "status": "Active",
                "location": "Warehouse",
                "image_url": "https://placehold.co/600x400?text=Conveyor",
            },
            {
                "id": "demo-3",
                "name": "Demo Air Compressor",
                "status": "Maintenance",
                "location": "Utility Room",
                "image_url": "https://placehold.co/600x400?text=Compressor",
            },
        ],
        "parts": [
            {
                "id": "demo-1",
                "name": "Demo Seal Kit",
                "stock": 25,
                "location": "Warehouse A",
                "image_url": "https://placehold.co/400x400?text=Seal+Kit",
            },
            {
                "id": "demo-2",
                "name": "Demo V-Belt",
                "stock": 15,
                "location": "Warehouse B",
                "image_url": "https://placehold.co/400x400?text=V-Belt",
            },
            {
                "id": "demo-3",
                "name": "Demo Air Filter",
                "stock": 30,
                "location": "Warehouse C",
                "image_url": "https://placehold.co/400x400?text=Air+Filter",
            },
        ],
        "work_orders": [
            {
                "id": "demo-1",
                "title": "Demo Maintenance Task",
                "priority": "Medium",
                "status": "Open",
            },
            {
                "id": "demo-2",
                "title": "Demo Inspection",
                "priority": "Low",
                "status": "In Progress",
            },
            {
                "id": "demo-3",
                "title": "Demo Repair",
                "priority": "High",
                "status": "Open",
            },
        ],
    }
