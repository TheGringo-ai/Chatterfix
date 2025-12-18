#!/bin/bash
# Test the application locally to debug issues

echo "🧪 Testing ChatterFix locally..."
echo "================================"

# Test Python imports
echo "1. Testing Python imports..."
python3 -c "
import sys
sys.path.append('.')
try:
    import main
    print('✅ Main module imports successfully')
    from app.routers import training
    print('✅ Training router imports successfully') 
    from app.core.firestore_db import get_firestore_manager
    print('✅ Firestore manager imports successfully')
except Exception as e:
    print(f'❌ Import error: {e}')
"

echo ""
echo "2. Testing with uvicorn directly..."
echo "Starting server for 10 seconds..."

# Test with uvicorn directly
timeout 10 python3 -m uvicorn main:app --host 0.0.0.0 --port 8080 &
SERVER_PID=$!

sleep 5
echo "Testing health endpoint..."
curl -s http://localhost:8080/health | python3 -m json.tool 2>/dev/null || echo "Health endpoint not ready"

echo "Testing test endpoint..."
curl -s http://localhost:8080/test | python3 -m json.tool 2>/dev/null || echo "Test endpoint not ready"

# Cleanup
kill $SERVER_PID 2>/dev/null || true

echo ""
echo "3. Checking VERSION.txt..."
if [ -f "VERSION.txt" ]; then
    echo "✅ VERSION.txt exists:"
    head -3 VERSION.txt
else
    echo "❌ VERSION.txt missing"
fi

echo ""
echo "4. Testing Docker build..."
echo "Building test image..."
docker build -t chatterfix-test . --platform linux/amd64
echo "✅ Docker build successful"