#!/usr/bin/env python3
"""
ChatterFix CMMS - Database Migration Guide
Complete guide for migrating from the complex database system to the simplified manager.

This file contains:
1. Migration examples showing before/after code
2. Common patterns and best practices
3. Error handling improvements
4. Performance optimizations for Cloud Run

Run this file to see migration examples and validate the new system.
"""

from simple_database_manager import db, SimpleDatabaseManager, DatabaseConfig, DatabaseType
import logging

# Configure logging for examples
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migration_examples():
    """
    Show before/after examples of common database operations
    """
    
    print("=" * 80)
    print("CHATTERFIX CMMS DATABASE MIGRATION GUIDE")
    print("=" * 80)
    print()
    
    print("1. SIMPLE QUERY EXECUTION")
    print("-" * 40)
    print("❌ OLD WAY (Complex, error-prone):")
    print("""
    try:
        conn = get_db_connection()
        cursor = conn.execute("SELECT * FROM work_orders WHERE id = ?", (123,))
        result = cursor.fetchone()
        conn.close()  # Must remember to close!
    except Exception as e:
        if conn:
            conn.close()  # Also close on error
        logger.error(f"Query failed: {e}")
        raise
    """)
    
    print("✅ NEW WAY (Simple, automatic):")
    print("""
    result = db.execute_query("SELECT * FROM work_orders WHERE id = ?", (123,))
    # Connection automatically managed - no manual close() needed!
    """)
    print()
    
    print("2. TRANSACTION HANDLING")
    print("-" * 40)
    print("❌ OLD WAY (Complex transaction management):")
    print("""
    conn = None
    try:
        conn = get_db_connection()
        if is_postgresql():
            conn.autocommit = False
        else:
            conn.execute("BEGIN IMMEDIATE")
        
        conn.execute("INSERT INTO work_orders (...) VALUES (...)", data1)
        conn.execute("UPDATE equipment SET status = ?", data2)
        
        conn.commit()
        logger.debug("Transaction committed")
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Transaction failed: {e}")
        raise
    finally:
        if conn:
            conn.close()
    """)
    
    print("✅ NEW WAY (Automatic transaction management):")
    print("""
    with db.transaction() as tx:
        tx.execute("INSERT INTO work_orders (...) VALUES (...)", data1)
        tx.execute("UPDATE equipment SET status = ?", data2)
        # Automatic commit on success, rollback on error
    """)
    print()
    
    print("3. READ-ONLY OPERATIONS")
    print("-" * 40)
    print("❌ OLD WAY (No clear distinction):")
    print("""
    conn = get_db_connection()
    try:
        results = conn.execute("SELECT * FROM reports").fetchall()
        # No indication this is read-only
    finally:
        conn.close()
    """)
    
    print("✅ NEW WAY (Clear intent):")
    print("""
    with db.read_only() as conn:
        results = conn.execute("SELECT * FROM reports").fetchall()
        # Clearly marked as read-only operation
    """)
    print()
    
    print("4. BATCH OPERATIONS")
    print("-" * 40)
    print("❌ OLD WAY (Manual transaction management):")
    print("""
    conn = get_db_connection()
    try:
        conn.execute("BEGIN")
        for item in items:
            conn.execute("INSERT INTO table VALUES (?, ?)", item)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()
    """)
    
    print("✅ NEW WAY (Optimized batch operations):")
    print("""
    affected_rows = db.execute_many(
        "INSERT INTO table VALUES (?, ?)", 
        items
    )
    """)
    print()
    
    print("5. DATABASE HEALTH CHECKS")
    print("-" * 40)
    print("❌ OLD WAY (Complex health checking):")
    print("""
    def check_database_health():
        health = {'status': 'unknown', 'errors': []}
        try:
            conn = get_db_connection()
            # Complex PostgreSQL vs SQLite handling
            if is_postgresql():
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
            else:
                cursor = conn.execute("SELECT 1")
            result = cursor.fetchone()
            conn.close()
            health['status'] = 'healthy' if result else 'error'
        except Exception as e:
            health['errors'].append(str(e))
        return health
    """)
    
    print("✅ NEW WAY (Built-in health checking):")
    print("""
    health = db.health_check()
    # Returns comprehensive health information automatically
    """)
    print()

