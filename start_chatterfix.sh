#!/bin/bash
cd /home/yoyofred_gringosgambit_com
pkill -f chatterfix_app.py || true
nohup python3 chatterfix_app.py > chatterfix.log 2>&1 &
echo "ChatterFix started on port 8080"
sleep 2
curl -s http://localhost:8080/health || echo "Health check failed"
