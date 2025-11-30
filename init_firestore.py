#!/usr/bin/env python3
"""
Initialize Firestore with ChatterFix CMMS collections and demo data
"""

import os
import sys
from datetime import datetime, timezone

# Add app to path
sys.path.append(os.getcwd())

def init_firestore():
    """Initialize Firestore with ChatterFix collections"""
    print("🔥 Initializing Firestore for ChatterFix CMMS")
    print("=" * 50)
    
    try:
        from app.services.firebase_auth import firebase_auth_service
        
        if not firebase_auth_service.is_available:
            print("❌ Firebase not available. Check your configuration.")
            print("   Run: python check_firebase.py")
            return False
            
        db = firebase_auth_service.db
        
        # Define collections to create
        collections_data = {
            'users': {
                '_init': {
                    'created_at': datetime.now(timezone.utc),
                    'description': 'Users collection for authentication and profiles',
                    'type': 'initialization',
                    'sample_structure': {
                        'uid': 'string',
                        'email': 'string', 
                        'display_name': 'string',
                        'role': 'technician|supervisor|manager|parts_manager',
                        'status': 'active|inactive',
                        'profile': {
                            'avatar_url': 'string',
                            'phone': 'string'
                        }
                    }
                }
            },
            'work_orders': {
                '_init': {
                    'created_at': datetime.now(timezone.utc),
                    'description': 'Work orders for maintenance tasks',
                    'type': 'initialization',
                    'sample_structure': {
                        'title': 'string',
                        'description': 'string',
                        'status': 'open|in_progress|completed|closed',
                        'priority': 'low|medium|high|urgent',
                        'assigned_to': 'string',
                        'asset_id': 'string',
                        'due_date': 'timestamp',
                        'location': 'string'
                    }
                }
            },
            'assets': {
                '_init': {
                    'created_at': datetime.now(timezone.utc),
                    'description': 'Equipment and asset management',
                    'type': 'initialization',
                    'sample_structure': {
                        'name': 'string',
                        'description': 'string',
                        'asset_tag': 'string',
                        'location': 'string',
                        'status': 'active|inactive|maintenance|retired',
                        'condition_rating': 'number (1-10)',
                        'manufacturer': 'string',
                        'model': 'string',
                        'serial_number': 'string'
                    }
                }
            },
            'inventory': {
                '_init': {
                    'created_at': datetime.now(timezone.utc),
                    'description': 'Parts and inventory management',
                    'type': 'initialization',
                    'sample_structure': {
                        'name': 'string',
                        'part_number': 'string',
                        'category': 'string',
                        'current_stock': 'number',
                        'minimum_stock': 'number',
                        'unit_cost': 'number',
                        'location': 'string'
                    }
                }
            },
            'ai_interactions': {
                '_init': {
                    'created_at': datetime.now(timezone.utc),
                    'description': 'AI chat interactions and history',
                    'type': 'initialization',
                    'sample_structure': {
                        'user_message': 'string',
                        'ai_response': 'string',
                        'timestamp': 'timestamp',
                        'user_id': 'string'
                    }
                }
            },
            'notifications': {
                '_init': {
                    'created_at': datetime.now(timezone.utc),
                    'description': 'User notifications and alerts',
                    'type': 'initialization',
                    'sample_structure': {
                        'user_id': 'string',
                        'type': 'string',
                        'title': 'string',
                        'message': 'string',
                        'read': 'boolean',
                        'priority': 'normal|high|urgent'
                    }
                }
            }
        }
        
        print("🗄️ Creating Firestore collections...")
        
        for collection_name, docs in collections_data.items():
            print(f"   📁 Creating collection: {collection_name}")
            for doc_id, doc_data in docs.items():
                doc_ref = db.collection(collection_name).document(doc_id)
                doc_ref.set(doc_data)
            print(f"   ✅ Collection {collection_name} initialized")
        
        # Create some demo data
        print("\n🎯 Creating demo data...")
        
        # Demo user
        demo_user_data = {
            'uid': 'demo_user',
            'email': 'demo@chatterfix.com',
            'display_name': 'Demo User',
            'role': 'technician',
            'status': 'active',
            'created_at': datetime.now(timezone.utc),
            'last_login': datetime.now(timezone.utc),
            'profile': {
                'avatar_url': '',
                'phone': ''
            }
        }
        
        db.collection('users').document('demo_user').set(demo_user_data)
        print("   👤 Demo user created")
        
        # Demo asset
        demo_asset_data = {
            'name': 'Demo HVAC Unit #1',
            'description': 'Main building HVAC system',
            'asset_tag': 'HVAC-001',
            'location': 'Building A - Roof',
            'status': 'active',
            'condition_rating': 8,
            'manufacturer': 'ACME HVAC',
            'model': 'AC-2000X',
            'serial_number': 'SN123456789',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
        
        asset_ref = db.collection('assets').add(demo_asset_data)
        asset_id = asset_ref[1].id
        print(f"   🏭 Demo asset created: {asset_id}")
        
        # Demo work order
        demo_wo_data = {
            'title': 'HVAC Filter Replacement',
            'description': 'Replace air filters in main HVAC unit',
            'status': 'open',
            'priority': 'medium',
            'assigned_to': 'demo_user',
            'asset_id': asset_id,
            'location': 'Building A - Roof',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
        
        wo_ref = db.collection('work_orders').add(demo_wo_data)
        wo_id = wo_ref[1].id
        print(f"   📋 Demo work order created: {wo_id}")
        
        print("\n🎉 Firestore initialization complete!")
        print("\n📊 Collections created:")
        for collection_name in collections_data.keys():
            print(f"   ✅ {collection_name}")
        
        print("\n🚀 ChatterFix is ready to use Firebase!")
        return True
        
    except Exception as e:
        print(f"❌ Firestore initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = init_firestore()
    sys.exit(0 if success else 1)