#!/bin/bash
set -e

echo "🐳 Building ChatterFix Enterprise Docker Images"

# Configuration
REGISTRY="${REGISTRY:-chatterfix}"
TAG="${TAG:-enterprise-latest}"

# Build frontend
echo "🎨 Building frontend image..."
docker build -f docker/frontend.Dockerfile -t $REGISTRY/ui:$TAG ./chatterfix-enterprise-frontend/

# Build auth service
echo "🔐 Building auth service..."
docker build -f docker/backend.Dockerfile -t $REGISTRY/auth:$TAG ./chatterfix-enterprise-backend/services/

# Build work orders service
echo "🔧 Building work orders service..."
docker build -f docker/backend.Dockerfile -t $REGISTRY/work-orders:$TAG ./core/cmms/

# Build AI service
echo "🤖 Building AI service..."
docker build -f docker/ai-service.Dockerfile -t $REGISTRY/ai:$TAG .

echo "✅ All images built successfully!"
echo "📤 Push images: docker push $REGISTRY/ui:$TAG"
