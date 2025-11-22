import sqlite3
import os

DB_PATH = "./data/cmms.db"

def migrate():
    print(f"Migrating database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Add image_url to assets if not exists
    try:
        cursor.execute("ALTER TABLE assets ADD COLUMN image_url TEXT")
        print("✅ Added image_url to assets table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️ image_url already exists in assets table")
        else:
            print(f"❌ Error adding image_url to assets: {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
