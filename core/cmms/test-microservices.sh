#!/bin/bash

# ChatterFix CMMS - Microservices Testing Script
# Test both services locally using Docker Compose

set -e

echo "🧪 Testing ChatterFix CMMS Microservices..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo_info() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo_step() {
    echo -e "${BLUE}🔄 $1${NC}"
}

# Check prerequisites
echo_step "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo_error "Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo_error "Docker Compose is not installed"
    exit 1
fi

echo_info "Prerequisites check passed"

# Clean up any existing containers
echo_step "Cleaning up existing containers..."
docker-compose down --remove-orphans > /dev/null 2>&1 || true

# Build and start services
echo_step "Building and starting microservices..."
docker-compose up -d --build

if [ $? -ne 0 ]; then
    echo_error "Failed to start services"
    exit 1
fi

# Wait for services to be ready
echo_step "Waiting for services to be ready..."
sleep 30

# Test database service
echo_step "Testing database service..."
for i in {1..10}; do
    if curl -s -f "http://localhost:8081/health" > /dev/null 2>&1; then
        echo_info "Database service is responding"
        break
    else
        if [ $i -eq 10 ]; then
            echo_error "Database service health check failed after 10 attempts"
            docker-compose logs database-service
            exit 1
        fi
        echo "Attempt $i/10: Database service not ready, waiting..."
        sleep 5
    fi
done

# Test main application
echo_step "Testing main application..."
for i in {1..10}; do
    if curl -s -f "http://localhost:8080/health" > /dev/null 2>&1; then
        echo_info "Main application is responding"
        break
    else
        if [ $i -eq 10 ]; then
            echo_error "Main application health check failed after 10 attempts"
            docker-compose logs main-app
            exit 1
        fi
        echo "Attempt $i/10: Main application not ready, waiting..."
        sleep 5
    fi
done

# Run comprehensive tests
echo ""
echo "===================="
echo "RUNNING TESTS"
echo "===================="

# Test 1: Health checks
echo_step "Test 1: Health checks"
DB_HEALTH=$(curl -s "http://localhost:8081/health")
MAIN_HEALTH=$(curl -s "http://localhost:8080/health")

if echo "$DB_HEALTH" | grep -q '"status":"healthy"'; then
    echo_info "Database service health check passed"
else
    echo_warning "Database service health: $DB_HEALTH"
fi

if echo "$MAIN_HEALTH" | grep -q '"status"'; then
    echo_info "Main application health check passed"
else
    echo_warning "Main application health: $MAIN_HEALTH"
fi

# Test 2: Database service endpoints
echo_step "Test 2: Database service endpoints"

# Test work orders endpoint
if curl -s -f "http://localhost:8081/api/work-orders" > /dev/null 2>&1; then
    echo_info "Work orders endpoint responding"
else
    echo_warning "Work orders endpoint failed"
fi

# Test assets endpoint
if curl -s -f "http://localhost:8081/api/assets" > /dev/null 2>&1; then
    echo_info "Assets endpoint responding"
else
    echo_warning "Assets endpoint failed"
fi

# Test 3: Main application endpoints
echo_step "Test 3: Main application endpoints"

# Test home page
if curl -s -f "http://localhost:8080/" > /dev/null 2>&1; then
    echo_info "Home page responding"
else
    echo_warning "Home page failed"
fi

# Test work orders page
if curl -s -f "http://localhost:8080/workorders" > /dev/null 2>&1; then
    echo_info "Work orders page responding"
else
    echo_warning "Work orders page failed"
fi

# Test API proxy endpoints
if curl -s -f "http://localhost:8080/api/work-orders" > /dev/null 2>&1; then
    echo_info "API proxy endpoints responding"
else
    echo_warning "API proxy endpoints failed"
fi

# Test 4: Create test data
echo_step "Test 4: Creating test data"

# Create test work order via main app
TEST_WO_RESPONSE=$(curl -s -X POST "http://localhost:8080/api/work-orders" \
    -H "Content-Type: application/json" \
    -d '{"title":"Test Work Order","description":"Test description","priority":"medium","status":"open"}')

if echo "$TEST_WO_RESPONSE" | grep -q '"id"'; then
    echo_info "Test work order created successfully"
else
    echo_warning "Test work order creation failed: $TEST_WO_RESPONSE"
fi

# Create test asset via database service
TEST_ASSET_RESPONSE=$(curl -s -X POST "http://localhost:8081/api/assets" \
    -H "Content-Type: application/json" \
    -d '{"name":"Test Asset","description":"Test asset","asset_type":"equipment","location":"warehouse","status":"active"}')

if echo "$TEST_ASSET_RESPONSE" | grep -q '"id"'; then
    echo_info "Test asset created successfully"
else
    echo_warning "Test asset creation failed: $TEST_ASSET_RESPONSE"
fi

echo ""
echo "===================="
echo "TEST RESULTS"
echo "===================="

echo ""
echo "🎉 Microservices Testing Summary:"
echo "================================="
echo ""
echo "📊 Services Status:"
echo "   • Database Service: http://localhost:8081"
echo "   • Main Application: http://localhost:8080"
echo ""
echo "🔧 Test Endpoints:"
echo "   • Database Health: http://localhost:8081/health"
echo "   • Main App Health: http://localhost:8080/health"
echo "   • Home Page: http://localhost:8080/"
echo "   • Work Orders: http://localhost:8080/workorders"
echo "   • Assets: http://localhost:8080/assets"
echo ""
echo "📋 Manual Testing:"
echo "   1. Open http://localhost:8080 in your browser"
echo "   2. Navigate through the different pages"
echo "   3. Try creating work orders and assets"
echo "   4. Check that data persists between requests"
echo ""

# Show logs
echo_step "Showing recent logs..."
echo ""
echo "Database Service Logs:"
docker-compose logs --tail=10 database-service
echo ""
echo "Main Application Logs:"
docker-compose logs --tail=10 main-app

echo ""
echo_info "🧪 Testing completed! Services are running."
echo_info "📱 Access the application at: http://localhost:8080"
echo_warning "⚠️  Run 'docker-compose down' to stop the services when done."