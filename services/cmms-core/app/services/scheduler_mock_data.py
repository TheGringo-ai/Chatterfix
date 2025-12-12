"""
Advanced Scheduler Mock Data Service
Generates comprehensive mock data for demonstration of enterprise-level scheduling capabilities
"""

import random
from datetime import datetime, time, timedelta
from typing import Any, Dict, List

from app.services.advanced_scheduler_service import (
    AssetRequirement,
    Skill,
    TechnicianProfile,
    TechnicianStatus,
    WorkShift,
)


class SchedulerMockDataService:
    """Service to generate comprehensive mock data for the advanced scheduler"""

    def __init__(self):
        self.locations = [
            "Building A - Production Floor",
            "Building B - Assembly Line",
            "Building C - Quality Control",
            "Warehouse North",
            "Warehouse South",
            "Outdoor Yard",
            "Maintenance Shop",
            "Utility Building",
        ]

        self.skill_definitions = {
            "hydraulics": {"base_rate": 28.50, "complexity": 4},
            "electrical": {"base_rate": 32.00, "complexity": 5},
            "mechanical": {"base_rate": 26.00, "complexity": 3},
            "hvac": {"base_rate": 29.00, "complexity": 4},
            "plumbing": {"base_rate": 25.50, "complexity": 3},
            "welding": {"base_rate": 31.00, "complexity": 5},
            "cnc_operation": {"base_rate": 35.00, "complexity": 5},
            "safety_inspection": {"base_rate": 24.00, "complexity": 2},
            "preventive_maintenance": {"base_rate": 22.50, "complexity": 2},
            "troubleshooting": {"base_rate": 30.00, "complexity": 4},
            "pneumatics": {"base_rate": 27.00, "complexity": 3},
            "conveyor_systems": {"base_rate": 26.50, "complexity": 3},
            "motor_repair": {"base_rate": 33.00, "complexity": 4},
            "bearing_alignment": {"base_rate": 34.50, "complexity": 5},
            "vibration_analysis": {"base_rate": 38.00, "complexity": 5},
            "robotics": {"base_rate": 42.00, "complexity": 5},
            "plc_programming": {"base_rate": 45.00, "complexity": 5},
            "instrumentation": {"base_rate": 36.00, "complexity": 4},
            "boiler_operation": {"base_rate": 31.50, "complexity": 4},
            "refrigeration": {"base_rate": 29.50, "complexity": 4},
        }

        self.shifts = [
            WorkShift(time(6, 0), time(14, 0), "UTC", [0, 1, 2, 3, 4]),  # Day shift
            WorkShift(
                time(14, 0), time(22, 0), "UTC", [0, 1, 2, 3, 4]
            ),  # Evening shift
            WorkShift(time(22, 0), time(6, 0), "UTC", [0, 1, 2, 3, 4]),  # Night shift
            WorkShift(time(7, 0), time(19, 0), "UTC", [0, 1, 2, 3, 4]),  # Extended day
            WorkShift(time(8, 0), time(16, 0), "UTC", [5, 6]),  # Weekend shift
        ]

    def generate_technician_profiles(
        self, count: int = 25
    ) -> Dict[str, TechnicianProfile]:
        """Generate comprehensive technician profiles"""
        technicians = {}

        # Realistic technician data
        names = [
            ("John", "Martinez"),
            ("Sarah", "Chen"),
            ("Mike", "Johnson"),
            ("Lisa", "Rodriguez"),
            ("David", "Kim"),
            ("Emma", "Wilson"),
            ("Carlos", "Lopez"),
            ("Jennifer", "Brown"),
            ("Robert", "Davis"),
            ("Angela", "Thompson"),
            ("James", "Garcia"),
            ("Maria", "Gonzalez"),
            ("Kevin", "Lee"),
            ("Rachel", "White"),
            ("Daniel", "Martinez"),
            ("Ashley", "Johnson"),
            ("Brandon", "Smith"),
            ("Stephanie", "Jones"),
            ("Tyler", "Williams"),
            ("Nicole", "Anderson"),
            ("Christopher", "Taylor"),
            ("Amanda", "Clark"),
            ("Justin", "Lewis"),
            ("Samantha", "Hall"),
            ("Anthony", "Young"),
            ("Rebecca", "Walker"),
            ("Michael", "Allen"),
            ("Laura", "King"),
            ("Ryan", "Wright"),
            ("Melissa", "Scott"),
            ("Jason", "Green"),
            ("Kimberly", "Adams"),
            ("Matthew", "Baker"),
            ("Elizabeth", "Nelson"),
            ("Andrew", "Carter"),
            ("Michelle", "Mitchell"),
        ]

        # Skill combinations that make sense
        skill_combinations = [
            ["hydraulics", "mechanical", "safety_inspection", "troubleshooting"],
            ["electrical", "plc_programming", "instrumentation", "troubleshooting"],
            ["welding", "mechanical", "fabrication", "safety_inspection"],
            ["hvac", "refrigeration", "electrical", "preventive_maintenance"],
            [
                "cnc_operation",
                "mechanical",
                "troubleshooting",
                "preventive_maintenance",
            ],
            ["conveyor_systems", "electrical", "mechanical", "troubleshooting"],
            ["motor_repair", "electrical", "vibration_analysis", "bearing_alignment"],
            ["pneumatics", "hydraulics", "troubleshooting", "preventive_maintenance"],
            ["robotics", "electrical", "plc_programming", "troubleshooting"],
            [
                "boiler_operation",
                "safety_inspection",
                "preventive_maintenance",
                "troubleshooting",
            ],
        ]

        for i in range(min(count, len(names))):
            first_name, last_name = names[i]
            tech_id = f"tech_{i + 1:03d}"

            # Assign skill combination
            base_skills = random.choice(skill_combinations)

            # Add 1-3 additional random skills
            additional_skills = random.sample(
                [
                    skill
                    for skill in self.skill_definitions.keys()
                    if skill not in base_skills
                ],
                random.randint(1, 3),
            )
            all_skills = base_skills + additional_skills

            # Create skill objects with realistic levels
            tech_skills = []
            total_skill_value = 0

            for skill_name in all_skills:
                if skill_name in self.skill_definitions:
                    # Primary skills get higher levels
                    if skill_name in base_skills:
                        level = random.randint(3, 5)
                    else:
                        level = random.randint(1, 3)

                    certified = level >= 4 and random.random() > 0.3
                    cert_expiry = None
                    if certified:
                        cert_expiry = datetime.now() + timedelta(
                            days=random.randint(180, 730)
                        )

                    tech_skills.append(
                        Skill(
                            name=skill_name,
                            level=level,
                            certified=certified,
                            certification_expiry=cert_expiry,
                        )
                    )

                    total_skill_value += (
                        level * self.skill_definitions[skill_name]["complexity"]
                    )

            # Calculate hourly rate based on skills and experience
            base_rate = 22.00
            skill_premium = total_skill_value * 0.8
            experience_premium = random.uniform(2.0, 12.0)  # 2-12 years experience
            hourly_rate = base_rate + skill_premium + experience_premium

            # Assign shift (weighted towards day shift)
            shift_weights = [0.5, 0.3, 0.15, 0.03, 0.02]
            shift_index = random.choices(
                range(len(self.shifts)), weights=shift_weights
            )[0]
            assigned_shift = self.shifts[shift_index]

            # Assign location
            location = random.choice(self.locations)

            # Determine status (mostly available)
            status_weights = [0.75, 0.05, 0.05, 0.05, 0.05, 0.05]
            status_options = list(TechnicianStatus)
            status = random.choices(status_options, weights=status_weights)[0]

            # Generate upcoming unavailability (vacations, training, etc.)
            unavailability = []
            if random.random() < 0.2:  # 20% chance of upcoming unavailability
                start_date = datetime.now() + timedelta(days=random.randint(7, 60))
                duration = random.randint(1, 5)  # 1-5 days
                end_date = start_date + timedelta(days=duration)
                unavailability.append((start_date, end_date))

            technicians[tech_id] = TechnicianProfile(
                id=tech_id,
                name=f"{first_name} {last_name}",
                email=f"{first_name.lower()}.{last_name.lower()}@chatterfix.com",
                phone=f"+1-555-{random.randint(1000, 9999)}",
                status=status,
                skills=tech_skills,
                location=location,
                shift=assigned_shift,
                hourly_rate=round(hourly_rate, 2),
                max_hours_per_day=(
                    8 if shift_index < 3 else 10
                ),  # Extended shifts allow more hours
                overtime_rate_multiplier=1.5,
                current_workload_hours=random.uniform(0, 4),  # Some existing workload
                upcoming_unavailability=unavailability,
            )

        return technicians

    def generate_asset_requirements(
        self, count: int = 50
    ) -> Dict[str, AssetRequirement]:
        """Generate comprehensive asset maintenance requirements"""
        assets = {}

        # Asset type definitions
        asset_types = [
            {
                "prefix": "hydraulic_press",
                "count": 8,
                "skills": ["hydraulics", "mechanical", "safety_inspection"],
                "duration_range": (3.5, 6.0),
                "criticality_range": (4, 5),
                "maintenance_interval": 30,
                "locations": [
                    "Building A - Production Floor",
                    "Building B - Assembly Line",
                ],
            },
            {
                "prefix": "cnc_machine",
                "count": 12,
                "skills": [
                    "cnc_operation",
                    "electrical",
                    "mechanical",
                    "troubleshooting",
                ],
                "duration_range": (4.0, 8.0),
                "criticality_range": (4, 5),
                "maintenance_interval": 21,
                "locations": [
                    "Building A - Production Floor",
                    "Building B - Assembly Line",
                ],
            },
            {
                "prefix": "conveyor_system",
                "count": 8,
                "skills": ["conveyor_systems", "electrical", "mechanical"],
                "duration_range": (2.5, 5.0),
                "criticality_range": (3, 4),
                "maintenance_interval": 14,
                "locations": [
                    "Warehouse North",
                    "Warehouse South",
                    "Building B - Assembly Line",
                ],
            },
            {
                "prefix": "motor_drive",
                "count": 15,
                "skills": ["motor_repair", "electrical", "vibration_analysis"],
                "duration_range": (2.0, 4.0),
                "criticality_range": (3, 4),
                "maintenance_interval": 45,
                "locations": [
                    "Building A - Production Floor",
                    "Building B - Assembly Line",
                    "Building C - Quality Control",
                ],
            },
            {
                "prefix": "hvac_unit",
                "count": 6,
                "skills": ["hvac", "electrical", "preventive_maintenance"],
                "duration_range": (3.0, 6.0),
                "criticality_range": (2, 4),
                "maintenance_interval": 90,
                "locations": [
                    "Building A - Production Floor",
                    "Building B - Assembly Line",
                    "Building C - Quality Control",
                ],
            },
            {
                "prefix": "air_compressor",
                "count": 4,
                "skills": ["pneumatics", "mechanical", "electrical"],
                "duration_range": (2.5, 4.5),
                "criticality_range": (3, 5),
                "maintenance_interval": 60,
                "locations": ["Utility Building", "Building A - Production Floor"],
            },
            {
                "prefix": "robotic_cell",
                "count": 6,
                "skills": [
                    "robotics",
                    "electrical",
                    "plc_programming",
                    "safety_inspection",
                ],
                "duration_range": (6.0, 12.0),
                "criticality_range": (5, 5),
                "maintenance_interval": 28,
                "locations": [
                    "Building A - Production Floor",
                    "Building B - Assembly Line",
                ],
            },
            {
                "prefix": "boiler_unit",
                "count": 3,
                "skills": [
                    "boiler_operation",
                    "safety_inspection",
                    "preventive_maintenance",
                ],
                "duration_range": (4.0, 8.0),
                "criticality_range": (4, 5),
                "maintenance_interval": 120,
                "locations": ["Utility Building"],
            },
            {
                "prefix": "crane_overhead",
                "count": 4,
                "skills": ["mechanical", "electrical", "safety_inspection"],
                "duration_range": (3.0, 6.0),
                "criticality_range": (4, 5),
                "maintenance_interval": 30,
                "locations": [
                    "Building A - Production Floor",
                    "Building B - Assembly Line",
                    "Warehouse North",
                ],
            },
            {
                "prefix": "forklift",
                "count": 8,
                "skills": ["mechanical", "hydraulics", "safety_inspection"],
                "duration_range": (1.5, 3.0),
                "criticality_range": (2, 3),
                "maintenance_interval": 21,
                "locations": ["Warehouse North", "Warehouse South", "Outdoor Yard"],
            },
        ]

        asset_counter = 1
        for asset_type in asset_types:
            for i in range(asset_type["count"]):
                asset_id = f"{asset_type['prefix']}_{i + 1:03d}"

                # Determine maintenance timing
                interval = asset_type["maintenance_interval"]
                last_maintenance = datetime.now() - timedelta(
                    days=random.randint(0, interval)
                )
                next_due = last_maintenance + timedelta(days=interval)

                # Add some variation to due dates
                variation_days = random.randint(-3, 7)  # Can be slightly early or late
                next_due += timedelta(days=variation_days)

                # Determine criticality
                criticality = random.randint(*asset_type["criticality_range"])

                # Determine duration
                duration = round(random.uniform(*asset_type["duration_range"]), 1)

                # Set maintenance window based on criticality
                maintenance_window = None
                if criticality >= 5:
                    # Critical equipment - off-hours maintenance
                    maintenance_window = (time(22, 0), time(6, 0))
                elif criticality >= 4:
                    # High importance - early morning or evening
                    maintenance_window = (time(6, 0), time(8, 0))

                # Assign location
                location = random.choice(asset_type["locations"])

                assets[asset_id] = AssetRequirement(
                    asset_id=asset_id,
                    required_skills=asset_type["skills"].copy(),
                    estimated_duration=duration,
                    criticality=criticality,
                    location=location,
                    last_maintenance=last_maintenance,
                    next_due=next_due,
                    maintenance_window=maintenance_window,
                )

                asset_counter += 1
                if asset_counter > count:
                    return assets

        return assets

    def generate_emergency_scenarios(self, count: int = 10) -> List[Dict[str, Any]]:
        """Generate emergency maintenance scenarios"""
        emergency_types = [
            {
                "title": "Hydraulic System Leak",
                "description": "Major hydraulic fluid leak detected",
                "affected_systems": ["hydraulic_press", "crane_overhead"],
                "required_skills": ["hydraulics", "mechanical", "safety_inspection"],
                "duration_multiplier": 2.0,
                "urgency": "EMERGENCY",
            },
            {
                "title": "Electrical Panel Fire",
                "description": "Smoke detected from main electrical panel",
                "affected_systems": ["cnc_machine", "motor_drive"],
                "required_skills": [
                    "electrical",
                    "safety_inspection",
                    "troubleshooting",
                ],
                "duration_multiplier": 1.8,
                "urgency": "EMERGENCY",
            },
            {
                "title": "Conveyor Belt Jam",
                "description": "Material jam causing production stoppage",
                "affected_systems": ["conveyor_system"],
                "required_skills": ["conveyor_systems", "mechanical"],
                "duration_multiplier": 1.3,
                "urgency": "URGENT",
            },
            {
                "title": "Robot Malfunction",
                "description": "Robotic arm stuck in unsafe position",
                "affected_systems": ["robotic_cell"],
                "required_skills": ["robotics", "plc_programming", "safety_inspection"],
                "duration_multiplier": 2.5,
                "urgency": "EMERGENCY",
            },
            {
                "title": "HVAC System Failure",
                "description": "Complete HVAC system shutdown",
                "affected_systems": ["hvac_unit"],
                "required_skills": ["hvac", "electrical", "troubleshooting"],
                "duration_multiplier": 1.5,
                "urgency": "HIGH",
            },
        ]

        scenarios = []
        for i in range(count):
            scenario_type = random.choice(emergency_types)

            # Create emergency work order
            emergency_time = datetime.now() + timedelta(
                hours=random.randint(1, 72)  # Emergency in next 3 days
            )

            scenario = {
                "id": f"emergency_{i + 1:03d}",
                "title": scenario_type["title"],
                "description": scenario_type["description"],
                "emergency_time": emergency_time,
                "required_skills": scenario_type["required_skills"],
                "duration_multiplier": scenario_type["duration_multiplier"],
                "urgency": scenario_type["urgency"],
                "affected_systems": scenario_type["affected_systems"],
            }
            scenarios.append(scenario)

        return scenarios

    def generate_workload_scenarios(self) -> Dict[str, Any]:
        """Generate various workload scenarios for testing"""
        return {
            "normal_operations": {
                "description": "Standard maintenance schedule with typical workload",
                "work_order_multiplier": 1.0,
                "emergency_rate": 0.05,  # 5% emergency rate
                "overtime_threshold": 8.0,
            },
            "peak_season": {
                "description": "High production season with increased maintenance needs",
                "work_order_multiplier": 1.4,
                "emergency_rate": 0.08,  # 8% emergency rate
                "overtime_threshold": 10.0,
            },
            "maintenance_shutdown": {
                "description": "Planned maintenance shutdown with major overhauls",
                "work_order_multiplier": 2.0,
                "emergency_rate": 0.02,  # 2% emergency rate (planned work)
                "overtime_threshold": 12.0,
            },
            "skeleton_crew": {
                "description": "Reduced staffing during holidays or downtime",
                "work_order_multiplier": 0.6,
                "emergency_rate": 0.12,  # 12% emergency rate (understaffed)
                "overtime_threshold": 6.0,
            },
        }

    def get_comprehensive_mock_data(self) -> Dict[str, Any]:
        """Get all mock data in a comprehensive package"""
        return {
            "technicians": self.generate_technician_profiles(25),
            "assets": self.generate_asset_requirements(50),
            "emergency_scenarios": self.generate_emergency_scenarios(10),
            "workload_scenarios": self.generate_workload_scenarios(),
            "locations": self.locations,
            "skills": self.skill_definitions,
            "shifts": [
                {
                    "name": "Day Shift",
                    "start": "06:00",
                    "end": "14:00",
                    "days": "Monday-Friday",
                },
                {
                    "name": "Evening Shift",
                    "start": "14:00",
                    "end": "22:00",
                    "days": "Monday-Friday",
                },
                {
                    "name": "Night Shift",
                    "start": "22:00",
                    "end": "06:00",
                    "days": "Monday-Friday",
                },
                {
                    "name": "Extended Day",
                    "start": "07:00",
                    "end": "19:00",
                    "days": "Monday-Friday",
                },
                {
                    "name": "Weekend Shift",
                    "start": "08:00",
                    "end": "16:00",
                    "days": "Saturday-Sunday",
                },
            ],
        }


# Global instance
scheduler_mock_service = SchedulerMockDataService()
