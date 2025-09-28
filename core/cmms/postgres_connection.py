"""
PostgreSQL Database Connection Utility for ChatterFix CMMS
Replaces SQLite connection with PostgreSQL Cloud SQL connection
"""

import os
import psycopg2
import psycopg2.extras
from typing import Optional, Dict, Any
import logging
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration from environment variables
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'chatterfix_cmms'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'sslmode': os.getenv('DB_SSLMODE', 'prefer')
}

class PostgreSQLManager:
    """PostgreSQL database manager for ChatterFix CMMS"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize PostgreSQL manager with configuration"""
        self.config = config or DATABASE_CONFIG
        self.connection_pool = None
        
    def get_connection_string(self) -> str:
        """Generate PostgreSQL connection string"""
        return (
            f"postgresql://{self.config['user']}:{self.config['password']}"
            f"@{self.config['host']}:{self.config['port']}"
            f"/{self.config['database']}?sslmode={self.config['sslmode']}"
        )
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with automatic cleanup"""
        conn = None
        try:
            conn = psycopg2.connect(**self.config)
            conn.autocommit = False  # Enable transaction control
            yield conn
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self, dict_cursor=True):
        """Get a database cursor with automatic cleanup"""
        with self.get_connection() as conn:
            cursor_factory = psycopg2.extras.DictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor, conn
            except Exception as e:
                conn.rollback()
                logger.error(f"Database cursor error: {e}")
                raise
            else:
                conn.commit()
            finally:
                cursor.close()
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    return result[0] == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def execute_query(self, query: str, params: tuple = None, fetch_results: bool = True):
        """Execute a query with optional parameters"""
        try:
            with self.get_cursor() as (cursor, conn):
                cursor.execute(query, params)
                if fetch_results:
                    return cursor.fetchall()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def execute_many(self, query: str, params_list: list):
        """Execute a query with multiple parameter sets"""
        try:
            with self.get_cursor() as (cursor, conn):
                cursor.executemany(query, params_list)
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Bulk query execution failed: {e}")
            raise

# Global database manager instance
db_manager = PostgreSQLManager()

# Convenience functions for backward compatibility with SQLite code
def get_db_connection():
    """Get database connection (compatibility function)"""
    return db_manager.get_connection()

def get_db_cursor():
    """Get database cursor (compatibility function)"""
    return db_manager.get_cursor()

# Environment variable for database path (compatibility)
DATABASE_PATH = db_manager.get_connection_string()

# Test the connection on import
if __name__ == "__main__":
    print("Testing PostgreSQL connection...")
    if db_manager.test_connection():
        print("✓ PostgreSQL connection successful!")
        
        # Test a simple query
        try:
            result = db_manager.execute_query("SELECT version()")
            print(f"✓ PostgreSQL version: {result[0][0]}")
        except Exception as e:
            print(f"✗ Query test failed: {e}")
    else:
        print("✗ PostgreSQL connection failed!")
        print("Please check your database configuration:")
        for key, value in DATABASE_CONFIG.items():
            if key == 'password':
                print(f"  {key}: {'*' * len(value) if value else 'NOT SET'}")
            else:
                print(f"  {key}: {value}")