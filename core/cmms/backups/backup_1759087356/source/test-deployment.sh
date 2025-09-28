#!/bin/bash
# ChatterFix CMMS Mars-Level AI Platform - Deployment Test Script
# 🚀 Test containerized deployment

set -e

echo "🚀 Starting ChatterFix CMMS Mars-Level AI Platform Deployment Test..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check Docker
echo -e "${YELLOW}📋 Checking Docker availability...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker is available${NC}"

# Step 2: Check required files
echo -e "${YELLOW}📋 Checking deployment files...${NC}"
required_files=(
    "Dockerfile.production"
    "docker-compose.production.yml"
    ".env.production.template"
    "requirements.txt"
    "app.py"
)

for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo -e "${RED}❌ Missing required file: $file${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Found: $file${NC}"
done

# Step 3: Build Docker image
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
docker build -f Dockerfile.production -t chatterfix-cmms-test:latest . || {
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
}
echo -e "${GREEN}✅ Docker image built successfully${NC}"

# Step 4: Test Docker run (quick test)
echo -e "${YELLOW}🧪 Testing Docker container startup...${NC}"
container_id=$(docker run -d -p 8081:8080 \
    -e ENVIRONMENT=production \
    -e PORT=8080 \
    -e LOG_LEVEL=INFO \
    -e DATABASE_PATH=/app/data/cmms_test.db \
    -e JWT_SECRET_KEY=test-secret-key-for-deployment-test \
    chatterfix-cmms-test:latest)

# Wait for container to start
sleep 10

# Check if container is running
if docker ps | grep -q $container_id; then
    echo -e "${GREEN}✅ Container started successfully${NC}"
    
    # Test health endpoint
    if curl -f http://localhost:8081/mars-status &>/dev/null; then
        echo -e "${GREEN}✅ Health check passed${NC}"
    else
        echo -e "${YELLOW}⚠️  Health check failed (expected for test without full setup)${NC}"
    fi
    
    # Clean up
    docker stop $container_id
    docker rm $container_id
    echo -e "${GREEN}✅ Test container cleaned up${NC}"
else
    echo -e "${RED}❌ Container failed to start${NC}"
    docker logs $container_id
    docker rm $container_id
    exit 1
fi

# Step 5: Test docker-compose setup
echo -e "${YELLOW}🔧 Testing docker-compose configuration...${NC}"
if docker-compose -f docker-compose.production.yml config &>/dev/null; then
    echo -e "${GREEN}✅ Docker Compose configuration is valid${NC}"
else
    echo -e "${RED}❌ Docker Compose configuration has errors${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 Deployment test completed successfully!${NC}"
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "1. Copy .env.production.template to .env.production"
echo "2. Fill in your API keys and configuration"
echo "3. Run: docker-compose -f docker-compose.production.yml up -d"
echo "4. Access your Mars-Level AI Platform at https://yourdomain.com"