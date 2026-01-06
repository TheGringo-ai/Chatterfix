#!/usr/bin/env python3
"""
Tier Management CLI
===================

Easy CLI for managing organization tiers.

Usage:
    # List all organizations
    python scripts/manage_tiers.py list

    # Show specific org
    python scripts/manage_tiers.py show acme-corp

    # Give enterprise for 30 days
    python scripts/manage_tiers.py set acme-corp enterprise --days 30

    # Permanent professional upgrade
    python scripts/manage_tiers.py set acme-corp professional

    # Downgrade to free
    python scripts/manage_tiers.py set acme-corp free

    # Extend trial by 14 days
    python scripts/manage_tiers.py extend acme-corp 14

    # Process expired trials (downgrade to free)
    python scripts/manage_tiers.py process-expired

Environment:
    export GOOGLE_APPLICATION_CREDENTIALS="secrets/firebase-admin.json"
"""
import argparse
import asyncio
import os
import sys
from datetime import datetime

# Add project root for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def format_date(iso_str):
    """Format ISO date string for display."""
    if not iso_str:
        return "Never"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return iso_str


def print_org_table(orgs):
    """Print organizations in a nice table format."""
    if not orgs:
        print("No organizations found.")
        return

    # Header
    print()
    print(f"{'ORG ID':<30} {'NAME':<25} {'TIER':<12} {'EXPIRES':<20} {'STATUS'}")
    print("-" * 110)

    for org in orgs:
        org_id = org.get("org_id", "")[:29]
        name = org.get("name", "")[:24]
        tier = org.get("tier", "free")
        expires = org.get("tier_expires_at")
        days = org.get("days_remaining")
        is_expired = org.get("is_expired", False)
        is_demo = org.get("is_demo", False)

        # Status
        if is_demo:
            status = "DEMO"
        elif is_expired:
            status = "EXPIRED"
        elif days is not None:
            status = f"{days} days left"
        else:
            status = "Permanent"

        # Expires display
        if expires:
            expires_display = format_date(expires)[:19]
        else:
            expires_display = "Never"

        print(f"{org_id:<30} {name:<25} {tier:<12} {expires_display:<20} {status}")

    print()
    print(f"Total: {len(orgs)} organizations")


def print_org_detail(info):
    """Print detailed org info."""
    print()
    print("=" * 60)
    print(f"Organization: {info.get('org_id')}")
    print("=" * 60)
    print(f"  Name:         {info.get('org_name')}")
    print(f"  Owner:        {info.get('owner_email')}")
    print(f"  Tier:         {info.get('tier')}")
    print(f"  Expires:      {format_date(info.get('tier_expires_at'))}")
    print(f"  Is Trial:     {info.get('is_trial')}")
    if info.get("days_remaining") is not None:
        print(f"  Days Left:    {info.get('days_remaining')}")
    print(f"  Created:      {format_date(info.get('created_at'))}")
    print()
    print("  Limits:")
    limits = info.get("limits", {})
    for key, value in limits.items():
        display = "Unlimited" if value == -1 else value
        print(f"    {key}: {display}")
    print()
    if info.get("usage"):
        print("  Current Usage:")
        usage = info.get("usage", {})
        for key, value in usage.items():
            print(f"    {key}: {value}")
    print()


async def cmd_list(args):
    """List all organizations."""
    from app.services.tier_management_service import get_tier_manager

    manager = get_tier_manager()
    orgs = await manager.list_orgs(
        tier_filter=args.tier,
        include_expired=not args.active_only,
        limit=args.limit,
    )
    print_org_table(orgs)


async def cmd_show(args):
    """Show specific organization."""
    from app.services.tier_management_service import get_tier_manager

    manager = get_tier_manager()
    info = await manager.get_org_tier_info(args.org_id)

    if not info:
        print(f"Organization '{args.org_id}' not found.")
        sys.exit(1)

    print_org_detail(info)


