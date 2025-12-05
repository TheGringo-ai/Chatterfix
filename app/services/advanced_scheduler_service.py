"""
Advanced Scheduler Service - Next-Generation Maintenance Planning & Scheduling
Designed to surpass MaintainX capabilities with AI-driven optimization
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, time
from dataclasses import dataclass, field
from enum import Enum
import logging
import asyncio
import random
from app.core.db_adapter import get_db_adapter

logger = logging.getLogger(__name__)


class ScheduleType(Enum):
    """Types of maintenance schedules"""
    TIME_BASED = "time_based"
    USAGE_BASED = "usage_based"
    CONDITION_BASED = "condition_based"
    CALENDAR_BASED = "calendar_based"
    SEASONAL = "seasonal"
    EMERGENCY = "emergency"


class Priority(Enum):
    """Work order priorities with numeric values for sorting"""
    EMERGENCY = 1
    URGENT = 2
    HIGH = 3
    MEDIUM = 4
    LOW = 5


class TechnicianStatus(Enum):
    """Technician availability status"""
    AVAILABLE = "available"
    BUSY = "busy"
    OFF_DUTY = "off_duty"
    TRAINING = "training"
    SICK_LEAVE = "sick_leave"
    VACATION = "vacation"


@dataclass
class Skill:
    """Technician skill definition"""
    name: str
    level: int  # 1-5 proficiency level
    certified: bool = False
    certification_expiry: Optional[datetime] = None


@dataclass
class WorkShift:
    """Work shift definition"""
    start_time: time
    end_time: time
    timezone: str = "UTC"
    days_of_week: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])  # Mon-Fri


@dataclass
class TechnicianProfile:
    """Enhanced technician profile with scheduling capabilities"""
    id: str
    name: str
    email: str
    phone: str
    status: TechnicianStatus
    skills: List[Skill]
    location: str
    shift: WorkShift
    hourly_rate: float
    max_hours_per_day: int = 8
    overtime_rate_multiplier: float = 1.5
    current_workload_hours: float = 0.0
    upcoming_unavailability: List[Tuple[datetime, datetime]] = field(default_factory=list)


@dataclass
class AssetRequirement:
    """Asset-specific requirements for maintenance"""
    asset_id: str
    required_skills: List[str]
    estimated_duration: float
    criticality: int  # 1-5 scale
    location: str
    last_maintenance: Optional[datetime] = None
    next_due: Optional[datetime] = None
    maintenance_window: Optional[Tuple[time, time]] = None  # Preferred maintenance window


@dataclass
class ScheduleConflict:
    """Scheduling conflict definition"""
    technician_id: str
    date: datetime
    conflict_type: str
    affected_work_orders: List[str]
    severity: int  # 1-5 scale
    resolution_suggestions: List[str]


@dataclass
class OptimizationResult:
    """Result of scheduling optimization"""
    total_cost: float
    completion_percentage: float
    conflicts: List[ScheduleConflict]
    resource_utilization: Dict[str, float]
    recommendations: List[str]


class AdvancedSchedulerService:
    """Advanced maintenance scheduling service"""
    
    def __init__(self):
        self.db = get_db_adapter()
        self.technicians: Dict[str, TechnicianProfile] = {}
        self.asset_requirements: Dict[str, AssetRequirement] = {}
        self.active_schedules: Dict[str, Dict] = {}
        
    async def initialize_scheduler(self):
        """Initialize the scheduler with current data"""
        logger.info("Initializing Advanced Scheduler Service...")
        await self.load_technician_profiles()
        await self.load_asset_requirements()
        await self.load_active_schedules()
        logger.info("Advanced Scheduler initialized successfully")
    
    async def load_technician_profiles(self):
        """Load technician profiles from database"""
        try:
            # This would integrate with your existing user management
            # For now, we'll initialize with comprehensive mock data
            await self._create_comprehensive_technician_data()
        except Exception as e:
            logger.error(f"Error loading technician profiles: {e}")
    
    async def _create_comprehensive_technician_data(self):
        """Create comprehensive technician mock data"""
        skills_catalog = {
            "hydraulics": [1, 2, 3, 4, 5],
            "electrical": [1, 2, 3, 4, 5],
            "mechanical": [1, 2, 3, 4, 5],
            "hvac": [1, 2, 3, 4],
            "plumbing": [1, 2, 3, 4],
            "welding": [1, 2, 3, 4, 5],
            "cnc_operation": [2, 3, 4, 5],
            "safety_inspection": [1, 2, 3, 4, 5],
            "preventive_maintenance": [1, 2, 3, 4, 5],
            "troubleshooting": [2, 3, 4, 5],
            "pneumatics": [1, 2, 3, 4],
            "conveyor_systems": [2, 3, 4],
            "motor_repair": [2, 3, 4, 5],
            "bearing_alignment": [2, 3, 4],
            "vibration_analysis": [3, 4, 5],
        }
        
        locations = ["Building A", "Building B", "Building C", "Warehouse", "Outdoor Yard"]
        shifts = [
            WorkShift(time(7, 0), time(15, 0)),  # Day shift
            WorkShift(time(15, 0), time(23, 0)),  # Evening shift
            WorkShift(time(23, 0), time(7, 0)),   # Night shift
        ]
        
        # Create 25 diverse technicians
        technician_data = [
            ("John Martinez", "john.martinez@chatterfix.com", "+1-555-0101", "hydraulics,mechanical,safety_inspection", "Building A"),
            ("Sarah Chen", "sarah.chen@chatterfix.com", "+1-555-0102", "electrical,cnc_operation,troubleshooting", "Building B"),
            ("Mike Johnson", "mike.johnson@chatterfix.com", "+1-555-0103", "welding,mechanical,pneumatics", "Building C"),
            ("Lisa Rodriguez", "lisa.rodriguez@chatterfix.com", "+1-555-0104", "hvac,electrical,preventive_maintenance", "Building A"),
            ("David Kim", "david.kim@chatterfix.com", "+1-555-0105", "cnc_operation,mechanical,troubleshooting", "Building B"),
            ("Emma Wilson", "emma.wilson@chatterfix.com", "+1-555-0106", "hydraulics,pneumatics,conveyor_systems", "Warehouse"),
            ("Carlos Lopez", "carlos.lopez@chatterfix.com", "+1-555-0107", "electrical,motor_repair,vibration_analysis", "Building C"),
            ("Jennifer Brown", "jennifer.brown@chatterfix.com", "+1-555-0108", "safety_inspection,preventive_maintenance,plumbing", "Building A"),
            ("Robert Davis", "robert.davis@chatterfix.com", "+1-555-0109", "welding,bearing_alignment,mechanical", "Outdoor Yard"),
            ("Angela Thompson", "angela.thompson@chatterfix.com", "+1-555-0110", "hvac,electrical,troubleshooting", "Building B"),
            ("James Garcia", "james.garcia@chatterfix.com", "+1-555-0111", "hydraulics,pneumatics,motor_repair", "Building C"),
            ("Maria Gonzalez", "maria.gonzalez@chatterfix.com", "+1-555-0112", "cnc_operation,mechanical,vibration_analysis", "Building A"),
            ("Kevin Lee", "kevin.lee@chatterfix.com", "+1-555-0113", "electrical,conveyor_systems,safety_inspection", "Warehouse"),
            ("Rachel White", "rachel.white@chatterfix.com", "+1-555-0114", "preventive_maintenance,hydraulics,plumbing", "Building B"),
            ("Daniel Martinez", "daniel.martinez@chatterfix.com", "+1-555-0115", "welding,mechanical,bearing_alignment", "Building C"),
            ("Ashley Johnson", "ashley.johnson@chatterfix.com", "+1-555-0116", "hvac,electrical,motor_repair", "Building A"),
            ("Brandon Smith", "brandon.smith@chatterfix.com", "+1-555-0117", "cnc_operation,troubleshooting,pneumatics", "Outdoor Yard"),
            ("Stephanie Jones", "stephanie.jones@chatterfix.com", "+1-555-0118", "safety_inspection,hydraulics,conveyor_systems", "Warehouse"),
            ("Tyler Williams", "tyler.williams@chatterfix.com", "+1-555-0119", "electrical,vibration_analysis,preventive_maintenance", "Building B"),
            ("Nicole Anderson", "nicole.anderson@chatterfix.com", "+1-555-0120", "mechanical,motor_repair,bearing_alignment", "Building C"),
            ("Christopher Taylor", "christopher.taylor@chatterfix.com", "+1-555-0121", "welding,hydraulics,plumbing", "Building A"),
            ("Amanda Clark", "amanda.clark@chatterfix.com", "+1-555-0122", "hvac,cnc_operation,safety_inspection", "Building B"),
            ("Justin Lewis", "justin.lewis@chatterfix.com", "+1-555-0123", "electrical,pneumatics,troubleshooting", "Building C"),
            ("Samantha Hall", "samantha.hall@chatterfix.com", "+1-555-0124", "preventive_maintenance,conveyor_systems,mechanical", "Warehouse"),
            ("Anthony Young", "anthony.young@chatterfix.com", "+1-555-0125", "vibration_analysis,motor_repair,hydraulics", "Outdoor Yard"),
        ]
        
        for i, (name, email, phone, skill_names, location) in enumerate(technician_data):
            # Create skills for technician
            tech_skills = []
            for skill_name in skill_names.split(','):
                if skill_name in skills_catalog:
                    level = max(skills_catalog[skill_name])  # Give them high proficiency
                    tech_skills.append(Skill(
                        name=skill_name,
                        level=level,
                        certified=level >= 4,
                        certification_expiry=datetime.now() + timedelta(days=365) if level >= 4 else None
                    ))
            
            # Assign shifts (distribute across all shifts)
            shift = shifts[i % 3]
            
            # Create technician profile
            tech_id = f"tech_{i+1:03d}"
            self.technicians[tech_id] = TechnicianProfile(
                id=tech_id,
                name=name,
                email=email,
                phone=phone,
                status=TechnicianStatus.AVAILABLE,
                skills=tech_skills,
                location=location,
                shift=shift,
                hourly_rate=25.0 + (i * 2.5),  # Varied hourly rates
                max_hours_per_day=8,
                overtime_rate_multiplier=1.5,
                current_workload_hours=0.0,
            )
    
    async def load_asset_requirements(self):
        """Load asset maintenance requirements"""
        try:
            # Create comprehensive asset requirements
            await self._create_asset_requirements()
        except Exception as e:
            logger.error(f"Error loading asset requirements: {e}")
    
    async def _create_asset_requirements(self):
        """Create comprehensive asset maintenance requirements"""
        asset_configs = [
            # High-criticality production equipment
            ("hydraulic_press_001", ["hydraulics", "mechanical", "safety_inspection"], 4.0, 5, "Building A"),
            ("hydraulic_press_002", ["hydraulics", "mechanical", "safety_inspection"], 4.0, 5, "Building A"),
            ("cnc_machine_001", ["cnc_operation", "electrical", "mechanical"], 6.0, 5, "Building B"),
            ("cnc_machine_002", ["cnc_operation", "electrical", "mechanical"], 6.0, 5, "Building B"),
            ("cnc_machine_003", ["cnc_operation", "electrical", "mechanical"], 6.0, 5, "Building B"),
            
            # Medium-criticality equipment
            ("conveyor_main_001", ["conveyor_systems", "electrical", "mechanical"], 3.0, 4, "Warehouse"),
            ("conveyor_main_002", ["conveyor_systems", "electrical", "mechanical"], 3.0, 4, "Warehouse"),
            ("air_compressor_001", ["pneumatics", "mechanical", "electrical"], 3.5, 4, "Building C"),
            ("air_compressor_002", ["pneumatics", "mechanical", "electrical"], 3.5, 4, "Building C"),
            ("motor_drive_001", ["motor_repair", "electrical", "vibration_analysis"], 2.5, 4, "Building A"),
            ("motor_drive_002", ["motor_repair", "electrical", "vibration_analysis"], 2.5, 4, "Building A"),
            ("motor_drive_003", ["motor_repair", "electrical", "vibration_analysis"], 2.5, 4, "Building B"),
            
            # HVAC Systems
            ("hvac_unit_001", ["hvac", "electrical", "preventive_maintenance"], 4.0, 3, "Building A"),
            ("hvac_unit_002", ["hvac", "electrical", "preventive_maintenance"], 4.0, 3, "Building B"),
            ("hvac_unit_003", ["hvac", "electrical", "preventive_maintenance"], 4.0, 3, "Building C"),
            
            # Material Handling
            ("forklift_001", ["mechanical", "hydraulics", "safety_inspection"], 2.0, 3, "Warehouse"),
            ("forklift_002", ["mechanical", "hydraulics", "safety_inspection"], 2.0, 3, "Warehouse"),
            ("forklift_003", ["mechanical", "hydraulics", "safety_inspection"], 2.0, 3, "Outdoor Yard"),
            ("crane_overhead_001", ["mechanical", "electrical", "safety_inspection"], 5.0, 5, "Building A"),
            ("crane_overhead_002", ["mechanical", "electrical", "safety_inspection"], 5.0, 5, "Building B"),
            
            # Utility Equipment
            ("generator_backup_001", ["electrical", "mechanical", "preventive_maintenance"], 3.0, 4, "Outdoor Yard"),
            ("water_pump_001", ["plumbing", "mechanical", "electrical"], 2.5, 3, "Building C"),
            ("water_pump_002", ["plumbing", "mechanical", "electrical"], 2.5, 3, "Building C"),
            ("welding_station_001", ["welding", "electrical", "safety_inspection"], 2.0, 2, "Building A"),
            ("welding_station_002", ["welding", "electrical", "safety_inspection"], 2.0, 2, "Building B"),
            
            # Additional production equipment
            ("stamping_press_001", ["hydraulics", "mechanical", "safety_inspection"], 4.5, 5, "Building A"),
            ("assembly_line_001", ["conveyor_systems", "pneumatics", "electrical"], 5.0, 4, "Building B"),
            ("quality_control_001", ["mechanical", "electrical", "troubleshooting"], 3.0, 3, "Building A"),
            ("packaging_line_001", ["pneumatics", "conveyor_systems", "mechanical"], 3.5, 3, "Building C"),
            ("sorting_system_001", ["conveyor_systems", "electrical", "troubleshooting"], 4.0, 4, "Warehouse"),
        ]
        
        for asset_id, required_skills, duration, criticality, location in asset_configs:
            # Set maintenance windows based on criticality and location
            if criticality >= 5:
                # Critical equipment - maintain during off-hours
                maintenance_window = (time(22, 0), time(6, 0))
            elif criticality >= 4:
                # High importance - early morning or late evening
                maintenance_window = (time(6, 0), time(8, 0))
            else:
                # Regular maintenance - flexible timing
                maintenance_window = None
                
            self.asset_requirements[asset_id] = AssetRequirement(
                asset_id=asset_id,
                required_skills=required_skills,
                estimated_duration=duration,
                criticality=criticality,
                location=location,
                last_maintenance=datetime.now() - timedelta(days=30 + (criticality * 10)),
                next_due=datetime.now() + timedelta(days=30 + (5 - criticality) * 10),
                maintenance_window=maintenance_window
            )
    
    async def load_active_schedules(self):
        """Load currently active schedules"""
        # Initialize with empty schedules - will be populated by scheduling algorithms
        self.active_schedules = {}
    
    async def optimize_schedule(self, start_date: datetime, end_date: datetime, 
                              objectives: List[str] = None) -> OptimizationResult:
        """
        Optimize maintenance schedule using advanced algorithms
        
        Args:
            start_date: Schedule start date
            end_date: Schedule end date
            objectives: List of optimization objectives
                       ['minimize_cost', 'maximize_efficiency', 'balance_workload', 'minimize_conflicts']
        """
        if objectives is None:
            objectives = ['minimize_cost', 'maximize_efficiency', 'balance_workload']
        
        logger.info(f"Optimizing schedule from {start_date} to {end_date}")
        
        # Step 1: Generate work orders for the period
        work_orders = await self._generate_scheduled_work_orders(start_date, end_date)
        
        # Step 2: Apply scheduling algorithms
        schedule = await self._apply_scheduling_algorithms(work_orders, objectives)
        
        # Step 3: Detect and resolve conflicts
        conflicts = await self._detect_scheduling_conflicts(schedule)
        resolved_schedule = await self._resolve_conflicts(schedule, conflicts)
        
        # Step 4: Calculate optimization metrics
        optimization_result = await self._calculate_optimization_metrics(resolved_schedule, conflicts)
        
        # Step 5: Store optimized schedule
        self.active_schedules[f"{start_date}_{end_date}"] = resolved_schedule
        
        return optimization_result
    
    async def _generate_scheduled_work_orders(self, start_date: datetime, 
                                            end_date: datetime) -> List[Dict[str, Any]]:
        """Generate work orders for the specified period"""
        work_orders = []
        
        for asset_id, requirements in self.asset_requirements.items():
            # Check if maintenance is due in this period
            if (requirements.next_due and 
                start_date <= requirements.next_due <= end_date):
                
                # Determine work order type based on asset criticality and due date
                if requirements.next_due < datetime.now():
                    priority = Priority.URGENT
                    schedule_type = ScheduleType.EMERGENCY
                elif requirements.criticality >= 5:
                    priority = Priority.HIGH
                    schedule_type = ScheduleType.TIME_BASED
                else:
                    priority = Priority.MEDIUM
                    schedule_type = ScheduleType.TIME_BASED
                
                work_order = {
                    'id': f"wo_{asset_id}_{int(requirements.next_due.timestamp())}",
                    'asset_id': asset_id,
                    'title': f"Scheduled Maintenance - {asset_id.replace('_', ' ').title()}",
                    'description': f"Preventive maintenance for {asset_id}",
                    'priority': priority,
                    'schedule_type': schedule_type,
                    'required_skills': requirements.required_skills,
                    'estimated_duration': requirements.estimated_duration,
                    'due_date': requirements.next_due,
                    'location': requirements.location,
                    'criticality': requirements.criticality,
                    'maintenance_window': requirements.maintenance_window,
                    'status': 'scheduled'
                }
                work_orders.append(work_order)
        
        # Add emergency work orders (simulated)
        emergency_count = max(1, len(work_orders) // 10)  # 10% emergency rate
        for i in range(emergency_count):
            emergency_date = start_date + timedelta(
                days=random.randint(0, (end_date - start_date).days)
            )
            asset_id = list(self.asset_requirements.keys())[i % len(self.asset_requirements)]
            requirements = self.asset_requirements[asset_id]
            
            emergency_wo = {
                'id': f"emergency_{asset_id}_{i}",
                'asset_id': asset_id,
                'title': f"EMERGENCY - {asset_id.replace('_', ' ').title()} Breakdown",
                'description': f"Emergency repair required for {asset_id}",
                'priority': Priority.EMERGENCY,
                'schedule_type': ScheduleType.EMERGENCY,
                'required_skills': requirements.required_skills,
                'estimated_duration': requirements.estimated_duration * 1.5,  # Emergencies take longer
                'due_date': emergency_date,
                'location': requirements.location,
                'criticality': 5,  # All emergencies are critical
                'maintenance_window': None,  # Emergencies can't wait
                'status': 'emergency'
            }
            work_orders.append(emergency_wo)
        
        return work_orders
    
    async def _apply_scheduling_algorithms(self, work_orders: List[Dict[str, Any]], 
                                         objectives: List[str]) -> Dict[str, Any]:
        """Apply advanced scheduling algorithms"""
        schedule = {
            'work_orders': work_orders,
            'assignments': {},
            'timeline': {},
            'resource_utilization': {}
        }
        
        # Sort work orders by priority and due date
        sorted_work_orders = sorted(work_orders, 
                                  key=lambda wo: (wo['priority'].value, wo['due_date']))
        
        for work_order in sorted_work_orders:
            # Find best technician match
            best_match = await self._find_best_technician_match(
                work_order, objectives
            )
            
            if best_match:
                technician_id, scheduled_time = best_match
                schedule['assignments'][work_order['id']] = {
                    'technician_id': technician_id,
                    'scheduled_start': scheduled_time,
                    'scheduled_end': scheduled_time + timedelta(
                        hours=work_order['estimated_duration']
                    ),
                    'work_order': work_order
                }
                
                # Update technician workload
                if technician_id in self.technicians:
                    self.technicians[technician_id].current_workload_hours += work_order['estimated_duration']
        
        return schedule
    
    async def _find_best_technician_match(self, work_order: Dict[str, Any], 
                                        objectives: List[str]) -> Optional[Tuple[str, datetime]]:
        """Find the best technician match for a work order using advanced algorithms"""
        best_matches = []
        
        for tech_id, technician in self.technicians.items():
            # Check skill compatibility
            skill_match = self._calculate_skill_match(technician.skills, work_order['required_skills'])
            if skill_match < 0.5:  # Require at least 50% skill match
                continue
            
            # Check availability
            available_slots = await self._find_available_time_slots(
                technician, work_order['due_date'], work_order['estimated_duration']
            )
            
            if not available_slots:
                continue
            
            # Calculate match score based on objectives
            for slot_start in available_slots:
                score = await self._calculate_assignment_score(
                    technician, work_order, slot_start, objectives
                )
                
                best_matches.append((tech_id, slot_start, score))
        
        if best_matches:
            # Return the best match
            best_matches.sort(key=lambda x: x[2], reverse=True)
            return best_matches[0][0], best_matches[0][1]
        
        return None
    
    def _calculate_skill_match(self, technician_skills: List[Skill], 
                              required_skills: List[str]) -> float:
        """Calculate skill match percentage between technician and work order"""
        if not required_skills:
            return 1.0
        
        skill_dict = {skill.name: skill.level for skill in technician_skills}
        
        matched_skills = 0
        total_skill_level = 0
        
        for required_skill in required_skills:
            if required_skill in skill_dict:
                matched_skills += 1
                total_skill_level += skill_dict[required_skill]
        
        if matched_skills == 0:
            return 0.0
        
        # Calculate match as percentage of skills matched, weighted by skill level
        skill_coverage = matched_skills / len(required_skills)
        avg_skill_level = total_skill_level / matched_skills / 5  # Normalize to 0-1
        
        return (skill_coverage + avg_skill_level) / 2
    
    async def _find_available_time_slots(self, technician: TechnicianProfile, 
                                       preferred_date: datetime, 
                                       duration: float) -> List[datetime]:
        """Find available time slots for a technician"""
        available_slots = []
        
        # Check for 7 days around the preferred date
        for days_offset in range(-3, 4):
            check_date = (preferred_date + timedelta(days=days_offset)).date()
            
            # Check if technician works this day
            if check_date.weekday() not in technician.shift.days_of_week:
                continue
            
            # Check if technician is available
            if technician.status != TechnicianStatus.AVAILABLE:
                continue
            
            # Find available hours in the shift
            shift_start = datetime.combine(check_date, technician.shift.start_time)
            shift_end = datetime.combine(check_date, technician.shift.end_time)
            
            # Handle overnight shifts
            if technician.shift.end_time < technician.shift.start_time:
                shift_end += timedelta(days=1)
            
            # Check for available blocks within the shift
            current_time = shift_start
            while current_time + timedelta(hours=duration) <= shift_end:
                # Check if this slot conflicts with existing assignments
                if not await self._has_scheduling_conflict(technician.id, current_time, duration):
                    available_slots.append(current_time)
                current_time += timedelta(hours=1)  # Check hourly slots
        
        return available_slots
    
    async def _has_scheduling_conflict(self, technician_id: str, 
                                     start_time: datetime, duration: float) -> bool:
        """Check if a time slot conflicts with existing assignments"""
        end_time = start_time + timedelta(hours=duration)
        
        # Check against all active schedules
        for schedule in self.active_schedules.values():
            for assignment in schedule['assignments'].values():
                if assignment['technician_id'] == technician_id:
                    assigned_start = assignment['scheduled_start']
                    assigned_end = assignment['scheduled_end']
                    
                    # Check for overlap
                    if (start_time < assigned_end and end_time > assigned_start):
                        return True
        
        return False
    
    async def _calculate_assignment_score(self, technician: TechnicianProfile,
                                        work_order: Dict[str, Any],
                                        scheduled_time: datetime,
                                        objectives: List[str]) -> float:
        """Calculate assignment score based on optimization objectives"""
        score = 0.0
        
        # Base score from skill match
        skill_match = self._calculate_skill_match(technician.skills, work_order['required_skills'])
        score += skill_match * 100
        
        # Location proximity bonus
        if technician.location == work_order['location']:
            score += 50
        
        # Time preference scoring
        if work_order['maintenance_window']:
            window_start, window_end = work_order['maintenance_window']
            scheduled_time_only = scheduled_time.time()
            
            # Handle overnight windows
            if window_end < window_start:
                if scheduled_time_only >= window_start or scheduled_time_only <= window_end:
                    score += 30
            else:
                if window_start <= scheduled_time_only <= window_end:
                    score += 30
        
        # Objective-based scoring
        if 'minimize_cost' in objectives:
            # Prefer lower-cost technicians
            cost_factor = 50 - (technician.hourly_rate - 25) * 2  # Normalize around $25/hr
            score += max(0, cost_factor)
        
        if 'balance_workload' in objectives:
            # Prefer technicians with lower current workload
            workload_factor = max(0, 40 - technician.current_workload_hours)
            score += workload_factor
        
        if 'maximize_efficiency' in objectives:
            # Prefer assignments that minimize travel time and maximize skill utilization
            score += skill_match * 25  # Additional weight for efficiency
        
        # Priority penalty for delays
        days_from_due = (scheduled_time.date() - work_order['due_date'].date()).days
        if days_from_due > 0:
            penalty = days_from_due * work_order['priority'].value * 10
            score -= penalty
        
        return score
    
    async def _detect_scheduling_conflicts(self, schedule: Dict[str, Any]) -> List[ScheduleConflict]:
        """Detect scheduling conflicts in the proposed schedule"""
        conflicts = []
        
        # Group assignments by technician and date
        tech_schedules = {}
        for wo_id, assignment in schedule['assignments'].items():
            tech_id = assignment['technician_id']
            date = assignment['scheduled_start'].date()
            
            if tech_id not in tech_schedules:
                tech_schedules[tech_id] = {}
            if date not in tech_schedules[tech_id]:
                tech_schedules[tech_id][date] = []
            
            tech_schedules[tech_id][date].append((wo_id, assignment))
        
        # Check for conflicts within each technician's schedule
        for tech_id, dates in tech_schedules.items():
            for date, assignments in dates.items():
                if len(assignments) > 1:
                    # Sort by start time
                    assignments.sort(key=lambda x: x[1]['scheduled_start'])
                    
                    # Check for overlaps
                    for i in range(len(assignments) - 1):
                        current_wo, current_assign = assignments[i]
                        next_wo, next_assign = assignments[i + 1]
                        
                        if current_assign['scheduled_end'] > next_assign['scheduled_start']:
                            conflicts.append(ScheduleConflict(
                                technician_id=tech_id,
                                date=datetime.combine(date, datetime.min.time()),
                                conflict_type="time_overlap",
                                affected_work_orders=[current_wo, next_wo],
                                severity=3,
                                resolution_suggestions=[
                                    "Reschedule one work order to a different time",
                                    "Assign one work order to a different technician",
                                    "Split work order into smaller tasks"
                                ]
                            ))
                
                # Check for workload conflicts
                total_hours = sum(assign['work_order']['estimated_duration'] 
                                for _, assign in assignments)
                
                if tech_id in self.technicians:
                    max_hours = self.technicians[tech_id].max_hours_per_day
                    if total_hours > max_hours:
                        wo_ids = [wo_id for wo_id, _ in assignments]
                        conflicts.append(ScheduleConflict(
                            technician_id=tech_id,
                            date=datetime.combine(date, datetime.min.time()),
                            conflict_type="workload_overload",
                            affected_work_orders=wo_ids,
                            severity=4,
                            resolution_suggestions=[
                                f"Reduce workload from {total_hours:.1f}h to {max_hours}h",
                                "Distribute work orders across multiple days",
                                "Assign some work orders to other technicians"
                            ]
                        ))
        
        return conflicts
    
    async def _resolve_conflicts(self, schedule: Dict[str, Any], 
                               conflicts: List[ScheduleConflict]) -> Dict[str, Any]:
        """Attempt to resolve scheduling conflicts automatically"""
        resolved_schedule = schedule.copy()
        
        # Sort conflicts by severity (highest first)
        conflicts.sort(key=lambda c: c.severity, reverse=True)
        
        for conflict in conflicts:
            if conflict.conflict_type == "time_overlap":
                await self._resolve_time_overlap(resolved_schedule, conflict)
            elif conflict.conflict_type == "workload_overload":
                await self._resolve_workload_overload(resolved_schedule, conflict)
        
        return resolved_schedule
    
    async def _resolve_time_overlap(self, schedule: Dict[str, Any], 
                                  conflict: ScheduleConflict):
        """Resolve time overlap conflicts"""
        affected_wos = conflict.affected_work_orders
        
        # Try to reschedule the lower priority work order
        if len(affected_wos) >= 2:
            wo1_id, wo2_id = affected_wos[0], affected_wos[1]
            
            if wo1_id in schedule['assignments'] and wo2_id in schedule['assignments']:
                assign1 = schedule['assignments'][wo1_id]
                assign2 = schedule['assignments'][wo2_id]
                
                # Determine which has lower priority
                priority1 = assign1['work_order']['priority'].value
                priority2 = assign2['work_order']['priority'].value
                
                if priority1 > priority2:  # Higher number = lower priority
                    # Reschedule wo1 to after wo2
                    new_start = assign2['scheduled_end'] + timedelta(minutes=30)  # 30min buffer
                    duration = assign1['work_order']['estimated_duration']
                    
                    schedule['assignments'][wo1_id]['scheduled_start'] = new_start
                    schedule['assignments'][wo1_id]['scheduled_end'] = new_start + timedelta(hours=duration)
                elif priority2 > priority1:
                    # Reschedule wo2 to after wo1
                    new_start = assign1['scheduled_end'] + timedelta(minutes=30)
                    duration = assign2['work_order']['estimated_duration']
                    
                    schedule['assignments'][wo2_id]['scheduled_start'] = new_start
                    schedule['assignments'][wo2_id]['scheduled_end'] = new_start + timedelta(hours=duration)
    
    async def _resolve_workload_overload(self, schedule: Dict[str, Any], 
                                       conflict: ScheduleConflict):
        """Resolve workload overload conflicts"""
        tech_id = conflict.technician_id
        affected_wos = conflict.affected_work_orders
        
        if tech_id not in self.technicians:
            return
        
        max_hours = self.technicians[tech_id].max_hours_per_day
        
        # Calculate current workload for the day
        total_duration = 0
        wo_durations = []
        
        for wo_id in affected_wos:
            if wo_id in schedule['assignments']:
                duration = schedule['assignments'][wo_id]['work_order']['estimated_duration']
                total_duration += duration
                wo_durations.append((wo_id, duration))
        
        # Sort by duration (largest first) and try to reassign
        wo_durations.sort(key=lambda x: x[1], reverse=True)
        
        remaining_hours = max_hours
        for wo_id, duration in wo_durations:
            if duration > remaining_hours:
                # Try to find another technician for this work order
                work_order = schedule['assignments'][wo_id]['work_order']
                new_match = await self._find_alternative_technician(work_order, tech_id)
                
                if new_match:
                    new_tech_id, new_start_time = new_match
                    schedule['assignments'][wo_id]['technician_id'] = new_tech_id
                    schedule['assignments'][wo_id]['scheduled_start'] = new_start_time
                    schedule['assignments'][wo_id]['scheduled_end'] = new_start_time + timedelta(hours=duration)
                else:
                    # Move to next day
                    current_start = schedule['assignments'][wo_id]['scheduled_start']
                    new_start = current_start + timedelta(days=1)
                    schedule['assignments'][wo_id]['scheduled_start'] = new_start
                    schedule['assignments'][wo_id]['scheduled_end'] = new_start + timedelta(hours=duration)
            else:
                remaining_hours -= duration
    
    async def _find_alternative_technician(self, work_order: Dict[str, Any], 
                                         exclude_tech_id: str) -> Optional[Tuple[str, datetime]]:
        """Find an alternative technician for a work order"""
        for tech_id, technician in self.technicians.items():
            if tech_id == exclude_tech_id:
                continue
            
            # Check skill compatibility
            skill_match = self._calculate_skill_match(technician.skills, work_order['required_skills'])
            if skill_match < 0.3:  # Lower threshold for alternatives
                continue
            
            # Find available slots
            available_slots = await self._find_available_time_slots(
                technician, work_order['due_date'], work_order['estimated_duration']
            )
            
            if available_slots:
                return tech_id, available_slots[0]
        
        return None
    
    async def _calculate_optimization_metrics(self, schedule: Dict[str, Any], 
                                            conflicts: List[ScheduleConflict]) -> OptimizationResult:
        """Calculate comprehensive optimization metrics"""
        total_cost = 0.0
        total_work_orders = len(schedule['work_orders'])
        scheduled_work_orders = len(schedule['assignments'])
        
        # Calculate costs and resource utilization
        resource_utilization = {}
        
        for wo_id, assignment in schedule['assignments'].items():
            tech_id = assignment['technician_id']
            duration = assignment['work_order']['estimated_duration']
            
            if tech_id in self.technicians:
                hourly_rate = self.technicians[tech_id].hourly_rate
                total_cost += duration * hourly_rate
                
                # Track utilization
                if tech_id not in resource_utilization:
                    resource_utilization[tech_id] = 0.0
                resource_utilization[tech_id] += duration
        
        # Calculate completion percentage
        completion_percentage = (scheduled_work_orders / total_work_orders * 100) if total_work_orders > 0 else 0
        
        # Generate recommendations
        recommendations = []
        
        if completion_percentage < 90:
            recommendations.append(f"Only {completion_percentage:.1f}% of work orders scheduled. Consider adding more technicians or extending timeline.")
        
        if len(conflicts) > 0:
            recommendations.append(f"Found {len(conflicts)} scheduling conflicts that need attention.")
        
        # Check for underutilized technicians
        avg_utilization = sum(resource_utilization.values()) / len(resource_utilization) if resource_utilization else 0
        underutilized = [tech_id for tech_id, util in resource_utilization.items() if util < avg_utilization * 0.5]
        
        if underutilized:
            recommendations.append(f"Consider redistributing work from overloaded technicians to: {', '.join(underutilized)}")
        
        return OptimizationResult(
            total_cost=total_cost,
            completion_percentage=completion_percentage,
            conflicts=conflicts,
            resource_utilization=resource_utilization,
            recommendations=recommendations
        )
    
    # Additional methods for calendar and Gantt chart support
    async def get_calendar_view(self, start_date: datetime, end_date: datetime, 
                              tech_id: Optional[str] = None) -> Dict[str, Any]:
        """Get calendar view data for the scheduler interface"""
        calendar_data = {
            'events': [],
            'technicians': [],
            'conflicts': [],
            'utilization': {}
        }
        
        # Find relevant schedule
        schedule_key = f"{start_date}_{end_date}"
        if schedule_key not in self.active_schedules:
            # Generate schedule if it doesn't exist
            await self.optimize_schedule(start_date, end_date)
        
        schedule = self.active_schedules.get(schedule_key, {})
        
        # Prepare events for calendar
        for wo_id, assignment in schedule.get('assignments', {}).items():
            if tech_id and assignment['technician_id'] != tech_id:
                continue
            
            event = {
                'id': wo_id,
                'title': assignment['work_order']['title'],
                'start': assignment['scheduled_start'].isoformat(),
                'end': assignment['scheduled_end'].isoformat(),
                'technician_id': assignment['technician_id'],
                'technician_name': self.technicians.get(assignment['technician_id'], {}).name if assignment['technician_id'] in self.technicians else 'Unknown',
                'priority': assignment['work_order']['priority'].name,
                'asset_id': assignment['work_order']['asset_id'],
                'location': assignment['work_order']['location'],
                'estimated_duration': assignment['work_order']['estimated_duration'],
                'status': assignment['work_order']['status'],
                'color': self._get_priority_color(assignment['work_order']['priority'])
            }
            calendar_data['events'].append(event)
        
        # Add technician information
        for tech_id, technician in self.technicians.items():
            if tech_id and tech_id != tech_id:
                continue
                
            calendar_data['technicians'].append({
                'id': tech_id,
                'name': technician.name,
                'status': technician.status.value,
                'location': technician.location,
                'skills': [skill.name for skill in technician.skills],
                'shift_start': technician.shift.start_time.strftime('%H:%M'),
                'shift_end': technician.shift.end_time.strftime('%H:%M')
            })
        
        return calendar_data
    
    def _get_priority_color(self, priority: Priority) -> str:
        """Get color code for work order priority"""
        color_map = {
            Priority.EMERGENCY: '#FF0000',  # Red
            Priority.URGENT: '#FF6600',     # Orange
            Priority.HIGH: '#FFAA00',       # Yellow-Orange
            Priority.MEDIUM: '#00AA00',     # Green
            Priority.LOW: '#0066AA'         # Blue
        }
        return color_map.get(priority, '#666666')
    
    async def get_technician_schedule(self, tech_id: str, start_date: datetime, 
                                    end_date: datetime) -> Dict[str, Any]:
        """Get detailed schedule for a specific technician"""
        if tech_id not in self.technicians:
            return {'error': 'Technician not found'}
        
        technician = self.technicians[tech_id]
        schedule_data = {
            'technician': {
                'id': tech_id,
                'name': technician.name,
                'email': technician.email,
                'phone': technician.phone,
                'location': technician.location,
                'status': technician.status.value,
                'skills': [{'name': s.name, 'level': s.level, 'certified': s.certified} for s in technician.skills]
            },
            'schedule': [],
            'statistics': {}
        }
        
        # Collect assignments for this technician
        total_hours = 0
        work_orders = []
        
        for schedule in self.active_schedules.values():
            for wo_id, assignment in schedule.get('assignments', {}).items():
                if assignment['technician_id'] == tech_id:
                    start_time = assignment['scheduled_start']
                    if start_date <= start_time <= end_date:
                        work_orders.append({
                            'id': wo_id,
                            'title': assignment['work_order']['title'],
                            'asset_id': assignment['work_order']['asset_id'],
                            'start_time': start_time.isoformat(),
                            'end_time': assignment['scheduled_end'].isoformat(),
                            'duration': assignment['work_order']['estimated_duration'],
                            'priority': assignment['work_order']['priority'].name,
                            'location': assignment['work_order']['location'],
                            'status': assignment['work_order']['status']
                        })
                        total_hours += assignment['work_order']['estimated_duration']
        
        schedule_data['schedule'] = sorted(work_orders, key=lambda x: x['start_time'])
        schedule_data['statistics'] = {
            'total_hours': total_hours,
            'work_order_count': len(work_orders),
            'utilization_percentage': min(100, (total_hours / (technician.max_hours_per_day * 7)) * 100)
        }
        
        return schedule_data


# Global instance
advanced_scheduler = AdvancedSchedulerService()