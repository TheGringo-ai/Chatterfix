#!/usr/bin/env python3
"""
ChatterFix CMMS - Simplified Database Manager
A simple, reliable, and maintainable database management system optimized for Cloud Run.

Key Features:
- Automatic connection management with context managers
- Clean separation between PostgreSQL and SQLite
- Zero manual connection management required
- Built-in error handling and logging
- Thread-safe and Cloud Run optimized
- Simple API that any developer can understand

Usage Examples:
    # Simple query execution
    result = db.execute_query("SELECT * FROM work_orders WHERE id = ?", (123,))
    
    # Multiple results
    results = db.execute_query("SELECT * FROM work_orders", fetch='all')
    
    # Transactions
    with db.transaction() as tx:
        tx.execute("INSERT INTO work_orders (...) VALUES (...)", data)
        tx.execute("UPDATE equipment SET status = ?", ("maintenance",))
    
    # Read-only operations
    with db.read_only() as conn:
        results = conn.execute("SELECT * FROM reports").fetchall()
"""

import sqlite3
import psycopg2
import psycopg2.extras
import os
import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

class DatabaseType(Enum):
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"

@dataclass
class DatabaseConfig:
    """Database configuration container"""
    db_type: DatabaseType
    connection_string: str
    max_retries: int = 3
    retry_delay: float = 0.1
    connection_timeout: int = 30

class DatabaseError(Exception):
    """Custom database error for better error handling"""
    pass

