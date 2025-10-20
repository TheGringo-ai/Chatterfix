#!/bin/bash
echo "🛑 Stopping ChatterFix Integrated System"
echo "========================================"

pkill -f "python.*database_service.py" || true
pkill -f "python.*work_orders_service.py" || true
pkill -f "python.*assets_service.py" || true
pkill -f "python.*parts_service.py" || true
pkill -f "python.*fix_it_fred_universal_ai.py" || true

echo "✅ All services stopped"
