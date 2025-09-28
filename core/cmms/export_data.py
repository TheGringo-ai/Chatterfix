#!/usr/bin/env python3
"""
SQLite to PostgreSQL Data Export Script
Exports all data from SQLite database to PostgreSQL-compatible CSV files
"""

import sqlite3
import csv
import os
import json
from datetime import datetime

# Database path
SQLITE_DB_PATH = "./data/cmms_enhanced.db"
OUTPUT_DIR = "./migration_data"

# List of all tables to export
TABLES = [
    'users', 'locations', 'suppliers', 'assets', 'work_orders', 'parts',
    'pm_templates', 'maintenance_schedules', 'sensor_readings', 'ai_predictions',
    'purchase_orders', 'po_line_items', 'inventory_transactions', 'attachments',
    'audit_log', 'media_files', 'ocr_results', 'speech_transcriptions',
    'ai_model_configs', 'ai_request_logs', 'model_fine_tuning', 'model_ab_tests',
    'ai_prompt_templates', 'ai_alerts'
]

def create_output_directory():
    """Create output directory if it doesn't exist"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created output directory: {OUTPUT_DIR}")

def convert_value_for_postgres(value):
    """Convert SQLite values to PostgreSQL-compatible format"""
    if value is None:
        return None
    
    # Handle boolean values
    if isinstance(value, int) and value in (0, 1):
        # Check if it's likely a boolean field based on common patterns
        return 'TRUE' if value == 1 else 'FALSE'
    
    # Handle JSON strings - ensure they're properly formatted
    if isinstance(value, str):
        try:
            # Try to parse as JSON to validate format
            json.loads(value)
            return value  # Keep as-is if valid JSON
        except (json.JSONDecodeError, ValueError):
            pass  # Not JSON, continue with normal processing
    
    return value

def export_table_data(conn, table_name):
    """Export data from a single table to CSV"""
    try:
        cursor = conn.cursor()
        
        # Get table info to understand column types
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        column_names = [col[1] for col in columns_info]
        
        # Fetch all data
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        if not rows:
            print(f"Table {table_name}: No data found")
            return
        
        output_file = os.path.join(OUTPUT_DIR, f"{table_name}.csv")
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
            
            # Write header
            writer.writerow(column_names)
            
            # Write data rows
            for row in rows:
                converted_row = [convert_value_for_postgres(value) for value in row]
                writer.writerow(converted_row)
        
        print(f"Exported {len(rows)} rows from {table_name} to {output_file}")
        
    except Exception as e:
        print(f"Error exporting table {table_name}: {e}")

def generate_import_script():
    """Generate PostgreSQL import script"""
    import_script = """#!/bin/bash
# PostgreSQL Data Import Script
# Run this script to import all CSV data into PostgreSQL

set -e  # Exit on any error

# Database connection details
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="chatterfix_cmms"
DB_USER="postgres"

echo "Starting data import..."

"""
    
    for table in TABLES:
        csv_file = f"{table}.csv"
        import_script += f"""
# Import {table}
echo "Importing {table}..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\\copy {table} FROM '{csv_file}' WITH (FORMAT csv, HEADER true, QUOTE '\"', ESCAPE '\"');"
"""
    
    import_script += """
echo "Data import completed successfully!"
echo "Updating sequences for SERIAL columns..."

# Update sequences for SERIAL primary keys
"""
    
    # Add sequence updates for tables with SERIAL primary keys
    serial_tables = [
        'users', 'locations', 'suppliers', 'assets', 'work_orders', 'parts',
        'pm_templates', 'maintenance_schedules', 'sensor_readings', 'ai_predictions',
        'purchase_orders', 'po_line_items', 'inventory_transactions', 'attachments',
        'audit_log', 'ocr_results', 'speech_transcriptions', 'ai_model_configs',
        'ai_request_logs', 'model_fine_tuning', 'model_ab_tests',
        'ai_prompt_templates', 'ai_alerts'
    ]
    
    for table in serial_tables:
        import_script += f"""
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT setval('{table}_id_seq', COALESCE((SELECT MAX(id) FROM {table}), 1));"
"""
    
    import_script += """
echo "All sequences updated!"
"""
    
    script_path = os.path.join(OUTPUT_DIR, "import_data.sh")
    with open(script_path, 'w') as f:
        f.write(import_script)
    
    os.chmod(script_path, 0o755)  # Make executable
    print(f"Generated import script: {script_path}")

def main():
    """Main export function"""
    print("Starting SQLite to PostgreSQL data export...")
    print(f"Source database: {SQLITE_DB_PATH}")
    
    # Create output directory
    create_output_directory()
    
    # Connect to SQLite database
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        
        # Export each table
        for table in TABLES:
            export_table_data(conn, table)
        
        # Generate import script
        generate_import_script()
        
        conn.close()
        print(f"\nExport completed successfully!")
        print(f"Output directory: {OUTPUT_DIR}")
        print(f"Files exported: {len(TABLES)} CSV files + import script")
        
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())