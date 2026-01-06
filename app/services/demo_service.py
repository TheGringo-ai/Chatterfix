"""
Demo Service
============

Creates isolated, time-limited demo organizations for one-click demo access.

Features:
- Creates demo org with realistic seed data
- Issues session cookie (no Firebase required)
- Auto-expires after 2 hours
- Rate-limited demo creation

Usage:
    from app.services.demo_service import demo_service

    result = await demo_service.create_demo_session(request)
    # Returns: {"org_id": "demo_xxx", "user_id": "demo_user_xxx", "session_token": "..."}
"""

import logging
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from app.core.firestore_db import get_firestore_manager
from app.services.org_bootstrap_service import SubscriptionTier, TIER_LIMITS, create_rate_limits

logger = logging.getLogger(__name__)

# Demo configuration
DEMO_TTL_HOURS = 2
DEMO_TIER = SubscriptionTier.STARTER  # Give demo users STARTER tier to show features
DEMO_RATE_LIMIT_PER_IP = 5  # Max demos per IP per hour


class DemoService:
    """Service for creating and managing demo organizations."""

    async def create_demo_session(
        self,
        client_ip: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new demo organization with seed data and return session info.

        Args:
            client_ip: Client IP for rate limiting (optional)

        Returns:
            {
                "success": True,
                "org_id": "demo_xxx",
                "user_id": "demo_user_xxx",
                "session_token": "xxx",
                "expires_at": "2024-01-06T...",
                "redirect_url": "/dashboard"
            }
        """
        firestore = get_firestore_manager()

        # Generate unique IDs
        demo_id = secrets.token_hex(4).upper()  # e.g., "7F3K2P1A"
        org_id = f"demo_{demo_id}"
        user_id = f"demo_user_{demo_id}"
        session_token = secrets.token_urlsafe(32)

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=DEMO_TTL_HOURS)

        try:
            # Create demo user
            user_data = {
                "uid": user_id,
                "email": f"demo_{demo_id}@chatterfix.demo",
                "full_name": "Demo User",
                "role": "owner",
                "organization_id": org_id,
                "organization_name": "ChatterFix Demo",
                "is_demo": True,
                "permissions": [
                    "view_dashboard",
                    "view_work_orders",
                    "create_work_order",
                    "update_work_order",
                    "view_assets",
                    "create_asset",
                    "update_asset",
                    "view_inventory",
                    "view_reports",
                    "view_team",
                    "view_pm_schedules",
                ],
                "session_token": session_token,
                "session_expires_at": expires_at.isoformat(),
                "created_at": now.isoformat(),
            }

            if firestore.db:
                firestore.db.collection("users").document(user_id).set(user_data)

            # Create demo organization
            org_data = {
                "name": "ChatterFix Demo",
                "slug": org_id,
                "tier": DEMO_TIER.value,
                "is_demo": True,
                "expires_at": expires_at.isoformat(),
                "owner_id": user_id,
                "owner_email": user_data["email"],
                "members": [
                    {
                        "user_id": user_id,
                        "email": user_data["email"],
                        "role": "owner",
                        "name": "Demo User",
                        "joined_at": now.isoformat(),
                    }
                ],
                "counts": {
                    "assets": 0,
                    "users": 1,
                    "pm_rules": 0,
                    "work_orders": 0,
                },
                "settings": {
                    "timezone": "America/Chicago",
                    "currency": "USD",
                    "date_format": "MM/DD/YYYY",
                },
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }

            if firestore.db:
                firestore.db.collection("organizations").document(org_id).set(org_data)

            # Create rate limits
            await create_rate_limits(org_id, DEMO_TIER)

            # Seed demo data
            await self._seed_demo_data(org_id)

            logger.info(f"Created demo org {org_id} (expires: {expires_at.isoformat()})")

            return {
                "success": True,
                "org_id": org_id,
                "user_id": user_id,
                "session_token": session_token,
                "expires_at": expires_at.isoformat(),
                "redirect_url": "/dashboard",
            }

        except Exception as e:
            logger.error(f"Failed to create demo session: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def _seed_demo_data(self, org_id: str) -> Dict[str, int]:
        """
        Seed realistic demo data for a new demo org.

        Returns counts of created items.
        """
        firestore = get_firestore_manager()
        now = datetime.now(timezone.utc)
        counts = {"assets": 0, "work_orders": 0, "pm_rules": 0, "parts": 0, "team": 0}

        if not firestore.db:
            return counts

        # ========================================
        # ASSETS - Food manufacturing equipment
        # ========================================
        assets = [
            {
                "name": "Cheese Line Conveyor A",
                "asset_tag": "CONV-001",
                "category": "Material Handling",
                "location": "Production Floor - Line 1",
                "status": "Operational",
                "criticality": "High",
                "manufacturer": "Dorner",
                "model": "2200 Series",
                "condition_rating": 8,
            },
            {
                "name": "Packaging Robot Cell 2",
                "asset_tag": "ROB-002",
                "category": "Automation",
                "location": "Packaging Area",
                "status": "Operational",
                "criticality": "Critical",
                "manufacturer": "FANUC",
                "model": "M-10iA",
                "condition_rating": 9,
            },
            {
                "name": "Boiler Feed Pump #1",
                "asset_tag": "PUMP-001",
                "category": "Utilities",
                "location": "Boiler Room",
                "status": "Maintenance Required",
                "criticality": "Critical",
                "manufacturer": "Grundfos",
                "model": "CR 45-3",
                "condition_rating": 5,
            },
            {
                "name": "Air Compressor #1",
                "asset_tag": "COMP-001",
                "category": "Compressed Air",
                "location": "Utility Room",
                "status": "Operational",
                "criticality": "High",
                "manufacturer": "Atlas Copco",
                "model": "GA 37",
                "condition_rating": 7,
            },
            {
                "name": "CIP Skid",
                "asset_tag": "CIP-001",
                "category": "Sanitation",
                "location": "CIP Room",
                "status": "Operational",
                "criticality": "High",
                "manufacturer": "Alfa Laval",
                "model": "Alsafe CIP",
                "condition_rating": 8,
            },
            {
                "name": "Chiller Unit #2",
                "asset_tag": "HVAC-002",
                "category": "HVAC",
                "location": "Mechanical Room",
                "status": "Operational",
                "criticality": "High",
                "manufacturer": "Carrier",
                "model": "30XA",
                "condition_rating": 7,
            },
            {
                "name": "Pasteurizer HTST",
                "asset_tag": "PAST-001",
                "category": "Processing",
                "location": "Production Floor",
                "status": "Operational",
                "criticality": "Critical",
                "manufacturer": "APV",
                "model": "Junior HTST",
                "condition_rating": 8,
            },
            {
                "name": "Forklift FL-003",
                "asset_tag": "FORK-003",
                "category": "Material Handling",
                "location": "Warehouse",
                "status": "Operational",
                "criticality": "Medium",
                "manufacturer": "Toyota",
                "model": "8FGCU25",
                "condition_rating": 6,
            },
        ]

        asset_ids = []
        for asset in assets:
            asset_data = {
                **asset,
                "organization_id": org_id,
                "last_maintenance": (now - timedelta(days=15)).isoformat(),
                "next_maintenance": (now + timedelta(days=45)).isoformat(),
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }
            doc_ref = firestore.db.collection("assets").document()
            doc_ref.set(asset_data)
            asset_ids.append(doc_ref.id)
            counts["assets"] += 1

        # Update org counts
        firestore.db.collection("organizations").document(org_id).update({
            "counts.assets": counts["assets"]
        })

        # ========================================
        # PM RULES - Preventive maintenance schedules
        # ========================================
        pm_rules = [
            {
                "title": "Conveyor Belt Lubrication",
                "description": "Lubricate conveyor bearings and check belt tension",
                "asset_id": asset_ids[0],
                "asset_name": "Cheese Line Conveyor A",
                "schedule_type": "time_based",
                "interval_days": 14,
                "priority": "Medium",
                "estimated_hours": 0.5,
                "next_due_date": (now - timedelta(days=2)).isoformat(),  # Overdue!
                "is_active": True,
            },
            {
                "title": "Air Compressor Oil Check",
                "description": "Check oil level and quality, top off if needed",
                "asset_id": asset_ids[3],
                "asset_name": "Air Compressor #1",
                "schedule_type": "time_based",
                "interval_days": 30,
                "priority": "High",
                "estimated_hours": 0.25,
                "next_due_date": (now + timedelta(days=5)).isoformat(),
                "is_active": True,
            },
            {
                "title": "Boiler Inspection",
                "description": "Annual boiler inspection per ASME requirements",
                "asset_id": asset_ids[2],
                "asset_name": "Boiler Feed Pump #1",
                "schedule_type": "time_based",
                "interval_days": 90,
                "priority": "Critical",
                "estimated_hours": 4.0,
                "next_due_date": (now + timedelta(days=30)).isoformat(),
                "is_active": True,
            },
            {
                "title": "CIP System Calibration",
                "description": "Calibrate flow meters and temperature sensors",
                "asset_id": asset_ids[4],
                "asset_name": "CIP Skid",
                "schedule_type": "time_based",
                "interval_days": 30,
                "priority": "High",
                "estimated_hours": 2.0,
                "next_due_date": (now - timedelta(days=1)).isoformat(),  # Due yesterday
                "is_active": True,
            },
            {
                "title": "Robot Cell Safety Inspection",
                "description": "Inspect safety interlocks, light curtains, and e-stops",
                "asset_id": asset_ids[1],
                "asset_name": "Packaging Robot Cell 2",
                "schedule_type": "time_based",
                "interval_days": 7,
                "priority": "Critical",
                "estimated_hours": 1.0,
                "next_due_date": (now + timedelta(days=3)).isoformat(),
                "is_active": True,
            },
        ]

        for rule in pm_rules:
            rule_data = {
                **rule,
                "organization_id": org_id,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }
            firestore.db.collection("pm_schedule_rules").add(rule_data)
            counts["pm_rules"] += 1

        firestore.db.collection("organizations").document(org_id).update({
            "counts.pm_rules": counts["pm_rules"]
        })

        # ========================================
        # WORK ORDERS - Mix of PM and breakdown
        # ========================================
        work_orders = [
            {
                "title": "[PM] Conveyor Belt Lubrication",
                "description": "Scheduled preventive maintenance for conveyor bearings",
                "work_order_type": "Preventive",
                "status": "Open",
                "priority": "Medium",
                "asset_id": asset_ids[0],
                "asset_name": "Cheese Line Conveyor A",
                "due_date": (now + timedelta(days=2)).isoformat(),
                "estimated_hours": 0.5,
            },
            {
                "title": "Pump Seal Replacement",
                "description": "Boiler feed pump showing signs of seal wear. Replace mechanical seal.",
                "work_order_type": "Corrective",
                "status": "In Progress",
                "priority": "High",
                "asset_id": asset_ids[2],
                "asset_name": "Boiler Feed Pump #1",
                "assigned_to": "Mike Johnson",
                "due_date": now.isoformat(),
                "estimated_hours": 3.0,
            },
            {
                "title": "[PM] Air Compressor Filter Change",
                "description": "Quarterly air filter replacement completed on schedule",
                "work_order_type": "Preventive",
                "status": "Completed",
                "priority": "Medium",
                "asset_id": asset_ids[3],
                "asset_name": "Air Compressor #1",
                "assigned_to": "Sarah Williams",
                "completed_date": (now - timedelta(days=3)).isoformat(),
                "actual_hours": 0.75,
            },
            {
                "title": "Emergency - Robot Cell E-Stop Fault",
                "description": "Robot cell reporting E-stop fault. Production line down.",
                "work_order_type": "Emergency",
                "status": "Completed",
                "priority": "Critical",
                "asset_id": asset_ids[1],
                "asset_name": "Packaging Robot Cell 2",
                "assigned_to": "Mike Johnson",
                "completed_date": (now - timedelta(days=1)).isoformat(),
                "actual_hours": 1.5,
                "resolution_notes": "Found loose connection on E-stop relay. Reconnected and tested.",
            },
            {
                "title": "Chiller Low Refrigerant Alarm",
                "description": "Chiller showing low refrigerant. Check for leaks and recharge.",
                "work_order_type": "Corrective",
                "status": "Open",
                "priority": "High",
                "asset_id": asset_ids[5],
                "asset_name": "Chiller Unit #2",
                "due_date": (now + timedelta(days=1)).isoformat(),
                "estimated_hours": 2.0,
            },
            {
                "title": "[PM] CIP System Calibration",
                "description": "Monthly calibration of CIP flow meters and sensors",
                "work_order_type": "Preventive",
                "status": "Open",
                "priority": "High",
                "asset_id": asset_ids[4],
                "asset_name": "CIP Skid",
                "due_date": (now - timedelta(days=1)).isoformat(),  # Overdue
                "estimated_hours": 2.0,
            },
            {
                "title": "Forklift Battery Replacement",
                "description": "Replace battery pack - showing reduced capacity",
                "work_order_type": "Corrective",
                "status": "Waiting for Parts",
                "priority": "Medium",
                "asset_id": asset_ids[7],
                "asset_name": "Forklift FL-003",
                "due_date": (now + timedelta(days=7)).isoformat(),
                "estimated_hours": 1.0,
            },
            {
                "title": "[PM] Pasteurizer COP Cleaning",
                "description": "Weekly clean-out-of-place procedure",
                "work_order_type": "Preventive",
                "status": "Completed",
                "priority": "High",
                "asset_id": asset_ids[6],
                "asset_name": "Pasteurizer HTST",
                "assigned_to": "Sarah Williams",
                "completed_date": (now - timedelta(days=2)).isoformat(),
                "actual_hours": 2.5,
            },
        ]

        for wo in work_orders:
            wo_data = {
                **wo,
                "organization_id": org_id,
                "created_at": (now - timedelta(days=5)).isoformat(),
                "created_date": (now - timedelta(days=5)).isoformat(),
                "updated_at": now.isoformat(),
            }
            firestore.db.collection("work_orders").add(wo_data)
            counts["work_orders"] += 1

        firestore.db.collection("organizations").document(org_id).update({
            "counts.work_orders": counts["work_orders"]
        })

        # ========================================
        # INVENTORY - Common maintenance parts
        # ========================================
        parts = [
            {"name": "Conveyor Belt 24\" x 50ft", "part_number": "BELT-24-50", "category": "Belts", "current_stock": 2, "minimum_stock": 1, "unit_cost": 450.00},
            {"name": "SKF 6205 Bearing", "part_number": "SKF-6205", "category": "Bearings", "current_stock": 12, "minimum_stock": 6, "unit_cost": 18.50},
            {"name": "Mechanical Seal 1.5\"", "part_number": "SEAL-1.5-M", "category": "Seals", "current_stock": 3, "minimum_stock": 2, "unit_cost": 125.00},
            {"name": "Air Filter Element", "part_number": "AF-GA37", "category": "Filters", "current_stock": 4, "minimum_stock": 2, "unit_cost": 85.00},
            {"name": "Compressor Oil 5 Gal", "part_number": "OIL-COMP-5", "category": "Lubricants", "current_stock": 2, "minimum_stock": 1, "unit_cost": 165.00},
            {"name": "V-Belt B68", "part_number": "VBELT-B68", "category": "Belts", "current_stock": 6, "minimum_stock": 4, "unit_cost": 22.00},
            {"name": "Temperature Sensor RTD", "part_number": "RTD-PT100", "category": "Sensors", "current_stock": 5, "minimum_stock": 3, "unit_cost": 45.00},
            {"name": "Flow Meter Gasket Kit", "part_number": "FM-GASK-KIT", "category": "Gaskets", "current_stock": 8, "minimum_stock": 4, "unit_cost": 35.00},
            {"name": "Forklift Battery 36V", "part_number": "BATT-36V-FL", "category": "Electrical", "current_stock": 0, "minimum_stock": 1, "unit_cost": 2500.00},
            {"name": "Hydraulic Oil ISO 46", "part_number": "HYD-ISO46-5", "category": "Lubricants", "current_stock": 3, "minimum_stock": 2, "unit_cost": 95.00},
            {"name": "Safety Relay 24VDC", "part_number": "REL-24DC-SF", "category": "Electrical", "current_stock": 4, "minimum_stock": 2, "unit_cost": 185.00},
            {"name": "Refrigerant R-410A 25lb", "part_number": "REF-R410A-25", "category": "HVAC", "current_stock": 1, "minimum_stock": 2, "unit_cost": 275.00},
        ]

        for part in parts:
            part_data = {
                **part,
                "organization_id": org_id,
                "location": "Main Storeroom",
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }
            firestore.db.collection("parts").add(part_data)
            counts["parts"] += 1

        # ========================================
        # TEAM MEMBERS (fake)
        # ========================================
        team_members = [
            {
                "name": "Mike Johnson",
                "email": "mike.j@demo.chatterfix.com",
                "role": "technician",
                "title": "Lead Maintenance Technician",
                "phone": "(555) 123-4567",
            },
            {
                "name": "Sarah Williams",
                "email": "sarah.w@demo.chatterfix.com",
                "role": "technician",
                "title": "Maintenance Technician",
                "phone": "(555) 234-5678",
            },
            {
                "name": "Demo User",
                "email": f"demo@demo.chatterfix.com",
                "role": "owner",
                "title": "Maintenance Supervisor",
                "phone": "(555) 345-6789",
            },
        ]

        # Add team members to org.members
        members_list = []
        for member in team_members:
            members_list.append({
                "user_id": f"demo_member_{secrets.token_hex(4)}",
                "email": member["email"],
                "role": member["role"],
                "name": member["name"],
                "title": member.get("title", ""),
                "joined_at": now.isoformat(),
            })
            counts["team"] += 1

        firestore.db.collection("organizations").document(org_id).update({
            "members": members_list
        })

        logger.info(
            f"Seeded demo data for {org_id}: "
            f"{counts['assets']} assets, {counts['work_orders']} WOs, "
            f"{counts['pm_rules']} PM rules, {counts['parts']} parts"
        )

        return counts

    async def get_demo_user_by_token(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Get demo user by session token.

        Returns user data if valid, None if expired or invalid.
        """
        firestore = get_firestore_manager()

        if not firestore.db:
            return None

        # Query users by session_token
        users_ref = firestore.db.collection("users")
        query = users_ref.where("session_token", "==", session_token).where("is_demo", "==", True).limit(1)

        docs = list(query.stream())
        if not docs:
            return None

        user_data = docs[0].to_dict()

        # Check expiration
        expires_at = user_data.get("session_expires_at")
        if expires_at:
            try:
                exp_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                if datetime.now(timezone.utc) > exp_dt:
                    logger.info(f"Demo session expired for user {user_data.get('uid')}")
                    return None
            except Exception:
                pass

        return user_data

    async def cleanup_expired_demos(self) -> Dict[str, Any]:
        """
        Clean up expired demo organizations and users.
        Should be run periodically (e.g., daily via Cloud Scheduler).

        Returns count of cleaned up items.
        """
        firestore = get_firestore_manager()

        if not firestore.db:
            return {"success": False, "error": "Firestore not initialized"}

        now = datetime.now(timezone.utc)
        cleaned = {"orgs": 0, "users": 0, "assets": 0, "work_orders": 0, "pm_rules": 0, "parts": 0}

        # Find expired demo orgs
        orgs_query = firestore.db.collection("organizations").where("is_demo", "==", True)

        for org_doc in orgs_query.stream():
            org_data = org_doc.to_dict()
            org_id = org_doc.id

            expires_at = org_data.get("expires_at")
            if not expires_at:
                continue

            try:
                exp_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                if datetime.now(timezone.utc) <= exp_dt:
                    continue  # Not expired yet
            except Exception:
                continue

            logger.info(f"Cleaning up expired demo org: {org_id}")

            # Delete related data
            for collection in ["assets", "work_orders", "pm_schedule_rules", "parts"]:
                docs = firestore.db.collection(collection).where("organization_id", "==", org_id).stream()
                for doc in docs:
                    doc.reference.delete()
                    cleaned[collection.replace("pm_schedule_rules", "pm_rules")] = cleaned.get(collection.replace("pm_schedule_rules", "pm_rules"), 0) + 1

            # Delete demo users
            users = firestore.db.collection("users").where("organization_id", "==", org_id).where("is_demo", "==", True).stream()
            for user in users:
                user.reference.delete()
                cleaned["users"] += 1

            # Delete rate limits
            firestore.db.collection("rate_limits").document(org_id).delete()

            # Delete org
            org_doc.reference.delete()
            cleaned["orgs"] += 1

        logger.info(f"Demo cleanup complete: {cleaned}")

        return {
            "success": True,
            "cleaned_at": now.isoformat(),
            "counts": cleaned,
        }


# Global instance
demo_service = DemoService()


def get_demo_service() -> DemoService:
    """Get the global demo service instance."""
    return demo_service
