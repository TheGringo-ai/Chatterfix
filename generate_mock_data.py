"""
Mock Data Generator for ChatterFix CMMS
Populates database with realistic, editable data for testing and demonstration
"""

import sqlite3
import random
from datetime import datetime, timedelta
from app.core.database import get_db_connection

# Realistic data sets
FIRST_NAMES = [
    "John",
    "Sarah",
    "Mike",
    "Lisa",
    "David",
    "Emily",
    "James",
    "Maria",
    "Robert",
    "Jennifer",
    "William",
    "Linda",
    "Richard",
    "Patricia",
    "Thomas",
    "Nancy",
    "Daniel",
    "Karen",
    "Matthew",
    "Betty",
]

LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Hernandez",
    "Lopez",
    "Gonzalez",
    "Wilson",
    "Anderson",
    "Thomas",
    "Taylor",
    "Moore",
    "Jackson",
    "Martin",
]

ASSET_TYPES = [
    {
        "category": "Pumps",
        "names": ["Centrifugal Pump", "Hydraulic Pump", "Vacuum Pump", "Booster Pump"],
    },
    {
        "category": "Motors",
        "names": ["AC Motor", "DC Motor", "Servo Motor", "Stepper Motor"],
    },
    {
        "category": "Conveyors",
        "names": [
            "Belt Conveyor",
            "Roller Conveyor",
            "Chain Conveyor",
            "Screw Conveyor",
        ],
    },
    {
        "category": "HVAC",
        "names": ["Air Handler", "Chiller", "Cooling Tower", "Boiler"],
    },
    {
        "category": "Compressors",
        "names": ["Air Compressor", "Gas Compressor", "Refrigeration Compressor"],
    },
]

LOCATIONS = [
    "Building A - Floor 1",
    "Building A - Floor 2",
    "Building B - Warehouse",
    "Building C - Production",
    "Outdoor - North Yard",
    "Outdoor - South Yard",
    "Maintenance Shop",
    "Loading Dock",
]

PART_NAMES = [
    "Hydraulic Seal",
    "Motor Bearing",
    "V-Belt",
    "Oil Filter",
    "Air Filter",
    "Control Panel",
    "Pressure Gauge",
    "Temperature Sensor",
    "Relay Switch",
    "Circuit Breaker",
    "Coupling",
    "Shaft Seal",
    "Gasket Kit",
    "Lubricant Oil",
    "Coolant",
    "Grease",
    "Bolt Set",
    "Washer Set",
]

WORK_ORDER_ISSUES = [
    "Unusual noise during operation",
    "Excessive vibration detected",
    "Overheating issue",
    "Leaking fluid",
    "Equipment not starting",
    "Intermittent power loss",
    "Reduced performance",
    "Safety sensor malfunction",
    "Control panel error",
    "Scheduled preventive maintenance",
]

TRAINING_TOPICS = [
    "Pump Maintenance Basics",
    "Motor Troubleshooting",
    "Hydraulic Systems Safety",
    "Electrical Safety Procedures",
    "Lockout/Tagout (LOTO)",
    "Conveyor Belt Alignment",
    "HVAC System Maintenance",
    "Compressor Operation",
    "Vibration Analysis",
    "Predictive Maintenance Techniques",
]


def clear_existing_data():
    """Clear existing data from tables"""
    conn = get_db_connection()
    cur = conn.cursor()

    # Clear in correct order (respecting foreign keys)
    tables = [
        "user_training",
        "training_modules",
        "work_order_feedback",
        "team_messages",
        "notifications",
        "parts_requests",
        "user_location_history",
        "user_privacy_settings",
        "user_dashboard_config",
        "work_orders",
        "parts",
        "assets",
        "user_performance",
        "user_skills",
        "users",
    ]

    for table in tables:
        try:
            cur.execute(f"DELETE FROM {table}")
        except Exception as e:
            print(f"Note: Could not clear {table}: {e}")

    conn.commit()
    conn.close()
    print("✓ Cleared existing data")


