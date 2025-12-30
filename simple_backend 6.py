#!/usr/bin/env python3
"""
Simple ChatterFix Backend - Minimal Version
Guaranteed to work on single VM
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sqlite3
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="ChatterFix Simple Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize simple database
def init_simple_db():
    conn = sqlite3.connect('simple_chatterfix.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_orders (
            id INTEGER PRIMARY KEY,
            title TEXT,
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Add sample data
    cursor.execute("SELECT COUNT(*) FROM work_orders")
    if cursor.fetchone()[0] == 0:
        sample_orders = [
            ("HVAC Maintenance", "open"),
            ("Pump Repair", "in-progress"),
            ("Safety Check", "completed")
        ]
        cursor.executemany(
            "INSERT INTO work_orders (title, status) VALUES (?, ?)",
            sample_orders
        )
    
    conn.commit()
    conn.close()

init_simple_db()

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "ChatterFix Simple Backend",
        "timestamp": datetime.now().isoformat(),
        "port": 8081,
        "database": "sqlite_working"
    }

@app.get("/api/work-orders")
def get_work_orders():
    conn = sqlite3.connect('simple_chatterfix.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM work_orders")
    
    orders = []
    for row in cursor.fetchall():
        orders.append({
            "id": row[0],
            "title": row[1], 
            "status": row[2],
            "created_at": row[3]
        })
    
    conn.close()
    return {"work_orders": orders, "count": len(orders)}

@app.get("/api/status")
def status():
    return {
        "backend": "running",
        "database": "sqlite",
        "apis": ["work_orders"],
        "message": "Simple backend operational"
    }

if __name__ == "__main__":
    print("🚀 Starting Simple ChatterFix Backend on port 8081...")
    uvicorn.run(app, host="0.0.0.0", port=8081)
