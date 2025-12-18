"""
Organization Service
Handles organization/tenant management for multi-tenant CMMS
Integrates with Firebase Authentication
"""

import logging
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from firebase_admin import firestore

from app.services.firebase_auth import firebase_auth_service

logger = logging.getLogger(__name__)

# Demo organization expiration time (48 hours)
DEMO_EXPIRATION_HOURS = 48


class OrganizationService:
    """
    Service for managing organizations/tenants.
    Uses Firebase Firestore for data storage.
    """

    def __init__(self):
        self.db = None
        self._ensure_db()

    def _ensure_db(self):
        """Ensure Firestore database is available"""
        if not self.db and firebase_auth_service.db:
            self.db = firebase_auth_service.db

    def _generate_org_id(self, company_name: str) -> str:
        """Generate a unique organization ID based on company name"""
        # Create a slug from company name
        slug = "".join(c if c.isalnum() else "-" for c in company_name.lower())
        slug = "-".join(filter(None, slug.split("-")))[:20]  # Max 20 chars
        # Add random suffix for uniqueness
        suffix = "".join(
            secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6)
        )
        return f"{slug}-{suffix}"

    async def create_organization(
        self,
        name: str,
        owner_user_id: str,
        owner_email: str,
        industry: Optional[str] = None,
        size: Optional[str] = None,
        phone: Optional[str] = None,
        is_demo: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a new organization when a user signs up.

        Args:
            name: Company/organization name
            owner_user_id: Firebase UID of the user creating the org (becomes owner)
            owner_email: Email of the owner
            industry: Industry category
            size: Company size
            phone: Contact phone
            is_demo: If True, this is a demo organization that will expire

        Returns:
            Organization data with ID
        """
        self._ensure_db()
        if not self.db:
            raise Exception("Firestore not initialized")

        try:
            org_id = self._generate_org_id(name)

            # Calculate expiration for demo orgs
            expires_at = None
            if is_demo:
                expires_at = (
                    datetime.now(timezone.utc) + timedelta(hours=DEMO_EXPIRATION_HOURS)
                ).isoformat()

            org_data = {
                "name": name,
                "slug": org_id,
                "owner_id": owner_user_id,
                "owner_email": owner_email,
                "industry": industry,
                "size": size,
                "phone": phone,
                "status": "active",
                "is_demo": is_demo,
                "expires_at": expires_at,
                "subscription": {
                    "plan": "demo" if is_demo else "free_trial",
                    "status": "active",
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "features": ["all"],  # Full access - demo gets everything
                },
                "settings": {
                    "timezone": "America/New_York",
                    "date_format": "MM/DD/YYYY",
                    "currency": "USD",
                },
                "members": [
                    {
                        "user_id": owner_user_id,
                        "email": owner_email,
                        "role": "owner",
                        "joined_at": datetime.now(timezone.utc).isoformat(),
                    }
                ],
                "member_count": 1,
                "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP,
            }

            # Create organization document
            org_ref = self.db.collection("organizations").document(org_id)
            org_ref.set(org_data)

            # Update user with organization_id
            user_ref = self.db.collection("users").document(owner_user_id)
            user_ref.update(
                {
                    "organization_id": org_id,
                    "organization_name": name,
                    "organization_role": "owner",
                    "updated_at": firestore.SERVER_TIMESTAMP,
                }
            )

            org_data["id"] = org_id
            logger.info(
                f"Created organization: {name} (ID: {org_id}) for user {owner_user_id}"
            )

            # Initialize default org data in background
            await self.initialize_organization_data(org_id)

            return org_data

        except Exception as e:
            logger.error(f"Error creating organization: {e}")
            raise

    async def get_organization(self, org_id: str) -> Optional[Dict[str, Any]]:
        """Get organization by ID"""
        self._ensure_db()
        if not self.db:
            return None

        try:
            org_ref = self.db.collection("organizations").document(org_id)
            org_doc = org_ref.get()

            if org_doc.exists:
                data = org_doc.to_dict()
                data["id"] = org_doc.id
                return data
            return None

        except Exception as e:
            logger.error(f"Error getting organization {org_id}: {e}")
            return None

    async def get_user_organization(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get organization that a user belongs to"""
        self._ensure_db()
        if not self.db:
            return None

        try:
            # Get user's organization_id
            user_ref = self.db.collection("users").document(user_id)
            user_doc = user_ref.get()

            if user_doc.exists:
                user_data = user_doc.to_dict()
                org_id = user_data.get("organization_id")
                if org_id:
                    return await self.get_organization(org_id)
            return None

        except Exception as e:
            logger.error(f"Error getting user organization: {e}")
            return None

    async def add_member(
        self, org_id: str, user_id: str, email: str, role: str = "technician"
    ) -> bool:
        """Add a member to an organization"""
        self._ensure_db()
        if not self.db:
            return False

        try:
            org = await self.get_organization(org_id)
            if not org:
                return False

            # Check if already a member
            members = org.get("members", [])
            if any(m.get("user_id") == user_id for m in members):
                return True  # Already a member

            # Add new member
            members.append(
                {
                    "user_id": user_id,
                    "email": email,
                    "role": role,
                    "joined_at": datetime.now(timezone.utc).isoformat(),
                }
            )

            # Update organization
            org_ref = self.db.collection("organizations").document(org_id)
            org_ref.update(
                {
                    "members": members,
                    "member_count": len(members),
                    "updated_at": firestore.SERVER_TIMESTAMP,
                }
            )

            # Update user with organization info
            user_ref = self.db.collection("users").document(user_id)
            user_ref.update(
                {
                    "organization_id": org_id,
                    "organization_name": org.get("name"),
                    "organization_role": role,
                    "updated_at": firestore.SERVER_TIMESTAMP,
                }
            )

            logger.info(f"Added member {user_id} to organization {org_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding member to organization: {e}")
            return False

    async def remove_member(self, org_id: str, user_id: str) -> bool:
        """Remove a member from an organization"""
        self._ensure_db()
        if not self.db:
            return False

        try:
            org = await self.get_organization(org_id)
            if not org:
                return False

            # Can't remove owner
            if org.get("owner_id") == user_id:
                logger.warning(
                    f"Cannot remove owner {user_id} from organization {org_id}"
                )
                return False

            members = org.get("members", [])
            members = [m for m in members if m.get("user_id") != user_id]

            # Update organization
            org_ref = self.db.collection("organizations").document(org_id)
            org_ref.update(
                {
                    "members": members,
                    "member_count": len(members),
                    "updated_at": firestore.SERVER_TIMESTAMP,
                }
            )

            # Remove organization from user
            user_ref = self.db.collection("users").document(user_id)
            user_ref.update(
                {
                    "organization_id": None,
                    "organization_name": None,
                    "organization_role": None,
                    "updated_at": firestore.SERVER_TIMESTAMP,
                }
            )

            logger.info(f"Removed member {user_id} from organization {org_id}")
            return True

        except Exception as e:
            logger.error(f"Error removing member from organization: {e}")
            return False

    async def get_organization_members(self, org_id: str) -> List[Dict[str, Any]]:
        """Get all members of an organization with their user details"""
        self._ensure_db()
        if not self.db:
            return []

        try:
            org = await self.get_organization(org_id)
            if not org:
                return []

            members = org.get("members", [])
            detailed_members = []

            for member in members:
                user_id = member.get("user_id")
                if user_id:
                    user_ref = self.db.collection("users").document(user_id)
                    user_doc = user_ref.get()
                    if user_doc.exists:
                        user_data = user_doc.to_dict()
                        detailed_members.append(
                            {
                                **member,
                                "full_name": user_data.get("full_name")
                                or user_data.get("display_name", "Unknown"),
                                "email": user_data.get("email", member.get("email")),
                                "status": user_data.get("status", "active"),
                            }
                        )
                    else:
                        detailed_members.append(member)

            return detailed_members

        except Exception as e:
            logger.error(f"Error getting organization members: {e}")
            return []

    async def create_invite(
        self, org_id: str, email: str, role: str, invited_by: str
    ) -> str:
        """Create an invitation for someone to join the organization"""
        self._ensure_db()
        if not self.db:
            raise Exception("Firestore not initialized")

        try:
            # Generate invite code
            invite_code = "".join(
                secrets.choice(string.ascii_letters + string.digits) for _ in range(32)
            )

            org = await self.get_organization(org_id)

            invite_data = {
                "organization_id": org_id,
                "organization_name": org.get("name") if org else "Unknown",
                "email": email,
                "role": role,
                "invited_by": invited_by,
                "status": "pending",
                "created_at": firestore.SERVER_TIMESTAMP,
            }

            invite_ref = self.db.collection("organization_invites").document(
                invite_code
            )
            invite_ref.set(invite_data)

            logger.info(
                f"Created invite {invite_code} for {email} to organization {org_id}"
            )
            return invite_code

        except Exception as e:
            logger.error(f"Error creating invite: {e}")
            raise

    async def accept_invite(self, invite_code: str, user_id: str) -> Optional[str]:
        """Accept an organization invitation"""
        self._ensure_db()
        if not self.db:
            return None

        try:
            invite_ref = self.db.collection("organization_invites").document(
                invite_code
            )
            invite_doc = invite_ref.get()

            if not invite_doc.exists:
                return None

            invite = invite_doc.to_dict()
            if invite.get("status") != "pending":
                return None

            org_id = invite.get("organization_id")

            # Add user to organization
            await self.add_member(
                org_id, user_id, invite.get("email"), invite.get("role", "technician")
            )

            # Mark invite as accepted
            invite_ref.update(
                {
                    "status": "accepted",
                    "accepted_at": firestore.SERVER_TIMESTAMP,
                    "accepted_by": user_id,
                }
            )

            logger.info(f"User {user_id} accepted invite to organization {org_id}")
            return org_id

        except Exception as e:
            logger.error(f"Error accepting invite: {e}")
            return None

    async def get_pending_invites(self, org_id: str) -> List[Dict[str, Any]]:
        """Get all pending invites for an organization"""
        self._ensure_db()
        if not self.db:
            return []

        try:
            invites_ref = self.db.collection("organization_invites")
            query = invites_ref.where("organization_id", "==", org_id).where(
                "status", "==", "pending"
            )
            docs = query.stream()

            invites = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                invites.append(data)

            return invites

        except Exception as e:
            logger.error(f"Error getting pending invites: {e}")
            return []

    async def initialize_organization_data(self, org_id: str) -> bool:
        """
        Initialize default data for a new organization.
        Creates default categories, priorities, etc.
        """
        self._ensure_db()
        if not self.db:
            return False

        try:
            # Create default asset categories for this organization
            default_categories = [
                {
                    "name": "HVAC",
                    "description": "Heating, Ventilation, and Air Conditioning",
                },
                {
                    "name": "Electrical",
                    "description": "Electrical systems and components",
                },
                {"name": "Plumbing", "description": "Plumbing and water systems"},
                {
                    "name": "Production Equipment",
                    "description": "Manufacturing and production machinery",
                },
                {
                    "name": "Safety Systems",
                    "description": "Fire suppression, alarms, and safety equipment",
                },
                {
                    "name": "Vehicles",
                    "description": "Fleet and transportation vehicles",
                },
            ]

            batch = self.db.batch()

            for category in default_categories:
                cat_ref = self.db.collection("asset_categories").document()
                batch.set(
                    cat_ref,
                    {
                        **category,
                        "organization_id": org_id,
                        "created_at": firestore.SERVER_TIMESTAMP,
                    },
                )

            # Create default locations
            default_locations = [
                {"name": "Main Building", "description": "Primary facility"},
                {"name": "Warehouse", "description": "Storage and inventory"},
            ]

            for location in default_locations:
                loc_ref = self.db.collection("locations").document()
                batch.set(
                    loc_ref,
                    {
                        **location,
                        "organization_id": org_id,
                        "created_at": firestore.SERVER_TIMESTAMP,
                    },
                )

            batch.commit()

            logger.info(f"Initialized default data for organization {org_id}")
            return True

        except Exception as e:
            logger.error(f"Error initializing organization data: {e}")
            return False

    async def update_organization(self, org_id: str, data: Dict[str, Any]) -> bool:
        """Update organization settings"""
        self._ensure_db()
        if not self.db:
            return False

        try:
            # Don't allow updating critical fields
            safe_fields = ["name", "industry", "size", "phone", "settings"]
            update_data = {k: v for k, v in data.items() if k in safe_fields}
            update_data["updated_at"] = firestore.SERVER_TIMESTAMP

            org_ref = self.db.collection("organizations").document(org_id)
            org_ref.update(update_data)

            logger.info(f"Updated organization {org_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating organization: {e}")
            return False

    # ==========================================
    # DEMO ORGANIZATION METHODS
    # ==========================================

    async def create_demo_organization(self, anonymous_uid: str) -> Dict[str, Any]:
        """
        Create a demo organization for an anonymous user.
        Demo orgs have full features but expire after DEMO_EXPIRATION_HOURS.

        Args:
            anonymous_uid: Firebase Anonymous Auth UID

        Returns:
            Organization data with ID
        """
        # Generate a fun demo name
        demo_names = [
            "Demo Factory",
            "Test Workshop",
            "Sample Facility",
            "Trial Plant",
            "Demo Site",
            "Sandbox Corp",
        ]
        import random

        demo_name = random.choice(demo_names)

        # Create demo org
        org_data = await self.create_organization(
            name=demo_name,
            owner_user_id=anonymous_uid,
            owner_email=f"demo-{anonymous_uid[:8]}@demo.chatterfix.com",
            is_demo=True,
        )

        logger.info(
            f"Created demo organization {org_data.get('id')} for anonymous user {anonymous_uid}"
        )
        return org_data

    async def convert_demo_to_real(
        self,
        org_id: str,
        new_owner_uid: str,
        new_owner_email: str,
        new_name: Optional[str] = None,
    ) -> bool:
        """
        Convert a demo organization to a real organization.
        Called when a demo user creates a real account.

        Args:
            org_id: The demo organization ID
            new_owner_uid: The new (real) Firebase UID after linking account
            new_owner_email: The new owner's email
            new_name: Optional new organization name

        Returns:
            True if successful
        """
        self._ensure_db()
        if not self.db:
            return False

        try:
            org = await self.get_organization(org_id)
            if not org:
                logger.error(f"Organization {org_id} not found for conversion")
                return False

            if not org.get("is_demo"):
                logger.warning(f"Organization {org_id} is not a demo org")
                return False

            # Update organization to real
            org_ref = self.db.collection("organizations").document(org_id)
            update_data = {
                "is_demo": False,
                "expires_at": None,
                "owner_id": new_owner_uid,
                "owner_email": new_owner_email,
                "subscription.plan": "free_trial",
                "updated_at": firestore.SERVER_TIMESTAMP,
            }

            if new_name:
                update_data["name"] = new_name

            # Update members list
            members = org.get("members", [])
            for member in members:
                if member.get("role") == "owner":
                    member["user_id"] = new_owner_uid
                    member["email"] = new_owner_email
            update_data["members"] = members

            org_ref.update(update_data)

            # Update user document
            user_ref = self.db.collection("users").document(new_owner_uid)
            user_ref.set(
                {
                    "uid": new_owner_uid,
                    "email": new_owner_email,
                    "organization_id": org_id,
                    "organization_name": new_name or org.get("name"),
                    "organization_role": "owner",
                    "role": "owner",
                    "status": "active",
                    "updated_at": firestore.SERVER_TIMESTAMP,
                },
                merge=True,
            )

            logger.info(f"Converted demo org {org_id} to real for user {new_owner_uid}")
            return True

        except Exception as e:
            logger.error(f"Error converting demo org: {e}")
            return False

    async def delete_organization(self, org_id: str) -> bool:
        """
        Delete an organization and ALL its data.
        Used for cleaning up expired demo orgs.

        Args:
            org_id: Organization ID to delete

        Returns:
            True if successful
        """
        self._ensure_db()
        if not self.db:
            return False

        try:
            # Collections to clean up (org-scoped data)
            collections_to_delete = [
                "work_orders",
                "assets",
                "parts",
                "vendors",
                "asset_categories",
                "locations",
                "training_assignments",
                "training_modules",
            ]

            batch = self.db.batch()
            deleted_count = 0

            # Delete all documents in each collection for this org
            for collection_name in collections_to_delete:
                query = self.db.collection(collection_name).where(
                    "organization_id", "==", org_id
                )
                docs = query.stream()
                for doc in docs:
                    batch.delete(doc.reference)
                    deleted_count += 1

                    # Commit in batches of 500 (Firestore limit)
                    if deleted_count >= 450:
                        batch.commit()
                        batch = self.db.batch()
                        deleted_count = 0

            # Delete organization invites
            invites_query = self.db.collection("organization_invites").where(
                "organization_id", "==", org_id
            )
            for doc in invites_query.stream():
                batch.delete(doc.reference)

            # Delete the organization document itself
            org_ref = self.db.collection("organizations").document(org_id)
            batch.delete(org_ref)

            # Commit final batch
            batch.commit()

            logger.info(f"Deleted organization {org_id} and all its data")
            return True

        except Exception as e:
            logger.error(f"Error deleting organization {org_id}: {e}")
            return False

    async def cleanup_expired_demos(self) -> int:
        """
        Clean up expired demo organizations.
        Should be called periodically (e.g., by a Cloud Function).

        Returns:
            Number of demo orgs deleted
        """
        self._ensure_db()
        if not self.db:
            return 0

        try:
            now = datetime.now(timezone.utc).isoformat()

            # Find expired demo orgs
            query = (
                self.db.collection("organizations")
                .where("is_demo", "==", True)
                .where("expires_at", "<=", now)
            )

            expired_orgs = list(query.stream())
            deleted_count = 0

            for org_doc in expired_orgs:
                org_id = org_doc.id
                org_data = org_doc.to_dict()
                logger.info(
                    f"Cleaning up expired demo org: {org_id} (expired: {org_data.get('expires_at')})"
                )

                if await self.delete_organization(org_id):
                    deleted_count += 1

            logger.info(f"Cleaned up {deleted_count} expired demo organizations")
            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up expired demos: {e}")
            return 0

    async def get_demo_time_remaining(self, org_id: str) -> Optional[int]:
        """
        Get remaining time for a demo organization in minutes.

        Returns:
            Minutes remaining, or None if not a demo or expired
        """
        org = await self.get_organization(org_id)
        if not org or not org.get("is_demo"):
            return None

        expires_at = org.get("expires_at")
        if not expires_at:
            return None

        try:
            expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            remaining = expiry - now

            if remaining.total_seconds() <= 0:
                return 0

            return int(remaining.total_seconds() / 60)

        except Exception:
            return None


# Global service instance
organization_service = OrganizationService()


def get_organization_service() -> OrganizationService:
    """Get the global organization service instance"""
    return organization_service
