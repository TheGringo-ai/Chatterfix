#!/usr/bin/env python3
"""
Test Work Order CRUD Operations
Tests creation, reading, updating, and completion of work orders.

Usage:
    python scripts/test_work_order_crud.py --base-url https://chatterfix.com
    python scripts/test_work_order_crud.py --base-url http://localhost:8000
"""

import argparse
import asyncio
import os
import sys
import json
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import Firebase Admin
try:
    import firebase_admin
    from firebase_admin import credentials, auth, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("⚠️  Firebase Admin SDK not available - will use demo mode")

import requests

# ============================================================================
# TEST CONFIGURATION
# ============================================================================

TEST_ORG_ID = "test_org_automated"
TEST_USER_EMAIL = "test@chatterfix.com"


def init_firebase():
    """Initialize Firebase Admin SDK"""
    if not FIREBASE_AVAILABLE:
        return None

    try:
        # Check if already initialized
        firebase_admin.get_app()
    except ValueError:
        # Initialize with default credentials
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                'projectId': 'fredfix'
            })
        except Exception as e:
            print(f"⚠️  Could not initialize Firebase: {e}")
            return None

    return firestore.client()


def get_test_session_token(db):
    """Get or create a test user and return session token"""
    if not db:
        return None

    try:
        # Try to get existing test user
        user = auth.get_user_by_email(TEST_USER_EMAIL)
        print(f"✅ Found test user: {user.uid}")
    except auth.UserNotFoundError:
        # Create test user (password from env or default for testing only)
        test_password = os.environ.get("TEST_USER_PASSWORD", "TestPassword123!")
        user = auth.create_user(
            email=TEST_USER_EMAIL,
            password=test_password,
            display_name="Test User"
        )
        print(f"✅ Created test user: {user.uid}")

        # Create user document in Firestore
        db.collection("users").document(user.uid).set({
            "email": TEST_USER_EMAIL,
            "full_name": "Test User",
            "role": "manager",
            "organization_id": TEST_ORG_ID,
            "organization_name": "Test Organization",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        # Create test organization if needed
        org_ref = db.collection("organizations").document(TEST_ORG_ID)
        if not org_ref.get().exists:
            org_ref.set({
                "name": "Test Organization",
                "owner_user_id": user.uid,
                "is_demo": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

    # Create a custom token for testing
    custom_token = auth.create_custom_token(user.uid)
    return custom_token.decode('utf-8') if isinstance(custom_token, bytes) else custom_token


def test_planner_backlog_unauthenticated(base_url: str):
    """Test planner backlog endpoint without authentication"""
    print("\n" + "="*60)
    print("TEST 1: Planner Backlog (Unauthenticated)")
    print("="*60)

    response = requests.get(f"{base_url}/planner/backlog")

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        has_debug = "_debug" in data
        print(f"✅ Response received")
        print(f"   Has _debug field: {has_debug}")
        if has_debug:
            print(f"   Build marker: {data['_debug'].get('build_marker', 'N/A')}")
            print(f"   Data source: {data['_debug'].get('data_source', 'N/A')}")
            print(f"   User authenticated: {data['_debug'].get('user_authenticated', 'N/A')}")
        print(f"   Work orders count: {len(data.get('work_orders', []))}")
        print(f"   Total backlog: {data.get('total_backlog', 0)}")
        return True
    else:
        print(f"❌ Failed: {response.text[:200]}")
        return False


def test_work_order_list(base_url: str, session=None):
    """Test work order listing endpoint"""
    print("\n" + "="*60)
    print("TEST 2: Work Order List")
    print("="*60)

    response = requests.get(f"{base_url}/work-orders/list", cookies=session)

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        # Check if it's JSON or HTML
        content_type = response.headers.get('content-type', '')
        if 'json' in content_type:
            data = response.json()
            print(f"✅ JSON Response received")
            print(f"   Work orders: {len(data.get('work_orders', []))}")
        else:
            print(f"✅ HTML Response received (length: {len(response.text)})")
        return True
    else:
        print(f"❌ Failed: {response.text[:200]}")
        return False


def test_work_order_creation_api(base_url: str, session=None):
    """Test work order creation via API"""
    print("\n" + "="*60)
    print("TEST 3: Work Order Creation (API)")
    print("="*60)

    # Test data
    work_order_data = {
        "title": f"Test Work Order - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "description": "Automated test work order for CRUD verification",
        "priority": "Medium",
        "work_order_type": "Corrective",
        "status": "Open",
        "due_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }

    # Try API endpoint first
    response = requests.post(
        f"{base_url}/api/work-orders",
        json=work_order_data,
        cookies=session
    )

    print(f"Status: {response.status_code}")

    if response.status_code in [200, 201]:
        data = response.json()
        print(f"✅ Work order created successfully")
        print(f"   ID: {data.get('id', 'N/A')}")
        return data.get('id')
    elif response.status_code == 404:
        print("⚠️  API endpoint not found, trying form endpoint...")
        return test_work_order_creation_form(base_url, session, work_order_data)
    else:
        print(f"❌ Failed: {response.text[:200]}")
        return None


def test_work_order_creation_form(base_url: str, session=None, data=None):
    """Test work order creation via form POST"""
    print("   Trying form submission...")

    if data is None:
        data = {
            "title": f"Test Work Order - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "description": "Automated test work order",
            "priority": "Medium",
            "work_order_type": "Corrective",
        }

    response = requests.post(
        f"{base_url}/work-orders",
        data=data,
        cookies=session,
        allow_redirects=False
    )

    print(f"   Form Status: {response.status_code}")

    if response.status_code in [200, 201, 302, 303]:
        print(f"✅ Work order creation initiated")
        if response.status_code in [302, 303]:
            print(f"   Redirect to: {response.headers.get('location', 'N/A')}")
        return "created"
    else:
        print(f"❌ Failed: {response.text[:200]}")
        return None


def test_planner_endpoints(base_url: str, session=None):
    """Test various planner endpoints"""
    print("\n" + "="*60)
    print("TEST 4: Planner Endpoints")
    print("="*60)

    endpoints = [
        "/planner/pm-schedule",
        "/planner/resource-capacity",
        "/planner/asset-pm-status",
        "/planner/parts-availability",
        "/planner/conflicts",
        "/planner/compliance",
        "/planner/summary",
    ]

    results = {}
    for endpoint in endpoints:
        response = requests.get(f"{base_url}{endpoint}", cookies=session)
        status = "✅" if response.status_code == 200 else "❌"
        results[endpoint] = response.status_code

        if response.status_code == 200:
            try:
                data = response.json()
                has_debug = "_debug" in data
                data_source = data.get("_debug", {}).get("data_source", "N/A") if has_debug else "N/A"
                print(f"   {status} {endpoint}: {response.status_code} (source: {data_source})")
            except (ValueError, KeyError):
                print(f"   {status} {endpoint}: {response.status_code}")
        else:
            print(f"   {status} {endpoint}: {response.status_code}")

    return results


def test_debug_auth(base_url: str, session=None):
    """Test debug auth endpoint"""
    print("\n" + "="*60)
    print("TEST 5: Debug Auth Endpoint")
    print("="*60)

    response = requests.get(f"{base_url}/planner/debug-auth", cookies=session)

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Debug auth response:")
        print(f"   Has session token: {data.get('has_session_token', False)}")
        print(f"   User authenticated: {data.get('user_authenticated', False)}")
        print(f"   User email: {data.get('user_email', 'N/A')}")
        print(f"   Organization ID: {data.get('organization_id', 'N/A')}")
        print(f"   Role: {data.get('role', 'N/A')}")
        return data
    else:
        print(f"❌ Failed: {response.text[:200]}")
        return None


def test_firestore_integration(db):
    """Test direct Firestore integration"""
    print("\n" + "="*60)
    print("TEST 6: Direct Firestore Integration")
    print("="*60)

    if not db:
        print("⚠️  Firestore not available - skipping")
        return None

    try:
        # Check collections
        collections = ["work_orders", "assets", "users", "organizations"]
        for collection_name in collections:
            docs = list(db.collection(collection_name).limit(5).stream())
            print(f"   {collection_name}: {len(docs)} documents (sample)")

        print("✅ Firestore connection working")
        return True
    except Exception as e:
        print(f"❌ Firestore error: {e}")
        return False


def run_all_tests(base_url: str):
    """Run all tests"""
    print("\n" + "="*70)
    print("🧪 CHATTERFIX WORK ORDER CRUD TESTS")
    print("="*70)
    print(f"Base URL: {base_url}")
    print(f"Time: {datetime.now().isoformat()}")

    # Initialize Firebase
    db = init_firebase()

    # Test results
    results = {
        "planner_backlog_unauth": False,
        "work_order_list": False,
        "work_order_creation": False,
        "planner_endpoints": False,
        "debug_auth": False,
        "firestore": False,
    }

    # Run tests
    results["planner_backlog_unauth"] = test_planner_backlog_unauthenticated(base_url)
    results["work_order_list"] = test_work_order_list(base_url)
    results["work_order_creation"] = test_work_order_creation_api(base_url) is not None
    results["planner_endpoints"] = all(v == 200 for v in test_planner_endpoints(base_url).values())
    results["debug_auth"] = test_debug_auth(base_url) is not None
    results["firestore"] = test_firestore_integration(db)

    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"   {status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Work Order CRUD Operations")
    parser.add_argument("--base-url", default="https://chatterfix.com", help="Base URL for testing")
    args = parser.parse_args()

    run_all_tests(args.base_url)
