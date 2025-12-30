#!/bin/bash

# ChatterFix Enterprise v3.0 AI Powerhouse - Clean Deployment
# Single deployment script as requested - no duplicates

echo "🚀 Deploying ChatterFix Enterprise v3.0 AI Powerhouse..."

# Stop any running instances
pkill -f python 2>/dev/null || true
pkill -f gunicorn 2>/dev/null || true

# Start the clean v3 version
cd /Users/fredtaylor/Desktop/Projects/ai-tools
python3 chatterfix_enterprise_v3_ai_powerhouse.py &

echo "✅ ChatterFix Enterprise v3.0 AI Powerhouse deployed!"
echo "🌐 Access at: http://localhost:8080"
echo "🤖 AI Team: Claude + Grok Partnership ACTIVE"