#!/usr/bin/env python3
"""
Demo Organization Cleanup Script

This script cleans up expired demo organizations and their associated data.
It should be run periodically (e.g., every hour via cron or Cloud Scheduler).

Usage:
    python scripts/cleanup_expired_demos.py

For Cloud Functions deployment, use the cloud_function_entry_point().
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def cleanup_expired_demos() -> dict:
    """Main cleanup function that removes expired demo organizations."""
    from app.services.organization_service import OrganizationService

    logger.info("Starting demo cleanup process...")
    start_time = datetime.now()

    org_service = OrganizationService()

    try:
        # Cleanup expired demos
        deleted_count = await org_service.cleanup_expired_demos()

        elapsed = (datetime.now() - start_time).total_seconds()

        result = {
            "success": True,
            "deleted_count": deleted_count,
            "elapsed_seconds": elapsed,
            "timestamp": datetime.now().isoformat(),
        }

        if deleted_count > 0:
            logger.info(
                f"Cleanup complete: Deleted {deleted_count} expired demo organizations in {elapsed:.2f}s"
            )
        else:
            logger.info(
                f"Cleanup complete: No expired demos found (checked in {elapsed:.2f}s)"
            )

        return result

    except Exception as e:
        logger.error(f"Cleanup failed with error: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


def cloud_function_entry_point(request):
    """
    Google Cloud Function entry point.

    Deploy with:
        gcloud functions deploy cleanup-expired-demos \
            --runtime python311 \
            --trigger-http \
            --entry-point cloud_function_entry_point \
            --source . \
            --set-env-vars GOOGLE_CLOUD_PROJECT=fredfix

    Or schedule with Cloud Scheduler:
        gcloud scheduler jobs create http cleanup-demos-hourly \
            --schedule="0 * * * *" \
            --uri="https://REGION-PROJECT.cloudfunctions.net/cleanup-expired-demos" \
            --http-method=POST
    """
    from flask import jsonify

    result = asyncio.run(cleanup_expired_demos())

    status_code = 200 if result.get("success") else 500
    return jsonify(result), status_code


# Alternative entry point for Cloud Functions Gen 2
try:
    import functions_framework

    @functions_framework.http
    def cleanup_demos_http(request):
        """HTTP Cloud Function entry point."""
        result = asyncio.run(cleanup_expired_demos())
        return result, 200 if result.get("success") else 500

except ImportError:
    pass  # functions_framework not available (local development)


async def get_demo_statistics() -> dict:
    """Get statistics about demo organizations for monitoring."""
    from app.services.organization_service import OrganizationService

    org_service = OrganizationService()

    if not org_service.db:
        return {"error": "Database not available"}

    try:
        # Count active demos
        active_demos = (
            org_service.db.collection("organizations")
            .where("is_demo", "==", True)
            .stream()
        )

        active_count = 0
        expiring_soon = 0  # Within 6 hours
        total_minutes_remaining = 0

        now = datetime.now()

        for doc in active_demos:
            data = doc.to_dict()
            active_count += 1

            expires_at = data.get("expires_at")
            if expires_at:
                if hasattr(expires_at, "timestamp"):
                    expires_at = datetime.fromtimestamp(expires_at.timestamp())

                remaining = (expires_at - now).total_seconds() / 60
                if remaining > 0:
                    total_minutes_remaining += remaining
                    if remaining <= 360:  # 6 hours
                        expiring_soon += 1

        avg_remaining = (
            total_minutes_remaining / active_count if active_count > 0 else 0
        )

        return {
            "active_demo_count": active_count,
            "expiring_soon_count": expiring_soon,
            "average_minutes_remaining": round(avg_remaining, 1),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get demo statistics: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    # Run cleanup when executed directly
    print("Demo Organization Cleanup Script")
    print("=" * 40)

    # Check for stats flag
    if len(sys.argv) > 1 and sys.argv[1] == "--stats":
        print("\nGathering demo statistics...\n")
        stats = asyncio.run(get_demo_statistics())

        if "error" not in stats:
            print(f"Active Demo Organizations: {stats['active_demo_count']}")
            print(f"Expiring within 6 hours: {stats['expiring_soon_count']}")
            print(
                f"Average time remaining: {stats['average_minutes_remaining']} minutes"
            )
        else:
            print(f"Error: {stats['error']}")
    else:
        print("\nRunning cleanup...\n")
        result = asyncio.run(cleanup_expired_demos())

        if result.get("success"):
            print(f"Success! Deleted {result['deleted_count']} expired demo(s)")
        else:
            print(f"Failed: {result.get('error')}")

        print(f"\nCompleted at: {result['timestamp']}")
