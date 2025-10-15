#!/bin/bash
set -e

echo "🎯 Final Backend Deployment"
echo "=========================="

cd /home/yoyofred_gringosgambit_com

# Kill existing processes on port 8081
echo "🛑 Stopping existing services..."
lsof -ti:8081 | xargs kill -9 || true
pkill -f "python.*8081" || true
pkill -f "uvicorn.*8081" || true
sleep 3

# Install requirements
echo "📦 Installing FastAPI..."
python3 -m pip install --user --quiet fastapi uvicorn

# Create the backend file
echo "📝 Creating backend..."
cat > chatterfix_backend.py << 'BACKEND_CODE'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sqlite3
from datetime import datetime

app = FastAPI(title="ChatterFix Backend")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def init_db():
    conn = sqlite3.connect('chatterfix.db')
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
    return {"status": "healthy", "service": "ChatterFix Backend", "timestamp": datetime.now().isoformat(), "port": 8081}

@app.get("/api/work-orders")
def get_work_orders():
    conn = sqlite3.connect('chatterfix.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM work_orders")
    orders = [{"id": row[0], "title": row[1], "status": row[2], "created_at": row[3]} for row in cursor.fetchall()]
    conn.close()
    return {"work_orders": orders, "count": len(orders)}

@app.get("/api/dashboard")
def dashboard():
    conn = sqlite3.connect('chatterfix.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM work_orders")
    count = cursor.fetchone()[0]
    conn.close()
    return {"work_orders": count, "status": "operational"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)
BACKEND_CODE

# Start backend
echo "🚀 Starting backend on port 8081..."
nohup python3 chatterfix_backend.py > backend.log 2>&1 &

# Wait for startup
sleep 10

# Test backend
echo "🧪 Testing backend..."
if curl -s http://localhost:8081/health; then
    echo ""
    echo "✅ Backend is running!"
else
    echo ""
    echo "⚠️ Backend may still be starting..."
fi

echo "✅ Deployment complete!"
