"""
PM Automation Engine - Advanced Preventive Maintenance Scheduling
Supports time-based, usage-based, condition-based, and predictive maintenance scheduling

Production-ready implementation using Firestore for persistence.
"""

import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.firestore_db import get_firestore_manager
from app.services.advanced_scheduler_service import (
    Priority,
    ScheduleType,
)

logger = logging.getLogger(__name__)


class MaintenanceType(Enum):
    """Types of preventive maintenance"""

    PREVENTIVE = "preventive"
    PREDICTIVE = "predictive"
    CONDITION_BASED = "condition_based"
    USAGE_BASED = "usage_based"
    TIME_BASED = "time_based"
    SEASONAL = "seasonal"
    REGULATORY = "regulatory"


class TriggerType(Enum):
    """Maintenance trigger types"""

    CALENDAR = "calendar"
    RUNTIME_HOURS = "runtime_hours"
    PRODUCTION_CYCLES = "production_cycles"
    VIBRATION_THRESHOLD = "vibration_threshold"
    TEMPERATURE_THRESHOLD = "temperature_threshold"
    PRESSURE_THRESHOLD = "pressure_threshold"
    OIL_ANALYSIS = "oil_analysis"
    WEAR_MEASUREMENT = "wear_measurement"
    SEASONAL_CHANGE = "seasonal_change"
    REGULATORY_DEADLINE = "regulatory_deadline"


# Seasonal adjustment factors (static configuration)
SEASONAL_FACTORS = {
    "hvac": {"spring": 1.2, "summer": 1.5, "fall": 1.1, "winter": 0.8},
    "outdoor_equipment": {
        "spring": 1.3,
        "summer": 1.4,
        "fall": 1.2,
        "winter": 0.9,
    },
    "production_equipment": {
        "spring": 1.1,
        "summer": 1.0,
        "fall": 1.2,
        "winter": 0.9,
    },
}