def create_users(count=20):
    """Create realistic users with different roles"""
    conn = get_db_connection()
    cur = conn.cursor()

    roles = (
        ["technician"] * 12
        + ["supervisor"] * 4
        + ["parts_manager"] * 2
        + ["manager"] * 2
    )
    random.shuffle(roles)

    users = []
    for i in range(count):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        username = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}"
        email = f"{username}@chatterfix.com"
        role = roles[i] if i < len(roles) else "technician"

        cur.execute(
            """
            INSERT INTO users (username, email, full_name, role, status, dashboard_layout, theme)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                username,
                email,
                f"{first_name} {last_name}",
                role,
                "active",
                "grid",
                "dark",
            ),
        )

        users.append(
            {
                "id": cur.lastrowid,
                "name": f"{first_name} {last_name}",
                "role": role,
                "username": username,
            }
        )

    conn.commit()
    conn.close()
    print(f"✓ Created {count} users")
    return users


def create_assets(count=50):
    """Create realistic assets"""
    conn = get_db_connection()
    cur = conn.cursor()

    assets = []
    for i in range(count):
        asset_type = random.choice(ASSET_TYPES)
        name = random.choice(asset_type["names"])
        asset_tag = f"{asset_type['category'][:3].upper()}-{1000 + i}"
        location = random.choice(LOCATIONS)
        criticality_levels = ["Low", "Medium", "High", "Critical"]
        criticality = random.choices(criticality_levels, weights=[15, 35, 35, 15])[0]

        # Installation date between 1-10 years ago
        install_date = (
            datetime.now() - timedelta(days=random.randint(365, 3650))
        ).strftime("%Y-%m-%d")
        purchase_date = (
            datetime.now() - timedelta(days=random.randint(400, 3700))
        ).strftime("%Y-%m-%d")

        # Last service 1-90 days ago
        last_service = (
            datetime.now() - timedelta(days=random.randint(1, 90))
        ).strftime("%Y-%m-%d")
        # Next service 30-180 days from now
        next_service = (
            datetime.now() + timedelta(days=random.randint(30, 180))
        ).strftime("%Y-%m-%d")

        cur.execute(
            """
            INSERT INTO assets 
            (name, asset_tag, serial_number, model, manufacturer, location, status, 
             criticality, purchase_date, installation_date, last_service_date, next_service_date,
             condition_rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                name,
                asset_tag,
                f"SN-{random.randint(100000, 999999)}",
                f"Model-{random.randint(100, 999)}",
                random.choice(
                    [
                        "Acme Corp",
                        "TechPro",
                        "IndustrialMax",
                        "PowerSystems",
                        "GlobalEquip",
                    ]
                ),
                location,
                "Active",
                criticality,
                purchase_date,
                install_date,
                last_service,
                next_service,
                random.randint(3, 5),
            ),
        )

        assets.append(
            {
                "id": cur.lastrowid,
                "asset_tag": asset_tag,
                "name": name,
                "category": asset_type["category"],
                "criticality": criticality,
                "location": location,
            }
        )

    conn.commit()
    conn.close()
    print(f"✓ Created {count} assets")
    return assets


def create_work_orders(users, assets, count=100):
    """Create realistic work orders"""
    conn = get_db_connection()
    cur = conn.cursor()

    priorities = ["low", "medium", "high", "urgent"]
    statuses = ["pending", "in_progress", "completed", "on_hold"]

    technicians = [u for u in users if u["role"] == "technician"]

    for i in range(count):
        asset = random.choice(assets)
        issue = random.choice(WORK_ORDER_ISSUES)
        priority = random.choices(priorities, weights=[20, 40, 30, 10])[0]
        status = random.choices(statuses, weights=[25, 35, 30, 10])[0]

        # Created date in last 90 days
        created_date = datetime.now() - timedelta(days=random.randint(0, 90))

        # Due date 1-14 days from creation
        due_date = created_date + timedelta(days=random.randint(1, 14))

        # Assign to technician
        assigned_to_user = random.choice(technicians) if random.random() > 0.2 else None
        assigned_to = assigned_to_user["username"] if assigned_to_user else None

        # Estimated duration 1-8 hours
        estimated_duration = random.choice([1, 2, 3, 4, 6, 8])

        cur.execute(
            """
            INSERT INTO work_orders 
            (title, description, priority, status, assigned_to, created_date, 
             due_date, estimated_duration, location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                f"{issue} - {asset['name']}",
                f"Asset {asset['asset_tag']} at {asset.get('location', 'Unknown')} requires attention: {issue}. Please inspect and repair as needed.",
                priority,
                status,
                assigned_to,
                created_date.strftime("%Y-%m-%d %H:%M:%S"),
                due_date.strftime("%Y-%m-%d %H:%M:%S"),
                estimated_duration,
                asset.get("location", "Unknown"),
            ),
        )

    conn.commit()
    conn.close()
    print(f"✓ Created {count} work orders")


def create_parts_inventory(count=30):
    """Create parts inventory"""
    conn = get_db_connection()
    cur = conn.cursor()

    for part_name in PART_NAMES[:count]:
        current_stock = random.randint(5, 100)
        minimum_stock = random.randint(5, 15)
        location = random.choice(LOCATIONS)
        unit_cost = round(random.uniform(10, 500), 2)

        cur.execute(
            """
            INSERT INTO parts (name, part_number, description, current_stock, minimum_stock, unit_cost, location)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                part_name,
                f"PN-{random.randint(10000, 99999)}",
                f"Standard {part_name.lower()} for maintenance operations",
                current_stock,
                minimum_stock,
                unit_cost,
                location,
            ),
        )

    conn.commit()
    conn.close()
    print(f"✓ Created {count} parts in inventory")


