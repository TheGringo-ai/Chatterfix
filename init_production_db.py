#!/usr/bin/env python3
"""
Initialize production Firestore database with required collections for purchasing system
"""

import os
from google.cloud import firestore

def init_firestore_collections():
    """Initialize Firestore collections for the purchasing system"""
    
    # Set up Firestore client
    os.environ['GOOGLE_CLOUD_PROJECT'] = 'fredfix'
    db = firestore.Client()
    
    print("🔥 Initializing Firestore Collections for ChatterFix")
    print("=" * 50)
    
    # Collections to initialize
    collections = [
        'purchase_orders',
        'po_documents', 
        'invoices',
        'invoice_documents',
        'vendor_documents',
        'po_line_items',
        'inventory_transactions',
        'supplier_quotes'
    ]
    
    for collection_name in collections:
        try:
            # Create a dummy document to initialize the collection
            doc_ref = db.collection(collection_name).document('_init')
            doc_ref.set({
                'initialized': True,
                'created_at': firestore.SERVER_TIMESTAMP,
                'note': 'Initialization document - can be deleted'
            })
            print(f"✅ Initialized collection: {collection_name}")
        except Exception as e:
            print(f"❌ Failed to initialize {collection_name}: {e}")
    
    # Create some sample vendors if they don't exist
    try:
        vendors_ref = db.collection('vendors')
        
        # Check if vendors already exist
        existing = list(vendors_ref.limit(1).stream())
        
        if not existing:
            sample_vendors = [
                {
                    'name': 'Industrial Supply Co',
                    'contact_name': 'John Smith',
                    'email': 'john@industrialsupply.com',
                    'phone': '555-0100',
                    'address': '123 Industrial Blvd',
                    'payment_terms': 'Net 30',
                    'tax_id': '12-3456789',
                    'created_date': firestore.SERVER_TIMESTAMP
                },
                {
                    'name': 'MRO Solutions',
                    'contact_name': 'Sarah Johnson', 
                    'email': 'sarah@mrosolutions.com',
                    'phone': '555-0200',
                    'address': '456 MRO Lane',
                    'payment_terms': 'Net 15',
                    'tax_id': '98-7654321',
                    'created_date': firestore.SERVER_TIMESTAMP
                }
            ]
            
            for vendor in sample_vendors:
                vendors_ref.add(vendor)
            
            print("✅ Added sample vendors")
        else:
            print("✅ Vendors collection already has data")
            
    except Exception as e:
        print(f"⚠️ Vendor initialization error: {e}")
    
    # Create some sample parts if they don't exist
    try:
        parts_ref = db.collection('parts')
        
        # Check if parts already exist
        existing = list(parts_ref.limit(1).stream())
        
        if not existing:
            sample_parts = [
                {
                    'name': 'Hydraulic Filter',
                    'part_number': 'HF-12345',
                    'description': 'High-pressure hydraulic filter',
                    'category': 'Filters',
                    'unit_cost': 45.99,
                    'current_stock': 25,
                    'minimum_stock': 5,
                    'barcode': '123456789012',
                    'location': 'A1-B2',
                    'created_date': firestore.SERVER_TIMESTAMP
                },
                {
                    'name': 'Motor Bearing',
                    'part_number': 'MB-67890',
                    'description': '6205-2RS deep groove ball bearing',
                    'category': 'Bearings',
                    'unit_cost': 12.50,
                    'current_stock': 15,
                    'minimum_stock': 10,
                    'barcode': '234567890123',
                    'location': 'A2-C1',
                    'created_date': firestore.SERVER_TIMESTAMP
                }
            ]
            
            for part in sample_parts:
                parts_ref.add(part)
            
            print("✅ Added sample parts")
        else:
            print("✅ Parts collection already has data")
            
    except Exception as e:
        print(f"⚠️ Parts initialization error: {e}")
    
    print("\n🎉 Firestore initialization complete!")
    print("\nCollections created for:")
    print("- Purchase Orders with document management")
    print("- Parts with photos and documents")
    print("- Vendor management")
    print("- Invoice processing")
    print("- Inventory tracking")
    print("- Barcode lookup system")

if __name__ == "__main__":
    init_firestore_collections()