async def cmd_set(args):
    """Set organization tier."""
    from app.services.tier_management_service import get_tier_manager

    manager = get_tier_manager()

    print(f"Setting {args.org_id} to tier '{args.tier}'", end="")
    if args.days:
        print(f" for {args.days} days...")
    else:
        print(" (permanent)...")

    result = await manager.set_tier(
        org_id=args.org_id,
        tier=args.tier,
        trial_days=args.days,
        reason=args.reason or "cli_change",
    )

    if result.get("success"):
        print(f"✅ {result.get('message')}")
        print(f"   New limits: {result.get('limits')}")
    else:
        print(f"❌ Error: {result.get('error')}")
        sys.exit(1)


async def cmd_extend(args):
    """Extend organization trial."""
    from app.services.tier_management_service import get_tier_manager

    manager = get_tier_manager()

    print(f"Extending {args.org_id} trial by {args.days} days...")

    result = await manager.extend_trial(
        org_id=args.org_id,
        additional_days=args.days,
    )

    if result.get("success"):
        print(f"✅ {result.get('message')}")
        print(f"   New expiration: {format_date(result.get('new_expires_at'))}")
    else:
        print(f"❌ Error: {result.get('error')}")
        sys.exit(1)


async def cmd_process_expired(args):
    """Process expired trials."""
    from app.services.tier_management_service import get_tier_manager

    manager = get_tier_manager()

    print("Processing expired trials...")

    result = await manager.process_expired_trials()

    if result.get("success"):
        count = result.get("downgraded_count", 0)
        print(f"✅ Processed {count} expired organizations")
        if count > 0:
            print("\nDowngraded:")
            for org in result.get("downgraded", []):
                print(f"  - {org.get('org_id')}: {org.get('previous_tier')} → free")
    else:
        print(f"❌ Error: {result.get('error')}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="ChatterFix Tier Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all organizations
  python scripts/manage_tiers.py list

  # Show specific org
  python scripts/manage_tiers.py show acme-corp

  # Give enterprise for 30 days
  python scripts/manage_tiers.py set acme-corp enterprise --days 30

  # Permanent professional upgrade
  python scripts/manage_tiers.py set acme-corp professional

  # Downgrade to free
  python scripts/manage_tiers.py set acme-corp free

  # Extend trial by 14 days
  python scripts/manage_tiers.py extend acme-corp 14

  # Process expired trials
  python scripts/manage_tiers.py process-expired
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # List command
    list_parser = subparsers.add_parser("list", help="List all organizations")
    list_parser.add_argument("--tier", help="Filter by tier")
    list_parser.add_argument("--active-only", action="store_true", help="Hide expired trials")
    list_parser.add_argument("--limit", type=int, default=100, help="Max orgs to show")

    # Show command
    show_parser = subparsers.add_parser("show", help="Show organization details")
    show_parser.add_argument("org_id", help="Organization ID")

    # Set command
    set_parser = subparsers.add_parser("set", help="Set organization tier")
    set_parser.add_argument("org_id", help="Organization ID")
    set_parser.add_argument("tier", choices=["free", "starter", "professional", "enterprise"])
    set_parser.add_argument("--days", type=int, help="Trial days (omit for permanent)")
    set_parser.add_argument("--reason", help="Reason for change")

    # Extend command
    extend_parser = subparsers.add_parser("extend", help="Extend trial period")
    extend_parser.add_argument("org_id", help="Organization ID")
    extend_parser.add_argument("days", type=int, help="Days to add")

    # Process expired command
    subparsers.add_parser("process-expired", help="Downgrade expired trials to free")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Run the appropriate command
    if args.command == "list":
        asyncio.run(cmd_list(args))
    elif args.command == "show":
        asyncio.run(cmd_show(args))
    elif args.command == "set":
        asyncio.run(cmd_set(args))
    elif args.command == "extend":
        asyncio.run(cmd_extend(args))
    elif args.command == "process-expired":
        asyncio.run(cmd_process_expired(args))


if __name__ == "__main__":
    main()
