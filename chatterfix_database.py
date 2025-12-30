"""
ChatterFix CMMS Database Integration
PostgreSQL connection and data management
"""
import os
import json
from datetime import datetime, date
import logging

# For now, use in-memory fallback until PostgreSQL password is configured
# Will seamlessly switch to PostgreSQL when connection is available
USE_POSTGRESQL = os.getenv('USE_POSTGRESQL', 'false').lower() == 'true'
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

if USE_POSTGRESQL and DB_PASSWORD:
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        DB_AVAILABLE = True
    except ImportError:
        DB_AVAILABLE = False
        logging.warning("psycopg2 not available, using fallback storage")
else:
    DB_AVAILABLE = False

# Database configuration
DB_CONFIG = {
    'host': '35.225.244.14',
    'database': 'chatterfix_cmms', 
    'user': 'postgres',
    'password': DB_PASSWORD,
    'port': 5432
}

# In-memory storage as fallback (will persist in files)
STORAGE_FILE = '/tmp/chatterfix_data.json'

def load_storage():
    """Load data from file storage"""
    try:
        if os.path.exists(STORAGE_FILE):
            with open(STORAGE_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    
    return {
        'work_orders': [
            {
                'id': 1,
                'work_order_number': 'WO-2025-001',
                'title': 'HVAC Filter Replacement',
                'description': 'Replace air filters in main HVAC unit',
                'asset_tag': 'HVAC-001',
                'priority': 'medium',
                'status': 'open',
                'assigned_to': 'John Smith',
                'created_at': '2025-10-13T10:00:00'
            }
        ],
        'assets': [
            {
                'id': 1,
                'asset_tag': 'HVAC-001',
                'name': 'Main HVAC Unit',
                'description': 'Primary building HVAC system',
                'manufacturer': 'Carrier',
                'location': 'Main Building',
                'status': 'active'
            },
            {
                'id': 2,
                'asset_tag': 'PUMP-001', 
                'name': 'Water Pump #1',
                'description': 'Primary water circulation pump',
                'manufacturer': 'Grundfos',
                'location': 'Mechanical Room',
                'status': 'active'
            }
        ],
        'parts': [
            {
                'id': 1,
                'part_number': 'FILTER-001',
                'name': 'HVAC Air Filter 20x25x4',
                'quantity_on_hand': 25,
                'min_stock_level': 5,
                'unit_cost': 45.99,
                'supplier': 'FilterCorp'
            },
            {
                'id': 2,
                'part_number': 'BELT-001',
                'name': 'V-Belt A-Section 48"', 
                'quantity_on_hand': 8,
                'min_stock_level': 2,
                'unit_cost': 12.50,
                'supplier': 'BeltSupply Inc'
            }
        ]
    }

def save_storage(data):
    """Save data to file storage"""
    try:
        with open(STORAGE_FILE, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logging.error(f"Failed to save storage: {e}")

# Data access layer
class ChatterFixDB:
    def __init__(self):
        self.storage = load_storage()
        
    def get_work_orders(self):
        """Get all work orders"""
        if DB_AVAILABLE:
            try:
                return self._query_db("SELECT * FROM work_orders ORDER BY created_at DESC")
            except:
                pass
        return self.storage['work_orders']
    
    def create_work_order(self, title, description, asset_tag=None, priority='medium', assigned_to=None):
        """Create a new work order"""
        if DB_AVAILABLE:
            try:
                query = """
                INSERT INTO work_orders (title, description, asset_tag, priority, assigned_to) 
                VALUES (%s, %s, %s, %s, %s) RETURNING id, work_order_number
                """
                result = self._query_db(query, (title, description, asset_tag, priority, assigned_to))
                return result[0] if result else None
            except:
                pass
        
        # Fallback to in-memory storage
        next_id = max([wo['id'] for wo in self.storage['work_orders']] + [0]) + 1
        work_order = {
            'id': next_id,
            'work_order_number': f'WO-2025-{next_id:03d}',
            'title': title,
            'description': description,
            'asset_tag': asset_tag,
            'priority': priority,
            'status': 'open',
            'assigned_to': assigned_to,
            'created_at': datetime.now().isoformat()
        }
        self.storage['work_orders'].append(work_order)
        save_storage(self.storage)
        return work_order
    
    def get_assets(self):
        """Get all assets"""
        if DB_AVAILABLE:
            try:
                return self._query_db("SELECT * FROM assets ORDER BY name")
            except:
                pass
        return self.storage['assets']
    
    def get_asset_by_tag(self, asset_tag):
        """Get asset by tag"""
        assets = self.get_assets()
        return next((a for a in assets if a['asset_tag'] == asset_tag), None)
    
    def get_parts_inventory(self):
        """Get parts inventory"""
        if DB_AVAILABLE:
            try:
                return self._query_db("SELECT * FROM parts_inventory ORDER BY name")
            except:
                pass
        return self.storage['parts']
    
    def get_low_stock_parts(self):
        """Get parts with low stock"""
        parts = self.get_parts_inventory()
        return [p for p in parts if p['quantity_on_hand'] <= p['min_stock_level']]
    
    def update_work_order_status(self, work_order_id, status):
        """Update work order status"""
        if DB_AVAILABLE:
            try:
                query = "UPDATE work_orders SET status = %s WHERE id = %s"
                self._query_db(query, (status, work_order_id), fetch=False)
                return True
            except:
                pass
        
        # Fallback
        for wo in self.storage['work_orders']:
            if wo['id'] == work_order_id:
                wo['status'] = status
                save_storage(self.storage)
                return True
        return False
    
    def _query_db(self, query, params=None, fetch=True):
        """Execute database query"""
        if not DB_AVAILABLE:
            return None
            
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        conn = psycopg2.connect(**DB_CONFIG)
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if fetch and cur.description:
                    return [dict(row) for row in cur.fetchall()]
                conn.commit()
                return cur.rowcount
        finally:
            conn.close()

# Global database instance
db = ChatterFixDB()
