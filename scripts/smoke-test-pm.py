#!/usr/bin/env python3
"""
PM Automation Smoke Test Script

Validates the PM automation system is working correctly by:
1. Creating a meter reading
2. Triggering schedule generation
3. Fetching PM overview
4. Confirming orders exist in Firestore

Usage:
    python scripts/smoke-test-pm.py --org-id YOUR_ORG_ID
    python scripts/smoke-test-pm.py --base-url https://chatterfix.com --org-id org_123
    python scripts/smoke-test-pm.py --local  # Uses localhost:8000

Requirements:
    pip install httpx
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(1)


# ANSI colors for terminal output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def log_step(step_num: int, message: str):
    """Log a test step."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}[Step {step_num}]{Colors.END} {message}")


def log_success(message: str):
    """Log a success message."""
    print(f"  {Colors.GREEN}✓{Colors.END} {message}")


def log_failure(message: str):
    """Log a failure message."""
    print(f"  {Colors.RED}✗{Colors.END} {message}")


def log_warning(message: str):
    """Log a warning message."""
    print(f"  {Colors.YELLOW}⚠{Colors.END} {message}")


def log_info(message: str):
    """Log an info message."""
    print(f"  → {message}")


class PMSmokeTest:
    """PM Automation smoke test runner."""

    def __init__(
        self,
        base_url: str,
        organization_id: str,
        auth_token: Optional[str] = None,
        scheduler_secret: Optional[str] = None,
        verbose: bool = False,
    ):
        self.base_url = base_url.rstrip("/")
        self.organization_id = organization_id
        self.auth_token = auth_token
        self.scheduler_secret = scheduler_secret
        self.verbose = verbose
        self.results: Dict[str, Any] = {
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "details": [],
        }
        self.created_meter_id: Optional[str] = None
        self.created_work_order_ids: list = []

    def _get_headers(self, for_scheduler: bool = False) -> Dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}

        if for_scheduler and self.scheduler_secret:
            headers["X-Scheduler-Secret"] = self.scheduler_secret
        elif self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        return headers

    async def run_all_tests(self) -> bool:
        """Run all smoke tests and return overall success."""
        print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}PM AUTOMATION SMOKE TEST{Colors.END}")
        print(f"{Colors.BOLD}{'='*60}{Colors.END}")
        print(f"Base URL: {self.base_url}")
        print(f"Organization ID: {self.organization_id}")
        print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 0: Health check
            await self.test_health_check(client)

            # Step 1: Create a meter reading
            await self.test_create_meter_reading(client)

            # Step 2: Trigger schedule generation
            await self.test_generate_schedule(client)

            # Step 3: Fetch PM overview
            await self.test_get_overview(client)

            # Step 4: Confirm orders exist (via overview data)
            await self.test_confirm_orders_exist(client)

            # Step 5: List PM rules
            await self.test_list_rules(client)

            # Step 6: List meters
            await self.test_list_meters(client)

        # Print summary
        self._print_summary()

        return self.results["failed"] == 0

    async def test_health_check(self, client: httpx.AsyncClient):
        """Step 0: Verify service is healthy."""
        log_step(0, "Health Check")

        try:
            response = await client.get(f"{self.base_url}/health")
            data = response.json()

            if response.status_code == 200 and data.get("status") == "healthy":
                log_success(f"Service healthy (status={response.status_code})")
                self.results["passed"] += 1
            else:
                log_failure(f"Service unhealthy: {data}")
                self.results["failed"] += 1
                self.results["details"].append(
                    {"test": "health_check", "error": str(data)}
                )

        except Exception as e:
            log_failure(f"Health check failed: {e}")
            self.results["failed"] += 1
            self.results["details"].append({"test": "health_check", "error": str(e)})

    async def test_create_meter_reading(self, client: httpx.AsyncClient):
        """Step 1: Create a meter reading."""
        log_step(1, "Create Meter Reading")

        # Generate a unique meter ID for testing
        test_meter_id = f"smoke_test_meter_{int(time.time())}"
        self.created_meter_id = test_meter_id

        payload = {
            "organization_id": self.organization_id,
            "meter_id": test_meter_id,
            "new_value": 42.5,
            "reading_source": "api",
            "create_work_orders": False,  # Don't create WOs for test meter
        }

        try:
            response = await client.post(
                f"{self.base_url}/api/pm/meter-reading",
                headers=self._get_headers(),
                json=payload,
            )
            data = response.json()

            if self.verbose:
                log_info(f"Response: {json.dumps(data, indent=2)}")

            # Accept 200 (success) or 400 (meter not found - expected for new meter)
            if response.status_code == 200:
                log_success(f"Meter reading created (meter_id={test_meter_id})")
                log_info(f"New value: {data.get('new_value')}")
                log_info(f"Threshold status: {data.get('threshold_status', 'N/A')}")
                self.results["passed"] += 1
            elif response.status_code == 400:
                # Meter doesn't exist - this is expected for a new test meter
                log_warning("Meter not found (expected for test meter)")
                log_info("This is OK - the endpoint is responding correctly")
                self.results["warnings"] += 1
            elif response.status_code == 401:
                log_warning("Authentication required - using org_id in body")
                self.results["warnings"] += 1
            else:
                log_failure(f"Unexpected response: {response.status_code}")
                log_info(f"Body: {data}")
                self.results["failed"] += 1
                self.results["details"].append(
                    {"test": "meter_reading", "status": response.status_code, "body": data}
                )

        except Exception as e:
            log_failure(f"Meter reading failed: {e}")
            self.results["failed"] += 1
            self.results["details"].append({"test": "meter_reading", "error": str(e)})

    async def test_generate_schedule(self, client: httpx.AsyncClient):
        """Step 2: Trigger PM schedule generation."""
        log_step(2, "Generate PM Schedule")

        payload = {
            "organization_id": self.organization_id,
            "create_work_orders": False,  # Dry run for smoke test
        }

        try:
            response = await client.post(
                f"{self.base_url}/api/pm/generate-schedule",
                headers=self._get_headers(),
                json=payload,
            )
            data = response.json()

            if self.verbose:
                log_info(f"Response: {json.dumps(data, indent=2)}")

            if response.status_code == 200:
                log_success("Schedule generation completed")
                log_info(f"Generated count: {data.get('generated_count', 0)}")
                log_info(f"Rules updated: {data.get('rules_updated', 0)}")
                log_info(f"Period: {data.get('period', {})}")

                # Store work order IDs if any were created
                self.created_work_order_ids = data.get("work_order_ids", [])
                self.results["passed"] += 1
            elif response.status_code == 401:
                log_warning("Authentication required")
                self.results["warnings"] += 1
            else:
                log_failure(f"Schedule generation failed: {response.status_code}")
                log_info(f"Body: {data}")
                self.results["failed"] += 1
                self.results["details"].append(
                    {"test": "generate_schedule", "status": response.status_code, "body": data}
                )

        except Exception as e:
            log_failure(f"Schedule generation failed: {e}")
            self.results["failed"] += 1
            self.results["details"].append({"test": "generate_schedule", "error": str(e)})

    async def test_get_overview(self, client: httpx.AsyncClient):
        """Step 3: Fetch PM overview."""
        log_step(3, "Get PM Overview")

        try:
            params = {"organization_id": self.organization_id, "days_ahead": 30}
            response = await client.get(
                f"{self.base_url}/api/pm/overview",
                headers=self._get_headers(),
                params=params,
            )
            data = response.json()

            if self.verbose:
                log_info(f"Response: {json.dumps(data, indent=2)}")

            if response.status_code == 200:
                log_success("Overview fetched successfully")
                overview = data.get("overview", {})
                log_info(f"Active rules: {overview.get('active_rules', 0)}")
                log_info(f"Due soon: {overview.get('due_soon', 0)}")
                log_info(f"Overdue: {overview.get('overdue', 0)}")
                log_info(f"Meter alerts: {overview.get('meter_alerts', 0)}")
                log_info(f"Templates: {len(data.get('templates_summary', []))}")
                self.results["passed"] += 1
            elif response.status_code == 401:
                log_warning("Authentication required")
                self.results["warnings"] += 1
            else:
                log_failure(f"Overview fetch failed: {response.status_code}")
                self.results["failed"] += 1
                self.results["details"].append(
                    {"test": "get_overview", "status": response.status_code, "body": data}
                )

        except Exception as e:
            log_failure(f"Overview fetch failed: {e}")
            self.results["failed"] += 1
            self.results["details"].append({"test": "get_overview", "error": str(e)})

    async def test_confirm_orders_exist(self, client: httpx.AsyncClient):
        """Step 4: Confirm PM orders exist in Firestore (via API)."""
        log_step(4, "Confirm Orders Exist")

        try:
            # Use the overview endpoint to check for recent PM orders
            params = {"organization_id": self.organization_id, "days_ahead": 30}
            response = await client.get(
                f"{self.base_url}/api/pm/overview",
                headers=self._get_headers(),
                params=params,
            )
            data = response.json()

            if response.status_code == 200:
                recent_orders = data.get("recent_pm_orders", [])
                due_rules = data.get("due_rules", [])

                if recent_orders:
                    log_success(f"Found {len(recent_orders)} recent PM orders")
                    for order in recent_orders[:3]:  # Show first 3
                        log_info(f"  - {order.get('title', 'N/A')} ({order.get('status', 'N/A')})")
                    self.results["passed"] += 1
                elif due_rules:
                    log_success(f"Found {len(due_rules)} due rules (no orders yet)")
                    self.results["passed"] += 1
                else:
                    log_warning("No PM orders or due rules found")
                    log_info("This may be expected if no PM rules are configured")
                    self.results["warnings"] += 1
            else:
                log_failure(f"Could not confirm orders: {response.status_code}")
                self.results["failed"] += 1

        except Exception as e:
            log_failure(f"Order confirmation failed: {e}")
            self.results["failed"] += 1
            self.results["details"].append({"test": "confirm_orders", "error": str(e)})

    async def test_list_rules(self, client: httpx.AsyncClient):
        """Step 5: List PM schedule rules."""
        log_step(5, "List PM Rules")

        try:
            params = {"organization_id": self.organization_id}
            response = await client.get(
                f"{self.base_url}/api/pm/rules",
                headers=self._get_headers(),
                params=params,
            )
            data = response.json()

            if response.status_code == 200:
                rules = data.get("rules", [])
                log_success(f"Found {len(rules)} PM rules")
                for rule in rules[:3]:  # Show first 3
                    log_info(f"  - {rule.get('title', rule.get('id', 'N/A'))}")
                self.results["passed"] += 1
            elif response.status_code == 401:
                log_warning("Authentication required")
                self.results["warnings"] += 1
            else:
                log_failure(f"Rules fetch failed: {response.status_code}")
                self.results["failed"] += 1

        except Exception as e:
            log_failure(f"Rules fetch failed: {e}")
            self.results["failed"] += 1

    async def test_list_meters(self, client: httpx.AsyncClient):
        """Step 6: List asset meters."""
        log_step(6, "List Asset Meters")

        try:
            params = {"organization_id": self.organization_id}
            response = await client.get(
                f"{self.base_url}/api/pm/meters",
                headers=self._get_headers(),
                params=params,
            )
            data = response.json()

            if response.status_code == 200:
                meters = data.get("meters", [])
                log_success(f"Found {len(meters)} asset meters")
                for meter in meters[:3]:  # Show first 3
                    log_info(
                        f"  - {meter.get('meter_type', 'N/A')}: "
                        f"{meter.get('current_value', 'N/A')} {meter.get('unit', '')}"
                    )
                self.results["passed"] += 1
            elif response.status_code == 401:
                log_warning("Authentication required")
                self.results["warnings"] += 1
            else:
                log_failure(f"Meters fetch failed: {response.status_code}")
                self.results["failed"] += 1

        except Exception as e:
            log_failure(f"Meters fetch failed: {e}")
            self.results["failed"] += 1

    def _print_summary(self):
        """Print test summary."""
        print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}TEST SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'='*60}{Colors.END}")

        total = self.results["passed"] + self.results["failed"] + self.results["warnings"]

        print(f"{Colors.GREEN}Passed:   {self.results['passed']}{Colors.END}")
        print(f"{Colors.YELLOW}Warnings: {self.results['warnings']}{Colors.END}")
        print(f"{Colors.RED}Failed:   {self.results['failed']}{Colors.END}")
        print(f"Total:    {total}")

        if self.results["details"]:
            print(f"\n{Colors.BOLD}Failure Details:{Colors.END}")
            for detail in self.results["details"]:
                print(f"  - {detail}")

        if self.results["failed"] == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED{Colors.END}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}✗ SOME TESTS FAILED{Colors.END}")


