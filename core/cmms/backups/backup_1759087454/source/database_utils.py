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

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Enhanced database manager with transaction safety"""
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        self._local = threading.local()
        self.connection_timeout = 30.0
        self.retry_attempts = 3
        
    def get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection with enhanced configuration"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
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
                
                self._local.connection = conn
                logger.debug("Database connection established")
                
            except sqlite3.Error as e:
                logger.error(f"Database connection failed: {e}")
                raise
        
        return self._local.connection
    
    def close_connection(self):
        """Close thread-local connection"""
        if hasattr(self._local, 'connection') and self._local.connection:
            try:
                self._local.connection.close()
                self._local.connection = None
                logger.debug("Database connection closed")
            except sqlite3.Error as e:
                logger.error(f"Error closing database connection: {e}")
    
    @contextmanager
    def transaction(self, read_only: bool = False):
        """Context manager for database transactions with automatic rollback"""
        conn = self.get_connection()
        
        if read_only:
            # For read-only operations, start a deferred transaction
            conn.execute("BEGIN DEFERRED")
        else:
            # For write operations, start an immediate transaction
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
    
    def execute_with_retry(self, query: str, params: Tuple = (), fetch: str = None) -> Any:
        """Execute query with retry logic for handling locked database"""
        last_error = None
        
        for attempt in range(self.retry_attempts):
            try:
                with self.transaction(read_only=fetch is not None) as conn:
                    cursor = conn.execute(query, params)
                    
                    if fetch == 'one':
                        return cursor.fetchone()
                    elif fetch == 'all':
                        return cursor.fetchall()
                    elif fetch == 'many':
                        return cursor.fetchmany()
                    else:
                        return cursor.lastrowid
                        
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
                raise
        
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
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.execute_with_retry(query, (table_name,), fetch='one')
        return result is not None

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self.transaction(read_only=True) as conn:
                stats = {}
                
                # Get database size
                stats['file_size'] = os.path.getsize(self.database_path)
                
                # Get table count
                cursor = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                stats['table_count'] = cursor.fetchone()[0]
                
                # Get page count and size
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