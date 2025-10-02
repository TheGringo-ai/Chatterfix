#!/usr/bin/env python3
"""
ChatterFix CMMS Enterprise - Enhanced Database Utilities
Transaction safety and connection management
"""

import sqlite3
import logging
import time
import threading
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple
import os

try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

logger = logging.getLogger(__name__)

def is_postgresql():
    """Check if we're using PostgreSQL or SQLite"""
    db_url = os.getenv("DATABASE_URL")
    return db_url is not None and POSTGRES_AVAILABLE and ("postgresql://" in db_url or "postgres://" in db_url)

def get_table_exists_query(table_name):
    """Get database-agnostic query to check if table exists"""
    if is_postgresql():
        return """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """, (table_name,)
    else:
        return "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)

def get_table_count_query():
    """Get database-agnostic query to count tables"""
    if is_postgresql():
        return """
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """, ()
    else:
        return "SELECT COUNT(*) FROM sqlite_master WHERE type='table'", ()

class DatabaseManager:
    """Enhanced database manager with transaction safety"""
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        self._local = threading.local()
        self.connection_timeout = 30.0
        self.retry_attempts = 3
        
    def get_connection(self):
        """Get fresh database connection for each request (Cloud Run optimized)"""
        # Check if we should use PostgreSQL
        if is_postgresql():
            try:
                # PostgreSQL connection
                if not POSTGRES_AVAILABLE:
                    raise ImportError("psycopg2 not available for PostgreSQL connection")
                
                db_url = os.getenv("DATABASE_URL")
                conn = psycopg2.connect(db_url, connect_timeout=5)
                conn.cursor_factory = psycopg2.extras.DictCursor
                logger.debug("PostgreSQL database connection established")
                return conn
                
            except Exception as e:
                logger.warning(f"PostgreSQL connection failed: {e}, falling back to SQLite")
        
        # SQLite fallback
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.database_path), exist_ok=True)
            
            # Create connection with optimized settings
            conn = sqlite3.connect(
                self.database_path,
                timeout=self.connection_timeout,
                check_same_thread=False
            )
            
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys=ON")
            
            # Optimize for performance
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")
            
            # Set row factory for easier data access
            conn.row_factory = sqlite3.Row
            
            logger.debug("SQLite database connection established")
            return conn
            
        except sqlite3.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def close_connection(self):
        """Close thread-local connection"""
        if hasattr(self._local, 'connection') and self._local.connection:
            try:
                self._local.connection.close()
                logger.debug("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
            finally:
                self._local.connection = None
    
    @contextmanager
    def managed_connection(self):
        """Context manager for safe connection handling"""
        conn = self.get_connection()
        try:
            yield conn
        finally:
            self.close_connection()
    
    @contextmanager
    def transaction(self, read_only: bool = False):
        """Context manager for database transactions with automatic rollback and connection closing."""
        conn = self.get_connection()
        try:
            if is_postgresql():
                # PostgreSQL transaction handling
                try:
                    yield conn
                    if not read_only:
                        conn.commit()
                        logger.debug("Transaction committed successfully")
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Transaction rolled back due to error: {e}")
                    raise
            else:
                # SQLite transaction handling
                if read_only:
                    conn.execute("BEGIN DEFERRED")
                else:
                    conn.execute("BEGIN IMMEDIATE")
                
                try:
                    yield conn
                    if not read_only:
                        conn.commit()
                        logger.debug("Transaction committed successfully")
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Transaction rolled back due to error: {e}")
                    raise
        finally:
            self.close_connection()

    def execute_with_retry(self, query: str, params: Tuple = (), fetch: str = None) -> Any:
        """Execute query with retry logic and proper connection management"""
        last_error = None
        
        for attempt in range(self.retry_attempts):
            conn = None
            try:
                # Get fresh connection for each attempt
                conn = self.get_connection()
                
                if is_postgresql():
                    # PostgreSQL execution with proper transaction handling
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    
                    if fetch == 'one':
                        result = cursor.fetchone()
                    elif fetch == 'all':
                        result = cursor.fetchall()
                    elif fetch == 'many':
                        result = cursor.fetchmany()
                    else:
                        result = cursor.rowcount
                    
                    # Commit for PostgreSQL
                    conn.commit()
                    return result
                    
                else:
                    # SQLite execution
                    cursor = conn.execute(query, params)
                    
                    if fetch == 'one':
                        result = cursor.fetchone()
                    elif fetch == 'all':
                        result = cursor.fetchall()
                    elif fetch == 'many':
                        result = cursor.fetchmany()
                    else:
                        result = cursor.lastrowid
                    
                    # Commit for SQLite
                    conn.commit()
                    return result
                        
            except sqlite3.OperationalError as e:
                last_error = e
                if "database is locked" in str(e).lower():
                    # Wait before retry for locked database
                    wait_time = 0.1 * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Database locked, retrying in {wait_time}s (attempt {attempt + 1})")
                    time.sleep(wait_time)
                    continue
                else:
                    raise
            except Exception as e:
                logger.error(f"Database operation failed: {e}")
                if conn:
                    try:
                        conn.rollback()
                    except:
                        pass
                raise
            finally:
                # Always close the connection
                if conn:
                    try:
                        conn.close()
                    except:
                        pass
        
        # If all retries failed
        logger.error(f"Database operation failed after {self.retry_attempts} attempts")
        raise last_error

    def execute_many_with_transaction(self, query: str, param_list: List[Tuple]) -> int:
        """Execute multiple statements in a single transaction"""
        try:
            with self.transaction() as conn:
                cursor = conn.executemany(query, param_list)
                affected_rows = cursor.rowcount
                logger.debug(f"Batch operation completed: {affected_rows} rows affected")
                return affected_rows
        except Exception as e:
            logger.error(f"Batch database operation failed: {e}")
            raise

    def create_backup(self, backup_path: str) -> bool:
        """Create database backup"""
        try:
            with self.transaction(read_only=True) as conn:
                backup = sqlite3.connect(backup_path)
                conn.backup(backup)
                backup.close()
                logger.info(f"Database backup created: {backup_path}")
                return True
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False

    def vacuum_database(self) -> bool:
        """Vacuum database to reclaim space and optimize"""
        try:
            conn = self.get_connection()
            conn.execute("VACUUM")
            logger.info("Database vacuum completed")
            return True
        except Exception as e:
            logger.error(f"Database vacuum failed: {e}")
            return False

    def get_table_info(self, table_name: str) -> List[sqlite3.Row]:
        """Get table schema information"""
        query = "PRAGMA table_info(?)"
        return self.execute_with_retry(query, (table_name,), fetch='all')

    def check_table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        query, params = get_table_exists_query(table_name)
        result = self.execute_with_retry(query, params, fetch='one')
        if is_postgresql():
            return result is not None and result[0]
        else:
            return result is not None

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self.transaction(read_only=True) as conn:
                stats = {}
                
                # Get database size
                stats['file_size'] = os.path.getsize(self.database_path)
                
                # Get table count using database-agnostic query
                query, params = get_table_count_query()
                cursor = conn.execute(query, params)
                stats['table_count'] = cursor.fetchone()[0]
                
                # Get database-specific metrics
                if is_postgresql():
                    # PostgreSQL: Get database size from pg_database
                    cursor = conn.execute("SELECT pg_database_size(current_database())")
                    db_size = cursor.fetchone()[0]
                    stats['page_count'] = db_size // 8192  # Assume 8KB pages
                    stats['page_size'] = 8192
                    stats['database_size_pages'] = stats['page_count']
                else:
                    # SQLite: Use PRAGMA commands
                    cursor = conn.execute("PRAGMA page_count")
                    stats['page_count'] = cursor.fetchone()[0]
                    
                    cursor = conn.execute("PRAGMA page_size")
                    stats['page_size'] = cursor.fetchone()[0]
                    
                    # Calculate database size in pages
                    stats['database_size_pages'] = stats['page_count']
                
                return stats
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}