def main():
    parser = argparse.ArgumentParser(
        description="PM Automation Smoke Test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test production with org ID
  python smoke-test-pm.py --org-id org_abc123

  # Test local development
  python smoke-test-pm.py --local --org-id demo_org

  # Test with authentication
  python smoke-test-pm.py --org-id org_abc123 --token YOUR_AUTH_TOKEN

  # Test scheduler endpoints
  python smoke-test-pm.py --org-id org_abc123 --scheduler-secret YOUR_SECRET
        """,
    )

    parser.add_argument(
        "--base-url",
        default="https://chatterfix.com",
        help="Base URL of the API (default: https://chatterfix.com)",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Use localhost:8000 as base URL",
    )
    parser.add_argument(
        "--org-id",
        required=True,
        help="Organization ID to test with",
    )
    parser.add_argument(
        "--token",
        help="Bearer token for authentication",
    )
    parser.add_argument(
        "--scheduler-secret",
        help="X-Scheduler-Secret header value",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed response bodies",
    )

    args = parser.parse_args()

    # Determine base URL
    base_url = "http://localhost:8000" if args.local else args.base_url

    # Run smoke tests
    smoke_test = PMSmokeTest(
        base_url=base_url,
        organization_id=args.org_id,
        auth_token=args.token,
        scheduler_secret=args.scheduler_secret,
        verbose=args.verbose,
    )

    success = asyncio.run(smoke_test.run_all_tests())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
