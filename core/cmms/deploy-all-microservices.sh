#!/bin/bash

# Deploy all ChatterFix microservices in the correct order
set -e

echo "🚀 Deploying all ChatterFix microservices..."

# Deploy in order of dependencies:
# 1. Database service first (no dependencies)
# 2. Core business services (depend on database)
# 3. AI Brain service (can run independently)
# 4. UI Gateway (orchestrates all services)

echo "🗄️ Step 1: Deploying Database Service..."
if ./deploy-database-service.sh; then
    echo "✅ Database service deployed"
else
    echo "⚠️ Database service deployment failed, continuing..."
fi

echo "🛠️ Step 2: Deploying Work Orders Service..."
if ./deploy-work-orders-service.sh; then
    echo "✅ Work Orders service deployed"
else
    echo "⚠️ Work Orders service deployment failed, continuing..."
fi

echo "📦 Step 3: Deploying Assets Service..."
if ./deploy-assets-service.sh; then
    echo "✅ Assets service deployed"
else
    echo "⚠️ Assets service deployment failed, continuing..."
fi

echo "🔧 Step 4: Deploying Parts Service..."
if ./deploy-parts-service.sh; then
    echo "✅ Parts service deployed"
else
    echo "⚠️ Parts service deployment failed, continuing..."
fi

echo "🧠 Step 5: Deploying AI Brain Service..."
if ./deploy-ai-brain-service.sh; then
    echo "✅ AI Brain service deployed"
else
    echo "⚠️ AI Brain service deployment failed, continuing..."
fi

echo "🌐 Step 6: Deploying Main UI Gateway..."
if ./deploy-chatterfix.sh; then
    echo "✅ UI Gateway deployed"
else
    echo "⚠️ UI Gateway deployment failed"
fi

echo ""
echo "🎉 Microservices deployment completed!"
echo ""
echo "🔍 Service Status:"
echo "   Database: https://chatterfix-database-psycl7nhha-uc.a.run.app"
echo "   Work Orders: https://chatterfix-work-orders-psycl7nhha-uc.a.run.app"
echo "   Assets: https://chatterfix-assets-psycl7nhha-uc.a.run.app"
echo "   Parts: https://chatterfix-parts-psycl7nhha-uc.a.run.app"
echo "   AI Brain: https://chatterfix-ai-brain-psycl7nhha-uc.a.run.app"
echo "   Main App: https://chatterfix-cmms-psycl7nhha-uc.a.run.app"
echo ""
echo "✅ All microservices deployment process completed!"