class PMAutomationEngine:
    """
    Production PM automation engine using Firestore for persistence.

    All methods require organization_id for multi-tenant data isolation.
    """

    def __init__(self):
        self.firestore_manager = get_firestore_manager()

    # ==========================================
    # PUBLIC API METHODS
    # ==========================================

    async def generate_pm_schedule(
        self,
        organization_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        create_work_orders: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate PM work orders for the specified period.

        Args:
            organization_id: Organization to generate schedule for
            start_date: Start of period (defaults to now)
            end_date: End of period (defaults to 30 days from now)
            create_work_orders: If True, creates actual work orders in Firestore

        Returns:
            Dict with generated orders and summary statistics
        """
        if not start_date:
            start_date = datetime.now(timezone.utc)
        if not end_date:
            end_date = start_date + timedelta(days=30)

        generated_orders = []
        work_orders_created = []

        # Get active schedule rules for this organization
        rules = await self.firestore_manager.get_pm_schedule_rules(
            organization_id, is_active=True
        )

        # Get templates (including global templates)
        templates = await self.firestore_manager.get_pm_templates(
            organization_id, include_global=True
        )
        templates_dict = {t["id"]: t for t in templates}

        # Process time-based rules
        for rule in rules:
            schedule_type = rule.get("schedule_type", "time_based")

            if schedule_type in ["condition_based", "usage_based"]:
                continue  # Handled separately

            orders = await self._generate_orders_for_rule(
                rule, templates_dict, start_date, end_date, organization_id
            )
            generated_orders.extend(orders)

        # Check condition-based triggers
        condition_orders = await self._check_condition_based_triggers(
            organization_id, templates_dict
        )
        generated_orders.extend(condition_orders)

        # Check usage-based triggers
        usage_orders = await self._check_usage_based_triggers(
            organization_id, rules, templates_dict
        )
        generated_orders.extend(usage_orders)

        # Apply seasonal adjustments
        self._apply_seasonal_adjustments(generated_orders)

        # Create actual work orders if requested
        if create_work_orders:
            for order in generated_orders:
                wo_id = await self._create_work_order_from_pm(order, organization_id)
                if wo_id:
                    work_orders_created.append(wo_id)
                    order["work_order_id"] = wo_id

        logger.info(
            f"Generated {len(generated_orders)} PM orders for org {organization_id}, "
            f"created {len(work_orders_created)} work orders"
        )

        return {
            "generated_count": len(generated_orders),
            "work_orders_created": len(work_orders_created),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "orders": generated_orders[:50],  # Limit response size
            "work_order_ids": work_orders_created,
        }

    async def get_pm_schedule_overview(
        self, organization_id: str, days_ahead: int = 30
    ) -> Dict[str, Any]:
        """Get comprehensive PM schedule overview from Firestore."""
        try:
            # Use the Firestore manager's PM overview method
            overview = await self.firestore_manager.get_pm_overview(
                organization_id, days_ahead
            )

            # Get templates for additional context
            templates = await self.firestore_manager.get_pm_templates(
                organization_id, include_global=True
            )

            # Categorize templates
            by_type = {}
            for template in templates:
                maint_type = template.get("maintenance_type", "preventive")
                by_type[maint_type] = by_type.get(maint_type, 0) + 1

            return {
                "overview": {
                    "total_active_rules": overview["summary"]["total_active_rules"],
                    "rules_due_soon": overview["summary"]["rules_due_soon"],
                    "overdue_count": overview["summary"]["overdue_count"],
                    "meters_warning": overview["summary"]["meters_warning"],
                    "meters_critical": overview["summary"]["meters_critical"],
                    "total_templates": len(templates),
                    "period_days": days_ahead,
                },
                "by_maintenance_type": by_type,
                "due_rules": overview["due_rules"],
                "critical_meters": overview["critical_meters"],
                "warning_meters": overview["warning_meters"],
                "recent_pm_orders": overview["recent_pm_orders"],
                "templates_summary": [
                    {
                        "id": t.get("id"),
                        "name": t.get("name"),
                        "type": t.get("maintenance_type"),
                        "criticality": t.get("criticality", 3),
                        "estimated_duration": t.get("estimated_duration", 1.0),
                    }
                    for t in templates
                ],
            }
        except Exception as e:
            logger.error(f"Error getting PM overview: {e}")
            return {
                "overview": {
                    "total_active_rules": 0,
                    "rules_due_soon": 0,
                    "overdue_count": 0,
                    "meters_warning": 0,
                    "meters_critical": 0,
                    "total_templates": 0,
                    "period_days": days_ahead,
                },
                "by_maintenance_type": {},
                "due_rules": [],
                "critical_meters": [],
                "warning_meters": [],
                "recent_pm_orders": [],
                "templates_summary": [],
            }

    async def update_meter_reading(
        self,
        organization_id: str,
        meter_id: str,
        new_value: float,
        reading_source: str = "manual",
        create_work_orders: bool = True,
    ) -> Dict[str, Any]:
        """
        Update a meter reading and check for triggered maintenance.

        Args:
            organization_id: Organization ID
            meter_id: Meter document ID
            new_value: New meter reading value
            reading_source: Source of reading ('manual', 'iot', 'api')
            create_work_orders: If True, creates work orders for triggered maintenance

        Returns:
            Dict with meter update result and any triggered maintenance
        """
        try:
            # Update meter in Firestore
            result = await self.firestore_manager.update_meter_reading(
                meter_id, new_value, organization_id, reading_source
            )

            triggered_orders = []

            # Check if threshold exceeded
            if result["threshold_status"] in ["warning", "critical"]:
                # Get templates to check for condition-based triggers
                templates = await self.firestore_manager.get_pm_templates(
                    organization_id, maintenance_type="condition_based"
                )

                for template in templates:
                    if self._meter_triggers_template(result, template):
                        order_data = self._build_condition_order(
                            result, template, organization_id
                        )
                        triggered_orders.append(order_data)

                        if create_work_orders:
                            wo_id = await self._create_work_order_from_pm(
                                order_data, organization_id
                            )
                            order_data["work_order_id"] = wo_id

            result["triggered_maintenance"] = len(triggered_orders)
            result["triggered_orders"] = triggered_orders

            return result

        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error updating meter reading: {e}")
            return {"error": f"Failed to update meter: {str(e)}"}

    async def get_maintenance_templates(
        self, organization_id: str, maintenance_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all maintenance templates for an organization."""
        return await self.firestore_manager.get_pm_templates(
            organization_id, maintenance_type=maintenance_type, include_global=True
        )

    async def get_asset_meters(
        self,
        organization_id: str,
        asset_id: Optional[str] = None,
        meter_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get asset meters for an organization."""
        return await self.firestore_manager.get_asset_meters(
            organization_id, asset_id=asset_id, meter_type=meter_type
        )

    async def get_schedule_rules(
        self,
        organization_id: str,
        asset_id: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """Get PM schedule rules for an organization."""
        return await self.firestore_manager.get_pm_schedule_rules(
            organization_id, asset_id=asset_id, is_active=is_active
        )

    # ==========================================
    # INTERNAL METHODS
    # ==========================================

    async def _generate_orders_for_rule(
        self,
        rule: Dict[str, Any],
        templates_dict: Dict[str, Dict[str, Any]],
        start_date: datetime,
        end_date: datetime,
        organization_id: str,
    ) -> List[Dict[str, Any]]:
        """Generate work orders for a specific schedule rule."""
        orders = []

        template_id = rule.get("template_id")
        template = templates_dict.get(template_id)

        if not template:
            logger.warning(f"Template {template_id} not found for rule {rule.get('id')}")
            return orders

        # Parse next_due date
        next_due = rule.get("next_due")
        if isinstance(next_due, str):
            next_due = datetime.fromisoformat(next_due.replace("Z", "+00:00"))

        if not next_due:
            next_due = start_date

        interval_value = rule.get("interval_value", 30)
        interval_unit = rule.get("interval_unit", "days")
        asset_id = rule.get("asset_id", "unknown")

        current_date = next_due

        while current_date <= end_date:
            if current_date >= start_date:
                order = {
                    "pm_order_id": f"PM_{asset_id}_{int(current_date.timestamp())}",
                    "asset_id": asset_id,
                    "template_id": template_id,
                    "title": f"{template.get('name', 'PM Task')} - {asset_id.replace('_', ' ').title()}",
                    "description": template.get("description", ""),
                    "priority": self._calculate_priority(template, current_date),
                    "due_date": current_date.isoformat(),
                    "estimated_duration": template.get("estimated_duration", 1.0),
                    "required_skills": template.get("required_skills", []),
                    "required_parts": template.get("required_parts", []),
                    "required_tools": template.get("required_tools", []),
                    "safety_requirements": template.get("safety_requirements", []),
                    "procedures": template.get("procedures", []),
                    "generated_date": datetime.now(timezone.utc).isoformat(),
                    "rule_id": rule.get("id"),
                    "trigger_reason": f"Scheduled {rule.get('schedule_type', 'time_based')} maintenance",
                    "can_be_deferred": template.get("can_be_deferred", True),
                    "maintenance_type": template.get("maintenance_type", "preventive"),
                }
                orders.append(order)

            # Calculate next due date
            if interval_unit == "days":
                current_date = current_date + timedelta(days=interval_value)
            elif interval_unit == "weeks":
                current_date = current_date + timedelta(weeks=interval_value)
            elif interval_unit == "months":
                current_date = current_date + timedelta(days=interval_value * 30)
            else:
                break

        # Update rule's next_due in Firestore
        if orders:
            await self.firestore_manager.update_pm_schedule_rule(
                rule.get("id"),
                {
                    "next_due": current_date,
                    "last_generated": datetime.now(timezone.utc),
                },
                organization_id,
            )

        return orders

    async def _check_condition_based_triggers(
        self,
        organization_id: str,
        templates_dict: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Check for condition-based maintenance triggers from meter readings."""
        orders = []

        # Get meters exceeding thresholds
        critical_meters = await self.firestore_manager.get_meters_exceeding_threshold(
            organization_id, "critical"
        )
        warning_meters = await self.firestore_manager.get_meters_exceeding_threshold(
            organization_id, "warning"
        )

        # Get condition-based templates
        condition_templates = [
            t for t in templates_dict.values()
            if t.get("maintenance_type") == "condition_based"
        ]

        # Check critical meters first
        for meter in critical_meters:
            for template in condition_templates:
                if self._meter_triggers_template(meter, template):
                    order = self._build_condition_order(meter, template, organization_id)
                    order["priority"] = "URGENT"
                    orders.append(order)

        # Then warning meters
        for meter in warning_meters:
            for template in condition_templates:
                if self._meter_triggers_template(meter, template):
                    order = self._build_condition_order(meter, template, organization_id)
                    orders.append(order)

        return orders

    async def _check_usage_based_triggers(
        self,
        organization_id: str,
        rules: List[Dict[str, Any]],
        templates_dict: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Check for usage-based maintenance triggers."""
        orders = []

        usage_rules = [r for r in rules if r.get("schedule_type") == "usage_based"]

        for rule in usage_rules:
            asset_id = rule.get("asset_id")
            interval_value = rule.get("interval_value", 100000)
            interval_unit = rule.get("interval_unit", "cycles")

            # Get meters for this asset
            meters = await self.firestore_manager.get_asset_meters(
                organization_id, asset_id=asset_id
            )

            for meter in meters:
                if interval_unit in meter.get("meter_type", ""):
                    current_value = meter.get("current_value", 0)
                    if current_value >= interval_value:
                        template = templates_dict.get(rule.get("template_id"))
                        if template:
                            order = {
                                "pm_order_id": f"UBM_{asset_id}_{int(datetime.now().timestamp())}",
                                "asset_id": asset_id,
                                "template_id": rule.get("template_id"),
                                "title": f"USAGE MILESTONE: {template.get('name')} - {asset_id.replace('_', ' ').title()}",
                                "description": f"Triggered by {meter.get('meter_type')}: {current_value} {meter.get('unit')}",
                                "priority": self._calculate_priority(template, datetime.now(timezone.utc)),
                                "due_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                                "estimated_duration": template.get("estimated_duration", 1.0),
                                "required_skills": template.get("required_skills", []),
                                "required_parts": template.get("required_parts", []),
                                "required_tools": template.get("required_tools", []),
                                "generated_date": datetime.now(timezone.utc).isoformat(),
                                "rule_id": rule.get("id"),
                                "trigger_reason": f"Usage threshold reached: {current_value} {meter.get('unit')}",
                                "can_be_deferred": template.get("can_be_deferred", True),
                                "maintenance_type": "usage_based",
                            }
                            orders.append(order)

        return orders

    def _meter_triggers_template(
        self, meter: Dict[str, Any], template: Dict[str, Any]
    ) -> bool:
        """Check if a meter reading should trigger a template."""
        meter_type = meter.get("meter_type", "")
        triggers = template.get("triggers", [])

        trigger_meter_map = {
            "vibration_threshold": "vibration",
            "temperature_threshold": "temperature",
            "pressure_threshold": "pressure",
            "runtime_hours": "runtime_hours",
            "production_cycles": ["production_cycles", "operation_cycles"],
        }

        for trigger in triggers:
            trigger_type = trigger.get("trigger_type", "")
            expected_types = trigger_meter_map.get(trigger_type, [])

            if isinstance(expected_types, str):
                expected_types = [expected_types]

            if meter_type in expected_types:
                return True

        return False

    def _build_condition_order(
        self,
        meter: Dict[str, Any],
        template: Dict[str, Any],
        organization_id: str,
    ) -> Dict[str, Any]:
        """Build a condition-based work order from meter and template."""
        asset_id = meter.get("asset_id", "unknown")

        return {
            "pm_order_id": f"CBM_{asset_id}_{int(datetime.now().timestamp())}",
            "asset_id": asset_id,
            "template_id": template.get("id"),
            "title": f"CONDITION ALERT: {template.get('name')} - {asset_id.replace('_', ' ').title()}",
            "description": f"Triggered by {meter.get('meter_type')}: {meter.get('current_value')} {meter.get('unit')}",
            "priority": "HIGH",
            "due_date": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            "estimated_duration": template.get("estimated_duration", 1.0),
            "required_skills": template.get("required_skills", []),
            "required_parts": template.get("required_parts", []),
            "required_tools": template.get("required_tools", []),
            "generated_date": datetime.now(timezone.utc).isoformat(),
            "rule_id": f"condition_{asset_id}",
            "trigger_reason": f"Condition threshold exceeded: {meter.get('meter_type')} = {meter.get('current_value')} {meter.get('unit')}",
            "can_be_deferred": False,
            "maintenance_type": "condition_based",
            "threshold_status": meter.get("threshold_exceeded", "warning"),
        }

    def _calculate_priority(
        self, template: Dict[str, Any], due_date: datetime
    ) -> str:
        """Calculate work order priority based on template and timing."""
        maintenance_type = template.get("maintenance_type", "preventive")
        criticality = template.get("criticality", 3)

        if maintenance_type == "regulatory":
            base_priority = "URGENT"
        elif maintenance_type == "condition_based":
            base_priority = "HIGH"
        elif criticality >= 5:
            base_priority = "HIGH"
        elif criticality >= 4:
            base_priority = "MEDIUM"
        else:
            base_priority = "LOW"

        # Escalate if overdue
        now = datetime.now(timezone.utc)
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))

        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=timezone.utc)

        if due_date < now:
            days_overdue = (now - due_date).days
            if days_overdue > 7:
                return "URGENT"
            elif days_overdue > 3:
                return "HIGH"
            elif days_overdue > 0 and base_priority == "LOW":
                return "MEDIUM"

        return base_priority

    def _apply_seasonal_adjustments(self, orders: List[Dict[str, Any]]):
        """Apply seasonal adjustments to maintenance due dates."""
        current_season = self._get_current_season(datetime.now())

        for order in orders:
            equipment_type = self._get_equipment_type(order.get("asset_id", ""))

            if equipment_type in SEASONAL_FACTORS:
                factor = SEASONAL_FACTORS[equipment_type].get(current_season, 1.0)

                due_date_str = order.get("due_date")
                if due_date_str:
                    due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))

                    if factor > 1.0:
                        days_earlier = int((factor - 1.0) * 7)
                        due_date = due_date - timedelta(days=days_earlier)
                    elif factor < 1.0:
                        days_later = int((1.0 - factor) * 14)
                        due_date = due_date + timedelta(days=days_later)

                    order["due_date"] = due_date.isoformat()
                    order["seasonal_adjustment"] = factor

    def _get_current_season(self, date: datetime) -> str:
        """Determine the current season based on date."""
        month = date.month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "fall"

    def _get_equipment_type(self, asset_id: str) -> str:
        """Determine equipment type from asset ID."""
        asset_id_lower = asset_id.lower()
        if "hvac" in asset_id_lower:
            return "hvac"
        elif any(x in asset_id_lower for x in ["forklift", "crane", "generator"]):
            return "outdoor_equipment"
        else:
            return "production_equipment"

    async def _create_work_order_from_pm(
        self, pm_order: Dict[str, Any], organization_id: str
    ) -> Optional[str]:
        """Create an actual work order in Firestore from PM order data."""
        try:
            work_order_data = {
                "title": pm_order.get("title"),
                "description": pm_order.get("description", ""),
                "priority": pm_order.get("priority", "Medium"),
                "status": "Open",
                "work_order_type": "Preventive",
                "asset_id": pm_order.get("asset_id"),
                "due_date": pm_order.get("due_date"),
                "estimated_hours": pm_order.get("estimated_duration", 1.0),
                "required_skills": pm_order.get("required_skills", []),
                "required_parts": pm_order.get("required_parts", []),
                "required_tools": pm_order.get("required_tools", []),
                "safety_requirements": pm_order.get("safety_requirements", []),
                "procedures": pm_order.get("procedures", []),
                # PM-specific metadata
                "pm_template_id": pm_order.get("template_id"),
                "pm_rule_id": pm_order.get("rule_id"),
                "pm_trigger_reason": pm_order.get("trigger_reason"),
                "pm_generated_date": pm_order.get("generated_date"),
                "maintenance_type": pm_order.get("maintenance_type", "preventive"),
            }

            # Create work order
            wo_id = await self.firestore_manager.create_org_work_order(
                work_order_data, organization_id
            )

            # Track in pm_generated_orders
            await self.firestore_manager.create_pm_generated_order(
                {
                    "work_order_id": wo_id,
                    "template_id": pm_order.get("template_id"),
                    "rule_id": pm_order.get("rule_id"),
                    "asset_id": pm_order.get("asset_id"),
                    "trigger_reason": pm_order.get("trigger_reason"),
                    "generated_date": datetime.now(timezone.utc),
                    "due_date": pm_order.get("due_date"),
                    "status": "work_order_created",
                },
                organization_id,
            )

            logger.info(f"Created PM work order {wo_id} for org {organization_id}")
            return wo_id

        except Exception as e:
            logger.error(f"Error creating work order from PM: {e}")
            return None

    # ==========================================
    # SEED DATA METHODS (For Initial Setup/Demo)
    # ==========================================

    async def seed_default_templates(
        self, organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Seed default PM templates into Firestore.
        If organization_id is None, creates global templates.

        Returns summary of created templates.
        """
        templates = self._get_default_templates()
        created = []

        for template_data in templates:
            try:
                template_id = await self.firestore_manager.create_pm_template(
                    template_data, organization_id
                )
                created.append(template_id)
            except Exception as e:
                logger.error(f"Error creating template {template_data.get('name')}: {e}")

        return {
            "templates_created": len(created),
            "template_ids": created,
            "organization_id": organization_id,
        }

    async def seed_demo_data(
        self, organization_id: str, asset_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Seed demo PM data for an organization.
        Creates schedule rules and meters for provided or default assets.
        """
        if not asset_ids:
            asset_ids = [
                "hydraulic_press_001",
                "cnc_machine_001",
                "conveyor_001",
                "hvac_unit_001",
            ]

        # First ensure templates exist
        templates = await self.firestore_manager.get_pm_templates(organization_id)
        if not templates:
            await self.seed_default_templates(organization_id)
            templates = await self.firestore_manager.get_pm_templates(organization_id)

        rules_created = []
        meters_created = []

        for asset_id in asset_ids:
            # Create schedule rule
            rule_data = self._get_rule_for_asset(asset_id, templates)
            if rule_data:
                rule_id = await self.firestore_manager.create_pm_schedule_rule(
                    rule_data, organization_id
                )
                rules_created.append(rule_id)

            # Create meters
            meter_data_list = self._get_meters_for_asset(asset_id)
            for meter_data in meter_data_list:
                meter_id = await self.firestore_manager.create_asset_meter(
                    meter_data, organization_id
                )
                meters_created.append(meter_id)

        return {
            "rules_created": len(rules_created),
            "meters_created": len(meters_created),
            "assets_configured": asset_ids,
        }

    def _get_default_templates(self) -> List[Dict[str, Any]]:
        """Get default PM template definitions."""
        return [
            {
                "name": "Hydraulic System Daily Check",
                "description": "Daily inspection of hydraulic systems",
                "maintenance_type": "preventive",
                "triggers": [
                    {
                        "trigger_type": "calendar",
                        "threshold_value": 1,
                        "warning_threshold": 0.8,
                        "description": "Daily inspection schedule",
                        "unit": "days",
                    }
                ],
                "required_skills": ["hydraulics", "safety_inspection"],
                "estimated_duration": 0.5,
                "required_tools": ["pressure_gauge", "visual_inspection_checklist"],
                "safety_requirements": ["safety_glasses", "gloves"],
                "procedures": [
                    "Check hydraulic fluid levels",
                    "Inspect for leaks",
                    "Check pressure readings",
                    "Test emergency stops",
                ],
                "criticality": 4,
                "can_be_deferred": True,
            },
            {
                "name": "Hydraulic System Monthly Maintenance",
                "description": "Comprehensive monthly hydraulic maintenance",
                "maintenance_type": "preventive",
                "triggers": [
                    {
                        "trigger_type": "calendar",
                        "threshold_value": 30,
                        "warning_threshold": 25,
                        "description": "Monthly maintenance schedule",
                        "unit": "days",
                    }
                ],
                "required_skills": ["hydraulics", "mechanical", "safety_inspection"],
                "estimated_duration": 4.0,
                "required_parts": ["hydraulic_filter", "o_rings"],
                "required_tools": ["pressure_gauge", "torque_wrench", "filter_wrench"],
                "safety_requirements": ["safety_glasses", "gloves", "lockout_tagout"],
                "procedures": [
                    "Change hydraulic filters",
                    "Test relief valves",
                    "Check cylinder seals",
                    "Calibrate pressure sensors",
                    "Update maintenance records",
                ],
                "criticality": 5,
                "can_be_deferred": True,
            },
            {
                "name": "Electrical System Weekly Inspection",
                "description": "Weekly electrical safety and performance check",
                "maintenance_type": "preventive",
                "triggers": [
                    {
                        "trigger_type": "calendar",
                        "threshold_value": 7,
                        "warning_threshold": 6,
                        "description": "Weekly inspection schedule",
                        "unit": "days",
                    }
                ],
                "required_skills": ["electrical", "safety_inspection"],
                "estimated_duration": 1.5,
                "required_tools": ["multimeter", "thermal_camera", "inspection_checklist"],
                "safety_requirements": ["arc_flash_protection", "insulated_tools"],
                "procedures": [
                    "Thermal imaging scan",
                    "Check electrical connections",
                    "Test emergency stops",
                    "Verify ground connections",
                ],
                "criticality": 5,
                "can_be_deferred": False,
            },
            {
                "name": "Motor Condition-Based Maintenance",
                "description": "Condition-based motor maintenance using vibration analysis",
                "maintenance_type": "condition_based",
                "triggers": [
                    {
                        "trigger_type": "vibration_threshold",
                        "threshold_value": 7.1,
                        "warning_threshold": 4.5,
                        "description": "Vibration threshold exceeded",
                        "unit": "mm/s",
                    },
                    {
                        "trigger_type": "temperature_threshold",
                        "threshold_value": 85,
                        "warning_threshold": 75,
                        "description": "Motor temperature threshold",
                        "unit": "°C",
                    },
                ],
                "required_skills": ["motor_repair", "vibration_analysis", "electrical"],
                "estimated_duration": 6.0,
                "required_parts": ["motor_bearings", "lubricant"],
                "required_tools": ["vibration_analyzer", "bearing_puller", "alignment_tools"],
                "safety_requirements": ["lockout_tagout", "safety_glasses"],
                "procedures": [
                    "Perform vibration analysis",
                    "Check bearing condition",
                    "Verify motor alignment",
                    "Replace bearings if needed",
                    "Update condition monitoring records",
                ],
                "criticality": 4,
                "can_be_deferred": False,
            },
            {
                "name": "Conveyor Usage-Based Maintenance",
                "description": "Maintenance based on production cycles and runtime",
                "maintenance_type": "usage_based",
                "triggers": [
                    {
                        "trigger_type": "production_cycles",
                        "threshold_value": 100000,
                        "warning_threshold": 85000,
                        "description": "Production cycle threshold",
                        "unit": "cycles",
                    }
                ],
                "required_skills": ["conveyor_systems", "mechanical"],
                "estimated_duration": 3.5,
                "required_parts": ["conveyor_belt", "drive_chain", "lubricant"],
                "required_tools": ["belt_tension_gauge", "chain_checker"],
                "safety_requirements": ["lockout_tagout", "safety_harness"],
                "procedures": [
                    "Check belt tension and alignment",
                    "Inspect drive chain wear",
                    "Lubricate drive components",
                    "Check safety guards",
                ],
                "criticality": 3,
                "can_be_deferred": True,
            },
            {
                "name": "HVAC Seasonal Maintenance",
                "description": "Seasonal HVAC system maintenance and tune-up",
                "maintenance_type": "seasonal",
                "triggers": [
                    {
                        "trigger_type": "seasonal_change",
                        "threshold_value": 1,
                        "warning_threshold": 0.9,
                        "description": "Seasonal maintenance schedule",
                        "unit": "seasons",
                    }
                ],
                "required_skills": ["hvac", "electrical", "preventive_maintenance"],
                "estimated_duration": 5.0,
                "required_parts": ["air_filters", "belts", "refrigerant"],
                "required_tools": ["manifold_gauges", "belt_tension_gauge"],
                "safety_requirements": ["safety_glasses", "refrigerant_handling_cert"],
                "procedures": [
                    "Replace air filters",
                    "Check refrigerant levels",
                    "Inspect and adjust belts",
                    "Calibrate thermostats",
                    "Clean condenser coils",
                ],
                "criticality": 3,
                "can_be_deferred": True,
            },
            {
                "name": "Annual Safety Inspection",
                "description": "Mandatory annual safety inspection for compliance",
                "maintenance_type": "regulatory",
                "triggers": [
                    {
                        "trigger_type": "regulatory_deadline",
                        "threshold_value": 365,
                        "warning_threshold": 335,
                        "description": "Annual regulatory inspection",
                        "unit": "days",
                    }
                ],
                "required_skills": ["safety_inspection", "regulatory_compliance"],
                "estimated_duration": 8.0,
                "required_tools": ["inspection_checklist", "measurement_tools"],
                "safety_requirements": ["certified_inspector"],
                "procedures": [
                    "Complete regulatory checklist",
                    "Document all findings",
                    "Test safety systems",
                    "Update compliance records",
                    "Submit regulatory reports",
                ],
                "criticality": 5,
                "can_be_deferred": False,
            },
        ]

    def _get_rule_for_asset(
        self, asset_id: str, templates: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Get appropriate schedule rule for an asset type."""
        asset_lower = asset_id.lower()

        template_id = None
        interval_value = 30
        interval_unit = "days"
        schedule_type = "time_based"

        if "hydraulic" in asset_lower:
            template_id = next(
                (t["id"] for t in templates if "hydraulic" in t.get("name", "").lower() and "monthly" in t.get("name", "").lower()),
                None
            )
        elif "cnc" in asset_lower or "electrical" in asset_lower:
            template_id = next(
                (t["id"] for t in templates if "electrical" in t.get("name", "").lower()),
                None
            )
            interval_value = 7
        elif "conveyor" in asset_lower:
            template_id = next(
                (t["id"] for t in templates if "conveyor" in t.get("name", "").lower()),
                None
            )
            schedule_type = "usage_based"
            interval_value = 100000
            interval_unit = "cycles"
        elif "hvac" in asset_lower:
            template_id = next(
                (t["id"] for t in templates if "hvac" in t.get("name", "").lower()),
                None
            )
            interval_value = 90

        if not template_id:
            return None

        return {
            "asset_id": asset_id,
            "template_id": template_id,
            "schedule_type": schedule_type,
            "interval_value": interval_value,
            "interval_unit": interval_unit,
            "start_date": datetime.now(timezone.utc),
            "next_due": datetime.now(timezone.utc) + timedelta(days=interval_value if interval_unit == "days" else 30),
            "is_active": True,
        }

    def _get_meters_for_asset(self, asset_id: str) -> List[Dict[str, Any]]:
        """Get appropriate meters for an asset type."""
        asset_lower = asset_id.lower()
        meters = []
        base_date = datetime.now(timezone.utc)

        if "hydraulic" in asset_lower:
            meters = [
                {
                    "asset_id": asset_id,
                    "meter_type": "pressure",
                    "current_value": 3000,
                    "last_reading_date": base_date,
                    "reading_frequency": 1,
                    "unit": "PSI",
                    "is_automated": True,
                    "threshold_warning": 3500,
                    "threshold_critical": 4000,
                },
                {
                    "asset_id": asset_id,
                    "meter_type": "operation_cycles",
                    "current_value": 20000,
                    "last_reading_date": base_date,
                    "reading_frequency": 1,
                    "unit": "cycles",
                    "is_automated": False,
                },
            ]
        elif "motor" in asset_lower or "cnc" in asset_lower:
            meters = [
                {
                    "asset_id": asset_id,
                    "meter_type": "vibration",
                    "current_value": 3.5,
                    "last_reading_date": base_date,
                    "reading_frequency": 1,
                    "unit": "mm/s",
                    "is_automated": True,
                    "threshold_warning": 4.5,
                    "threshold_critical": 7.1,
                },
                {
                    "asset_id": asset_id,
                    "meter_type": "temperature",
                    "current_value": 70,
                    "last_reading_date": base_date,
                    "reading_frequency": 1,
                    "unit": "°C",
                    "is_automated": True,
                    "threshold_warning": 75,
                    "threshold_critical": 85,
                },
            ]
        elif "conveyor" in asset_lower:
            meters = [
                {
                    "asset_id": asset_id,
                    "meter_type": "production_cycles",
                    "current_value": 75000,
                    "last_reading_date": base_date,
                    "reading_frequency": 1,
                    "unit": "cycles",
                    "is_automated": True,
                    "threshold_warning": 85000,
                    "threshold_critical": 100000,
                },
                {
                    "asset_id": asset_id,
                    "meter_type": "runtime_hours",
                    "current_value": 1800,
                    "last_reading_date": base_date,
                    "reading_frequency": 1,
                    "unit": "hours",
                    "is_automated": True,
                    "threshold_warning": 1800,
                    "threshold_critical": 2000,
                },
            ]

        return meters


# Factory function to get engine instance
def get_pm_automation_engine() -> PMAutomationEngine:
    """Get a PM automation engine instance."""
    return PMAutomationEngine()


# Global instance for backward compatibility
pm_automation_engine = PMAutomationEngine()
