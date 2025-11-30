#!/usr/bin/env python3
"""
Automated Firebase Setup Script for ChatterFix CMMS
This script helps configure Firebase Authentication and Firestore
"""

import os
import json
import subprocess
import sys
from pathlib import Path

def print_step(step, description):
    print(f"\n🔥 Step {step}: {description}")
    print("-" * 50)

def check_firebase_dependencies():
    """Check if Firebase dependencies are installed"""
    print("📦 Checking Firebase dependencies...")
    
    try:
        import firebase_admin
        import pyrebase
        print("✅ Firebase dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing Firebase dependencies: {e}")
        print("\n📥 Installing Firebase dependencies...")
        
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", 
                "firebase-admin", "pyrebase4", "google-cloud-firestore"
            ], check=True)
            print("✅ Firebase dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False

def create_firebase_config_template():
    """Create Firebase configuration template"""
    config_template = {
        "type": "service_account",
        "project_id": "your-project-id",
        "private_key_id": "your-private-key-id", 
        "private_key": "-----BEGIN PRIVATE KEY-----\\nYOUR_PRIVATE_KEY\\n-----END PRIVATE KEY-----\\n",
        "client_email": "firebase-adminsdk-xxxxx@your-project-id.iam.gserviceaccount.com",
        "client_id": "your-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxxx%40your-project-id.iam.gserviceaccount.com"
    }
    
    template_path = "firebase-credentials-template.json"
    with open(template_path, 'w') as f:
        json.dump(config_template, f, indent=2)
    
    print(f"📄 Created template: {template_path}")
    return template_path

def update_env_file():
    """Update .env file with Firebase configuration"""
    print("\n⚙️ Updating .env file...")
    
    env_lines = []
    firebase_config = """
# Firebase Configuration (Updated for Production)
USE_FIRESTORE=true
GOOGLE_CLOUD_PROJECT=fredfix
GOOGLE_APPLICATION_CREDENTIALS=./firebase-credentials.json

# Firebase Web App Configuration (from Firebase Console)
FIREBASE_API_KEY=your_firebase_api_key_here
FIREBASE_AUTH_DOMAIN=fredfix.firebaseapp.com
FIREBASE_PROJECT_ID=fredfix
FIREBASE_STORAGE_BUCKET=fredfix.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id

# Optional: Firebase Admin SDK initialization
FIREBASE_DATABASE_URL=https://fredfix-default-rtdb.firebaseio.com/
"""

    # Read existing .env
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            content = f.read()
        
        # Remove old Firebase config if exists
        lines = content.split('\n')
        in_firebase_section = False
        for line in lines:
            if '# Firebase Configuration' in line:
                in_firebase_section = True
                continue
            elif line.startswith('#') and 'Configuration' in line and in_firebase_section:
                in_firebase_section = False
            elif not in_firebase_section:
                env_lines.append(line)
    
    # Add new Firebase config
    env_content = '\n'.join(env_lines) + firebase_config
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Updated .env file with Firebase configuration")

def create_firebase_init_script():
    """Create a script to initialize Firestore with basic collections"""
    init_script = '''#!/usr/bin/env python3
"""
Initialize Firestore with basic ChatterFix collections and sample data
"""

import os
import sys
from datetime import datetime

# Add app to path
sys.path.append(os.getcwd())

def init_firestore():
    """Initialize Firestore with ChatterFix collections"""
    try:
        from app.services.firebase_auth import firebase_auth_service
        
        if not firebase_auth_service.is_available:
            print("❌ Firebase not available. Check your configuration.")
            return False
            
        db = firebase_auth_service.db
        
        # Create basic collections
        collections = [
            'users',
            'work_orders', 
            'assets',
            'inventory',
            'teams',
            'notifications'
        ]
        
        print("🗄️ Initializing Firestore collections...")
        
        for collection_name in collections:
            # Create a sample document to initialize collection
            doc_ref = db.collection(collection_name).document('_init')
            doc_ref.set({
                'created_at': datetime.now(),
                'description': f'Initial document for {collection_name} collection',
                'type': 'initialization'
            })
            print(f"✅ Created collection: {collection_name}")
        
        print("🎉 Firestore initialization complete!")
        return True
        
    except Exception as e:
        print(f"❌ Firestore initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = init_firestore()
    sys.exit(0 if success else 1)
'''
    
    with open('init_firestore.py', 'w') as f:
        f.write(init_script)
    
    print("📄 Created Firestore initialization script: init_firestore.py")

def create_firebase_test_script():
    """Create a script to test Firebase connectivity"""
    test_script = '''#!/usr/bin/env python3
"""
Test Firebase Authentication and Firestore connectivity
"""

import os
import sys
from datetime import datetime

# Add app to path
sys.path.append(os.getcwd())

def test_firebase():
    """Test Firebase services"""
    print("🧪 Testing Firebase connectivity...")
    
    try:
        from app.services.firebase_auth import firebase_auth_service
        
        print(f"Firebase available: {firebase_auth_service.is_available}")
        print(f"Initialized: {firebase_auth_service._initialized}")
        
        if not firebase_auth_service.is_available:
            print("❌ Firebase not available")
            return False
            
        # Test Firestore
        db = firebase_auth_service.db
        test_doc = db.collection('test').document('connectivity')
        test_doc.set({
            'timestamp': datetime.now(),
            'test': 'Firebase connectivity test',
            'status': 'success'
        })
        
        # Read back the document
        doc = test_doc.get()
        if doc.exists:
            print("✅ Firestore read/write test successful")
            
            # Clean up test document
            test_doc.delete()
            print("✅ Firestore cleanup successful")
        else:
            print("❌ Firestore read test failed")
            return False
            
        print("🎉 All Firebase tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Firebase test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_firebase()
    sys.exit(0 if success else 1)
'''
    
    with open('test_firebase.py', 'w') as f:
        f.write(test_script)
    
    print("📄 Created Firebase test script: test_firebase.py")

def main():
    """Main setup function"""
    print("🔥 ChatterFix Firebase Setup Assistant")
    print("=" * 60)
    
    # Step 1: Check dependencies
    print_step(1, "Checking Firebase Dependencies")
    if not check_firebase_dependencies():
        print("❌ Setup failed. Please install dependencies manually.")
        return False
    
    # Step 2: Create configuration files
    print_step(2, "Creating Configuration Files")
    create_firebase_config_template()
    update_env_file()
    create_firebase_init_script()
    create_firebase_test_script()
    
    # Step 3: Instructions
    print_step(3, "Next Steps")
    print("""
📋 TO COMPLETE FIREBASE SETUP:

1. 🌐 Go to Firebase Console: https://console.firebase.google.com/
   
2. 🆕 Create a new project (or use existing 'fredfix'):
   - Project name: fredfix (or chatterfix-cmms)
   - Enable Google Analytics (optional)

3. 🔐 Enable Authentication:
   - Go to Authentication → Get started
   - Sign-in method → Enable Email/Password

4. 🗄️ Enable Firestore:
   - Go to Firestore Database → Create database
   - Start in test mode → Choose region (us-central1)

5. 🔑 Download Service Account Key:
   - Project Settings → Service accounts
   - Generate new private key → Download JSON
   - Save as: firebase-credentials.json (in project root)

6. 🌐 Get Web App Config:
   - Project Settings → General → Add app → Web
   - Copy config values to .env file

7. ✅ Test the setup:
   python test_firebase.py

8. 🚀 Initialize Firestore:
   python init_firestore.py

""")
    
    print("📄 Configuration files created:")
    print("  ├── firebase-credentials-template.json (template)")
    print("  ├── .env (updated with Firebase vars)")
    print("  ├── test_firebase.py (test script)")
    print("  └── init_firestore.py (initialization script)")
    
    print("\n🎯 Current Firebase Status: CONFIGURED FOR SETUP")
    print("📋 Next: Follow the steps above to complete Firebase integration")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
'''