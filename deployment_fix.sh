#!/bin/bash
set -e

echo "🔧 ChatterFix Deployment Fix"
echo "============================"

cd /home/yoyofred_gringosgambit_com

# Kill any existing backend processes
pkill -f "python.*8081" || true
pkill -f "simple_backend" || true

# Install dependencies quietly
python3 -m pip install --user --quiet fastapi uvicorn

# Create simple backend (embedded in script)
cat > simple_backend.py << 'SIMPLE_EOF'
#!/usr/bin/env python3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sqlite3
from datetime import datetime

app = FastAPI(title="ChatterFix Simple Backend")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def init_db():
    conn = sqlite3.connect('simple_chatterfix.db')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS work_orders (id INTEGER PRIMARY KEY, title TEXT, status TEXT DEFAULT 'open', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    cursor.execute("SELECT COUNT(*) FROM work_orders")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO work_orders (title, status) VALUES (?, ?)", [("HVAC Maintenance", "open"), ("Pump Repair", "in-progress"), ("Safety Check", "completed")])
    conn.commit()
    conn.close()

init_db()

@app.get("/health")
def health():
    return {"status": "healthy", "service": "ChatterFix Simple Backend", "timestamp": datetime.now().isoformat(), "port": 8081}

@app.get("/api/work-orders")
def get_work_orders():
    conn = sqlite3.connect('simple_chatterfix.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM work_orders")
    orders = [{"id": row[0], "title": row[1], "status": row[2], "created_at": row[3]} for row in cursor.fetchall()]
    conn.close()
    return {"work_orders": orders, "count": len(orders)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)
SIMPLE_EOF

# Start the simple backend
echo "🚀 Starting simple backend..."
nohup python3 simple_backend.py > simple_backend.log 2>&1 &

# Wait and test
sleep 5
if curl -s http://localhost:8081/health > /dev/null; then
    echo "✅ Simple backend is running on port 8081"
else
    echo "⚠️ Backend may still be starting"
fi

echo "✅ Deployment fix completed"
