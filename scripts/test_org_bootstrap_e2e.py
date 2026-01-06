#!/usr/bin/env python3
"""
Organization Bootstrap End-to-End Test
=======================================

Tests the complete organization onboarding flow:
1. Bootstrap creates org + rate limits + user
2. Status endpoint returns correct data
3. Idempotent - second call returns existing org
4. Sample data option creates assets + PM rules
5. Delete removes all data

Usage:
    export GOOGLE_APPLICATION_CREDENTIALS="secrets/firebase-admin.json"
    python3 scripts/test_org_bootstrap_e2e.py
"""
import asyncio
import os
import sys

# Add project root for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.cloud import firestore

# Test configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or "fredfix"
TEST_ORG_ID = "TEST_BOOTSTRAP_E2E"
TEST_OWNER_UID = "test_owner_uid_bootstrap"
TEST_OWNER_EMAIL = "bootstrap_test@example.com"


def log(message: str, indent: int = 0):
    prefix = "   " * indent
    print(f"{prefix}{message}")


class BootstrapE2ETest:
    """End-to-end test for organization bootstrap."""

    def __init__(self):
        self.db = None

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
            for collection in ["work_orders", "pm_schedule_rules", "assets", "parts", "vendors", "pm_evaluations", "asset_categories", "locations"]:
                docs = list(
                    self.db.collection(collection)
                    .where("organization_id", "==", TEST_ORG_ID)
                    .stream()
                )
                for doc in docs:
                    doc.reference.delete()
                if docs:
                    log(f"   Deleted {len(docs)} {collection}", 1)

            # Delete rate limits
            try:
                self.db.collection("rate_limits").document(TEST_ORG_ID).delete()
            except Exception:
                pass

            # Delete organization
            try:
                self.db.collection("organizations").document(TEST_ORG_ID).delete()
            except Exception:
                pass

            # Delete test user
            try:
                self.db.collection("users").document(TEST_OWNER_UID).delete()
            except Exception:
                pass

            log("   🧹 Cleanup complete")
        except Exception as e:
            log(f"   Warning: Cleanup error: {e}")

    async def test_bootstrap_creates_org(self) -> bool:
        """Test that bootstrap creates organization and required documents."""
        log("TEST 1: Bootstrap creates organization + rate limits + user")

        from app.services.org_bootstrap_service import bootstrap_org, SubscriptionTier

        result = await bootstrap_org(
            org_id=TEST_ORG_ID,
            org_name="Test Bootstrap Corp",
            owner_user_id=TEST_OWNER_UID,
            owner_email=TEST_OWNER_EMAIL,
            owner_name="Test Owner",
            tier=SubscriptionTier.STARTER,
            timezone_str="America/New_York",
            include_sample_data=False,
            force=True,
        )

        if not result.success:
            log(f"   ❌ FAIL: Bootstrap returned success=False: {result.message}")
            return False

        # Verify organization created
        org = self.db.collection("organizations").document(TEST_ORG_ID).get()
        if not org.exists:
            log("   ❌ FAIL: Organization not created in Firestore")
            return False
        org_data = org.to_dict()
        if org_data.get("name") != "Test Bootstrap Corp":
            log("   ❌ FAIL: Organization name mismatch")
            return False
        if org_data.get("tier") != "starter":
            log("   ❌ FAIL: Organization tier mismatch")
            return False
        log("   ✓ Organization created correctly", 1)

        # Verify rate limits created
        rate_limits = self.db.collection("rate_limits").document(TEST_ORG_ID).get()
        if not rate_limits.exists:
            log("   ❌ FAIL: Rate limits not created")
            return False
        rl_data = rate_limits.to_dict()
        if rl_data.get("tier") != "starter":
            log("   ❌ FAIL: Rate limits tier mismatch")
            return False
        if rl_data.get("limits", {}).get("ai_requests_per_day") != 100:
            log("   ❌ FAIL: Rate limits values incorrect for starter tier")
            return False
        log("   ✓ Rate limits created with correct tier", 1)

        # Verify user created
        user = self.db.collection("users").document(TEST_OWNER_UID).get()
        if not user.exists:
            log("   ❌ FAIL: User not created")
            return False
        user_data = user.to_dict()
        if user_data.get("organization_id") != TEST_ORG_ID:
            log("   ❌ FAIL: User organization_id not set")
            return False
        if user_data.get("role") != "owner":
            log("   ❌ FAIL: User role not 'owner'")
            return False
        log("   ✓ User created with correct role", 1)

        log("   ✅ PASS: Bootstrap creates all required documents")
        return True

    async def test_bootstrap_idempotent(self) -> bool:
        """Test that bootstrap is idempotent (doesn't overwrite without force)."""
        log("TEST 2: Bootstrap is idempotent")

        from app.services.org_bootstrap_service import bootstrap_org, SubscriptionTier

        # Try to bootstrap again without force
        result = await bootstrap_org(
            org_id=TEST_ORG_ID,
            org_name="Different Name",
            owner_user_id="different_uid",
            owner_email="different@example.com",
            tier=SubscriptionTier.ENTERPRISE,  # Different tier
            force=False,
        )

        # Should return existing org, not overwrite
        if not result.success:
            log("   ❌ FAIL: Idempotent call returned success=False")
            return False

        if result.org_name != "Test Bootstrap Corp":
            log(f"   ❌ FAIL: Should return existing name, got {result.org_name}")
            return False

        if len(result.documents_created) > 0:
            log("   ❌ FAIL: Should not create new documents without force")
            return False

        # Verify original org unchanged
        org = self.db.collection("organizations").document(TEST_ORG_ID).get()
        org_data = org.to_dict()
        if org_data.get("tier") != "starter":
            log("   ❌ FAIL: Original tier was overwritten!")
            return False

        log("   ✅ PASS: Bootstrap is idempotent (returns existing, doesn't overwrite)")
        return True

    async def test_org_status_endpoint(self) -> bool:
        """Test that status endpoint returns correct data."""
        log("TEST 3: Status endpoint returns correct data")

        from app.services.org_bootstrap_service import get_org_status

        status = await get_org_status(TEST_ORG_ID)

        if status is None:
            log("   ❌ FAIL: Status returned None")
            return False

        if status.org_id != TEST_ORG_ID:
            log(f"   ❌ FAIL: Wrong org_id: {status.org_id}")
            return False

        if status.tier != "starter":
            log(f"   ❌ FAIL: Wrong tier: {status.tier}")
            return False

        if status.status != "ready":
            log(f"   ❌ FAIL: Status not 'ready': {status.status}")
            return False

        if status.rate_limits is None:
            log("   ❌ FAIL: Rate limits not in status")
            return False

        if status.counts is None:
            log("   ❌ FAIL: Counts not in status")
            return False

        log(f"   Status: tier={status.tier}, counts={status.counts}", 1)
        log("   ✅ PASS: Status endpoint returns correct data")
        return True

    async def test_bootstrap_with_sample_data(self) -> bool:
        """Test that bootstrap can seed sample data."""
        log("TEST 4: Bootstrap with sample data creates assets + PM rules")

        from app.services.org_bootstrap_service import bootstrap_org, SubscriptionTier

        # Bootstrap with sample data (force to overwrite)
        result = await bootstrap_org(
            org_id=TEST_ORG_ID,
            org_name="Sample Data Corp",
            owner_user_id=TEST_OWNER_UID,
            owner_email=TEST_OWNER_EMAIL,
            tier=SubscriptionTier.FREE,
            include_sample_data=True,  # KEY: Include sample data
            force=True,
        )

        if not result.success:
            log(f"   ❌ FAIL: Bootstrap with sample data failed: {result.message}")
            return False

        if result.sample_data_created is None:
            log("   ❌ FAIL: sample_data_created is None")
            return False

        assets_created = result.sample_data_created.get("assets", 0)
        pm_rules_created = result.sample_data_created.get("pm_rules", 0)

        log(f"   Created {assets_created} assets, {pm_rules_created} PM rules", 1)

        if assets_created < 1:
            log("   ❌ FAIL: No sample assets created")
            return False

        if pm_rules_created < 1:
            log("   ❌ FAIL: No sample PM rules created")
            return False

        # Verify assets in Firestore
        assets = list(
            self.db.collection("assets")
            .where("organization_id", "==", TEST_ORG_ID)
            .stream()
        )
        if len(assets) < 1:
            log("   ❌ FAIL: No assets found in Firestore")
            return False

        # Verify PM rules in Firestore
        pm_rules = list(
            self.db.collection("pm_schedule_rules")
            .where("organization_id", "==", TEST_ORG_ID)
            .stream()
        )
        if len(pm_rules) < 1:
            log("   ❌ FAIL: No PM rules found in Firestore")
            return False

        log("   ✅ PASS: Sample data created successfully")
        return True

    async def test_delete_organization(self) -> bool:
        """Test that delete removes all organization data."""
        log("TEST 5: Delete removes all organization data")

        from app.services.org_bootstrap_service import delete_org

        # Delete should work
        result = await delete_org(TEST_ORG_ID)

        if not result.success:
            log(f"   ❌ FAIL: Delete returned success=False: {result.error}")
            return False

        log(f"   Deleted counts: {result.deleted_counts}", 1)

        # Verify organization gone
        org = self.db.collection("organizations").document(TEST_ORG_ID).get()
        if org.exists:
            log("   ❌ FAIL: Organization still exists after delete")
            return False

        # Verify rate limits gone
        rl = self.db.collection("rate_limits").document(TEST_ORG_ID).get()
        if rl.exists:
            log("   ❌ FAIL: Rate limits still exist after delete")
            return False

        # Verify assets gone
        assets = list(
            self.db.collection("assets")
            .where("organization_id", "==", TEST_ORG_ID)
            .stream()
        )
        if len(assets) > 0:
            log("   ❌ FAIL: Assets still exist after delete")
            return False

        log("   ✅ PASS: Delete removes all organization data")
        return True

    async def run_tests(self) -> bool:
        """Run all E2E tests."""
        print("=" * 60)
        print("Organization Bootstrap End-to-End Test")
        print("=" * 60)
        print(f"Project:  {PROJECT_ID}")
        print(f"Test Org: {TEST_ORG_ID}")
        print()

        if not self.connect():
            return False

        # Clean before test
        self.cleanup()

        all_passed = True
        tests = [
            self.test_bootstrap_creates_org,
            self.test_bootstrap_idempotent,
            self.test_org_status_endpoint,
            self.test_bootstrap_with_sample_data,
            self.test_delete_organization,
        ]

        for test in tests:
            print()
            try:
                if not await test():
                    all_passed = False
            except Exception as e:
                log(f"   ❌ FAIL: Test threw exception: {e}")
                all_passed = False

        # Final cleanup
        print()
        self.cleanup()

        print()
        print("=" * 60)
        if all_passed:
            print("🎉 ALL TESTS PASSED")
            print()
            print("Verified:")
            print("  • Bootstrap creates org, rate limits, and user")
            print("  • Bootstrap is idempotent (safe to call multiple times)")
            print("  • Status endpoint returns correct data")
            print("  • Sample data option works")
            print("  • Delete removes all data")
            print()
            print("✅ Organization onboarding is production-ready!")
        else:
            print("⚠️  SOME TESTS FAILED")
        print("=" * 60)

        return all_passed


async def main():
    test = BootstrapE2ETest()
    success = await test.run_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
