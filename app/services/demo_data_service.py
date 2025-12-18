"""
ChatterFix Comprehensive Demo Data Service
Single source of truth for all demo/mock data across the platform.

This service provides rich, realistic demo data for:
- Work Orders (with completion rates, KPIs)
- Assets (with health scores, maintenance history)
- Inventory (parts, vendors, stock levels)
- Team (technicians with skills, performance)
- Analytics (KPIs, trends, charts)
- IoT (sensors, readings, alerts)
- Quality (HACCP, audits, compliance)
- Safety (incidents, violations, lab results)

Demo data is always available without authentication.
"""

import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class DemoDataService:
    """
    Comprehensive demo data service providing realistic CMMS data.
    All data is generated deterministically for consistency.
    """

    def __init__(self):
        self._cache = {}
        self._initialized = False
        self._seed_random()

    def _seed_random(self):
        """Seed random for consistent demo data"""
        random.seed(42)

    # ============================================================
    # WORK ORDERS
    # ============================================================

    def get_work_orders(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get demo work orders with realistic distribution"""
        if "work_orders" in self._cache:
            return self._cache["work_orders"][:limit]

        statuses = ["Open", "In Progress", "Completed", "On Hold"]
        priorities = ["Critical", "High", "Medium", "Low"]
        types = ["Corrective", "Preventive", "Emergency", "Inspection"]

        work_orders = []
        assets = self.get_assets()
        technicians = self.get_technicians()

        for i in range(156):  # Match analytics expectations
            created_days_ago = random.randint(0, 90)
            created_date = datetime.now() - timedelta(days=created_days_ago)

            # Realistic status distribution (70% completed for good KPIs)
            status_weights = [
                0.12,
                0.15,
                0.70,
                0.03,
            ]  # Open, In Progress, Completed, On Hold
            status = random.choices(statuses, weights=status_weights)[0]

            # Priority distribution
            priority_weights = [0.05, 0.20, 0.50, 0.25]
            priority = random.choices(priorities, weights=priority_weights)[0]

            work_order = {
                "id": f"WO-2024-{str(i+1).zfill(4)}",
                "title": self._generate_work_order_title(i),
                "description": self._generate_work_order_description(i),
                "status": status,
                "priority": priority,
                "type": random.choice(types),
                "asset_id": random.choice(assets)["id"],
                "asset_name": random.choice(assets)["name"],
                "assigned_to": random.choice(technicians)["id"],
                "assigned_name": random.choice(technicians)["name"],
                "created_at": created_date.isoformat(),
                "due_date": (
                    created_date + timedelta(days=random.randint(1, 14))
                ).isoformat(),
                "completed_at": (
                    (created_date + timedelta(days=random.randint(1, 7))).isoformat()
                    if status == "Completed"
                    else None
                ),
                "estimated_hours": round(random.uniform(0.5, 8), 1),
                "actual_hours": (
                    round(random.uniform(0.5, 10), 1) if status == "Completed" else None
                ),
                "labor_cost": (
                    round(random.uniform(50, 500), 2) if status == "Completed" else None
                ),
                "parts_cost": (
                    round(random.uniform(20, 300), 2) if status == "Completed" else None
                ),
                "location": random.choice(
                    [
                        "Building A",
                        "Building B",
                        "Warehouse",
                        "Production Floor",
                        "Maintenance Shop",
                    ]
                ),
            }
            work_orders.append(work_order)

        self._cache["work_orders"] = work_orders
        return work_orders[:limit]

    def _generate_work_order_title(self, index: int) -> str:
        titles = [
            "Replace HVAC filters",
            "Conveyor belt tension adjustment",
            "Hydraulic pump maintenance",
            "Electrical panel inspection",
            "Forklift service",
            "Compressor oil change",
            "Safety guard repair",
            "Motor bearing replacement",
            "PLC programming update",
            "Lubrication schedule",
            "Calibration check",
            "Valve replacement",
            "Gearbox inspection",
            "Belt replacement",
            "Sensor calibration",
            "Emergency stop test",
            "Fire suppression check",
            "Air quality monitor calibration",
            "Cooling system flush",
            "Pressure relief valve test",
            "Vibration analysis",
            "Thermal imaging inspection",
            "Alignment check",
            "Filter replacement",
            "Routine maintenance",
            "Preventive maintenance",
            "Equipment overhaul",
        ]
        return titles[index % len(titles)]

    def _generate_work_order_description(self, index: int) -> str:
        descriptions = [
            "Scheduled maintenance as per manufacturer recommendations",
            "Reported unusual noise during operation - investigate and repair",
            "Annual preventive maintenance inspection",
            "Replace worn components before failure",
            "Emergency repair - equipment down",
            "Routine calibration and testing",
            "Safety compliance inspection",
            "Performance optimization maintenance",
        ]
        return descriptions[index % len(descriptions)]

    # ============================================================
    # ASSETS
    # ============================================================

    def get_assets(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get demo assets with health scores"""
        if "assets" in self._cache:
            return self._cache["assets"][:limit]

        asset_types = [
            (
                "Production Line",
                ["Conveyor", "Assembly Station", "Packaging Unit", "Palletizer"],
            ),
            ("HVAC", ["Chiller", "Air Handler", "Cooling Tower", "Exhaust Fan"]),
            ("Material Handling", ["Forklift", "Pallet Jack", "Crane", "Conveyor"]),
            (
                "Compressors",
                ["Air Compressor", "Refrigeration Compressor", "Vacuum Pump"],
            ),
            ("Electrical", ["Transformer", "Motor Control Center", "Generator", "UPS"]),
            (
                "Pumps",
                [
                    "Centrifugal Pump",
                    "Hydraulic Pump",
                    "Vacuum Pump",
                    "Submersible Pump",
                ],
            ),
            ("CNC Machines", ["CNC Lathe", "CNC Mill", "CNC Router", "CNC Grinder"]),
            ("Welding", ["MIG Welder", "TIG Welder", "Spot Welder", "Plasma Cutter"]),
        ]

        locations = [
            "Building A",
            "Building B",
            "Warehouse",
            "Production Floor",
            "Maintenance Shop",
            "Loading Dock",
        ]
        statuses = ["Operational", "Needs Attention", "Under Maintenance", "Critical"]

        assets = []
        for i in range(50):
            asset_type, subtypes = random.choice(asset_types)
            subtype = random.choice(subtypes)

            # Health score distribution (mostly good)
            health_score = random.choices(
                [
                    random.randint(85, 100),
                    random.randint(60, 84),
                    random.randint(30, 59),
                    random.randint(0, 29),
                ],
                weights=[0.6, 0.25, 0.10, 0.05],
            )[0]

            status = (
                "Operational"
                if health_score >= 70
                else "Needs Attention" if health_score >= 40 else "Critical"
            )

            asset = {
                "id": f"AST-{str(i+1).zfill(4)}",
                "name": f"{subtype} #{i+1}",
                "type": asset_type,
                "subtype": subtype,
                "location": random.choice(locations),
                "status": status,
                "health_score": health_score,
                "criticality": random.choice(["High", "Medium", "Low"]),
                "manufacturer": random.choice(
                    [
                        "Siemens",
                        "ABB",
                        "Rockwell",
                        "Honeywell",
                        "Schneider",
                        "GE",
                        "Emerson",
                    ]
                ),
                "model": f"Model-{random.randint(100, 999)}",
                "serial_number": f"SN-{random.randint(10000, 99999)}",
                "install_date": (
                    datetime.now() - timedelta(days=random.randint(365, 3650))
                ).isoformat(),
                "last_maintenance": (
                    datetime.now() - timedelta(days=random.randint(1, 90))
                ).isoformat(),
                "next_maintenance": (
                    datetime.now() + timedelta(days=random.randint(1, 60))
                ).isoformat(),
                "replacement_cost": round(random.uniform(5000, 150000), 2),
                "maintenance_cost_ytd": round(random.uniform(500, 15000), 2),
                "uptime_percentage": round(random.uniform(85, 99.9), 1),
                "mtbf_hours": round(random.uniform(500, 5000), 1),
                "mttr_hours": round(random.uniform(0.5, 8), 1),
            }
            assets.append(asset)

        self._cache["assets"] = assets
        return assets[:limit]

    # ============================================================
    # TECHNICIANS / TEAM
    # ============================================================

    def get_technicians(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Get demo technicians with skills and performance"""
        if "technicians" in self._cache:
            return self._cache["technicians"][:limit]

        first_names = [
            "Mike",
            "Sarah",
            "Alex",
            "John",
            "Emily",
            "David",
            "Maria",
            "James",
            "Lisa",
            "Robert",
            "Jennifer",
            "Michael",
            "Jessica",
            "William",
            "Amanda",
            "Daniel",
            "Ashley",
            "Chris",
            "Nicole",
            "Kevin",
            "Samantha",
            "Brian",
            "Rachel",
            "Ryan",
            "Laura",
        ]
        last_names = [
            "Johnson",
            "Chen",
            "Rodriguez",
            "Smith",
            "Williams",
            "Brown",
            "Jones",
            "Garcia",
            "Miller",
            "Davis",
            "Martinez",
            "Anderson",
            "Taylor",
            "Thomas",
            "Moore",
            "Jackson",
            "Martin",
            "Lee",
            "Thompson",
            "White",
        ]

        skills = [
            "Electrical",
            "Mechanical",
            "HVAC",
            "Plumbing",
            "Welding",
            "PLC Programming",
            "Hydraulics",
            "Pneumatics",
            "Instrumentation",
            "Preventive Maintenance",
            "CNC Operation",
            "Robotics",
            "Conveyor Systems",
            "Refrigeration",
            "Safety Systems",
        ]

        shifts = [
            "Day Shift (6AM-2PM)",
            "Swing Shift (2PM-10PM)",
            "Night Shift (10PM-6AM)",
            "Rotating",
        ]
        roles = [
            "Lead Technician",
            "Senior Technician",
            "Technician",
            "Junior Technician",
            "Apprentice",
        ]

        technicians = []
        for i in range(25):
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            tech_skills = random.sample(skills, random.randint(3, 7))

            # Performance metrics
            completion_rate = round(random.uniform(85, 99), 1)
            avg_response_time = round(random.uniform(10, 45), 0)  # minutes
            customer_rating = round(random.uniform(4.2, 5.0), 1)

            technician = {
                "id": f"TECH-{str(i+1).zfill(3)}",
                "name": name,
                "email": f"{name.lower().replace(' ', '.')}@chatterfix.com",
                "role": random.choice(roles),
                "shift": random.choice(shifts),
                "skills": tech_skills,
                "certifications": random.sample(
                    [
                        "OSHA 10",
                        "OSHA 30",
                        "EPA 608",
                        "Electrical License",
                        "Welding Cert",
                    ],
                    random.randint(1, 3),
                ),
                "hire_date": (
                    datetime.now() - timedelta(days=random.randint(180, 3650))
                ).isoformat(),
                "performance": {
                    "completion_rate": completion_rate,
                    "avg_response_time_min": avg_response_time,
                    "customer_rating": customer_rating,
                    "work_orders_completed_mtd": random.randint(15, 45),
                    "work_orders_completed_ytd": random.randint(150, 450),
                    "training_hours_ytd": random.randint(20, 80),
                },
                "hourly_rate": round(random.uniform(25, 55), 2),
                "status": random.choices(
                    ["Available", "On Job", "Off Duty", "Training"],
                    weights=[0.4, 0.35, 0.15, 0.1],
                )[0],
                "avatar_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={name.replace(' ', '')}",
            }
            technicians.append(technician)

        self._cache["technicians"] = technicians
        return technicians[:limit]

    # ============================================================
    # INVENTORY / PARTS
    # ============================================================

    def get_parts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get demo inventory parts"""
        if "parts" in self._cache:
            return self._cache["parts"][:limit]

        part_categories = {
            "Filters": [
                "HVAC Filter",
                "Oil Filter",
                "Air Filter",
                "Hydraulic Filter",
                "Fuel Filter",
            ],
            "Bearings": [
                "Ball Bearing",
                "Roller Bearing",
                "Thrust Bearing",
                "Sleeve Bearing",
            ],
            "Belts": ["V-Belt", "Timing Belt", "Flat Belt", "Serpentine Belt"],
            "Seals": ["O-Ring", "Gasket", "Lip Seal", "Mechanical Seal"],
            "Electrical": [
                "Contactor",
                "Relay",
                "Fuse",
                "Circuit Breaker",
                "Motor Starter",
            ],
            "Lubricants": ["Motor Oil", "Hydraulic Fluid", "Grease", "Gear Oil"],
            "Fasteners": ["Bolts", "Nuts", "Screws", "Washers"],
            "Sensors": [
                "Temperature Sensor",
                "Pressure Sensor",
                "Flow Sensor",
                "Proximity Sensor",
            ],
        }

        parts = []
        for i in range(100):
            category = random.choice(list(part_categories.keys()))
            part_name = random.choice(part_categories[category])

            stock_qty = random.randint(0, 100)
            reorder_point = random.randint(5, 20)
            stock_status = (
                "In Stock"
                if stock_qty > reorder_point
                else "Low Stock" if stock_qty > 0 else "Out of Stock"
            )

            part = {
                "id": f"PRT-{str(i+1).zfill(5)}",
                "name": f"{part_name} - {random.choice(['Standard', 'Heavy Duty', 'Premium', 'Economy'])}",
                "sku": f"SKU-{random.randint(10000, 99999)}",
                "category": category,
                "description": f"High-quality {part_name.lower()} for industrial applications",
                "manufacturer": random.choice(
                    ["SKF", "NSK", "Gates", "Parker", "Timken", "3M", "Loctite"]
                ),
                "unit_cost": round(random.uniform(5, 500), 2),
                "quantity_on_hand": stock_qty,
                "reorder_point": reorder_point,
                "reorder_quantity": reorder_point * 3,
                "stock_status": stock_status,
                "location": f"Bin {random.choice(['A', 'B', 'C', 'D'])}-{random.randint(1, 20)}",
                "last_ordered": (
                    datetime.now() - timedelta(days=random.randint(1, 90))
                ).isoformat(),
                "lead_time_days": random.randint(1, 14),
                "usage_ytd": random.randint(10, 200),
                "critical_spare": random.random() < 0.2,
            }
            parts.append(part)

        self._cache["parts"] = parts
        return parts[:limit]

    # ============================================================
    # ANALYTICS / KPIs
    # ============================================================

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get comprehensive analytics summary with KPIs"""
        work_orders = self.get_work_orders()
        assets = self.get_assets()
        technicians = self.get_technicians()

        # Calculate real metrics from demo data
        completed_wos = [wo for wo in work_orders if wo["status"] == "Completed"]
        completion_rate = (
            len(completed_wos) / len(work_orders) * 100 if work_orders else 0
        )

        # Work order metrics
        total_labor_cost = sum(wo.get("labor_cost", 0) or 0 for wo in completed_wos)
        total_parts_cost = sum(wo.get("parts_cost", 0) or 0 for wo in completed_wos)

        # Asset metrics
        avg_health_score = (
            sum(a["health_score"] for a in assets) / len(assets) if assets else 0
        )
        critical_assets = len([a for a in assets if a["status"] == "Critical"])

        return {
            "overview": {
                "total_work_orders": len(work_orders),
                "completed_work_orders": len(completed_wos),
                "open_work_orders": len(
                    [wo for wo in work_orders if wo["status"] == "Open"]
                ),
                "in_progress_work_orders": len(
                    [wo for wo in work_orders if wo["status"] == "In Progress"]
                ),
                "completion_rate": round(completion_rate, 1),
                "total_assets": len(assets),
                "critical_assets": critical_assets,
                "total_technicians": len(technicians),
            },
            "kpis": {
                "mttr": {
                    "value": 2.4,
                    "unit": "hours",
                    "trend": "down",
                    "change_percent": -8.5,
                    "target": 3.0,
                    "status": "good",
                },
                "mtbf": {
                    "value": 168.5,
                    "unit": "hours",
                    "trend": "up",
                    "change_percent": 12.3,
                    "target": 150.0,
                    "status": "good",
                },
                "completion_rate": {
                    "value": round(completion_rate, 1),
                    "unit": "%",
                    "trend": "up",
                    "change_percent": 5.2,
                    "target": 90.0,
                    "status": "good" if completion_rate >= 85 else "warning",
                },
                "pm_compliance": {
                    "value": 92.5,
                    "unit": "%",
                    "trend": "up",
                    "change_percent": 3.8,
                    "target": 90.0,
                    "status": "good",
                },
                "asset_uptime": {
                    "value": 97.3,
                    "unit": "%",
                    "trend": "stable",
                    "change_percent": 0.5,
                    "target": 95.0,
                    "status": "good",
                },
                "avg_health_score": {
                    "value": round(avg_health_score, 1),
                    "unit": "score",
                    "trend": "up",
                    "change_percent": 2.1,
                    "target": 80.0,
                    "status": "good" if avg_health_score >= 75 else "warning",
                },
            },
            "costs": {
                "total_maintenance_cost": round(total_labor_cost + total_parts_cost, 2),
                "labor_cost": round(total_labor_cost, 2),
                "parts_cost": round(total_parts_cost, 2),
                "cost_per_work_order": (
                    round((total_labor_cost + total_parts_cost) / len(completed_wos), 2)
                    if completed_wos
                    else 0
                ),
                "budget_used_percent": 67.5,
                "projected_annual": round((total_labor_cost + total_parts_cost) * 4, 2),
            },
            "trends": self._generate_trend_data(),
            "charts": self._generate_chart_data(work_orders, assets),
        }

    def _generate_trend_data(self) -> Dict[str, List]:
        """Generate 30-day trend data"""
        trend_data = {
            "dates": [],
            "work_orders_created": [],
            "work_orders_completed": [],
            "avg_completion_time": [],
            "costs": [],
        }

        for i in range(30):
            date = datetime.now() - timedelta(days=29 - i)
            trend_data["dates"].append(date.strftime("%Y-%m-%d"))
            trend_data["work_orders_created"].append(random.randint(3, 12))
            trend_data["work_orders_completed"].append(random.randint(3, 10))
            trend_data["avg_completion_time"].append(round(random.uniform(1.5, 4.5), 1))
            trend_data["costs"].append(round(random.uniform(500, 2500), 2))

        return trend_data

    def _generate_chart_data(self, work_orders: List, assets: List) -> Dict[str, Any]:
        """Generate data for dashboard charts"""
        # Work order status distribution
        status_counts = {}
        for wo in work_orders:
            status = wo["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        # Priority distribution
        priority_counts = {}
        for wo in work_orders:
            priority = wo["priority"]
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        # Asset health distribution
        health_ranges = {
            "Excellent (85-100)": 0,
            "Good (70-84)": 0,
            "Fair (50-69)": 0,
            "Poor (0-49)": 0,
        }
        for asset in assets:
            score = asset["health_score"]
            if score >= 85:
                health_ranges["Excellent (85-100)"] += 1
            elif score >= 70:
                health_ranges["Good (70-84)"] += 1
            elif score >= 50:
                health_ranges["Fair (50-69)"] += 1
            else:
                health_ranges["Poor (0-49)"] += 1

        return {
            "work_order_status": {
                "labels": list(status_counts.keys()),
                "data": list(status_counts.values()),
                "colors": ["#3498db", "#f39c12", "#27ae60", "#e74c3c"],
            },
            "priority_distribution": {
                "labels": list(priority_counts.keys()),
                "data": list(priority_counts.values()),
                "colors": ["#e74c3c", "#f39c12", "#3498db", "#95a5a6"],
            },
            "asset_health": {
                "labels": list(health_ranges.keys()),
                "data": list(health_ranges.values()),
                "colors": ["#27ae60", "#3498db", "#f39c12", "#e74c3c"],
            },
            "maintenance_by_type": {
                "labels": ["Preventive", "Corrective", "Emergency", "Inspection"],
                "data": [45, 32, 12, 11],
                "colors": ["#27ae60", "#3498db", "#e74c3c", "#9b59b6"],
            },
        }

    # ============================================================
    # IoT DATA
    # ============================================================

    def get_iot_sensors(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Get demo IoT sensors with current readings"""
        if "sensors" in self._cache:
            return self._cache["sensors"][:limit]

        sensor_types = [
            ("Temperature", "°C", 15, 85, 20, 75),
            ("Pressure", "PSI", 0, 200, 20, 150),
            ("Vibration", "mm/s", 0, 50, 0, 25),
            ("Humidity", "%", 20, 80, 30, 70),
            ("Flow Rate", "L/min", 0, 500, 50, 400),
            ("Power", "kW", 0, 100, 10, 80),
        ]

        assets = self.get_assets()
        sensors = []

        for i in range(25):
            sensor_type, unit, min_val, max_val, low_limit, high_limit = random.choice(
                sensor_types
            )
            current_value = round(random.uniform(min_val, max_val), 1)

            status = "Normal"
            if current_value < low_limit or current_value > high_limit:
                status = "Warning"
            if current_value < min_val * 0.1 or current_value > max_val * 0.95:
                status = "Critical"

            sensor = {
                "id": f"SNS-{str(i+1).zfill(4)}",
                "name": f"{sensor_type} Sensor {i+1}",
                "type": sensor_type,
                "unit": unit,
                "asset_id": random.choice(assets)["id"],
                "asset_name": random.choice(assets)["name"],
                "location": random.choice(
                    ["Building A", "Building B", "Production Floor"]
                ),
                "current_value": current_value,
                "min_threshold": low_limit,
                "max_threshold": high_limit,
                "status": status,
                "last_reading": datetime.now().isoformat(),
                "battery_level": random.randint(20, 100),
                "signal_strength": random.randint(60, 100),
                "readings_24h": [
                    round(random.uniform(min_val, max_val), 1) for _ in range(24)
                ],
            }
            sensors.append(sensor)

        self._cache["sensors"] = sensors
        return sensors[:limit]

    # ============================================================
    # QUALITY DATA
    # ============================================================

    def get_quality_data(self) -> Dict[str, Any]:
        """Get demo quality management data"""
        return {
            "haccp_plans": [
                {
                    "id": "HACCP-001",
                    "name": "Pasteurization CCP",
                    "process": "Milk Pasteurization",
                    "critical_limit": "72°C for 15 seconds",
                    "monitoring": "Continuous temperature recording",
                    "corrective_action": "Divert product and recycle",
                    "status": "Active",
                    "last_review": (datetime.now() - timedelta(days=30)).isoformat(),
                },
                {
                    "id": "HACCP-002",
                    "name": "Metal Detection CCP",
                    "process": "Final Packaging",
                    "critical_limit": "No metal > 2mm",
                    "monitoring": "100% inline detection",
                    "corrective_action": "Reject and investigate",
                    "status": "Active",
                    "last_review": (datetime.now() - timedelta(days=15)).isoformat(),
                },
            ],
            "temperature_logs": [
                {
                    "location": "Cold Storage A",
                    "current": 2.5,
                    "target": 4.0,
                    "status": "Compliant",
                },
                {
                    "location": "Freezer B",
                    "current": -18.2,
                    "target": -18.0,
                    "status": "Compliant",
                },
                {
                    "location": "Processing Room",
                    "current": 12.1,
                    "target": 12.0,
                    "status": "Compliant",
                },
            ],
            "compliance_metrics": {
                "overall_compliance": 96.8,
                "haccp_compliance": 100,
                "gmp_compliance": 95.2,
                "sanitation_compliance": 97.5,
                "training_compliance": 94.3,
            },
            "recent_audits": [
                {"date": "2024-12-01", "type": "Internal", "score": 94, "findings": 3},
                {"date": "2024-11-15", "type": "Customer", "score": 97, "findings": 1},
                {
                    "date": "2024-10-20",
                    "type": "Regulatory",
                    "score": 92,
                    "findings": 5,
                },
            ],
        }

    # ============================================================
    # SAFETY DATA
    # ============================================================

    def get_safety_data(self) -> Dict[str, Any]:
        """Get demo safety management data"""
        return {
            "incidents_ytd": 8,
            "near_misses_ytd": 45,
            "days_without_incident": 47,
            "trir": 2.4,
            "dart_rate": 1.8,
            "recent_incidents": [
                {
                    "id": "INC-2024-008",
                    "date": (datetime.now() - timedelta(days=47)).isoformat(),
                    "type": "Near Miss",
                    "severity": "Low",
                    "description": "Forklift near miss in warehouse",
                    "status": "Closed",
                    "corrective_action": "Additional signage installed",
                },
                {
                    "id": "INC-2024-007",
                    "date": (datetime.now() - timedelta(days=62)).isoformat(),
                    "type": "First Aid",
                    "severity": "Low",
                    "description": "Minor cut during maintenance",
                    "status": "Closed",
                    "corrective_action": "PPE reminder issued",
                },
            ],
            "compliance": {
                "osha_compliance": 94.2,
                "training_current": 96.8,
                "ppe_compliance": 98.5,
                "inspection_compliance": 92.1,
            },
            "upcoming_inspections": [
                {"date": "2024-12-20", "type": "Fire Safety", "area": "All Buildings"},
                {"date": "2025-01-15", "type": "OSHA", "area": "Production Floor"},
            ],
        }

    # ============================================================
    # DASHBOARD DATA
    # ============================================================

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get complete dashboard data combining all sources"""
        analytics = self.get_analytics_summary()
        work_orders = self.get_work_orders(10)
        assets = self.get_assets(10)
        technicians = self.get_technicians(5)

        return {
            "summary": analytics["overview"],
            "kpis": analytics["kpis"],
            "costs": analytics["costs"],
            "charts": analytics["charts"],
            "recent_work_orders": work_orders,
            "critical_assets": [
                a for a in assets if a["status"] in ["Critical", "Needs Attention"]
            ][:5],
            "top_technicians": sorted(
                technicians,
                key=lambda t: t["performance"]["completion_rate"],
                reverse=True,
            )[:5],
            "alerts": [
                {
                    "type": "warning",
                    "message": "3 assets require attention",
                    "time": "2 hours ago",
                },
                {
                    "type": "info",
                    "message": "Preventive maintenance due for 5 assets",
                    "time": "4 hours ago",
                },
                {
                    "type": "success",
                    "message": "All safety inspections completed",
                    "time": "1 day ago",
                },
            ],
            "activity_feed": [
                {
                    "action": "Work order completed",
                    "details": "WO-2024-0145 - HVAC Filter Replacement",
                    "user": "Mike Johnson",
                    "time": "15 minutes ago",
                },
                {
                    "action": "Part checked out",
                    "details": "SKU-12345 - Bearing Assembly (qty: 2)",
                    "user": "Sarah Chen",
                    "time": "1 hour ago",
                },
                {
                    "action": "Asset inspection",
                    "details": "AST-0012 passed routine inspection",
                    "user": "Alex Rodriguez",
                    "time": "2 hours ago",
                },
            ],
        }


# Global instance
demo_data_service = DemoDataService()


# Convenience functions
def get_demo_work_orders(limit: int = 50) -> List[Dict]:
    return demo_data_service.get_work_orders(limit)


def get_demo_assets(limit: int = 50) -> List[Dict]:
    return demo_data_service.get_assets(limit)


def get_demo_technicians(limit: int = 25) -> List[Dict]:
    return demo_data_service.get_technicians(limit)


def get_demo_parts(limit: int = 100) -> List[Dict]:
    return demo_data_service.get_parts(limit)


def get_demo_analytics() -> Dict:
    return demo_data_service.get_analytics_summary()


def get_demo_dashboard() -> Dict:
    return demo_data_service.get_dashboard_data()


def get_demo_iot_sensors(limit: int = 25) -> List[Dict]:
    return demo_data_service.get_iot_sensors(limit)


def get_demo_quality_data() -> Dict:
    return demo_data_service.get_quality_data()


def get_demo_safety_data() -> Dict:
    return demo_data_service.get_safety_data()


logger.info("Demo Data Service initialized with comprehensive mock data")