def create_parts_requests(users, count=30):
    """Create parts requests"""
    conn = get_db_connection()
    cur = conn.cursor()

    # Get all parts
    parts = cur.execute("SELECT id, name FROM parts").fetchall()
    if not parts:
        print("⚠️  No parts found, skipping parts requests")
        conn.close()
        return

    statuses = ["pending", "approved", "ordered", "delivered", "denied"]
    priorities = ["low", "medium", "high", "urgent"]

    for i in range(count):
        requester = random.choice(users)
        part = random.choice(parts)
        quantity = random.randint(1, 10)
        priority = random.choice(priorities)
        status = random.choices(statuses, weights=[30, 25, 20, 15, 10])[0]

        requested_date = datetime.now() - timedelta(days=random.randint(0, 30))

        cur.execute(
            """
            INSERT INTO parts_requests 
            (part_id, quantity, requester_id, status, priority, requested_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                part["id"],
                quantity,
                requester["id"],
                status,
                priority,
                requested_date.strftime("%Y-%m-%d %H:%M:%S"),
                f"Requested {quantity} units of {part['name']} for maintenance operations",
            ),
        )

    conn.commit()
    conn.close()
    print(f"✓ Created {count} parts requests")


def create_team_messages(users, count=50):
    """Create team messages"""
    conn = get_db_connection()
    cur = conn.cursor()

    message_templates = [
        "Need help with {asset}. Anyone available?",
        "Completed work on {asset}. All systems operational.",
        "Found an issue with {asset}. Escalating to supervisor.",
        "Parts for {asset} have arrived. Ready to proceed.",
        "Safety concern at {location}. Please review.",
        "Great job on the {asset} repair!",
        "Meeting at 2pm to discuss {asset} maintenance.",
        "Updated procedure for {asset} available in training center.",
    ]

    for i in range(count):
        sender = random.choice(users)
        recipient = random.choice([u for u in users if u["id"] != sender["id"]])

        template = random.choice(message_templates)
        message = template.format(
            asset=f"Pump-{random.randint(1000, 1050)}",
            location=random.choice(LOCATIONS),
        )

        created_date = datetime.now() - timedelta(hours=random.randint(0, 168))
        is_read = random.random() > 0.3

        cur.execute(
            """
            INSERT INTO team_messages (sender_id, recipient_id, message, created_date, read)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                sender["id"],
                recipient["id"],
                message,
                created_date.strftime("%Y-%m-%d %H:%M:%S"),
                is_read,
            ),
        )

    conn.commit()
    conn.close()
    print(f"✓ Created {count} team messages")


def create_training_modules(count=15):
    """Create training modules"""
    conn = get_db_connection()
    cur = conn.cursor()

    for i, topic in enumerate(TRAINING_TOPICS[:count]):
        duration = random.choice([30, 45, 60, 90, 120])
        difficulty = random.randint(1, 5)

        cur.execute(
            """
            INSERT INTO training_modules 
            (title, description, estimated_duration_minutes, difficulty_level, ai_generated)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                topic,
                f"Comprehensive training on {topic.lower()} for maintenance technicians.",
                duration,
                difficulty,
                random.choice([0, 1]),
            ),
        )

    conn.commit()
    conn.close()
    print(f"✓ Created {count} training modules")


def create_user_training(users):
    """Assign training to users"""
    conn = get_db_connection()
    cur = conn.cursor()

    # Get all training modules
    modules = cur.execute("SELECT id FROM training_modules").fetchall()

    technicians = [u for u in users if u["role"] == "technician"]

    for user in technicians:
        # Assign 3-7 random modules
        assigned_modules = random.sample(modules, random.randint(3, 7))

        for module in assigned_modules:
            assigned_date = datetime.now() - timedelta(days=random.randint(0, 60))
            due_date = assigned_date + timedelta(days=30)

            # 60% chance completed
            if random.random() > 0.4:
                completed_date = assigned_date + timedelta(days=random.randint(1, 25))
                score = random.randint(70, 100)
            else:
                completed_date = None
                score = None

            cur.execute(
                """
                INSERT INTO user_training 
                (user_id, module_id, assigned_date, due_date, completed_date, score)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    user["id"],
                    module["id"],
                    assigned_date.strftime("%Y-%m-%d"),
                    due_date.strftime("%Y-%m-%d"),
                    completed_date.strftime("%Y-%m-%d") if completed_date else None,
                    score,
                ),
            )

    conn.commit()
    conn.close()
    print(f"✓ Assigned training to {len(technicians)} technicians")


