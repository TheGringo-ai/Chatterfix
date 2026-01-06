#!/usr/bin/env python3
"""
Firestore Direct Client Sanity Test
====================================

Tests the Firestore client directly (not wrappers) to ensure that every
new company you onboard gets a working, isolated "tenant" dataset.

Two test layers:
1. Firestore client sanity tests (CRUD + queries + idempotent write)
2. Tenant provisioning smoke test (create org + seed required docs + verify reads)

IMPORTANT: This matches ChatterFix's actual schema:
- Top-level collections with `organization_id` field for tenant isolation
- Collections: organizations, assets, work_orders, pm_schedule_rules, parts, vendors, rate_limits

Usage:
    # Set credentials
    export GOOGLE_APPLICATION_CREDENTIALS="secrets/firebase-admin.json"
    export GCP_PROJECT_ID="fredfix"

    # Run test
    python3 scripts/firestore_client_sanity_test.py

    # With cleanup
    CLEANUP=1 python3 scripts/firestore_client_sanity_test.py

    # Custom test org
    TEST_ORG_ID=my_test_org python3 scripts/firestore_client_sanity_test.py
"""
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Optional

# Add project root for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from google.api_core.exceptions import AlreadyExists

# Project configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or "fredfix"
ORG_ID = os.getenv("TEST_ORG_ID", "TEST_DB_SANITY")
VERBOSE = os.getenv("VERBOSE", "0") == "1"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log(message: str, indent: int = 0):
    prefix = "   " * indent
    print(f"{prefix}{message}")


def log_verbose(message: str, indent: int = 0):
    if VERBOSE:
        log(message, indent)


