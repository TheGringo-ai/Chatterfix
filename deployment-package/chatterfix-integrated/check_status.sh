#!/bin/bash
echo "🔍 ChatterFix Integrated System Status"
echo "====================================="

echo ""
echo "📊 Service Status:"
for port in 8001 8002 8003 8004 8005; do
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "  ✅ Port $port: Running"
    else
        echo "  ❌ Port $port: Not responding"
    fi
done

echo ""
echo "🔗 Process Status:"
echo "Database Service:    $(pgrep -f database_service.py || echo 'Not running')"
echo "Work Orders Service: $(pgrep -f work_orders_service.py || echo 'Not running')"
echo "Assets Service:      $(pgrep -f assets_service.py || echo 'Not running')"
echo "Parts Service:       $(pgrep -f parts_service.py || echo 'Not running')"
echo "Fix It Fred AI:      $(pgrep -f fix_it_fred_universal_ai.py || echo 'Not running')"

echo ""
echo "📝 Recent logs:"
echo "Last 5 lines from Fix It Fred AI:"
tail -5 logs/fix_it_fred.log 2>/dev/null || echo "No log file found"