class SimpleDatabaseManager:
    """
    Simplified database manager with automatic connection handling.
    
    This class provides a clean, simple API for database operations with:
    - Automatic connection management (no manual close() needed)
    - Built-in error handling and retries
    - Support for both PostgreSQL and SQLite
    - Context managers for transactions and read-only operations
    - Thread-safe design optimized for Cloud Run
    """
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Initialize the database manager.
        
        Args:
            config: Database configuration. If None, auto-detects from environment.
        """
        self.config = config or self._auto_detect_config()
        logger.info(f"Initialized database manager for {self.config.db_type.value}")
    
    def _auto_detect_config(self) -> DatabaseConfig:
        """Auto-detect database configuration from environment"""
        db_url = os.getenv("DATABASE_URL")
        
        if db_url and ("postgresql://" in db_url or "postgres://" in db_url):
            return DatabaseConfig(
                db_type=DatabaseType.POSTGRESQL,
                connection_string=db_url,
                connection_timeout=5  # Shorter timeout for Cloud Run
            )
        else:
            # SQLite fallback
            db_path = os.getenv("DATABASE_PATH", "./data/cmms.db")
            # Ensure directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            return DatabaseConfig(
                db_type=DatabaseType.SQLITE,
                connection_string=db_path
            )
    
    def _create_connection(self):
        """Create a new database connection"""
        try:
            if self.config.db_type == DatabaseType.POSTGRESQL:
                conn = psycopg2.connect(
                    self.config.connection_string,
                    connect_timeout=self.config.connection_timeout,
                    cursor_factory=psycopg2.extras.DictCursor
                )
                conn.autocommit = True  # Default to autocommit for simple operations
                logger.debug("PostgreSQL connection created")
                return conn
            
            else:  # SQLite
                conn = sqlite3.connect(
                    self.config.connection_string,
                    timeout=self.config.connection_timeout,
                    check_same_thread=False
                )
                
                # Optimize SQLite settings
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA foreign_keys=ON")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=10000")
                conn.execute("PRAGMA temp_store=MEMORY")
                conn.row_factory = sqlite3.Row
                
                logger.debug("SQLite connection created")
                return conn
                
        except Exception as e:
            logger.error(f"Failed to create database connection: {e}")
            raise DatabaseError(f"Connection failed: {e}")
    
    @contextmanager
    def connection(self):
        """
        Context manager for automatic connection handling.
        
        Usage:
            with db.connection() as conn:
                result = conn.execute("SELECT * FROM table")
        """
        conn = None
        try:
            conn = self._create_connection()
            yield conn
        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if conn:
                try:
                    conn.close()
                    logger.debug("Connection closed")
                except Exception as e:
                    logger.warning(f"Error closing connection: {e}")
    
    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions with automatic rollback.
        
        Usage:
            with db.transaction() as tx:
                tx.execute("INSERT INTO ...", data)
                tx.execute("UPDATE ...", data)
                # Automatic commit on success, rollback on error
        """
        conn = None
        try:
            conn = self._create_connection()
            
            if self.config.db_type == DatabaseType.POSTGRESQL:
                conn.autocommit = False
                cursor = conn.cursor()
                try:
                    yield cursor
                    conn.commit()
                    logger.debug("Transaction committed")
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Transaction rolled back: {e}")
                    raise
            else:  # SQLite
                conn.execute("BEGIN IMMEDIATE")
                try:
                    yield conn
                    conn.commit()
                    logger.debug("Transaction committed")
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Transaction rolled back: {e}")
                    raise
                    
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            raise
        finally:
            if conn:
                try:
                    conn.close()
                except Exception as e:
                    logger.warning(f"Error closing connection: {e}")
    
    @contextmanager
    def read_only(self):
        """
        Context manager for read-only operations.
        
        Usage:
            with db.read_only() as conn:
                results = conn.execute("SELECT * FROM table").fetchall()
        """
        conn = None
        try:
            conn = self._create_connection()
            
            if self.config.db_type == DatabaseType.POSTGRESQL:
                cursor = conn.cursor()
                cursor.execute("SET TRANSACTION READ ONLY")
                yield cursor
            else:  # SQLite
                conn.execute("BEGIN DEFERRED")
                yield conn
                
        except Exception as e:
            logger.error(f"Read-only operation failed: {e}")
            raise
        finally:
            if conn:
                try:
                    conn.close()
                except Exception as e:
                    logger.warning(f"Error closing connection: {e}")
    
    def execute_query(self, 
                     query: str, 
                     params: Union[Tuple, Dict] = (), 
                     fetch: Optional[str] = 'one') -> Any:
        """
        Execute a single query with automatic connection management.
        
        Args:
            query: SQL query to execute
            params: Query parameters (tuple for positional, dict for named)
            fetch: 'one', 'all', 'many', or None (for INSERT/UPDATE operations)
            
        Returns:
            Query result based on fetch parameter
            
        Usage:
            # Single result
            result = db.execute_query("SELECT * FROM users WHERE id = ?", (123,))
            
            # Multiple results
            results = db.execute_query("SELECT * FROM users", fetch='all')
            
            # Insert/Update (returns affected rows)
            affected = db.execute_query("UPDATE users SET name = ? WHERE id = ?", 
                                      ("John", 123), fetch=None)
        """
        return self._execute_with_retry(query, params, fetch)
    
    def _execute_with_retry(self, query: str, params: Union[Tuple, Dict], fetch: Optional[str]) -> Any:
        """Execute query with automatic retry logic"""
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                with self.connection() as conn:
                    if self.config.db_type == DatabaseType.POSTGRESQL:
                        cursor = conn.cursor()
                        cursor.execute(query, params)
                        
                        if fetch == 'one':
                            return cursor.fetchone()
                        elif fetch == 'all':
                            return cursor.fetchall()
                        elif fetch == 'many':
                            return cursor.fetchmany()
                        else:
                            return cursor.rowcount
                    
                    else:  # SQLite
                        cursor = conn.execute(query, params)
                        
                        if fetch == 'one':
                            return cursor.fetchone()
                        elif fetch == 'all':
                            return cursor.fetchall()
                        elif fetch == 'many':
                            return cursor.fetchmany()
                        else:
                            return cursor.rowcount
                            
            except sqlite3.OperationalError as e:
                last_error = e
                if "database is locked" in str(e).lower() and attempt < self.config.max_retries - 1:
                    wait_time = self.config.retry_delay * (2 ** attempt)
                    logger.warning(f"Database locked, retrying in {wait_time}s (attempt {attempt + 1})")
                    time.sleep(wait_time)
                    continue
                else:
                    raise DatabaseError(f"SQLite error: {e}")
            
            except Exception as e:
                logger.error(f"Database operation failed: {e}")
                raise DatabaseError(f"Query execution failed: {e}")
        
        # If all retries failed
        raise DatabaseError(f"Operation failed after {self.config.max_retries} attempts: {last_error}")
    
    def execute_many(self, query: str, param_list: List[Union[Tuple, Dict]]) -> int:
        """
        Execute the same query multiple times with different parameters.
        
        Args:
            query: SQL query to execute
            param_list: List of parameter tuples/dicts
            
        Returns:
            Number of affected rows
            
        Usage:
            affected = db.execute_many(
                "INSERT INTO users (name, email) VALUES (?, ?)",
                [("John", "john@example.com"), ("Jane", "jane@example.com")]
            )
        """
        try:
            with self.transaction() as tx:
                if self.config.db_type == DatabaseType.POSTGRESQL:
                    for params in param_list:
                        tx.execute(query, params)
                    return len(param_list)
                else:  # SQLite
                    cursor = tx.executemany(query, param_list)
                    return cursor.rowcount
                    
        except Exception as e:
            logger.error(f"Batch operation failed: {e}")
            raise DatabaseError(f"Batch execution failed: {e}")
    
    def check_table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database"""
        try:
            if self.config.db_type == DatabaseType.POSTGRESQL:
                query = """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    )
                """
                result = self.execute_query(query, (table_name,))
                return result[0] if result else False
            else:  # SQLite
                query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
                result = self.execute_query(query, (table_name,))
                return result is not None
                
        except Exception as e:
            logger.error(f"Failed to check table existence: {e}")
            return False
    
    def get_table_list(self) -> List[str]:
        """Get list of all tables in the database"""
        try:
            if self.config.db_type == DatabaseType.POSTGRESQL:
                query = """
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                """
                results = self.execute_query(query, fetch='all')
                return [row[0] for row in results] if results else []
            else:  # SQLite
                query = "SELECT name FROM sqlite_master WHERE type='table'"
                results = self.execute_query(query, fetch='all')
                return [row['name'] for row in results] if results else []
                
        except Exception as e:
            logger.error(f"Failed to get table list: {e}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a comprehensive health check of the database.
        
        Returns:
            Dictionary with health status information
        """
        health = {
            'status': 'unknown',
            'database_type': self.config.db_type.value,
            'connection': False,
            'tables': 0,
            'errors': []
        }
        
        try:
            # Test basic connection
            with self.connection() as conn:
                health['connection'] = True
                
                # Count tables
                tables = self.get_table_list()
                health['tables'] = len(tables)
                
                # Test a simple query
                if self.config.db_type == DatabaseType.POSTGRESQL:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                else:  # SQLite
                    cursor = conn.execute("SELECT 1")
                    result = cursor.fetchone()
                
                if result:
                    health['status'] = 'healthy'
                else:
                    health['status'] = 'degraded'
                    health['errors'].append("Test query returned no result")
                    
        except Exception as e:
            health['status'] = 'error'
            health['errors'].append(str(e))
            logger.error(f"Database health check failed: {e}")
        
        return health

# Global database manager instance
# This can be imported and used throughout the application
db = SimpleDatabaseManager()

# Convenience functions for backward compatibility
def get_database_manager() -> SimpleDatabaseManager:
    """Get the global database manager instance"""
    return db

def execute_query(query: str, params: Union[Tuple, Dict] = (), fetch: Optional[str] = 'one') -> Any:
    """Execute a query using the global database manager"""
    return db.execute_query(query, params, fetch)

def check_database_health() -> Dict[str, Any]:
    """Check database health using the global database manager"""
    return db.health_check()