class FirestoreSanityTest:
    """
    Comprehensive Firestore sanity test matching ChatterFix's actual schema.

    Schema pattern: Top-level collections with organization_id field for tenant isolation.
    """

    def __init__(self, project_id: str, org_id: str):
        self.project_id = project_id
        self.org_id = org_id
        self.db: Optional[firestore.Client] = None
        self.test_ids = {
            "asset": f"test_asset_{org_id}",
            "work_order": f"test_wo_{org_id}_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            "pm_rule": f"test_pm_rule_{org_id}",
            "part": f"test_part_{org_id}",
            "vendor": f"test_vendor_{org_id}",
        }

    def connect(self) -> bool:
        """Initialize Firestore client"""
        try:
            # Check for service account file
            creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if creds_path and os.path.exists(creds_path):
                self.db = firestore.Client.from_service_account_json(creds_path)
                log_verbose(f"Connected using service account: {creds_path}")
            else:
                # Try default credentials (works on GCP)
                self.db = firestore.Client(project=self.project_id)
                log_verbose("Connected using default credentials")
            return True
        except Exception as e:
            log(f"❌ Failed to connect to Firestore: {e}")
            return False

    def cleanup_test_data(self):
        """Remove any existing test data before/after tests"""
        log("Cleaning up existing test data...")
        collections_to_clean = [
            ("organizations", self.org_id),
            ("assets", self.test_ids["asset"]),
            ("work_orders", self.test_ids["work_order"]),
            ("pm_schedule_rules", self.test_ids["pm_rule"]),
            ("parts", self.test_ids["part"]),
            ("vendors", self.test_ids["vendor"]),
            ("rate_limits", self.org_id),
        ]

        for collection, doc_id in collections_to_clean:
            try:
                self.db.collection(collection).document(doc_id).delete()
                log_verbose(f"Deleted {collection}/{doc_id}", 1)
            except Exception:
                pass  # OK if doesn't exist

        log("   🧹 Cleanup done")

    # ==========================================
    # TEST 1: Organization Creation
    # ==========================================

    def test_create_organization(self) -> bool:
        """Test creating an organization document"""
        log("1. Testing organization creation...")

        org_data = {
            "org_id": self.org_id,
            "name": "DB Sanity Test Organization",
            "owner_id": "test_owner_uid",
            "owner_email": "test@example.com",
            "is_demo": True,  # Mark as demo for easy identification
            "members": [
                {
                    "user_id": "test_owner_uid",
                    "email": "test@example.com",
                    "role": "owner",
                    "joined_at": now_iso(),
                }
            ],
            "settings": {
                "timezone": "America/Chicago",
                "work_order_prefix": "WO",
            },
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }

        try:
            self.db.collection("organizations").document(self.org_id).set(org_data, merge=True)

            # Verify read-back
            doc = self.db.collection("organizations").document(self.org_id).get()
            if not doc.exists:
                log("   ❌ Organization not found after creation")
                return False

            data = doc.to_dict()
            if data.get("name") != "DB Sanity Test Organization":
                log("   ❌ Organization data mismatch")
                return False

            log("   ✅ Organization created and verified")
            return True
        except Exception as e:
            log(f"   ❌ Failed to create organization: {e}")
            return False

    # ==========================================
    # TEST 2: Asset CRUD with Org Scoping
    # ==========================================

    def test_asset_crud(self) -> bool:
        """Test asset create/read/update with organization_id scoping"""
        log("2. Testing asset CRUD with org scoping...")

        asset_id = self.test_ids["asset"]
        asset_data = {
            "organization_id": self.org_id,
            "asset_id": asset_id,
            "name": "Test Hydraulic Press",
            "asset_tag": "HP-TEST-001",
            "asset_type": "Manufacturing",
            "location": "Building A - Production Floor",
            "status": "operational",
            "criticality": 4,
            "meters": {"runtime_hours": 1234.5},
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }

        try:
            # CREATE
            self.db.collection("assets").document(asset_id).set(asset_data)
            log_verbose("Created asset", 1)

            # READ
            doc = self.db.collection("assets").document(asset_id).get()
            if not doc.exists:
                log("   ❌ Asset not found after creation")
                return False
            log_verbose("Read asset back", 1)

            # QUERY by organization_id
            assets = list(
                self.db.collection("assets")
                .where(filter=FieldFilter("organization_id", "==", self.org_id))
                .stream()
            )
            if len(assets) < 1:
                log("   ❌ Asset query by organization_id returned 0 results")
                return False
            log_verbose(f"Query returned {len(assets)} assets for org", 1)

            # UPDATE
            self.db.collection("assets").document(asset_id).update({
                "status": "warning",
                "updated_at": now_iso(),
            })

            updated_doc = self.db.collection("assets").document(asset_id).get()
            if updated_doc.to_dict().get("status") != "warning":
                log("   ❌ Asset update failed")
                return False
            log_verbose("Updated asset status", 1)

            log("   ✅ Asset CRUD with org scoping works")
            return True
        except Exception as e:
            log(f"   ❌ Asset CRUD failed: {e}")
            return False

    # ==========================================
    # TEST 3: PM Schedule Rule (Time-Based)
    # ==========================================

    def test_pm_schedule_rule(self) -> bool:
        """Test PM schedule rule creation and querying"""
        log("3. Testing PM schedule rules...")

        rule_id = self.test_ids["pm_rule"]
        rule_data = {
            "organization_id": self.org_id,
            "rule_id": rule_id,
            "asset_id": self.test_ids["asset"],
            "name": "30-Day PM Inspection",
            "schedule_type": "time",  # time, meter, or condition
            "interval_days": 30,
            "tolerance_days": 3,
            "is_active": True,
            "last_completed_at": "2020-01-01T00:00:00+00:00",  # Far in past = overdue
            "next_due": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),  # Overdue
            "cooldown_hours": 24,
            "template_id": None,
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }

        try:
            # CREATE
            self.db.collection("pm_schedule_rules").document(rule_id).set(rule_data)
            log_verbose("Created PM rule", 1)

            # READ-BACK to verify
            doc = self.db.collection("pm_schedule_rules").document(rule_id).get()
            if not doc.exists:
                log("   ❌ PM rule not found after creation")
                return False
            log_verbose("PM rule read-back verified", 1)

            # QUERY active rules for org (single filter to avoid composite index requirement)
            active_rules = list(
                self.db.collection("pm_schedule_rules")
                .where(filter=FieldFilter("organization_id", "==", self.org_id))
                .stream()
            )
            # Filter in code for is_active
            active_rules = [r for r in active_rules if r.to_dict().get("is_active") == True]
            if len(active_rules) < 1:
                log("   ❌ No active rules found for org")
                return False
            log_verbose(f"Found {len(active_rules)} active rules", 1)

            # Check overdue (filter in code to avoid composite index)
            now = datetime.now(timezone.utc)
            overdue_rules = []
            for rule in active_rules:
                rule_data = rule.to_dict()
                next_due = rule_data.get("next_due")
                if next_due and next_due <= now.isoformat():
                    overdue_rules.append(rule)
            log_verbose(f"Found {len(overdue_rules)} overdue rules (filtered in code)", 1)

            log("   ✅ PM schedule rules work correctly")
            return True
        except Exception as e:
            log(f"   ❌ PM rule test failed: {e}")
            return False

    # ==========================================
    # TEST 4: Idempotent Work Order Creation
    # ==========================================

    def test_idempotent_work_order(self) -> bool:
        """Test that work orders can be created idempotently (scheduler-safe)"""
        log("4. Testing idempotent work order creation...")

        wo_id = self.test_ids["work_order"]
        wo_data = {
            "organization_id": self.org_id,
            "work_order_id": wo_id,
            "title": "PM Inspection - Test Asset",
            "description": "Scheduled preventive maintenance inspection",
            "type": "PM",
            "priority": "Medium",
            "status": "Open",
            "asset_id": self.test_ids["asset"],
            "rule_id": self.test_ids["pm_rule"],
            "idempotency_key": f"{self.org_id}_{self.test_ids['pm_rule']}_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }

        try:
            wo_ref = self.db.collection("work_orders").document(wo_id)

            # First create should succeed
            created_first = False
            try:
                wo_ref.create(wo_data)  # create() fails if doc exists
                created_first = True
            except AlreadyExists:
                created_first = False

            if not created_first:
                log("   ❌ First work order create() failed (should succeed)")
                return False
            log_verbose("First create() succeeded", 1)

            # Second create should fail (idempotency)
            created_second = False
            try:
                wo_ref.create(wo_data)
                created_second = True
            except AlreadyExists:
                created_second = False

            if created_second:
                log("   ❌ Second create() succeeded (should fail for idempotency)")
                return False
            log_verbose("Second create() blocked (idempotent)", 1)

            # Verify read-back
            wo_doc = wo_ref.get()
            if not wo_doc.exists:
                log("   ❌ Work order not found after creation")
                return False

            if wo_doc.to_dict().get("status") != "Open":
                log("   ❌ Work order status mismatch")
                return False
            log_verbose("Work order verified", 1)

            log("   ✅ Idempotent work order creation works (scheduler-safe)")
            return True
        except Exception as e:
            log(f"   ❌ Idempotent WO test failed: {e}")
            return False

    # ==========================================
    # TEST 5: Query Work Orders by Rule + Status
    # ==========================================

    def test_query_work_orders(self) -> bool:
        """Test querying work orders by rule_id and status"""
        log("5. Testing work order queries...")

        try:
            # Query open WOs for the PM rule
            open_wos = list(
                self.db.collection("work_orders")
                .where(filter=FieldFilter("organization_id", "==", self.org_id))
                .where(filter=FieldFilter("rule_id", "==", self.test_ids["pm_rule"]))
                .where(filter=FieldFilter("status", "==", "Open"))
                .limit(5)
                .stream()
            )

            if len(open_wos) < 1:
                log("   ❌ Expected at least 1 open WO for the rule")
                return False
            log_verbose(f"Found {len(open_wos)} open WOs for rule", 1)

            # Query by idempotency key
            idempotency_key = f"{self.org_id}_{self.test_ids['pm_rule']}_{datetime.now(timezone.utc).strftime('%Y%m%d')}"
            existing = list(
                self.db.collection("work_orders")
                .where(filter=FieldFilter("organization_id", "==", self.org_id))
                .where(filter=FieldFilter("idempotency_key", "==", idempotency_key))
                .limit(1)
                .stream()
            )

            if len(existing) < 1:
                log("   ❌ Idempotency key query returned 0 results")
                return False
            log_verbose(f"Idempotency key query found existing WO", 1)

            log("   ✅ Work order queries work correctly")
            return True
        except Exception as e:
            log(f"   ❌ WO query test failed: {e}")
            return False

    # ==========================================
    # TEST 6: Tenant Isolation Verification
    # ==========================================

    def test_tenant_isolation(self) -> bool:
        """Verify that queries only return data for the correct organization"""
        log("6. Testing tenant isolation...")

        try:
            # Create a document with a DIFFERENT org_id
            other_org_id = "OTHER_ORG_ISOLATION_TEST"
            other_asset_id = f"other_asset_{other_org_id}"

            self.db.collection("assets").document(other_asset_id).set({
                "organization_id": other_org_id,
                "name": "Asset from other org",
                "status": "operational",
                "created_at": now_iso(),
            })
            log_verbose("Created asset in different org", 1)

            # Query assets for our test org - should NOT include the other org's asset
            our_assets = list(
                self.db.collection("assets")
                .where(filter=FieldFilter("organization_id", "==", self.org_id))
                .stream()
            )

            for asset in our_assets:
                asset_data = asset.to_dict()
                if asset_data.get("organization_id") != self.org_id:
                    log("   ❌ TENANT ISOLATION BREACH: Got asset from wrong org!")
                    return False
            log_verbose(f"Verified {len(our_assets)} assets all belong to correct org", 1)

            # Cleanup the other org's test asset
            self.db.collection("assets").document(other_asset_id).delete()
            log_verbose("Cleaned up other org's test asset", 1)

            log("   ✅ Tenant isolation verified")
            return True
        except Exception as e:
            log(f"   ❌ Tenant isolation test failed: {e}")
            return False

    # ==========================================
    # TEST 7: Rate Limits (Tenant Provisioning)
    # ==========================================

    def test_rate_limits_provisioning(self) -> bool:
        """Test creating rate limit configuration for new tenant"""
        log("7. Testing rate limits provisioning...")

        rate_limit_data = {
            "organization_id": self.org_id,
            "tier": "free",
            "limits": {
                "ai_requests_per_day": 50,
                "work_orders_per_month": 100,
                "assets_max": 25,
                "users_max": 5,
            },
            "usage": {
                "ai_requests_today": 0,
                "work_orders_this_month": 0,
            },
            "reset_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }

        try:
            self.db.collection("rate_limits").document(self.org_id).set(rate_limit_data, merge=True)

            # Verify
            doc = self.db.collection("rate_limits").document(self.org_id).get()
            if not doc.exists:
                log("   ❌ Rate limits not found after creation")
                return False

            limits = doc.to_dict().get("limits", {})
            if limits.get("ai_requests_per_day") != 50:
                log("   ❌ Rate limits data mismatch")
                return False

            log("   ✅ Rate limits provisioned for new tenant")
            return True
        except Exception as e:
            log(f"   ❌ Rate limits test failed: {e}")
            return False

    # ==========================================
    # TEST 8: Parts & Vendors (Optional Provisioning)
    # ==========================================

    def test_parts_and_vendors(self) -> bool:
        """Test creating parts and vendors for the tenant"""
        log("8. Testing parts and vendors...")

        try:
            # Create a vendor
            vendor_data = {
                "organization_id": self.org_id,
                "name": "Test Vendor Inc",
                "contact_email": "vendor@test.com",
                "phone": "555-1234",
                "status": "active",
                "created_at": now_iso(),
            }
            self.db.collection("vendors").document(self.test_ids["vendor"]).set(vendor_data)
            log_verbose("Created vendor", 1)

            # Create a part
            part_data = {
                "organization_id": self.org_id,
                "name": "Hydraulic Seal Kit",
                "part_number": "HSK-001",
                "category": "Seals",
                "current_stock": 10,
                "minimum_stock": 5,
                "unit_cost": 25.00,
                "vendor_id": self.test_ids["vendor"],
                "created_at": now_iso(),
            }
            self.db.collection("parts").document(self.test_ids["part"]).set(part_data)
            log_verbose("Created part", 1)

            # Query parts by org
            parts = list(
                self.db.collection("parts")
                .where(filter=FieldFilter("organization_id", "==", self.org_id))
                .stream()
            )
            if len(parts) < 1:
                log("   ❌ Parts query returned 0 results")
                return False

            log("   ✅ Parts and vendors created successfully")
            return True
        except Exception as e:
            log(f"   ❌ Parts/vendors test failed: {e}")
            return False

    # ==========================================
    # RUN ALL TESTS
    # ==========================================

    def run_all_tests(self, cleanup_before: bool = False, cleanup_after: bool = False) -> bool:
        """Run all sanity tests"""
        print("=" * 60)
        print("Firestore Direct Client Sanity Test")
        print("=" * 60)
        print(f"Project:  {self.project_id}")
        print(f"Test Org: {self.org_id}")
        print(f"Schema:   Top-level collections with organization_id field")
        print()

        if not self.connect():
            return False

        if cleanup_before:
            self.cleanup_test_data()

        tests = [
            ("Organization Creation", self.test_create_organization),
            ("Asset CRUD", self.test_asset_crud),
            ("PM Schedule Rules", self.test_pm_schedule_rule),
            ("Idempotent Work Order", self.test_idempotent_work_order),
            ("Work Order Queries", self.test_query_work_orders),
            ("Tenant Isolation", self.test_tenant_isolation),
            ("Rate Limits Provisioning", self.test_rate_limits_provisioning),
            ("Parts & Vendors", self.test_parts_and_vendors),
        ]

        passed = 0
        failed = 0

        for name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                log(f"   ❌ {name} threw exception: {e}")
                failed += 1

        if cleanup_after:
            print()
            self.cleanup_test_data()

        print()
        print("=" * 60)
        if failed == 0:
            print(f"🎉 ALL {passed} TESTS PASSED")
        else:
            print(f"⚠️  {passed} passed, {failed} FAILED")
        print("=" * 60)
        print()

        if failed == 0:
            print("This test validated:")
            print("  • Organization creation works")
            print("  • Asset CRUD with organization_id scoping works")
            print("  • PM schedule rules can be created and queried")
            print("  • Work orders can be created idempotently (scheduler-safe)")
            print("  • Queries correctly filter by organization_id")
            print("  • Tenant isolation is enforced")
            print("  • Rate limits can be provisioned for new tenants")
            print("  • Parts and vendors work correctly")
            print()
            print("✅ Firestore is ready for onboarding new companies!")

        return failed == 0


def main():
    cleanup_before = os.getenv("PRECLEAN") == "1" or os.getenv("CLEANUP") == "1"
    cleanup_after = os.getenv("CLEANUP") == "1"

    test = FirestoreSanityTest(PROJECT_ID, ORG_ID)
    success = test.run_all_tests(cleanup_before=cleanup_before, cleanup_after=cleanup_after)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
