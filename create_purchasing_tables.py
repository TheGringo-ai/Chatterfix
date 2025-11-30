#!/usr/bin/env python3
"""
Create database tables for enhanced purchasing and POS system
"""

import sqlite3
import os

def create_purchasing_tables():
    """Create all necessary tables for purchasing system"""
    
    # Use the same database path as the main application
    db_path = "data/cmms.db"
    
    # Ensure the data directory exists
    os.makedirs("data", exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Creating purchasing system tables...")
    
    # Purchase Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_number TEXT UNIQUE NOT NULL,
            vendor_id INTEGER,
            description TEXT,
            total_amount REAL DEFAULT 0.0,
            delivery_date TEXT,
            status TEXT DEFAULT 'Draft',
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors (id)
        )
    """)
    
    # Purchase Order Documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS po_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT DEFAULT 'document',
            filename TEXT NOT NULL,
            description TEXT,
            uploaded_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (po_id) REFERENCES purchase_orders (id)
        )
    """)
    
    # Invoices table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_id INTEGER,
            invoice_number TEXT NOT NULL,
            amount REAL NOT NULL,
            invoice_date TEXT NOT NULL,
            due_date TEXT,
            status TEXT DEFAULT 'Pending',
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (po_id) REFERENCES purchase_orders (id)
        )
    """)
    
    # Invoice Documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT DEFAULT 'document',
            filename TEXT NOT NULL,
            description TEXT,
            uploaded_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (invoice_id) REFERENCES invoices (id)
        )
    """)
    
    # Vendor Documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendor_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT DEFAULT 'document',
            filename TEXT NOT NULL,
            description TEXT,
            uploaded_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors (id)
        )
    """)
    
    # Enhanced Vendors table (add missing columns if they don't exist)
    try:
        cursor.execute("ALTER TABLE vendors ADD COLUMN payment_terms TEXT DEFAULT 'Net 30'")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE vendors ADD COLUMN tax_id TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        cursor.execute("ALTER TABLE vendors ADD COLUMN created_date DATETIME DEFAULT CURRENT_TIMESTAMP")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Enhanced Parts table (add missing columns)
    try:
        cursor.execute("ALTER TABLE parts ADD COLUMN barcode TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        cursor.execute("ALTER TABLE parts ADD COLUMN location TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        cursor.execute("ALTER TABLE parts ADD COLUMN created_date DATETIME DEFAULT CURRENT_TIMESTAMP")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Purchase Order Line Items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS po_line_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_id INTEGER NOT NULL,
            part_id INTEGER,
            description TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (po_id) REFERENCES purchase_orders (id),
            FOREIGN KEY (part_id) REFERENCES parts (id)
        )
    """)
    
    # Inventory Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL, -- 'IN', 'OUT', 'ADJUSTMENT'
            quantity INTEGER NOT NULL,
            unit_price REAL,
            total_value REAL,
            reference_type TEXT, -- 'PO', 'WO', 'ADJUSTMENT'
            reference_id INTEGER,
            description TEXT,
            transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (part_id) REFERENCES parts (id)
        )
    """)
    
    # Supplier Quotes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS supplier_quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER NOT NULL,
            quote_number TEXT,
            part_id INTEGER,
            description TEXT,
            quantity INTEGER,
            unit_price REAL,
            total_price REAL,
            delivery_time TEXT,
            valid_until TEXT,
            status TEXT DEFAULT 'Active',
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors (id),
            FOREIGN KEY (part_id) REFERENCES parts (id)
        )
    """)
    
    # Create indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_po_vendor ON purchase_orders(vendor_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_po_docs_po ON po_documents(po_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoice_po ON invoices(po_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_parts_barcode ON parts(barcode)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_parts_vendor ON parts(vendor_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_trans_part ON inventory_transactions(part_id)")
    
    conn.commit()
    conn.close()
    
    print("✅ All purchasing system tables created successfully!")
    print("\n🎉 Purchasing system database setup complete!")
    print("\nNew features available:")
    print("- Purchase Orders with document attachments")
    print("- Parts management with photos and documents")
    print("- Vendor management with documents")
    print("- Invoice processing with file uploads")
    print("- Barcode lookup and inventory tracking")
    print("- Low stock alerts and purchasing workflows")

if __name__ == "__main__":
    create_purchasing_tables()