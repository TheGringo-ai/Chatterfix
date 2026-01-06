#!/usr/bin/env python3
"""
One-time script to seed default rate limits to Firestore.
Run this after deploying the rate limiting system.

Usage:
    python scripts/seed_rate_limits.py
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment for Firestore
os.environ.setdefault("USE_FIRESTORE", "true")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "fredfix")


async def main():
    print("=" * 60)
    print("ChatterFix Rate Limit Seeder")
    print("=" * 60)

    try:
        from app.services.rate_limit_service import seed_default_rate_limits, DEFAULT_LIMITS

        print("\nDefault rate limit tiers:")
        for plan, config in DEFAULT_LIMITS.items():
            print(f"  {plan}: {config.requests_per_minute} rpm, {config.burst_limit} burst")

        print("\nSeeding to Firestore...")
        success = await seed_default_rate_limits()

        if success:
            print("\n✅ Successfully seeded default rate limits!")
            print("\nYou can verify at: https://console.cloud.google.com/firestore/databases/-default-/data/panel/rate_limits?project=fredfix")
            print("\nRate limiting is now active:")
            print("  - Public users: 30 requests/minute")
            print("  - Trial users: 120 requests/minute")
            print("  - Pro users: 600 requests/minute")
            print("  - Enterprise users: 3000 requests/minute")
        else:
            print("\n❌ Failed to seed rate limits. Check logs for details.")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
