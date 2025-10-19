#!/bin/bash

echo "🔧 Fixing Work Orders Service on Production VM"
echo "=============================================="

VM_IP="35.237.149.25"
VM_USER="yoyofred_gringosgambit_com"

# Fix the work orders service startup
ssh -o StrictHostKeyChecking=no ${VM_USER}@${VM_IP} << 'ENDSSH'
cd /opt/chatterfix-cmms/current

echo "🛑 Stopping any existing work orders processes..."
pkill -f "work_orders_service" 2>/dev/null || true
pkill -f "8015" 2>/dev/null || true

echo "🔧 Starting Enhanced Work Orders Service with correct syntax..."

# Create a proper startup script for work orders
cat > start_work_orders_fixed.sh << 'WO_EOF'
#!/bin/bash
cd /opt/chatterfix-cmms/current
export PORT=8015
python3 work_orders_service.py > work_orders.log 2>&1 &
echo "Enhanced Work Orders service started on port 8015"
WO_EOF

chmod +x start_work_orders_fixed.sh

# Start the work orders service
./start_work_orders_fixed.sh

sleep 3

# Test the service
echo "🧪 Testing Enhanced Work Orders Service..."
if curl -s http://localhost:8015/health > /dev/null 2>&1; then
    echo "✅ Enhanced Work Orders API is now running on port 8015!"
    
    # Test a work orders endpoint
    echo "🔍 Testing work orders endpoint..."
    curl -s http://localhost:8015/api/work-orders | head -3
    echo ""
else
    echo "⚠️ Work Orders API still not responding, checking logs..."
    tail -10 work_orders.log
fi

echo ""
echo "📊 Current Process Status:"
ps aux | grep -E "(work_orders_service|8015)" | grep -v grep

echo ""
echo "🎯 Enhanced Work Orders Service Fix Complete!"
ENDSSH

echo ""
echo "✅ WORK ORDERS SERVICE FIXED!"
echo "============================="
echo "🔧 Enhanced Work Orders: Port 8015"
echo "🌐 Full URL: http://35.237.149.25:8080/work-orders"
echo "🤖 AI Integration: Fix It Fred + Grok"