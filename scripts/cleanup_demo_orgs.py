#!/usr/bin/env python3
"""
Demo Organization Cleanup Script
=================================

Cleans up expired demo organizations from Firestore.

This script should be run daily via Cloud Scheduler or cron job.
It finds all demo orgs with expires_at < now and deletes:
- The organization document
- All associated assets, work orders, PM rules, parts
- The demo user
- Rate limits document

Usage:
    # Run locally
    export GOOGLE_APPLICATION_CREDENTIALS="secrets/firebase-admin.json"
    python scripts/cleanup_demo_orgs.py

    # Or via Cloud Scheduler hitting the API endpoint:
    curl -X POST https://your-domain/api/v1/demo/cleanup \
        -H "X-Admin-Secret: your-secret"

Environment:
    GOOGLE_APPLICATION_CREDENTIALS - Path to Firebase admin credentials
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

# Add project root for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main():
    """Run the demo cleanup process."""
    from app.services.demo_service import demo_service

    print(f"\n{'='*60}")
    print("DEMO ORGANIZATION CLEANUP")
    print(f"{'='*60}")
    print(f"Started at: {datetime.now(timezone.utc).isoformat()}")

    try:
        result = await demo_service.cleanup_expired_demos()

        if result.get("success"):
            counts = result.get("counts", {})
            print(f"\nCleanup completed successfully!")
            print(f"  Organizations deleted: {counts.get('orgs', 0)}")
            print(f"  Users deleted: {counts.get('users', 0)}")
            print(f"  Assets deleted: {counts.get('assets', 0)}")
            print(f"  Work orders deleted: {counts.get('work_orders', 0)}")
            print(f"  PM rules deleted: {counts.get('pm_rules', 0)}")
            print(f"  Parts deleted: {counts.get('parts', 0)}")
        else:
            print(f"\nCleanup failed: {result.get('error')}")
            sys.exit(1)

    except Exception as e:
        print(f"\nError during cleanup: {e}")
        sys.exit(1)

    print(f"\nCompleted at: {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
