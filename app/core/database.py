import logging

logger = logging.getLogger(__name__)

def init_database():
    """Initialize the database (No-op for Firestore-only mode)"""
    logger.info("Database initialization skipped (Firestore mode)")

def get_db_connection():
    """Get a database connection (Deprecated/Removed)"""
    raise ImportError("SQLite support has been removed. Use Firestore.")

def get_database():
    """Get the preferred database adapter"""
    from app.core.db_adapter import get_db_adapter
    return get_db_adapter()

def get_db_connection_sqlite():
    """Get a direct SQLite connection (Removed)"""
    raise ImportError("SQLite support has been removed.")
