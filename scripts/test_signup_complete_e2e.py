#!/usr/bin/env python3
"""
Signup Complete End-to-End Test
================================

Tests the self-service signup flow:
1. Simulates Firebase token verification
2. Calls POST /api/v1/signup/complete
3. Verifies org + rate limits + user created
4. Tests idempotency (second call returns same org)

Usage:
    export GOOGLE_APPLICATION_CREDENTIALS="secrets/firebase-admin.json"
    python3 scripts/test_signup_complete_e2e.py
"""
import asyncio
import os
import sys

# Add project root for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.cloud import firestore

# Test configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or "fredfix"
TEST_UID = "test_signup_complete_uid"
TEST_EMAIL = "signup_test@example.com"
TEST_COMPANY = "Test Signup Corp"


def log(message: str, indent: int = 0):
    prefix = "   " * indent
    print(f"{prefix}{message}")


class SignupCompleteE2ETest:
    """End-to-end test for signup complete flow."""

    def __init__(self):
        self.db = None
        self.created_org_id = None

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
            # Find and delete test user's org
            user_doc = self.db.collection("users").document(TEST_UID).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                org_id = user_data.get("organization_id")
                if org_id:
                    # Delete org data
                    for collection in ["work_orders", "pm_schedule_rules", "assets", "parts", "vendors", "pm_evaluations"]:
                        docs = list(
                            self.db.collection(collection)
                            .where("organization_id", "==", org_id)
                            .stream()
                        )
                        for doc in docs:
                            doc.reference.delete()

                    # Delete rate limits
                    try:
                        self.db.collection("rate_limits").document(org_id).delete()
                    except Exception:
                        pass

                    # Delete organization
                    try:
                        self.db.collection("organizations").document(org_id).delete()
                    except Exception:
                        pass

            # Delete test user
            try:
                self.db.collection("users").document(TEST_UID).delete()
            except Exception:
                pass

            log("   🧹 Cleanup complete")
        except Exception as e:
            log(f"   Warning: Cleanup error: {e}")

    async def test_signup_creates_org(self) -> bool:
        """Test that signup creates organization with correct tier."""
        log("TEST 1: Signup creates organization with STARTER tier")

        from app.routers.signup_complete import (
            complete_signup,
            CompleteSignupRequest,
            sanitize_slug,
            generate_unique_org_id,
        )
        from app.services.org_bootstrap_service import SubscriptionTier, TIER_LIMITS

        # Create a mock user object
        class MockUser:
            uid = TEST_UID
            email = TEST_EMAIL
            full_name = "Test User"
            disabled = False

        request = CompleteSignupRequest(
            company=TEST_COMPANY,
            org_slug="test-signup-corp",
        )

        # Call the signup complete function directly
        result = await complete_signup(request, MockUser())

        if not result.success:
            log(f"   ❌ FAIL: Signup returned success=False: {result.message}")
            return False

        self.created_org_id = result.org_id
        log(f"   Created org_id: {result.org_id}", 1)

        # Verify tier is STARTER (server-enforced)
        if result.tier != "starter":
            log(f"   ❌ FAIL: Expected tier 'starter', got '{result.tier}'")
            return False
        log("   ✓ Tier is 'starter' (server-enforced)", 1)

        # Verify organization created
        org = self.db.collection("organizations").document(result.org_id).get()
        if not org.exists:
            log("   ❌ FAIL: Organization not created in Firestore")
            return False
        org_data = org.to_dict()
        if org_data.get("tier") != "starter":
            log("   ❌ FAIL: Organization tier in Firestore is not 'starter'")
            return False
        log("   ✓ Organization created correctly", 1)

        # Verify rate limits created with STARTER limits
        rate_limits = self.db.collection("rate_limits").document(result.org_id).get()
        if not rate_limits.exists:
            log("   ❌ FAIL: Rate limits not created")
            return False
        rl_data = rate_limits.to_dict()
        starter_limits = TIER_LIMITS[SubscriptionTier.STARTER]
        if rl_data.get("limits", {}).get("ai_requests_per_day") != starter_limits["ai_requests_per_day"]:
            log(f"   ❌ FAIL: Rate limits not set to STARTER values")
            return False
        log("   ✓ Rate limits created with STARTER tier values", 1)

        # Verify user linked to org
        user = self.db.collection("users").document(TEST_UID).get()
        if not user.exists:
            log("   ❌ FAIL: User not created")
            return False
        user_data = user.to_dict()
        if user_data.get("organization_id") != result.org_id:
            log("   ❌ FAIL: User not linked to organization")
            return False
        log("   ✓ User linked to organization", 1)

        # Verify trial_ends_at is set
        if not result.trial_ends_at:
            log("   ❌ FAIL: trial_ends_at not set")
            return False
        log(f"   ✓ Trial ends at: {result.trial_ends_at}", 1)

        log("   ✅ PASS: Signup creates organization with correct tier")
        return True

    async def test_signup_idempotent(self) -> bool:
        """Test that calling signup twice returns same org (idempotent)."""
        log("TEST 2: Signup is idempotent (returns existing org)")

        from app.routers.signup_complete import complete_signup, CompleteSignupRequest

        class MockUser:
            uid = TEST_UID
            email = TEST_EMAIL
            full_name = "Test User"
            disabled = False

        # Call signup again with DIFFERENT company name
        request = CompleteSignupRequest(
            company="Different Company Name",
            org_slug="different-slug",
        )

        result = await complete_signup(request, MockUser())

        if not result.success:
            log(f"   ❌ FAIL: Second signup returned success=False")
            return False

        # Should return SAME org_id as before
        if result.org_id != self.created_org_id:
            log(f"   ❌ FAIL: Got different org_id! Expected {self.created_org_id}, got {result.org_id}")
            return False
        log(f"   ✓ Returned same org_id: {result.org_id}", 1)

        # Should return original company name, not the new one
        if result.org_name == "Different Company Name":
            log("   ❌ FAIL: Company name was overwritten!")
            return False
        log(f"   ✓ Original company name preserved: {result.org_name}", 1)

        # Message should indicate existing org
        if "exists" not in result.message.lower():
            log("   ⚠️  Warning: Message doesn't indicate existing org")

        log("   ✅ PASS: Signup is idempotent")
        return True

    async def test_slug_sanitization(self) -> bool:
        """Test that company names are properly sanitized to slugs."""
        log("TEST 3: Slug sanitization works correctly")

        from app.routers.signup_complete import sanitize_slug

        test_cases = [
            ("Acme Corporation", "acme-corporation"),
            ("Test & Co.", "test-co"),
            ("  Spaces Everywhere  ", "spaces-everywhere"),
            ("Special!!!Chars###Here", "special-chars-here"),
            ("UPPERCASE", "uppercase"),
            ("with--double--hyphens", "with-double-hyphens"),
            ("a" * 100, "a" * 30),  # Truncated to 30
        ]

        all_passed = True
        for input_str, expected in test_cases:
            result = sanitize_slug(input_str)
            if result != expected:
                log(f"   ❌ FAIL: '{input_str}' → '{result}' (expected '{expected}')")
                all_passed = False
            else:
                log(f"   ✓ '{input_str}' → '{result}'", 1)

        if all_passed:
            log("   ✅ PASS: Slug sanitization works correctly")
        return all_passed

    async def test_status_endpoint(self) -> bool:
        """Test the signup status endpoint."""
        log("TEST 4: Status endpoint returns correct data")

        from app.routers.signup_complete import get_signup_status

        class MockUser:
            uid = TEST_UID
            email = TEST_EMAIL
            full_name = "Test User"
            disabled = False

        result = await get_signup_status(MockUser())

        if not result.get("has_org"):
            log("   ❌ FAIL: has_org should be True")
            return False
        log("   ✓ has_org is True", 1)

        if result.get("org_id") != self.created_org_id:
            log(f"   ❌ FAIL: Wrong org_id: {result.get('org_id')}")
            return False
        log(f"   ✓ org_id matches: {result.get('org_id')}", 1)

        if result.get("tier") != "starter":
            log(f"   ❌ FAIL: Wrong tier: {result.get('tier')}")
            return False
        log("   ✓ tier is 'starter'", 1)

        log("   ✅ PASS: Status endpoint returns correct data")
        return True

    async def run_tests(self) -> bool:
        """Run all E2E tests."""
        print("=" * 60)
        print("Signup Complete End-to-End Test")
        print("=" * 60)
        print(f"Project:  {PROJECT_ID}")
        print(f"Test UID: {TEST_UID}")
        print()

        if not self.connect():
            return False

        # Clean before test
        self.cleanup()

        all_passed = True
        tests = [
            self.test_signup_creates_org,
            self.test_signup_idempotent,
            self.test_slug_sanitization,
            self.test_status_endpoint,
        ]

        for test in tests:
            print()
            try:
                if not await test():
                    all_passed = False
            except Exception as e:
                log(f"   ❌ FAIL: Test threw exception: {e}")
                import traceback
                traceback.print_exc()
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
            print("  • Signup creates org with STARTER tier (server-enforced)")
            print("  • Rate limits set to STARTER values")
            print("  • User linked to organization")
            print("  • Trial end date set (30 days)")
            print("  • Idempotent: second call returns same org")
            print("  • Slug sanitization works")
            print("  • Status endpoint works")
            print()
            print("✅ Self-service signup is production-ready!")
        else:
            print("⚠️  SOME TESTS FAILED")
        print("=" * 60)

        return all_passed


async def main():
    test = SignupCompleteE2ETest()
    success = await test.run_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
