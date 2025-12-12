#!/usr/bin/env python3
"""
Firebase connectivity check script for ChatterFix.
This script verifies Firebase Admin SDK and Firestore connectivity.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import firebase_admin
    from firebase_admin import credentials, firestore

    print("✅ Firebase Admin SDK imported successfully")
except ImportError as e:
    print(f"❌ Failed to import Firebase Admin SDK: {e}")
    print("Run: pip install firebase-admin")
    sys.exit(1)


def check_environment():
    """Check required environment variables."""
    print("\n🔍 Checking environment variables...")

    # Check for service account credentials
    google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not google_creds:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
        print("Set it to the path of your service account JSON file:")
        print("export GOOGLE_APPLICATION_CREDENTIALS='./secrets/firebase-admin.json'")
        return False

    if not os.path.exists(google_creds):
        print(f"❌ Service account file not found: {google_creds}")
        return False

    print(f"✅ Service account file found: {google_creds}")

    # Check other Firebase config
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("FIREBASE_PROJECT_ID")
    if not project_id:
        print(
            "⚠️  GOOGLE_CLOUD_PROJECT not set (will use project ID from service account)"
        )
    else:
        print(f"✅ Project ID: {project_id}")

    return True


def check_firebase_admin():
    """Initialize and test Firebase Admin SDK."""
    print("\n🔥 Initializing Firebase Admin SDK...")

    try:
        # Initialize Firebase Admin (uses GOOGLE_APPLICATION_CREDENTIALS automatically)
        if not firebase_admin._apps:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)

        print("✅ Firebase Admin SDK initialized successfully")
        return True

    except Exception as e:
        print(f"❌ Failed to initialize Firebase Admin SDK: {e}")
        return False


def check_firestore():
    """Test Firestore connectivity."""
    print("\n🗄️  Testing Firestore connectivity...")

    try:
        db = firestore.client()

        # Try to read from a test collection
        test_ref = db.collection("connectivity_test").document("test_doc")

        # Try to write a test document
        test_data = {"timestamp": firestore.SERVER_TIMESTAMP, "test": True}
        test_ref.set(test_data)
        print("✅ Firestore write test successful")

        # Try to read the document back
        doc = test_ref.get()
        if doc.exists:
            print("✅ Firestore read test successful")
            # Clean up test document
            test_ref.delete()
            print("✅ Test document cleaned up")
        else:
            print("⚠️  Could not read back test document")

        return True

    except Exception as e:
        print(f"❌ Firestore connectivity failed: {e}")
        return False


def check_firebase_auth():
    """Test Firebase Authentication."""
    print("\n🔐 Testing Firebase Auth connectivity...")

    try:
        from firebase_admin import auth

        # Try to list users (this will fail gracefully if no users exist)
        users = auth.list_users(max_results=1)
        print("✅ Firebase Auth connectivity successful")
        return True

    except Exception as e:
        print(f"❌ Firebase Auth connectivity failed: {e}")
        return False


def main():
    """Run all connectivity checks."""
    print("🚀 ChatterFix Firebase Connectivity Check")
    print("=" * 50)

    success = True

    # Environment check
    if not check_environment():
        success = False

    # Firebase Admin SDK check
    if success and not check_firebase_admin():
        success = False

    # Firestore check
    if success and not check_firestore():
        success = False

    # Firebase Auth check
    if success and not check_firebase_auth():
        success = False

    print("\n" + "=" * 50)
    if success:
        print("🎉 All Firebase connectivity checks passed!")
        print("Your Firebase setup is ready for ChatterFix.")
    else:
        print("💥 Some connectivity checks failed.")
        print("Please resolve the issues above before starting the application.")
        sys.exit(1)


if __name__ == "__main__":
    main()