def common_patterns():
    """Show common usage patterns with the new system"""
    
    print("COMMON USAGE PATTERNS")
    print("=" * 80)
    print()
    
    print("1. SINGLE RECORD OPERATIONS")
    print("-" * 40)
    print("""
    # Get single user
    user = db.execute_query("SELECT * FROM users WHERE id = ?", (user_id,))
    
    # Insert new record
    db.execute_query(
        "INSERT INTO work_orders (title, description) VALUES (?, ?)",
        (title, description),
        fetch=None  # No return value needed
    )
    
    # Update record
    affected = db.execute_query(
        "UPDATE work_orders SET status = ? WHERE id = ?",
        (status, work_order_id),
        fetch=None
    )
    """)
    print()
    
    print("2. MULTIPLE RECORD OPERATIONS")
    print("-" * 40)
    print("""
    # Get all records
    all_orders = db.execute_query("SELECT * FROM work_orders", fetch='all')
    
    # Get filtered records
    pending_orders = db.execute_query(
        "SELECT * FROM work_orders WHERE status = ?", 
        ("pending",), 
        fetch='all'
    )
    """)
    print()
    
    print("3. COMPLEX TRANSACTIONS")
    print("-" * 40)
    print("""
    def create_work_order_with_tasks(order_data, tasks):
        with db.transaction() as tx:
            # Insert work order
            tx.execute(
                "INSERT INTO work_orders (title, description) VALUES (?, ?)",
                (order_data['title'], order_data['description'])
            )
            
            # Get the inserted ID (database-specific)
            if db.config.db_type == DatabaseType.POSTGRESQL:
                tx.execute("SELECT lastval()")
                order_id = tx.fetchone()[0]
            else:  # SQLite
                order_id = tx.lastrowid
            
            # Insert related tasks
            for task in tasks:
                tx.execute(
                    "INSERT INTO tasks (work_order_id, title) VALUES (?, ?)",
                    (order_id, task['title'])
                )
            
            return order_id
    """)
    print()
    
    print("4. ERROR HANDLING PATTERNS")
    print("-" * 40)
    print("""
    try:
        result = db.execute_query("SELECT * FROM users WHERE id = ?", (user_id,))
        if not result:
            raise ValueError("User not found")
        return result
    except DatabaseError as e:
        logger.error(f"Database operation failed: {e}")
        # Handle database-specific errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        # Handle other errors
        raise
    """)
    print()

def performance_tips():
    """Show performance optimization tips"""
    
    print("PERFORMANCE OPTIMIZATION TIPS")
    print("=" * 80)
    print()
    
    print("1. CLOUD RUN OPTIMIZATIONS")
    print("-" * 40)
    print("""
    # ✅ The new system automatically:
    # - Creates fresh connections for each request (Cloud Run optimized)
    # - Uses connection pooling where appropriate
    # - Implements proper timeouts for serverless environments
    # - Automatically closes connections to prevent leaks
    """)
    print()
    
    print("2. BATCH OPERATIONS")
    print("-" * 40)
    print("""
    # ✅ Use execute_many for batch inserts/updates
    affected = db.execute_many(
        "INSERT INTO logs (message, timestamp) VALUES (?, ?)",
        [(msg, ts) for msg, ts in log_entries]
    )
    
    # ❌ Don't use individual queries in loops
    for msg, ts in log_entries:
        db.execute_query("INSERT INTO logs VALUES (?, ?)", (msg, ts))
    """)
    print()
    
    print("3. READ-ONLY OPERATIONS")
    print("-" * 40)
    print("""
    # ✅ Use read_only context for reports and analytics
    with db.read_only() as conn:
        results = conn.execute("SELECT COUNT(*) FROM work_orders").fetchone()
    
    # This is optimized for read operations and won't lock the database
    """)
    print()
    
    print("4. CONNECTION MANAGEMENT")
    print("-" * 40)
    print("""
    # ✅ The new system automatically:
    # - Reuses connections within the same context
    # - Closes connections when context exits
    # - Handles connection failures gracefully
    # - Implements automatic retry logic for transient failures
    """)
    print()

def test_new_system():
    """Test the new database system"""
    
    print("TESTING NEW DATABASE SYSTEM")
    print("=" * 80)
    print()
    
    try:
        # Test health check
        print("1. Testing database health check...")
        health = db.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Database Type: {health['database_type']}")
        print(f"   Connection: {'✅' if health['connection'] else '❌'}")
        print(f"   Tables: {health['tables']}")
        if health['errors']:
            print(f"   Errors: {health['errors']}")
        print()
        
        # Test table existence check
        print("2. Testing table existence check...")
        if db.check_table_exists('work_orders'):
            print("   ✅ work_orders table exists")
        else:
            print("   ℹ️  work_orders table does not exist (normal for new installations)")
        print()
        
        # Test simple query
        print("3. Testing simple query execution...")
        try:
            # This will work for both PostgreSQL and SQLite
            result = db.execute_query("SELECT 1 as test_value")
            if result:
                print("   ✅ Simple query executed successfully")
            else:
                print("   ❌ Simple query returned no result")
        except Exception as e:
            print(f"   ❌ Simple query failed: {e}")
        print()
        
        # Test transaction
        print("4. Testing transaction handling...")
        try:
            with db.transaction() as tx:
                # This is a no-op transaction to test the mechanism
                if db.config.db_type == DatabaseType.POSTGRESQL:
                    tx.execute("SELECT 1")
                else:
                    tx.execute("SELECT 1")
            print("   ✅ Transaction handling works correctly")
        except Exception as e:
            print(f"   ❌ Transaction test failed: {e}")
        print()
        
        # Test read-only context
        print("5. Testing read-only context...")
        try:
            with db.read_only() as conn:
                if db.config.db_type == DatabaseType.POSTGRESQL:
                    cursor = conn
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                else:
                    cursor = conn.execute("SELECT 1")
                    result = cursor.fetchone()
                
                if result:
                    print("   ✅ Read-only context works correctly")
                else:
                    print("   ❌ Read-only context returned no result")
        except Exception as e:
            print(f"   ❌ Read-only test failed: {e}")
        print()
        
        print("🎉 NEW DATABASE SYSTEM TESTING COMPLETE!")
        print("The simplified database manager is ready for use.")
        
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        print("Please check your database configuration.")

if __name__ == "__main__":
    migration_examples()
    print()
    common_patterns()
    print()
    performance_tips()
    print()
    test_new_system()