# Global database manager instance
DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/cmms.db")
db_manager = DatabaseManager(DATABASE_PATH)

# Convenience functions for common operations
def get_db_connection():
    """Get database connection (legacy compatibility)"""
    return db_manager.get_connection()

def execute_query(query: str, params: Tuple = (), fetch: str = None):
    """Execute query with enhanced error handling"""
    return db_manager.execute_with_retry(query, params, fetch)

def execute_transaction(operations: List[Tuple[str, Tuple]]) -> bool:
    """Execute multiple operations in a single transaction"""
    try:
        with db_manager.transaction() as conn:
            for query, params in operations:
                conn.execute(query, params)
        return True
    except Exception as e:
        logger.error(f"Transaction failed: {e}")
        return False

# Database health check
def check_database_health() -> Dict[str, Any]:
    """Comprehensive database health check"""
    health = {
        'status': 'unknown',
        'connection': False,
        'integrity': False,
        'stats': {},
        'errors': []
    }
    
    try:
        # Test connection
        conn = db_manager.get_connection()
        health['connection'] = True
        
        # Check integrity
        cursor = conn.execute("PRAGMA integrity_check")
        integrity_result = cursor.fetchone()[0]
        health['integrity'] = integrity_result == 'ok'
        
        if not health['integrity']:
            health['errors'].append(f"Integrity check failed: {integrity_result}")
        
        # Get database stats
        health['stats'] = db_manager.get_database_stats()
        
        # Overall status
        if health['connection'] and health['integrity']:
            health['status'] = 'healthy'
        else:
            health['status'] = 'degraded'
            
    except Exception as e:
        health['status'] = 'error'
        health['errors'].append(str(e))
        logger.error(f"Database health check failed: {e}")
    
    return health