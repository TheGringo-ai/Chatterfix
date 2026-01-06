#!/usr/bin/env python3
"""
Quota Enforcement E2E Test
==========================

Tests that asset limits are enforced correctly using Firestore transactions.

Test Plan:
1. Bootstrap a new org with FREE tier (10 assets max)
2. Create 10 assets → should all succeed
3. Try to create 11th asset → should get 403 QuotaExceededError
4. Verify the count is exactly 10 (not 11)

Usage:
    export GOOGLE_APPLICATION_CREDENTIALS="secrets/firebase-admin.json"
    python scripts/test_quota_enforcement_e2e.py
"""
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone

# Add project root for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_quota_enforcement():
    """Test asset quota enforcement end-to-end."""
    from app.services.org_bootstrap_service import bootstrap_org, SubscriptionTier, TIER_LIMITS
    from app.services.quota_service import quota_service, QuotaExceededError
    from app.core.firestore_db import get_firestore_manager

    # Generate unique test identifiers
    test_id = uuid.uuid4().hex[:8]
    org_id = f"test_quota_{test_id}"
    owner_user_id = f"user_quota_{test_id}"
    owner_email = f"quota_test_{test_id}@example.com"
    org_name = f"Quota Test Org {test_id}"

    print(f"\n{'='*60}")
    print("QUOTA ENFORCEMENT E2E TEST")
    print(f"{'='*60}")
    print(f"Test ID: {test_id}")
    print(f"Org ID: {org_id}")

    firestore = get_firestore_manager()

    try:
        # ========================================
        # STEP 1: Bootstrap org with FREE tier
        # ========================================
        print(f"\n--- STEP 1: Bootstrap org with FREE tier ---")

        result = await bootstrap_org(
            org_id=org_id,
            org_name=org_name,
            owner_user_id=owner_user_id,
            owner_email=owner_email,
            tier=SubscriptionTier.FREE,
        )

        if not result.success:
            print(f"FAIL: Bootstrap failed: {result.error}")
            return False

        # Verify the tier and limits
        free_limits = TIER_LIMITS[SubscriptionTier.FREE]
        assets_max = free_limits["assets_max"]
        print(f"Org bootstrapped with FREE tier")
        print(f"Asset limit: {assets_max}")

        # Verify counts were initialized
        org_doc = await firestore.get_document("organizations", org_id)
        counts = org_doc.get("counts", {})
        print(f"Initial counts: {counts}")

        if counts.get("assets", 0) != 0:
            print(f"FAIL: Expected initial asset count of 0, got {counts.get('assets')}")
            return False

        print("PASS: Org bootstrapped with counts initialized to 0")

        # ========================================
        # STEP 2: Create assets up to limit
        # ========================================
        print(f"\n--- STEP 2: Create {assets_max} assets (should succeed) ---")

        for i in range(1, assets_max + 1):
            try:
                # Reserve slot via quota service
                await quota_service.reserve_asset_slot(org_id)

                # Create the actual asset document
                asset_data = {
                    "name": f"Test Asset {i}",
                    "organization_id": org_id,
                    "status": "Active",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                asset_id = await firestore.create_document("assets", asset_data)

                if i % 5 == 0 or i == assets_max:
                    print(f"  Created asset {i}/{assets_max}: {asset_id[:8]}...")

            except QuotaExceededError as e:
                print(f"FAIL: Unexpected quota exceeded at asset {i}: {e}")
                return False
            except Exception as e:
                print(f"FAIL: Error creating asset {i}: {e}")
                return False

        # Verify count is exactly at limit
        org_doc = await firestore.get_document("organizations", org_id)
        counts = org_doc.get("counts", {})
        current_count = counts.get("assets", 0)
        print(f"Current asset count: {current_count}/{assets_max}")

        if current_count != assets_max:
            print(f"FAIL: Expected count {assets_max}, got {current_count}")
            return False

        print(f"PASS: Successfully created {assets_max} assets")

        # ========================================
        # STEP 3: Try to create one more (should fail)
        # ========================================
        print(f"\n--- STEP 3: Try to create asset #{assets_max + 1} (should FAIL) ---")

        try:
            await quota_service.reserve_asset_slot(org_id)
            print(f"FAIL: Expected QuotaExceededError but slot was reserved!")
            return False

        except QuotaExceededError as e:
            print(f"PASS: Got expected QuotaExceededError")
            print(f"  Error: {e}")
            print(f"  Resource: {e.resource_type}")
            print(f"  Limit: {e.limit}")
            print(f"  Current: {e.current}")
            print(f"  Tier: {e.tier}")

            # Verify the error has the right info
            if e.resource_type != "assets":
                print(f"FAIL: Expected resource_type 'assets', got '{e.resource_type}'")
                return False
            if e.limit != assets_max:
                print(f"FAIL: Expected limit {assets_max}, got {e.limit}")
                return False
            if e.current != assets_max:
                print(f"FAIL: Expected current {assets_max}, got {e.current}")
                return False
            if e.tier != "free":
                print(f"FAIL: Expected tier 'free', got '{e.tier}'")
                return False

        except Exception as e:
            print(f"FAIL: Got unexpected error: {type(e).__name__}: {e}")
            return False

        # ========================================
        # STEP 4: Verify count didn't change
        # ========================================
        print(f"\n--- STEP 4: Verify count stayed at {assets_max} ---")

        org_doc = await firestore.get_document("organizations", org_id)
        counts = org_doc.get("counts", {})
        final_count = counts.get("assets", 0)

        if final_count != assets_max:
            print(f"FAIL: Count changed to {final_count} after failed reservation")
            return False

        print(f"PASS: Count correctly stayed at {final_count}")

        # ========================================
        # ALL TESTS PASSED
        # ========================================
        print(f"\n{'='*60}")
        print("ALL QUOTA ENFORCEMENT TESTS PASSED!")
        print(f"{'='*60}")
        return True

    finally:
        # ========================================
        # CLEANUP: Delete test data
        # ========================================
        print(f"\n--- CLEANUP: Removing test data ---")
        try:
            # Delete test assets
            if firestore.db:
                assets_query = firestore.db.collection("assets").where(
                    "organization_id", "==", org_id
                )
                deleted_assets = 0
                for doc in assets_query.stream():
                    doc.reference.delete()
                    deleted_assets += 1
                print(f"  Deleted {deleted_assets} test assets")

                # Delete rate limits
                firestore.db.collection("rate_limits").document(org_id).delete()
                print(f"  Deleted rate_limits/{org_id}")

                # Delete organization
                firestore.db.collection("organizations").document(org_id).delete()
                print(f"  Deleted organizations/{org_id}")

                # Delete test user
                firestore.db.collection("users").document(owner_user_id).delete()
                print(f"  Deleted users/{owner_user_id}")

        except Exception as e:
            print(f"  Cleanup warning: {e}")


async def test_release_slot():
    """Test that releasing slots decrements the count correctly."""
    from app.services.org_bootstrap_service import bootstrap_org, SubscriptionTier
    from app.services.quota_service import quota_service, QuotaExceededError
    from app.core.firestore_db import get_firestore_manager

    # Generate unique test identifiers
    test_id = uuid.uuid4().hex[:8]
    org_id = f"test_release_{test_id}"
    owner_user_id = f"user_release_{test_id}"
    owner_email = f"release_test_{test_id}@example.com"
    org_name = f"Release Test Org {test_id}"

    print(f"\n{'='*60}")
    print("SLOT RELEASE TEST")
    print(f"{'='*60}")

    firestore = get_firestore_manager()

    try:
        # Bootstrap org
        await bootstrap_org(
            org_id=org_id,
            org_name=org_name,
            owner_user_id=owner_user_id,
            owner_email=owner_email,
            tier=SubscriptionTier.FREE,
        )

        # Reserve 5 slots
        print("Reserving 5 asset slots...")
        for i in range(5):
            await quota_service.reserve_asset_slot(org_id)

        # Verify count is 5
        org_doc = await firestore.get_document("organizations", org_id)
        count = org_doc.get("counts", {}).get("assets", 0)
        print(f"Count after reserving 5: {count}")

        if count != 5:
            print(f"FAIL: Expected 5, got {count}")
            return False

        # Release 2 slots
        print("Releasing 2 slots...")
        await quota_service.release_asset_slot(org_id)
        await quota_service.release_asset_slot(org_id)

        # Verify count is 3
        org_doc = await firestore.get_document("organizations", org_id)
        count = org_doc.get("counts", {}).get("assets", 0)
        print(f"Count after releasing 2: {count}")

        if count != 3:
            print(f"FAIL: Expected 3, got {count}")
            return False

        print("PASS: Slot release works correctly")
        return True

    finally:
        # Cleanup
        print("Cleaning up...")
        try:
            if firestore.db:
                firestore.db.collection("rate_limits").document(org_id).delete()
                firestore.db.collection("organizations").document(org_id).delete()
                firestore.db.collection("users").document(owner_user_id).delete()
        except Exception as e:
            print(f"  Cleanup warning: {e}")


async def test_unlimited_tier():
    """Test that ENTERPRISE tier has unlimited assets (-1 limit)."""
    from app.services.org_bootstrap_service import bootstrap_org, SubscriptionTier, TIER_LIMITS
    from app.services.quota_service import quota_service
    from app.core.firestore_db import get_firestore_manager

    test_id = uuid.uuid4().hex[:8]
    org_id = f"test_unlimited_{test_id}"
    owner_user_id = f"user_unlimited_{test_id}"
    owner_email = f"unlimited_test_{test_id}@example.com"

    print(f"\n{'='*60}")
    print("UNLIMITED TIER TEST (ENTERPRISE)")
    print(f"{'='*60}")

    firestore = get_firestore_manager()

    try:
        # Verify enterprise has unlimited assets
        enterprise_limits = TIER_LIMITS[SubscriptionTier.ENTERPRISE]
        assets_max = enterprise_limits["assets_max"]
        print(f"Enterprise asset limit: {assets_max} (-1 = unlimited)")

        if assets_max != -1:
            print(f"FAIL: Expected -1 (unlimited), got {assets_max}")
            return False

        # Bootstrap with enterprise
        await bootstrap_org(
            org_id=org_id,
            org_name=f"Unlimited Test {test_id}",
            owner_user_id=owner_user_id,
            owner_email=owner_email,
            tier=SubscriptionTier.ENTERPRISE,
        )

        # Try to reserve 50 slots (way more than free tier allows)
        print("Reserving 50 asset slots (unlimited tier)...")
        for i in range(50):
            await quota_service.reserve_asset_slot(org_id)

        # Verify count is 50 (still tracked, just not limited)
        org_doc = await firestore.get_document("organizations", org_id)
        count = org_doc.get("counts", {}).get("assets", 0)
        print(f"Count after reserving 50: {count}")

        if count != 50:
            print(f"FAIL: Expected 50, got {count}")
            return False

        print("PASS: Unlimited tier allows unlimited reservations")
        return True

    finally:
        print("Cleaning up...")
        try:
            if firestore.db:
                firestore.db.collection("rate_limits").document(org_id).delete()
                firestore.db.collection("organizations").document(org_id).delete()
                firestore.db.collection("users").document(owner_user_id).delete()
        except Exception as e:
            print(f"  Cleanup warning: {e}")


def main():
    """Run all quota enforcement tests."""
    print("\n" + "=" * 60)
    print("QUOTA ENFORCEMENT TEST SUITE")
    print("=" * 60)

    results = []

    # Test 1: Basic quota enforcement
    result1 = asyncio.run(test_quota_enforcement())
    results.append(("Quota Enforcement", result1))

    # Test 2: Slot release
    result2 = asyncio.run(test_release_slot())
    results.append(("Slot Release", result2))

    # Test 3: Unlimited tier
    result3 = asyncio.run(test_unlimited_tier())
    results.append(("Unlimited Tier", result3))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    all_passed = True
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    main()