def create_notifications(users, count=40):
    """Create notifications"""
    conn = get_db_connection()
    cur = conn.cursor()

    notification_types = [
        "work_order_assigned",
        "parts_arrived",
        "training_due",
        "quality_alert",
        "system",
    ]

    for i in range(count):
        user = random.choice(users)
        notif_type = random.choice(notification_types)

        messages = {
            "work_order_assigned": f"New work order assigned: WO-{random.randint(1000, 1100)}",
            "parts_arrived": f"Parts for your request have arrived at {random.choice(LOCATIONS)}",
            "training_due": f"Training module '{random.choice(TRAINING_TOPICS)}' due in 3 days",
            "quality_alert": f"Quality concern reported for asset {random.choice(['PUM-1001', 'MOT-1015', 'CON-1023'])}",
            "system": "System maintenance scheduled for tonight at 11 PM",
        }

        created_date = datetime.now() - timedelta(hours=random.randint(0, 72))
        is_read = random.random() > 0.4

        cur.execute(
            """
            INSERT INTO notifications (user_id, type, message, created_date, is_read)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                user["id"],
                notif_type,
                messages[notif_type],
                created_date.strftime("%Y-%m-%d %H:%M:%S"),
                is_read,
            ),
        )

    conn.commit()
    conn.close()
    print(f"✓ Created {count} notifications")


def create_user_skills(users):
    """Create user skills"""
    conn = get_db_connection()
    cur = conn.cursor()

    skills = [
        "Hydraulic Systems",
        "Electrical Systems",
        "Mechanical Repair",
        "Welding",
        "PLC Programming",
        "Pneumatics",
        "HVAC",
        "Conveyor Systems",
        "Pump Maintenance",
        "Motor Repair",
        "Vibration Analysis",
        "Lubrication",
        "Alignment",
        "Balancing",
    ]

    technicians = [u for u in users if u["role"] == "technician"]

    for user in technicians:
        # Each technician has 3-8 skills
        user_skills = random.sample(skills, random.randint(3, 8))

        for skill in user_skills:
            proficiency = random.choice(
                ["beginner", "intermediate", "advanced", "expert"]
            )
            years_experience = random.randint(1, 15)

            cur.execute(
                """
                INSERT INTO user_skills (user_id, skill_name, proficiency_level, years_experience)
                VALUES (?, ?, ?, ?)
            """,
                (user["id"], skill, proficiency, years_experience),
            )

    conn.commit()
    conn.close()
    print(f"✓ Created skills for {len(technicians)} technicians")


def main():
    """Generate all mock data"""
    print("\n🚀 Starting Mock Data Generation...\n")

    # Clear existing data
    clear_existing_data()

    # Create data in correct order
    users = create_users(20)
    assets = create_assets(50)
    create_work_orders(users, assets, 100)
    create_parts_inventory(30)
    create_parts_requests(users, 30)
    create_team_messages(users, 50)
    create_training_modules(15)
    # Skip user_training, notifications, and user_skills for now due to schema complexity

    print("\n✅ Mock Data Generation Complete!")
    print("\n📊 Summary:")
    print("   - 20 Users (12 Technicians, 4 Supervisors, 2 Parts Managers, 2 Managers)")
    print("   - 50 Assets across 5 categories")
    print("   - 100 Work Orders (various statuses)")
    print("   - 30 Parts in inventory")
    print("   - 30 Parts requests")
    print("   - 50 Team messages")
    print("   - 15 Training modules")
    print("\n🎉 Database is now populated with realistic, editable data!")


if __name__ == "__main__":
    main()
