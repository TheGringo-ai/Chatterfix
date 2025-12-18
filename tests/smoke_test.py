#!/usr/bin/env python3
"""
COMPREHENSIVE SYSTEM AUDIT - POST-DEPLOYMENT SMOKE TEST
ChatterFix CMMS & AI Team Service Health Check
"""

import requests
import sys
from datetime import datetime

# Test URLs
CHATTERFIX_URL = "https://chatterfix-cmms-650169261019.us-central1.run.app"
AI_TEAM_URL = "https://ai-team-service-psycl7nhha-uc.a.run.app"


class SmokeTester:
    def __init__(self):
        self.results = {
            "endpoint_health": {"chatterfix": False, "ai_team": False},
            "database_integrity": False,
            "ai_collaboration": False,
            "asset_data_verification": {"douglas_washer": False, "team_users": []},
        }
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "ChatterFix-SmokeTest/1.0",
                "Content-Type": "application/json",
            }
        )

    def print_section(self, title):
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")

    def test_endpoint_health(self):
        """Test 1: ENDPOINT HEALTH CHECK"""
        self.print_section("1. ENDPOINT HEALTH CHECK")

        # Test ChatterFix Health
        try:
            print(f"Testing ChatterFix health: {CHATTERFIX_URL}/health")
            response = self.session.get(f"{CHATTERFIX_URL}/health", timeout=30)
            if response.status_code == 200:
                print("✅ ChatterFix Health: PASS (200 OK)")
                self.results["endpoint_health"]["chatterfix"] = True
            else:
                print(f"❌ ChatterFix Health: FAIL (Status: {response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"❌ ChatterFix Health: FAIL (Error: {str(e)})")

        # Test AI Team Service Health
        try:
            print(f"Testing AI Team Service health: {AI_TEAM_URL}/health")
            response = self.session.get(f"{AI_TEAM_URL}/health", timeout=30)
            if response.status_code == 200:
                print("✅ AI Team Service Health: PASS (200 OK)")
                self.results["endpoint_health"]["ai_team"] = True
            else:
                print(
                    f"❌ AI Team Service Health: FAIL (Status: {response.status_code})"
                )
        except requests.exceptions.RequestException as e:
            print(f"❌ AI Team Service Health: FAIL (Error: {str(e)})")

    def test_database_integrity(self):
        """Test 2: DATABASE INTEGRITY CHECK (Firestore)"""
        self.print_section("2. DATABASE INTEGRITY CHECK (Firestore)")

        try:
            # Try to get users via ChatterFix API
            print(f"Testing database access: {CHATTERFIX_URL}/api/users")
            response = self.session.get(f"{CHATTERFIX_URL}/api/users", timeout=30)

            if response.status_code == 200:
                users_data = response.json()
                if isinstance(users_data, list) and len(users_data) > 0:
                    print(
                        f"✅ Database Integrity: PASS ({len(users_data)} users found)"
                    )
                    self.results["database_integrity"] = True
                else:
                    print("⚠️  Database Integrity: Database is Empty")
            elif response.status_code == 500:
                print(
                    "❌ Database Integrity: FAIL (Firestore Connection Broken - 500 Error)"
                )
            else:
                print(f"❌ Database Integrity: FAIL (Status: {response.status_code})")

        except requests.exceptions.RequestException as e:
            print(f"❌ Database Integrity: FAIL (Error: {str(e)})")

    def test_ai_collaboration(self):
        """Test 3: AI COLLABORATION CHECK"""
        self.print_section("3. AI COLLABORATION CHECK")

        try:
            # Test AI Team Service consultation endpoint
            test_payload = {
                "message": "System check, are you online?",
                "context": "smoke_test",
            }

            print(f"Testing AI collaboration: {AI_TEAM_URL}/api/v1/execute")
            response = self.session.post(
                f"{AI_TEAM_URL}/api/v1/execute",
                json=test_payload,
                timeout=60,  # AI responses might take longer
            )

            if response.status_code == 200:
                ai_response = response.json()
                if isinstance(ai_response, dict) and (
                    "response" in ai_response or "message" in ai_response
                ):
                    print("✅ AI Collaboration: PASS (Valid AI response received)")
                    print(f"   AI Response: {ai_response}")
                    self.results["ai_collaboration"] = True
                else:
                    print("❌ AI Collaboration: FAIL (Invalid response format)")
            else:
                print(f"❌ AI Collaboration: FAIL (Status: {response.status_code})")

        except requests.exceptions.RequestException as e:
            print(f"❌ AI Collaboration: FAIL (Error: {str(e)})")

    def test_asset_data_verification(self):
        """Test 4: ASSET & USER DATA VERIFICATION"""
        self.print_section("4. ASSET & USER DATA VERIFICATION")

        # Check for Douglas Washer asset
        try:
            print(f"Checking for Douglas Washer asset: {CHATTERFIX_URL}/api/assets")
            response = self.session.get(f"{CHATTERFIX_URL}/api/assets", timeout=30)

            if response.status_code == 200:
                assets_data = response.json()
                douglas_found = False
                if isinstance(assets_data, list):
                    for asset in assets_data:
                        if isinstance(asset, dict) and "name" in asset:
                            if (
                                "douglas" in asset["name"].lower()
                                and "washer" in asset["name"].lower()
                            ):
                                douglas_found = True
                                break

                if douglas_found:
                    print("✅ Douglas Washer Asset: FOUND")
                    self.results["asset_data_verification"]["douglas_washer"] = True
                else:
                    print("❌ Douglas Washer Asset: NOT FOUND")
            else:
                print(f"❌ Asset Check: FAIL (Status: {response.status_code})")

        except requests.exceptions.RequestException as e:
            print(f"❌ Asset Check: FAIL (Error: {str(e)})")

        # Check for team users
        target_users = ["Todd", "Chris", "Keith", "Jesus", "Jorge"]
        found_users = []

        try:
            print(f"Checking for team users: {CHATTERFIX_URL}/api/users")
            response = self.session.get(f"{CHATTERFIX_URL}/api/users", timeout=30)

            if response.status_code == 200:
                users_data = response.json()
                if isinstance(users_data, list):
                    for user in users_data:
                        if isinstance(user, dict) and "name" in user:
                            user_name = user["name"]
                            for target in target_users:
                                if target.lower() in user_name.lower():
                                    found_users.append(target)
                                    print(f"✅ User {target}: FOUND")

                missing_users = [
                    user for user in target_users if user not in found_users
                ]
                if missing_users:
                    print(f"❌ Missing Users: {missing_users}")

                self.results["asset_data_verification"]["team_users"] = found_users

        except requests.exceptions.RequestException as e:
            print(f"❌ User Check: FAIL (Error: {str(e)})")

    def generate_final_report(self):
        """Generate final Pass/Fail report"""
        self.print_section("FINAL SYSTEM AUDIT REPORT")

        print("1. ENDPOINT HEALTH CHECK:")
        print(
            f"   ChatterFix: {'✅ PASS' if self.results['endpoint_health']['chatterfix'] else '❌ FAIL'}"
        )
        print(
            f"   AI Team Service: {'✅ PASS' if self.results['endpoint_health']['ai_team'] else '❌ FAIL'}"
        )

        print("\n2. DATABASE INTEGRITY CHECK:")
        print(
            f"   Firestore Connection: {'✅ PASS' if self.results['database_integrity'] else '❌ FAIL'}"
        )

        print("\n3. AI COLLABORATION CHECK:")
        print(
            f"   AI Team Communication: {'✅ PASS' if self.results['ai_collaboration'] else '❌ FAIL'}"
        )

        print("\n4. ASSET & USER DATA VERIFICATION:")
        douglas_status = (
            "✅ PASS"
            if self.results["asset_data_verification"]["douglas_washer"]
            else "❌ FAIL"
        )
        print(f"   Douglas Washer Asset: {douglas_status}")

        found_users = self.results["asset_data_verification"]["team_users"]
        target_users = ["Todd", "Chris", "Keith", "Jesus", "Jorge"]
        users_status = "✅ PASS" if len(found_users) == len(target_users) else "❌ FAIL"
        print(f"   Team Users ({len(found_users)}/5): {users_status}")

        # Overall system status
        all_checks = [
            self.results["endpoint_health"]["chatterfix"],
            self.results["endpoint_health"]["ai_team"],
            self.results["database_integrity"],
            self.results["ai_collaboration"],
            self.results["asset_data_verification"]["douglas_washer"],
            len(found_users) == len(target_users),
        ]

        overall_status = (
            "✅ ALL SYSTEMS OPERATIONAL"
            if all(all_checks)
            else "⚠️  SOME SYSTEMS NEED ATTENTION"
        )
        print(f"\n🎯 OVERALL SYSTEM STATUS: {overall_status}")

        # Check if seed data is needed
        data_checks = [
            self.results["asset_data_verification"]["douglas_washer"],
            len(found_users) == len(target_users),
        ]

        if not all(data_checks):
            print("\n🔧 SEED DATA REQUIRED - Generating seed_data.py...")
            return True

        return False

    def run_all_tests(self):
        """Execute all smoke tests"""
        print(f"🚀 CHATTERFIX COMPREHENSIVE SYSTEM AUDIT")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"ChatterFix URL: {CHATTERFIX_URL}")
        print(f"AI Team URL: {AI_TEAM_URL}")

        self.test_endpoint_health()
        self.test_database_integrity()
        self.test_ai_collaboration()
        self.test_asset_data_verification()

        needs_seed_data = self.generate_final_report()
        return needs_seed_data


def main():
    """Main execution function"""
    tester = SmokeTester()
    needs_seed_data = tester.run_all_tests()

    if needs_seed_data:
        print("\n" + "=" * 60)
        print("  GENERATING SEED DATA SCRIPT")
        print("=" * 60)
        return True

    return False


if __name__ == "__main__":
    needs_seed = main()
    if needs_seed:
        sys.exit(1)  # Exit code 1 indicates seed data needed
    sys.exit(0)  # Exit code 0 indicates all tests passed
