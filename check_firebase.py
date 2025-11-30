#!/usr/bin/env python3
"""
Firebase Configuration Checker for ChatterFix CMMS
Verifies Firebase setup and credentials
"""

import os
import sys
import json
from pathlib import Path


def check_firebase_config():
    """Check Firebase configuration"""
    print("🔥 ChatterFix Firebase Configuration Checker")
    print("=" * 50)

    # Check environment variables
    print("\n📋 Environment Variables:")
    required_vars = [
        "USE_FIRESTORE",
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_APPLICATION_CREDENTIALS",
    ]

    optional_vars = [
        "FIREBASE_API_KEY",
        "FIREBASE_AUTH_DOMAIN",
        "FIREBASE_PROJECT_ID",
        "FIREBASE_STORAGE_BUCKET",
        "FIREBASE_MESSAGING_SENDER_ID",
        "FIREBASE_APP_ID",
    ]

    missing_required = []

    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == "GOOGLE_APPLICATION_CREDENTIALS":
                # Check if file exists
                if os.path.exists(value):
                    print(f"✅ {var}: {value} (file exists)")
                else:
                    print(f"❌ {var}: {value} (file not found)")
                    missing_required.append(var)
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
            missing_required.append(var)

    print("\n📋 Optional Variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            # Hide sensitive values
            if "KEY" in var:
                print(f"✅ {var}: {'*' * len(value)}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"⚠️ {var}: Not set")

    # Check Firebase dependencies
    print("\n📦 Firebase Dependencies:")
    try:
        import firebase_admin

        print("✅ firebase_admin: Available")
    except ImportError:
        print("❌ firebase_admin: Not installed")
        missing_required.append("firebase_admin")

    try:
        import pyrebase

        print("✅ pyrebase4: Available")
    except ImportError:
        print("❌ pyrebase4: Not installed")
        missing_required.append("pyrebase4")

    try:
        from google.cloud import firestore

        print("✅ google-cloud-firestore: Available")
    except ImportError:
        print("❌ google-cloud-firestore: Not installed")
        missing_required.append("google-cloud-firestore")

    # Test Firebase initialization
    print("\n🔥 Firebase Initialization Test:")
    try:
        # Import and test the service
        sys.path.append(".")
        from app.services.firebase_auth import firebase_auth_service

        if firebase_auth_service.is_available:
            print("✅ Firebase Auth Service: Initialized")
            if firebase_auth_service.db:
                print("✅ Firestore Client: Connected")

                # Try a simple read test
                test_doc = firebase_auth_service.db.collection("test").document(
                    "connection"
                )
                test_doc.get()
                print("✅ Firestore Access: Working")
            else:
                print("❌ Firestore Client: Not connected")
        else:
            print("❌ Firebase Auth Service: Not initialized")
    except Exception as e:
        print(f"❌ Firebase Test Failed: {e}")

    # Summary
    print("\n" + "=" * 50)
    if missing_required:
        print("❌ FIREBASE STATUS: INCOMPLETE")
        print("Missing requirements:")
        for item in missing_required:
            print(f"   - {item}")
        print("\n📋 Next Steps:")
        print(
            "1. Install missing dependencies: pip install firebase-admin pyrebase4 google-cloud-firestore"
        )
        print("2. Download service account key from Firebase Console")
        print("3. Save as firebase-credentials.json in project root")
        print("4. Set FIREBASE_API_KEY and other web config variables")
        return False
    else:
        print("✅ FIREBASE STATUS: READY")
        print("🎉 All Firebase requirements satisfied!")
        print("🚀 ChatterFix will use Firestore for all data operations")
        return True


if __name__ == "__main__":
    success = check_firebase_config()
    sys.exit(0 if success else 1)
