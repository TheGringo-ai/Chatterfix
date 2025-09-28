#!/usr/bin/env python3
"""
TechFlow Manufacturing Corp - Enterprise Mock Data Generator
Generates comprehensive, realistic enterprise-level test data for ChatterFix CMMS
Company: TechFlow Manufacturing Corp (250 employees, 3 facilities)
Business: Manufacturing electronics components
"""

import sqlite3
import os
import json
import random
from datetime import datetime, timedelta
from enhanced_database import init_enhanced_database
import bcrypt

DATABASE_PATH = "./data/cmms_enhanced.db"

class TechFlowDataGenerator:
    def __init__(self):
        self.conn = None
        self.cursor = None
        
        # Company Information
        self.company_name = "TechFlow Manufacturing Corp"
        self.total_employees = 250
        self.facilities_count = 3
        
        # Realistic Data Sets
        self.departments = [
            "Production", "Maintenance", "Quality Control", "Engineering", 
            "Safety", "Procurement", "IT", "HR", "Finance", "Operations",
            "Logistics", "Planning", "Environmental"
        ]
        
        self.first_names = [
            "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
            "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
            "Thomas", "Sarah", "Christopher", "Karen", "Charles", "Nancy", "Daniel", "Lisa",
            "Matthew", "Betty", "Anthony", "Helen", "Mark", "Sandra", "Donald", "Donna",
            "Steven", "Carol", "Paul", "Ruth", "Andrew", "Sharon", "Joshua", "Michelle",
            "Kenneth", "Laura", "Kevin", "Sarah", "Brian", "Kimberly", "George", "Deborah",
            "Edward", "Dorothy", "Ronald", "Lisa", "Timothy", "Nancy", "Jason", "Karen",
            "Jeffrey", "Betty", "Ryan", "Helen", "Jacob", "Sandra", "Gary", "Donna"
        ]
        
        self.last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
            "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
            "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
            "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
            "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
            "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
            "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
            "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy"
        ]
        
        # Asset Categories and Types
        self.asset_categories = {
            "Production Equipment": [
                "CNC Machine", "Assembly Line", "Injection Molding Machine", "SMT Line",
                "Pick and Place Machine", "Reflow Oven", "Wave Solder Machine", "Test Equipment",
                "Industrial Robot", "Conveyor System", "Packaging Equipment", "Quality Scanner"
            ],
            "HVAC Systems": [
                "Air Handler", "Chiller", "Cooling Tower", "Boiler", "Heat Pump",
                "Exhaust Fan", "Air Compressor", "Dehumidifier", "Air Filtration System"
            ],
            "Electrical Systems": [
                "Main Electrical Panel", "Sub Panel", "Transformer", "UPS System",
                "Generator", "Motor Control Center", "Variable Frequency Drive", "Lighting System"
            ],
            "Facility Equipment": [
                "Forklift", "Overhead Crane", "Dock Door", "Security System", "Fire Suppression",
                "Emergency Lighting", "Elevator", "Loading Dock Equipment"
            ],
            "IT Infrastructure": [
                "Server", "Network Switch", "Router", "Firewall", "Storage Array",
                "Backup System", "Workstation", "Printer", "Scanner"
            ],
            "Utility Systems": [
                "Water Treatment", "Compressed Air System", "Steam Boiler", "Waste Treatment",
                "Chemical Storage Tank", "Pump", "Valve", "Meter"
            ]
        }
        
        # Parts Categories
        self.parts_categories = {
            "Mechanical": [
                "Bearings", "Belts", "Gears", "Seals", "Gaskets", "O-Rings", "Springs",
                "Fasteners", "Couplings", "Bushings", "Pulleys", "Chains"
            ],
            "Electrical": [
                "Motors", "Sensors", "Switches", "Contactors", "Relays", "Fuses",
                "Circuit Breakers", "Cables", "Connectors", "Transformers", "Capacitors"
            ],
            "HVAC": [
                "Filters", "Valves", "Thermostats", "Dampers", "Coils", "Fans",
                "Compressors", "Refrigerant", "Insulation", "Ductwork"
            ],
            "Consumables": [
                "Lubricants", "Grease", "Coolant", "Cleaning Supplies", "Adhesives",
                "Solvents", "Rags", "Gloves", "Safety Equipment"
            ],
            "Electronics": [
                "PCBs", "ICs", "Resistors", "Capacitors", "Inductors", "Diodes",
                "Transistors", "Connectors", "Displays", "Memory Modules"
            ]
        }
        
        # Manufacturers
        self.manufacturers = [
            "Siemens", "Allen-Bradley", "Schneider Electric", "ABB", "Honeywell",
            "Johnson Controls", "Emerson", "GE", "Mitsubishi", "Omron", "Fanuc",
            "Bosch Rexroth", "Parker Hannifin", "Eaton", "Phoenix Contact",
            "Pepperl+Fuchs", "Balluff", "Festo", "SMC", "Keyence", "Cognex"
        ]
        
        # Work Order Types
        self.work_order_types = [
            "Preventive Maintenance", "Corrective Maintenance", "Emergency Repair",
            "Safety Inspection", "Equipment Upgrade", "Installation", "Calibration",
            "Cleaning", "Lubrication", "Replacement", "Modification", "Testing"
        ]
        
        # Priorities
        self.priorities = ["Critical", "High", "Medium", "Low"]
        self.statuses = ["Open", "In Progress", "On Hold", "Completed", "Cancelled"]
        
    def connect_database(self):
        """Connect to the database"""
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.cursor = self.conn.cursor()
        
    def close_database(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            
    def generate_locations(self):
        """Generate realistic location hierarchy for 3 facilities"""
        print("🏭 Generating location hierarchy...")
        
        facilities = [
            {
                "code": "TF-FAC-001",
                "name": "TechFlow Main Manufacturing Facility",
                "address": "1250 Industrial Blvd, Austin, TX 78744",
                "type": "Manufacturing Facility"
            },
            {
                "code": "TF-FAC-002", 
                "name": "TechFlow Assembly & Testing Center",
                "address": "2100 Technology Dr, Austin, TX 78758",
                "type": "Assembly Facility"
            },
            {
                "code": "TF-FAC-003",
                "name": "TechFlow Warehouse & Distribution",
                "address": "5500 Distribution Way, Austin, TX 78719",
                "type": "Warehouse"
            }
        ]
        
        location_id = 1
        
        for facility in facilities:
            # Insert facility
            self.cursor.execute('''
                INSERT INTO locations (id, location_code, name, description, location_type, 
                                     address, city, state, zip_code, country, timezone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                location_id, facility["code"], facility["name"], facility["name"],
                facility["type"], facility["address"], "Austin", "TX", 
                facility["address"].split()[-1], "USA", "America/Chicago"
            ))
            
            facility_id = location_id
            location_id += 1
            
            # Add buildings/areas for each facility
            if "Manufacturing" in facility["name"]:
                buildings = ["Production Building A", "Production Building B", "Engineering Building", "Administration Building"]
            elif "Assembly" in facility["name"]:
                buildings = ["Assembly Hall", "Testing Lab", "Quality Control", "Shipping"]
            else:  # Warehouse
                buildings = ["Warehouse A", "Warehouse B", "Receiving", "Shipping"]
                
            for building_idx, building in enumerate(buildings):
                building_code = f"{facility['code']}-{building.replace(' ', '').replace('&', '').upper()[:3]}{building_idx+1:02d}"
                self.cursor.execute('''
                    INSERT INTO locations (id, location_code, name, description, location_type,
                                         parent_location_id, building, address, city, state, zip_code, country, timezone)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    location_id, building_code, building, f"{building} at {facility['name']}",
                    "Building", facility_id, building, facility["address"], "Austin", "TX",
                    facility["address"].split()[-1], "USA", "America/Chicago"
                ))
                
                building_id = location_id
                location_id += 1
                
                # Add floors
                floors = ["Ground Floor", "Mezzanine"] if "Warehouse" in building else ["Floor 1", "Floor 2"]
                for floor_idx, floor in enumerate(floors):
                    floor_code = f"{building_code}-{floor.replace(' ', '').upper()[:3]}{floor_idx+1:02d}"
                    self.cursor.execute('''
                        INSERT INTO locations (id, location_code, name, description, location_type,
                                             parent_location_id, building, floor, address, city, state, zip_code, country, timezone)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        location_id, floor_code, f"{building} - {floor}", f"{floor} of {building}",
                        "Floor", building_id, building, floor, facility["address"], "Austin", "TX",
                        facility["address"].split()[-1], "USA", "America/Chicago"
                    ))
                    
                    floor_id = location_id
                    location_id += 1
                    
                    # Add rooms/areas
                    if "Production" in building:
                        rooms = ["Line 1", "Line 2", "Line 3", "Line 4", "Quality Station", "Maintenance Shop"]
                    elif "Assembly" in building:
                        rooms = ["Station A", "Station B", "Station C", "Final Test", "Packaging"]
                    elif "Warehouse" in building:
                        rooms = ["Zone A", "Zone B", "Zone C", "Zone D"]
                    else:
                        rooms = ["Room 101", "Room 102", "Room 103", "Conference Room", "Break Room"]
                        
                    for room_idx, room in enumerate(rooms):
                        room_code = f"{floor_code}-{room.replace(' ', '').upper()[:3]}{room_idx+1:02d}"
                        self.cursor.execute('''
                            INSERT INTO locations (id, location_code, name, description, location_type,
                                                 parent_location_id, building, floor, room, address, city, state, zip_code, country, timezone)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            location_id, room_code, f"{building} - {floor} - {room}", 
                            f"{room} in {floor} of {building}",
                            "Room", floor_id, building, floor, room, facility["address"], "Austin", "TX",
                            facility["address"].split()[-1], "USA", "America/Chicago"
                        ))
                        
                        location_id += 1
        
        print(f"✅ Created {location_id - 1} locations with proper hierarchy")
        
    def generate_users(self):
        """Generate 250 realistic employee records"""
        print("👥 Generating employee records...")
        
        roles_distribution = {
            "Production Operator": 80,
            "Maintenance Technician": 25,
            "Quality Inspector": 20,
            "Production Supervisor": 15,
            "Maintenance Supervisor": 8,
            "Engineer": 25,
            "Manager": 12,
            "Administrator": 10,
            "Safety Coordinator": 8,
            "Planner": 15,
            "Purchasing Agent": 8,
            "IT Specialist": 12,
            "HR Specialist": 8,
            "Accountant": 4
        }
        
        certification_levels = ["Level 1", "Level 2", "Level 3", "Level 4", "Master"]
        
        user_id = 1
        used_emails = set()
        used_usernames = set()
        
        for role, count in roles_distribution.items():
            for i in range(count):
                first_name = random.choice(self.first_names)
                last_name = random.choice(self.last_names)
                
                # Ensure unique username and email
                username = f"{first_name.lower()}.{last_name.lower()}"
                counter = 1
                while username in used_usernames:
                    username = f"{first_name.lower()}.{last_name.lower()}{counter}"
                    counter += 1
                used_usernames.add(username)
                
                email = f"{username}@techflowmfg.com"
                used_emails.add(email)
                
                # Generate realistic employee ID
                employee_id = f"TF{random.randint(1000, 9999)}"
                
                # Assign department based on role
                if "Production" in role:
                    department = "Production"
                elif "Maintenance" in role:
                    department = "Maintenance"
                elif "Quality" in role:
                    department = "Quality Control"
                elif "Engineer" in role:
                    department = "Engineering"
                elif "Safety" in role:
                    department = "Safety"
                elif "IT" in role:
                    department = "IT"
                elif "HR" in role:
                    department = "HR"
                elif "Purchasing" in role or "Planner" in role:
                    department = "Procurement"
                else:
                    department = random.choice(self.departments)
                
                # Generate hourly rate based on role
                rate_ranges = {
                    "Production Operator": (18, 28),
                    "Maintenance Technician": (25, 40),
                    "Quality Inspector": (20, 32),
                    "Production Supervisor": (35, 50),
                    "Maintenance Supervisor": (40, 60),
                    "Engineer": (35, 65),
                    "Manager": (50, 80),
                    "Administrator": (18, 35),
                    "Safety Coordinator": (30, 45),
                    "Planner": (25, 40),
                    "Purchasing Agent": (22, 38),
                    "IT Specialist": (30, 55),
                    "HR Specialist": (25, 45),
                    "Accountant": (28, 50)
                }
                
                min_rate, max_rate = rate_ranges.get(role, (20, 40))
                hourly_rate = round(random.uniform(min_rate, max_rate), 2)
                
                # Hash password (default: "password123")
                password_hash = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                # Create realistic phone number
                phone = f"512-{random.randint(200, 999)}-{random.randint(1000, 9999)}"
                
                # Assign certification level
                cert_level = random.choice(certification_levels) if "Technician" in role or "Engineer" in role else None
                
                # Create join date (within last 5 years)
                created_date = datetime.now() - timedelta(days=random.randint(30, 1825))
                
                self.cursor.execute('''
                    INSERT INTO users (id, username, email, password_hash, role, department, full_name,
                                     phone, employee_id, certification_level, hourly_rate, is_active, created_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, username, email, password_hash, role, department, f"{first_name} {last_name}",
                    phone, employee_id, cert_level, hourly_rate, True, created_date
                ))
                
                user_id += 1
        
        print(f"✅ Created {user_id - 1} employee records")
        
    def generate_suppliers(self):
        """Generate realistic supplier records"""
        print("🏢 Generating supplier records...")
        
        suppliers_data = [
            ("SUP-001", "Industrial Components Inc", "Austin", "TX", "Industrial supplies"),
            ("SUP-002", "AutomationPro Supply", "Dallas", "TX", "Automation equipment"),
            ("SUP-003", "MRO Solutions LLC", "Houston", "TX", "Maintenance supplies"),
            ("SUP-004", "TechParts Distributors", "San Antonio", "TX", "Electronic components"),
            ("SUP-005", "Bearing & Power Systems", "Austin", "TX", "Mechanical components"),
            ("SUP-006", "Electrical Supply Co", "Dallas", "TX", "Electrical supplies"),
            ("SUP-007", "HVAC Systems Texas", "Houston", "TX", "HVAC equipment"),
            ("SUP-008", "Safety First Supply", "Austin", "TX", "Safety equipment"),
            ("SUP-009", "Precision Tools Inc", "Dallas", "TX", "Tools and equipment"),
            ("SUP-010", "Chemical Solutions Ltd", "Houston", "TX", "Chemicals and fluids"),
            ("SUP-011", "Fastener World", "Austin", "TX", "Fasteners and hardware"),
            ("SUP-012", "Motor & Drive Systems", "San Antonio", "TX", "Motors and drives")
        ]
        
        for i, (code, name, city, state, notes) in enumerate(suppliers_data, 1):
            contact_person = f"{random.choice(self.first_names)} {random.choice(self.last_names)}"
            phone = f"512-{random.randint(200, 999)}-{random.randint(1000, 9999)}"
            email = f"orders@{name.lower().replace(' ', '').replace('&', 'and')[:15]}.com"
            address = f"{random.randint(100, 9999)} {random.choice(['Industrial', 'Commerce', 'Business', 'Tech'])} Dr"
            
            self.cursor.execute('''
                INSERT INTO suppliers (id, supplier_code, name, contact_person, email, phone,
                                     address, city, state, zip_code, country, payment_terms, 
                                     lead_time_days, rating, notes, is_preferred, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                i, code, name, contact_person, email, phone, address, city, state,
                f"7{random.randint(8000, 8999)}", "USA", "Net 30", random.randint(3, 14),
                round(random.uniform(3.5, 5.0), 1), notes, i <= 6, True
            ))
        
        print(f"✅ Created {len(suppliers_data)} supplier records")
        
    def generate_assets(self):
        """Generate 30+ realistic manufacturing assets"""
        print("🏭 Generating manufacturing assets...")
        
        # Get location IDs for realistic assignment
        self.cursor.execute("SELECT id, location_code, name FROM locations WHERE location_type = 'Room'")
        locations = self.cursor.fetchall()
        
        asset_id = 1
        
        for category, types in self.asset_categories.items():
            for asset_type in types:
                # Generate 1-3 assets of each type
                count = random.randint(1, 3)
                for i in range(count):
                    # Generate enterprise asset tag
                    asset_tag = f"TF-{category.replace(' ', '')[:3].upper()}-{asset_id:04d}"
                    
                    # Select appropriate location
                    location = random.choice(locations)
                    
                    # Generate realistic asset name
                    manufacturer = random.choice(self.manufacturers)
                    model_suffix = f"-{random.randint(100, 999)}{random.choice(['A', 'B', 'X', 'Pro'])}"
                    model = f"{manufacturer.split()[0]}{model_suffix}"
                    
                    asset_name = f"{manufacturer} {asset_type} {model}"
                    
                    # Generate realistic specifications
                    specs = self.generate_asset_specifications(category, asset_type)
                    
                    # Generate realistic dates
                    purchase_date = datetime.now() - timedelta(days=random.randint(365, 2555))  # 1-7 years ago
                    installation_date = purchase_date + timedelta(days=random.randint(7, 60))
                    warranty_expiry = purchase_date + timedelta(days=random.randint(365, 1825))  # 1-5 years
                    
                    # Generate costs
                    cost_ranges = {
                        "Production Equipment": (50000, 500000),
                        "HVAC Systems": (10000, 100000),
                        "Electrical Systems": (5000, 75000),
                        "Facility Equipment": (15000, 80000),
                        "IT Infrastructure": (2000, 25000),
                        "Utility Systems": (8000, 60000)
                    }
                    
                    min_cost, max_cost = cost_ranges.get(category, (5000, 50000))
                    purchase_cost = random.randint(min_cost, max_cost)
                    current_value = purchase_cost * random.uniform(0.4, 0.8)  # Depreciated value
                    
                    # Generate maintenance info
                    frequencies = [30, 60, 90, 180, 365]  # days
                    maintenance_frequency = random.choice(frequencies)
                    last_maintenance = datetime.now() - timedelta(days=random.randint(1, maintenance_frequency))
                    next_maintenance = last_maintenance + timedelta(days=maintenance_frequency)
                    
                    # Generate operating hours
                    years_in_service = (datetime.now() - installation_date).days / 365
                    avg_hours_per_day = random.uniform(8, 24)  # 8-24 hours per day
                    operating_hours = int(years_in_service * 365 * avg_hours_per_day)
                    max_operating_hours = operating_hours + random.randint(10000, 50000)
                    
                    # Generate serial number
                    serial_number = f"{manufacturer[:3].upper()}{random.randint(100000, 999999)}"
                    
                    # Criticality based on category
                    criticality_map = {
                        "Production Equipment": random.choice(["Critical", "High", "High"]),
                        "HVAC Systems": random.choice(["High", "Medium"]),
                        "Electrical Systems": random.choice(["Critical", "High"]),
                        "Facility Equipment": random.choice(["Medium", "Low"]),
                        "IT Infrastructure": random.choice(["High", "Medium"]),
                        "Utility Systems": random.choice(["High", "Medium"])
                    }
                    
                    criticality = criticality_map.get(category, "Medium")
                    
                    self.cursor.execute('''
                        INSERT INTO assets (id, asset_tag, name, category, subcategory, location_id,
                                          manufacturer, model, serial_number, purchase_date, installation_date,
                                          warranty_expiry, purchase_cost, current_value, status, condition_rating,
                                          criticality, last_maintenance_date, next_maintenance_due, 
                                          maintenance_frequency_days, operating_hours, max_operating_hours,
                                          specifications, created_date, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        asset_id, asset_tag, asset_name, category, asset_type, location[0],
                        manufacturer, model, serial_number, purchase_date, installation_date,
                        warranty_expiry, purchase_cost, current_value, "Active", random.randint(3, 5),
                        criticality, last_maintenance, next_maintenance, maintenance_frequency,
                        operating_hours, max_operating_hours, json.dumps(specs), datetime.now(), 1
                    ))
                    
                    asset_id += 1
        
        print(f"✅ Created {asset_id - 1} manufacturing assets")
        
    def generate_asset_specifications(self, category, asset_type):
        """Generate realistic specifications for assets"""
        specs = {}
        
        if category == "Production Equipment":
            specs = {
                "Power Rating": f"{random.randint(5, 50)} kW",
                "Voltage": random.choice(["480V", "240V", "208V"]),
                "Dimensions": f"{random.randint(2, 8)}m x {random.randint(1, 4)}m x {random.randint(2, 3)}m",
                "Weight": f"{random.randint(500, 5000)} kg",
                "Production Rate": f"{random.randint(100, 1000)} units/hour"
            }
        elif category == "HVAC Systems":
            specs = {
                "Capacity": f"{random.randint(10, 100)} tons",
                "Efficiency": f"{random.uniform(12, 20):.1f} SEER",
                "Refrigerant": random.choice(["R-410A", "R-134a", "R-404A"]),
                "Power": f"{random.randint(5, 25)} kW"
            }
        elif category == "Electrical Systems":
            specs = {
                "Voltage": random.choice(["480V", "240V", "208V", "120V"]),
                "Current": f"{random.randint(100, 1000)} A",
                "Power": f"{random.randint(10, 200)} kW",
                "Protection": random.choice(["IP65", "IP54", "NEMA 4"])
            }
        
        return specs
        
    def generate_parts(self):
        """Generate 100+ realistic parts inventory"""
        print("📦 Generating parts inventory...")
        
        part_id = 1
        
        # Get some supplier IDs
        self.cursor.execute("SELECT id FROM suppliers LIMIT 5")
        supplier_ids = [row[0] for row in self.cursor.fetchall()]
        
        for category, subcategories in self.parts_categories.items():
            for subcategory in subcategories:
                # Generate 3-8 parts per subcategory
                count = random.randint(3, 8)
                for i in range(count):
                    # Generate enterprise part number
                    part_number = f"TF-{category[:3].upper()}-{subcategory[:3].upper()}-{part_id:04d}"
                    
                    # Generate realistic part name
                    manufacturer = random.choice(self.manufacturers)
                    model_suffix = random.randint(100, 999)
                    
                    part_name = f"{manufacturer} {subcategory} {model_suffix}"
                    description = f"High-quality {subcategory.lower()} for industrial applications"
                    
                    # Generate manufacturer part number
                    mfg_part_number = f"{manufacturer[:3].upper()}{random.randint(10000, 99999)}"
                    
                    # Generate costs based on category
                    cost_ranges = {
                        "Mechanical": (5, 500),
                        "Electrical": (10, 1000),
                        "HVAC": (20, 800),
                        "Consumables": (1, 50),
                        "Electronics": (5, 2000)
                    }
                    
                    min_cost, max_cost = cost_ranges.get(category, (5, 100))
                    unit_cost = round(random.uniform(min_cost, max_cost), 2)
                    
                    # Generate inventory levels
                    max_stock = random.randint(20, 200)
                    min_stock = int(max_stock * 0.1)
                    reorder_point = int(max_stock * 0.2)
                    reorder_quantity = int(max_stock * 0.3)
                    current_stock = random.randint(min_stock, max_stock)
                    
                    # Generate other attributes
                    units = random.choice(["EA", "FT", "LB", "GAL", "BOX", "ROLL"])
                    lead_time = random.randint(3, 21)
                    
                    # Storage locations
                    storage_locations = [
                        "Warehouse A-1", "Warehouse A-2", "Warehouse B-1", "Warehouse B-2",
                        "Maintenance Shop", "Tool Crib", "Chemical Storage", "Electronics Lab"
                    ]
                    storage_location = random.choice(storage_locations)
                    
                    bin_location = f"{storage_location}-{random.choice(['A', 'B', 'C'])}{random.randint(1, 20):02d}"
                    
                    # Generate barcode
                    barcode = f"TF{random.randint(100000000000, 999999999999)}"
                    
                    # ABC classification
                    abc_class = random.choices(["A", "B", "C"], weights=[20, 30, 50])[0]
                    
                    # Usage rate (monthly)
                    usage_rate = round(random.uniform(1, 50), 2)
                    
                    self.cursor.execute('''
                        INSERT INTO parts (id, part_number, name, description, category, subcategory,
                                         manufacturer, manufacturer_part_number, supplier_id, unit_of_measure,
                                         unit_cost, stock_quantity, min_stock_level, max_stock_level,
                                         reorder_point, reorder_quantity, lead_time_days, storage_location,
                                         bin_location, barcode, abc_classification, usage_rate_monthly,
                                         created_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        part_id, part_number, part_name, description, category, subcategory,
                        manufacturer, mfg_part_number, random.choice(supplier_ids), units,
                        unit_cost, current_stock, min_stock, max_stock, reorder_point,
                        reorder_quantity, lead_time, storage_location, bin_location,
                        barcode, abc_class, usage_rate, datetime.now()
                    ))
                    
                    part_id += 1
        
        print(f"✅ Created {part_id - 1} parts in inventory")
        
    def generate_work_orders(self):
        """Generate 50+ realistic work orders"""
        print("🔧 Generating work orders...")
        
        # Get data for realistic work orders
        self.cursor.execute("SELECT id, asset_tag, name, category FROM assets")
        assets = self.cursor.fetchall()
        
        self.cursor.execute("SELECT id, full_name, role FROM users WHERE role LIKE '%Technician%' OR role LIKE '%Supervisor%'")
        technicians = self.cursor.fetchall()
        
        self.cursor.execute("SELECT id, full_name FROM users WHERE role NOT LIKE '%Technician%'")
        requesters = self.cursor.fetchall()
        
        wo_id = 1
        current_year = datetime.now().year
        
        # Generate work orders for the last 6 months
        start_date = datetime.now() - timedelta(days=180)
        
        for day_offset in range(0, 180, 3):  # Every 3 days on average
            work_date = start_date + timedelta(days=day_offset)
            
            # Generate 1-3 work orders per period
            daily_count = random.randint(1, 3)
            
            for i in range(daily_count):
                # Generate enterprise WO number
                wo_number = f"WO-{current_year}-{wo_id:04d}"
                
                # Select random asset
                asset = random.choice(assets)
                asset_id, asset_tag, asset_name, asset_category = asset
                
                # Select work order type
                work_type = random.choice(self.work_order_types)
                
                # Generate title and description based on type and asset
                title, description = self.generate_work_order_content(work_type, asset_name, asset_category)
                
                # Assign priority based on work type
                if work_type == "Emergency Repair":
                    priority = "Critical"
                elif work_type in ["Safety Inspection", "Corrective Maintenance"]:
                    priority = random.choice(["High", "Medium"])
                else:
                    priority = random.choice(["Medium", "Low", "Low"])  # Bias toward lower priority
                
                # Assign technician
                assigned_tech = random.choice(technicians)
                
                # Assign requester
                requester = random.choice(requesters)
                
                # Generate realistic timing
                estimated_hours = self.get_estimated_hours(work_type, asset_category)
                
                # Determine status and completion
                age_days = (datetime.now() - work_date).days
                if age_days > 30:
                    status = random.choices(["Completed", "Completed", "Completed", "Cancelled"], weights=[80, 10, 5, 5])[0]
                elif age_days > 7:
                    status = random.choices(["Completed", "In Progress", "On Hold"], weights=[70, 25, 5])[0]
                else:
                    status = random.choices(["Open", "In Progress", "Completed"], weights=[40, 35, 25])[0]
                
                # Calculate actual hours and costs if completed
                actual_hours = None
                actual_cost = None
                completion_date = None
                completion_notes = None
                
                if status == "Completed":
                    actual_hours = estimated_hours * random.uniform(0.8, 1.3)  # ±30% variation
                    completion_date = work_date + timedelta(hours=random.randint(1, 72))
                    completion_notes = self.generate_completion_notes(work_type)
                    
                    # Calculate cost (labor + parts)
                    labor_cost = actual_hours * random.uniform(35, 65)  # $35-65/hour
                    parts_cost = random.uniform(50, 500) if random.random() > 0.3 else 0  # 70% chance of parts
                    actual_cost = labor_cost + parts_cost
                
                # Due date
                due_date = work_date + timedelta(days=self.get_due_days(priority, work_type))
                
                # Safety and permit info
                permit_required = work_type in ["Installation", "Modification", "Emergency Repair"] and random.random() > 0.7
                permit_number = f"PERMIT-{random.randint(1000, 9999)}" if permit_required else None
                
                safety_notes = self.generate_safety_notes(work_type, asset_category) if random.random() > 0.5 else None
                
                self.cursor.execute('''
                    INSERT INTO work_orders (id, wo_number, title, description, work_type, priority,
                                           status, asset_id, assigned_to, requested_by, created_by,
                                           estimated_hours, actual_hours, estimated_cost, actual_cost,
                                           due_date, completion_date, completion_notes, safety_notes,
                                           permit_required, permit_number, created_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    wo_id, wo_number, title, description, work_type, priority, status, asset_id,
                    assigned_tech[0], requester[0], 1, estimated_hours, actual_hours,
                    estimated_hours * 50 if estimated_hours else None, actual_cost,
                    due_date, completion_date, completion_notes, safety_notes,
                    permit_required, permit_number, work_date
                ))
                
                wo_id += 1
        
        print(f"✅ Created {wo_id - 1} work orders")
        
    def generate_work_order_content(self, work_type, asset_name, asset_category):
        """Generate realistic work order titles and descriptions"""
        
        templates = {
            "Preventive Maintenance": {
                "titles": [
                    f"Scheduled PM - {asset_name}",
                    f"Monthly Maintenance - {asset_name}",
                    f"Quarterly Service - {asset_name}"
                ],
                "descriptions": [
                    "Perform scheduled preventive maintenance per manufacturer specifications",
                    "Complete routine maintenance checklist including lubrication, inspection, and calibration",
                    "Conduct preventive maintenance tasks to ensure optimal performance and reliability"
                ]
            },
            "Corrective Maintenance": {
                "titles": [
                    f"Repair Issue - {asset_name}",
                    f"Fix Performance Problem - {asset_name}",
                    f"Correct Malfunction - {asset_name}"
                ],
                "descriptions": [
                    "Address reported performance issues and restore normal operation",
                    "Investigate and repair malfunction affecting production efficiency",
                    "Troubleshoot and correct operational problems"
                ]
            },
            "Emergency Repair": {
                "titles": [
                    f"URGENT: Equipment Down - {asset_name}",
                    f"EMERGENCY: Critical Failure - {asset_name}",
                    f"IMMEDIATE: System Failure - {asset_name}"
                ],
                "descriptions": [
                    "EMERGENCY: Equipment failure causing production shutdown. Immediate repair required.",
                    "CRITICAL: System malfunction affecting safety and operations. Priority repair needed.",
                    "URGENT: Complete equipment failure. Restore operation immediately."
                ]
            },
            "Safety Inspection": {
                "titles": [
                    f"Safety Inspection - {asset_name}",
                    f"Annual Safety Check - {asset_name}",
                    f"Compliance Inspection - {asset_name}"
                ],
                "descriptions": [
                    "Conduct comprehensive safety inspection per OSHA requirements",
                    "Perform annual safety compliance check and documentation",
                    "Complete mandatory safety inspection and update certifications"
                ]
            },
            "Equipment Upgrade": {
                "titles": [
                    f"Upgrade Components - {asset_name}",
                    f"Modernization Project - {asset_name}",
                    f"Performance Enhancement - {asset_name}"
                ],
                "descriptions": [
                    "Upgrade equipment components to improve performance and efficiency",
                    "Install modern components and update control systems",
                    "Enhance equipment capabilities with new technology"
                ]
            }
        }
        
        template = templates.get(work_type, {
            "titles": [f"Maintenance Work - {asset_name}"],
            "descriptions": ["Perform required maintenance work on equipment"]
        })
        
        title = random.choice(template["titles"])
        description = random.choice(template["descriptions"])
        
        return title, description
        
    def get_estimated_hours(self, work_type, asset_category):
        """Get realistic estimated hours based on work type and asset"""
        
        base_hours = {
            "Preventive Maintenance": 2,
            "Corrective Maintenance": 4,
            "Emergency Repair": 6,
            "Safety Inspection": 1,
            "Equipment Upgrade": 8,
            "Installation": 12,
            "Calibration": 2,
            "Cleaning": 1,
            "Lubrication": 0.5,
            "Replacement": 6,
            "Modification": 10,
            "Testing": 2
        }
        
        # Asset complexity multipliers
        complexity_multipliers = {
            "Production Equipment": 1.5,
            "HVAC Systems": 1.2,
            "Electrical Systems": 1.3,
            "Facility Equipment": 1.0,
            "IT Infrastructure": 0.8,
            "Utility Systems": 1.1
        }
        
        base = base_hours.get(work_type, 2)
        multiplier = complexity_multipliers.get(asset_category, 1.0)
        
        return round(base * multiplier * random.uniform(0.8, 1.5), 1)
        
    def get_due_days(self, priority, work_type):
        """Get due date offset based on priority and work type"""
        
        if priority == "Critical":
            return random.randint(0, 1)  # Same day or next day
        elif priority == "High":
            return random.randint(1, 3)  # 1-3 days
        elif priority == "Medium":
            return random.randint(3, 7)  # 3-7 days
        else:  # Low
            return random.randint(7, 14)  # 1-2 weeks
            
    def generate_completion_notes(self, work_type):
        """Generate realistic completion notes"""
        
        notes_templates = {
            "Preventive Maintenance": [
                "All scheduled maintenance tasks completed successfully. Equipment operating within normal parameters.",
                "PM checklist completed. Found minor wear on component, monitoring for future replacement.",
                "Routine maintenance completed. All systems checked and lubricated as required."
            ],
            "Corrective Maintenance": [
                "Issue identified and repaired. Root cause was worn bearing, replaced with new part.",
                "Problem resolved by adjusting calibration settings and replacing faulty sensor.",
                "Malfunction corrected. Updated control parameters and tested operation."
            ],
            "Emergency Repair": [
                "Emergency repair completed. Replaced failed component and restored production.",
                "Critical failure resolved. Implemented temporary fix and scheduled permanent repair.",
                "System restored to operation. Identified failure mode for prevention planning."
            ]
        }
        
        templates = notes_templates.get(work_type, [
            "Work completed as requested. Equipment tested and returned to service."
        ])
        
        return random.choice(templates)
        
    def generate_safety_notes(self, work_type, asset_category):
        """Generate realistic safety notes"""
        
        safety_templates = [
            "LOTO procedures followed. All energy sources isolated before work.",
            "PPE required: Safety glasses, hard hat, steel-toed boots.",
            "Hot work permit required. Fire watch posted during operation.",
            "Confined space entry procedures required. Gas monitoring completed.",
            "Electrical work performed by qualified personnel only.",
            "Fall protection required when working at height.",
            "Chemical handling procedures followed. MSDS reviewed."
        ]
        
        return random.choice(safety_templates)
        
    def generate_pm_schedules(self):
        """Generate preventive maintenance schedules"""
        print("📅 Generating PM schedules...")
        
        # Create basic PM templates first
        pm_templates = [
            ("Monthly Equipment PM", "Monthly preventive maintenance", "Production Equipment", "Calendar", 30),
            ("Quarterly HVAC PM", "Quarterly HVAC system maintenance", "HVAC Systems", "Calendar", 90),
            ("Annual Safety Inspection", "Annual safety compliance check", "All Categories", "Calendar", 365),
            ("Weekly Lubrication", "Weekly lubrication of moving parts", "Production Equipment", "Calendar", 7),
            ("Semi-Annual Calibration", "Bi-annual calibration check", "Production Equipment", "Calendar", 180)
        ]
        
        for i, (name, desc, category, freq_type, freq_value) in enumerate(pm_templates, 1):
            self.cursor.execute('''
                INSERT INTO pm_templates (id, template_name, description, asset_category,
                                        frequency_type, frequency_value, estimated_duration,
                                        is_active, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (i, name, desc, category, freq_type, freq_value, 2.0, True, 1))
        
        # Create schedules for assets
        self.cursor.execute("SELECT id, category FROM assets")
        assets = self.cursor.fetchall()
        
        schedule_id = 1
        
        for asset_id, category in assets:
            # Assign 1-3 PM schedules per asset
            applicable_templates = [1, 2, 3]  # Basic templates that apply to most assets
            
            if category == "Production Equipment":
                applicable_templates.extend([4, 5])  # Add production-specific templates
            
            for template_id in random.sample(applicable_templates, random.randint(1, 2)):
                next_due = datetime.now() + timedelta(days=random.randint(1, 30))
                
                self.cursor.execute('''
                    INSERT INTO maintenance_schedules (id, asset_id, pm_template_id, 
                                                     frequency_days, next_due_date, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (schedule_id, asset_id, template_id, 30, next_due, True))
                
                schedule_id += 1
        
        print(f"✅ Created {schedule_id - 1} PM schedules")
        
    def run_generation(self):
        """Run the complete data generation process"""
        print(f"\n🚀 Starting enterprise data generation for {self.company_name}")
        print("=" * 60)
        
        # Initialize database
        print("📊 Initializing enhanced database schema...")
        init_enhanced_database()
        
        # Connect to database
        self.connect_database()
        
        try:
            # Generate all data
            self.generate_locations()
            self.generate_users()
            self.generate_suppliers()
            self.generate_assets()
            self.generate_parts()
            self.generate_work_orders()
            self.generate_pm_schedules()
            
            # Commit all changes
            self.conn.commit()
            
            print("\n" + "=" * 60)
            print("✅ ENTERPRISE DATA GENERATION COMPLETED SUCCESSFULLY!")
            print(f"🏭 Company: {self.company_name}")
            print(f"👥 Employees: {self.total_employees}")
            print(f"🏢 Facilities: {self.facilities_count}")
            print("🎯 Ready for enterprise-level demonstration!")
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Error during data generation: {e}")
            self.conn.rollback()
            raise
        finally:
            self.close_database()

if __name__ == "__main__":
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Generate enterprise data
    generator = TechFlowDataGenerator()
    generator.run_generation()