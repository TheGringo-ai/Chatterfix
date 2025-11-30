import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from app.core.database import get_db_connection

DB_PATH = "./data/cmms.db"

def migrate():
    print(f"Migrating database at {DB_PATH}...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Add image_url to assets if not exists
    try:
        cursor.execute("ALTER TABLE assets ADD COLUMN image_url TEXT")
        print("✅ Added image_url to assets table")
    except Exception as e:
        if "duplicate column name" in str(e):
            print("ℹ️ image_url already exists in assets table")
        else:
            print(f"❌ Error adding image_url to assets: {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
