#!/usr/bin/env python3
"""
ChatterFix CMMS - Database Service (Port 8001)
Handles all database operations for the microservices architecture
"""

import os
import sqlite3
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

app = FastAPI(title="ChatterFix Database Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "cmms.db")

def get_db_connection():
    """Get database connection with error handling"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

def init_database():
    """Initialize database with all required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Work Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS work_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            priority TEXT DEFAULT 'medium',
            asset_id INTEGER,
            assigned_to TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            due_date TIMESTAMP,
            completed_at TIMESTAMP,
            estimated_hours REAL,
            actual_hours REAL
        )
    ''')
    
    # Assets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            asset_type TEXT DEFAULT 'equipment',
            location TEXT,
            status TEXT DEFAULT 'active',
            manufacturer TEXT,
            model TEXT,
            serial_number TEXT,
            purchase_date DATE,
            warranty_expiry DATE,
            next_maintenance_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Parts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            part_number TEXT,
            category TEXT,
            current_stock INTEGER DEFAULT 0,
            min_stock_level INTEGER DEFAULT 5,
            max_stock_level INTEGER DEFAULT 100,
            unit_cost REAL DEFAULT 0.0,
            supplier TEXT,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT DEFAULT 'technician',
            first_name TEXT,
            last_name TEXT,
            department TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # AI Chat Sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_id INTEGER,
            message TEXT NOT NULL,
            response TEXT,
            context_type TEXT DEFAULT 'general',
            ai_provider TEXT DEFAULT 'ollama',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Work Order Parts junction table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS work_order_parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_order_id INTEGER NOT NULL,
            part_id INTEGER NOT NULL,
            quantity_used INTEGER DEFAULT 1,
            cost REAL DEFAULT 0.0,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (work_order_id) REFERENCES work_orders (id),
            FOREIGN KEY (part_id) REFERENCES parts (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    params: Optional[Dict[str, Any]] = {}

class QueryResponse(BaseModel):
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    rows_affected: Optional[int] = None

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_database()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return {
            "status": "healthy",
            "service": "ChatterFix Database Service",
            "port": 8001,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unhealthy: {str(e)}")

@app.post("/api/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """Execute a database query (SELECT)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(request.query, request.params)
        rows = cursor.fetchall()
        
        # Convert rows to list of dictionaries
        data = [dict(row) for row in rows]
        
        conn.close()
        
        return QueryResponse(success=True, data=data)
    
    except Exception as e:
        return QueryResponse(success=False, error=str(e))

@app.post("/api/execute", response_model=QueryResponse)
async def execute_command(request: QueryRequest):
    """Execute a database command (INSERT, UPDATE, DELETE)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(request.query, request.params)
        rows_affected = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return QueryResponse(success=True, rows_affected=rows_affected)
    
    except Exception as e:
        return QueryResponse(success=False, error=str(e))

@app.get("/api/tables")
async def get_tables():
    """Get list of all tables in the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return {"success": True, "tables": tables}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/schema/{table_name}")
async def get_table_schema(table_name: str):
    """Get schema for a specific table"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        schema = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
        
        conn.close()
        
        return {"success": True, "table": table_name, "schema": schema}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_database_stats():
    """Get database statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Get row counts for each table
        tables = ['work_orders', 'assets', 'parts', 'users', 'ai_chat_sessions']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[f"{table}_count"] = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='ChatterFix Database Service')
    parser.add_argument('--init-db', action='store_true', help='Initialize database and exit')
    parser.add_argument('--port', type=int, default=8001, help='Port to run service on')
    
    args = parser.parse_args()
    
    if args.init_db:
        init_database()
        print("Database initialized successfully")
        exit(0)
    
    print(f"🗄️  Starting ChatterFix Database Service on port {args.port}...")
    uvicorn.run(app, host="0.0.0.0", port=args.port)