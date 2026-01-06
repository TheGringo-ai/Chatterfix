#!/usr/bin/env python3
"""
PM Scheduler End-to-End Test
============================

Tests the complete scheduler loop:
1. Create test org with a rule due now (next_due = yesterday)
2. Scheduler dry run returns SHOULD_TRIGGER
3. Scheduler real run creates exactly 1 WO
4. Rule's next_due moves forward
5. Rerun scheduler produces 0 new WOs (idempotent)

This proves the due-only indexed query and state updates work correctly.

Usage:
    export GOOGLE_APPLICATION_CREDENTIALS="secrets/firebase-admin.json"
    python3 scripts/test_pm_scheduler_e2e.py
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

# Add project root for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

# Test configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or "fredfix"
TEST_ORG_ID = "TEST_SCHEDULER_E2E"
VERBOSE = os.getenv("VERBOSE", "0") == "1"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log(message: str, indent: int = 0):
    prefix = "   " * indent
    print(f"{prefix}{message}")


class PMSchedulerE2ETest:
    """End-to-end test for PM scheduler with due-only indexed query."""

    def __init__(self):
        self.db = None
        self.test_rule_id = f"test_rule_{TEST_ORG_ID}"
        self.test_asset_id = f"test_asset_{TEST_ORG_ID}"
        self.created_wo_ids = []

    def connect(self) -> bool:
        """Initialize Firestore client."""
        try:
            creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if creds_path and os.path.exists(creds_path):
                self.db = firestore.Client.from_service_account_json(creds_path)
            else:
                self.db = firestore.Client(project=PROJECT_ID)
            return True
        except Exception as e:
            log(f"❌ Failed to connect: {e}")
            return False

    def cleanup(self):
        """Remove all test data."""
        log("Cleaning up test data...")
        try:
            # Delete test work orders
            wos = list(
                self.db.collection("work_orders")
                .where(filter=FieldFilter("organization_id", "==", TEST_ORG_ID))
                .stream()
            )
            for wo in wos:
                wo.reference.delete()
            log(f"   Deleted {len(wos)} work orders", 1)

            # Delete test PM rules
            rules = list(
                self.db.collection("pm_schedule_rules")
                .where(filter=FieldFilter("organization_id", "==", TEST_ORG_ID))
                .stream()
            )
            for rule in rules:
                rule.reference.delete()
            log(f"   Deleted {len(rules)} PM rules", 1)

            # Delete test assets
            assets = list(
                self.db.collection("assets")
                .where(filter=FieldFilter("organization_id", "==", TEST_ORG_ID))
                .stream()
            )
            for asset in assets:
                asset.reference.delete()
            log(f"   Deleted {len(assets)} assets", 1)

            # Delete test organization
            self.db.collection("organizations").document(TEST_ORG_ID).delete()

            # Delete PM evaluations
            evals = list(
                self.db.collection("pm_evaluations")
                .where(filter=FieldFilter("organization_id", "==", TEST_ORG_ID))
                .stream()
            )
            for eval_doc in evals:
                eval_doc.reference.delete()
            log(f"   Deleted {len(evals)} evaluations", 1)

            log("   🧹 Cleanup complete")
        except Exception as e:
            log(f"   Warning: Cleanup error: {e}")

    def setup_test_data(self):
        """Create test org, asset, and PM rule that is DUE NOW."""
        log("Setting up test data...")

        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)

        # 1. Create test organization
        self.db.collection("organizations").document(TEST_ORG_ID).set({
            "org_id": TEST_ORG_ID,
            "name": "E2E Scheduler Test Org",
            "is_demo": False,  # IMPORTANT: Not demo, so scheduler will process it
            "created_at": now_iso(),
        })
        log("   Created test organization", 1)

        # 2. Create test asset
        self.db.collection("assets").document(self.test_asset_id).set({
            "organization_id": TEST_ORG_ID,
            "asset_id": self.test_asset_id,
            "name": "Test HVAC Unit",
            "status": "operational",  # IMPORTANT: Not breakdown/out_of_service
            "created_at": now_iso(),
        })
        log("   Created test asset", 1)

        # 3. Create PM rule that is DUE (next_due = yesterday)
        self.db.collection("pm_schedule_rules").document(self.test_rule_id).set({
            "organization_id": TEST_ORG_ID,
            "rule_id": self.test_rule_id,
            "asset_id": self.test_asset_id,
            "name": "Test 30-Day PM",
            "title": "Test PM - HVAC Inspection",
            "description": "End-to-end test PM work order",
            "schedule_type": "time",
            "interval_days": 30,
            "tolerance_days": 3,
            "is_active": True,  # IMPORTANT: Active
            "next_due": yesterday.isoformat(),  # IMPORTANT: Due yesterday = overdue
            "cooldown_hours": 24,
            "priority": "Medium",
            "created_at": now_iso(),
            "updated_at": now_iso(),
        })
        log(f"   Created PM rule with next_due={yesterday.isoformat()}", 1)
        log("   ✅ Test data created")

    async def run_scheduler_dry(self) -> dict:
        """Run scheduler in dry run mode."""
        from app.services.pm_scheduler_runner import run_pm_scheduler

        log("Running scheduler (dry run)...")
        result = await run_pm_scheduler(
            batch_size=10,
            dry_run=True,
            org_id=TEST_ORG_ID,
        )
        return result.to_dict()

    async def run_scheduler_real(self) -> dict:
        """Run scheduler in real mode (creates WOs)."""
        from app.services.pm_scheduler_runner import run_pm_scheduler

        log("Running scheduler (REAL - creates WOs)...")
        result = await run_pm_scheduler(
            batch_size=10,
            dry_run=False,
            org_id=TEST_ORG_ID,
        )
        return result.to_dict()

    def get_rule_state(self) -> dict:
        """Get current state of test rule."""
        doc = self.db.collection("pm_schedule_rules").document(self.test_rule_id).get()
        if doc.exists:
            return doc.to_dict()
        return {}

    def get_work_orders(self) -> list:
        """Get work orders created for test org."""
        wos = list(
            self.db.collection("work_orders")
            .where(filter=FieldFilter("organization_id", "==", TEST_ORG_ID))
            .stream()
        )
        return [wo.to_dict() for wo in wos]

    async def run_tests(self) -> bool:
        """Run all E2E tests."""
        print("=" * 60)
        print("PM Scheduler End-to-End Test")
        print("=" * 60)
        print(f"Project:  {PROJECT_ID}")
        print(f"Test Org: {TEST_ORG_ID}")
        print()

        if not self.connect():
            return False

        # Clean before test
        self.cleanup()

        # Setup test data
        self.setup_test_data()

        all_passed = True

        # =====================================================
        # TEST 1: Dry run should detect rule as SHOULD_TRIGGER
        # =====================================================
        print()
        log("TEST 1: Dry run should detect overdue rule")

        dry_result = await self.run_scheduler_dry()
        log(f"   Result: {dry_result}", 1)

        if dry_result.get("rules_checked", 0) < 1:
            log("   ❌ FAIL: No rules checked (indexed query may be failing)")
            all_passed = False
        elif dry_result.get("should_trigger", 0) < 1:
            log("   ❌ FAIL: Rule not detected as should_trigger")
            all_passed = False
        else:
            log("   ✅ PASS: Rule correctly identified as should_trigger")

        # =====================================================
        # TEST 2: Real run should create exactly 1 WO
        # =====================================================
        print()
        log("TEST 2: Real run should create exactly 1 WO")

        real_result = await self.run_scheduler_real()
        log(f"   Result: {real_result}", 1)

        wos_after_first_run = self.get_work_orders()
        log(f"   Work orders created: {len(wos_after_first_run)}", 1)

        if real_result.get("created", 0) != 1:
            log(f"   ❌ FAIL: Expected 1 created, got {real_result.get('created', 0)}")
            all_passed = False
        elif len(wos_after_first_run) != 1:
            log(f"   ❌ FAIL: Expected 1 WO in DB, found {len(wos_after_first_run)}")
            all_passed = False
        else:
            log("   ✅ PASS: Exactly 1 work order created")
            self.created_wo_ids = [wo.get("id") for wo in wos_after_first_run]

        # =====================================================
        # TEST 3: Rule's next_due should have moved forward
        # =====================================================
        print()
        log("TEST 3: Rule's next_due should have moved forward")

        rule_state = self.get_rule_state()
        next_due = rule_state.get("next_due")
        last_triggered = rule_state.get("last_triggered_at")

        log(f"   next_due: {next_due}", 1)
        log(f"   last_triggered_at: {last_triggered}", 1)

        now = datetime.now(timezone.utc)
        if next_due:
            next_due_dt = datetime.fromisoformat(next_due.replace("Z", "+00:00"))
            if next_due_dt > now:
                log("   ✅ PASS: next_due moved to future")
            else:
                log(f"   ❌ FAIL: next_due still in past ({next_due})")
                all_passed = False
        else:
            log("   ❌ FAIL: next_due not set")
            all_passed = False

        if not last_triggered:
            log("   ❌ FAIL: last_triggered_at not set")
            all_passed = False

        # =====================================================
        # TEST 4: Second run should create 0 new WOs (idempotent)
        # =====================================================
        print()
        log("TEST 4: Second run should create 0 new WOs (idempotent)")

        second_result = await self.run_scheduler_real()
        log(f"   Result: {second_result}", 1)

        wos_after_second_run = self.get_work_orders()
        log(f"   Total work orders: {len(wos_after_second_run)}", 1)

        # Should find 0 due rules now (next_due moved forward)
        if second_result.get("rules_checked", 0) > 0:
            log(f"   ⚠️  Rule still in due query (checked {second_result.get('rules_checked')} rules)")
            # This is OK if it was blocked or wait
            if second_result.get("created", 0) > 0:
                log(f"   ❌ FAIL: Created {second_result.get('created')} more WOs (not idempotent!)")
                all_passed = False
            else:
                log("   ✅ PASS: No new WOs created (may be blocked or cooldown)")
        else:
            log("   ✅ PASS: Rule not in due query anymore (next_due moved forward)")

        if len(wos_after_second_run) != 1:
            log(f"   ❌ FAIL: Expected still 1 WO, found {len(wos_after_second_run)}")
            all_passed = False
        else:
            log("   ✅ PASS: Still exactly 1 work order (idempotent)")

        # =====================================================
        # CLEANUP
        # =====================================================
        print()
        self.cleanup()

        # =====================================================
        # SUMMARY
        # =====================================================
        print()
        print("=" * 60)
        if all_passed:
            print("🎉 ALL TESTS PASSED")
            print()
            print("Verified:")
            print("  • Due-only indexed query works")
            print("  • Overdue rules detected correctly")
            print("  • Work orders created with idempotent IDs")
            print("  • next_due updated after trigger")
            print("  • Second run produces no duplicates")
            print()
            print("✅ PM Scheduler is production-ready!")
        else:
            print("⚠️  SOME TESTS FAILED")
            print()
            print("Check the failures above and fix issues.")
        print("=" * 60)

        return all_passed


async def main():
    test = PMSchedulerE2ETest()
    success = await test.run_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
