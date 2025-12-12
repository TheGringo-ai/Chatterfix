#!/bin/bash

# 🚀 ChatterFix Deployment Performance Benchmarking Tool
# Measures deployment speed, optimizations, and provides recommendations

set -euo pipefail

# Configuration
PROJECT_ID="fredfix"
REGION="us-central1"
SERVICE_NAME="gringo-core"
BENCHMARK_RUNS=3
RESULTS_FILE="deployment-benchmark-$(date +%Y%m%d-%H%M%S).json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# Banner
echo -e "${CYAN}"
echo "🚀 ChatterFix Deployment Performance Benchmark"
echo "=============================================="
echo -e "${NC}"

# Initialize results
cat > "$RESULTS_FILE" << EOF
{
  "benchmark_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "project_id": "$PROJECT_ID",
  "service_name": "$SERVICE_NAME", 
  "region": "$REGION",
  "runs": [],
  "averages": {},
  "recommendations": []
}
EOF

# Function to measure time
measure_time() {
    local start_time=$(date +%s.%N)
    "$@"
    local end_time=$(date +%s.%N)
    echo "scale=2; $end_time - $start_time" | bc
}

# Function to check network speed
check_network_speed() {
    log "Checking network speed..."
    local start_time=$(date +%s.%N)
    curl -s -o /dev/null "https://www.google.com"
    local end_time=$(date +%s.%N)
    local network_latency=$(echo "scale=3; $end_time - $start_time" | bc)
    echo "$network_latency"
}

# Function to analyze Docker build performance
analyze_build_performance() {
    local dockerfile="$1"
    local build_context_size build_time image_size layers
    
    log "Analyzing build performance for $dockerfile..."
    
    # Measure build context size
    build_context_size=$(du -sh . | awk '{print $1}')
    
    # Count layers in Dockerfile
    layers=$(grep -c "^RUN\|^COPY\|^ADD\|^FROM" "$dockerfile" 2>/dev/null || echo "unknown")
    
    # Build and measure time
    build_start=$(date +%s.%N)
    docker build -f "$dockerfile" -t benchmark-test:latest . >/dev/null 2>&1 || true
    build_end=$(date +%s.%N)
    build_time=$(echo "scale=2; $build_end - $build_start" | bc)
    
    # Measure image size
    image_size=$(docker images benchmark-test:latest --format "table {{.Size}}" | tail -n1 | tr -d ' ')
    
    # Clean up
    docker rmi benchmark-test:latest >/dev/null 2>&1 || true
    
    echo "{\"build_time\": $build_time, \"image_size\": \"$image_size\", \"layers\": $layers, \"context_size\": \"$build_context_size\"}"
}

# Function to benchmark deployment
benchmark_deployment() {
    local run_number="$1"
    local commit_sha=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    
    log "🏃 Benchmark Run #$run_number"
    log "==============================="
    
    local start_time=$(date +%s.%N)
    local results="{\"run\": $run_number, \"commit_sha\": \"$commit_sha\", \"stages\": {}}"
    
    # Stage 1: Pre-deployment checks
    log "Stage 1: Pre-deployment checks"
    stage_start=$(date +%s.%N)
    
    # Check authentication
    gcloud auth list --filter=status:ACTIVE >/dev/null 2>&1
    
    # Check git status
    git_changes=$(git status --porcelain | wc -l)
    
    stage_end=$(date +%s.%N)
    stage_time=$(echo "scale=3; $stage_end - $stage_start" | bc)
    results=$(echo "$results" | jq ".stages.precheck = {\"time\": $stage_time, \"git_changes\": $git_changes}")
    
    # Stage 2: Docker build
    log "Stage 2: Docker build"
    stage_start=$(date +%s.%N)
    
    # Regular Dockerfile
    if [[ -f "Dockerfile" ]]; then
        regular_build=$(analyze_build_performance "Dockerfile")
        results=$(echo "$results" | jq ".stages.build_regular = $regular_build")
    fi
    
    # Optimized Dockerfile
    if [[ -f "Dockerfile.optimized" ]]; then
        optimized_build=$(analyze_build_performance "Dockerfile.optimized")
        results=$(echo "$results" | jq ".stages.build_optimized = $optimized_build")
    fi
    
    stage_end=$(date +%s.%N)
    stage_time=$(echo "scale=3; $stage_end - $stage_start" | bc)
    
    # Stage 3: Registry operations
    log "Stage 3: Registry push simulation"
    stage_start=$(date +%s.%N)
    
    # Simulate registry operations (check existing images)
    existing_tags=$(gcloud container images list-tags gcr.io/$PROJECT_ID/$SERVICE_NAME --limit=5 --format="value(tags)" 2>/dev/null | wc -l || echo "0")
    
    stage_end=$(date +%s.%N)
    stage_time=$(echo "scale=3; $stage_end - $stage_start" | bc)
    results=$(echo "$results" | jq ".stages.registry = {\"time\": $stage_time, \"existing_tags\": $existing_tags}")
    
    # Stage 4: Cloud Run deployment simulation
    log "Stage 4: Cloud Run status check"
    stage_start=$(date +%s.%N)
    
    # Check current service status
    current_revisions=$(gcloud run revisions list --service=$SERVICE_NAME --region=$REGION --limit=5 --format="value(metadata.name)" 2>/dev/null | wc -l || echo "0")
    service_url=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)" 2>/dev/null || echo "")
    
    stage_end=$(date +%s.%N)
    stage_time=$(echo "scale=3; $stage_end - $stage_start" | bc)
    results=$(echo "$results" | jq ".stages.cloudrun = {\"time\": $stage_time, \"revisions\": $current_revisions, \"service_url\": \"$service_url\"}")
    
    # Stage 5: Health check simulation
    log "Stage 5: Health check test"
    stage_start=$(date +%s.%N)
    
    health_status="unknown"
    health_time="0"
    if [[ -n "$service_url" ]]; then
        health_start=$(date +%s.%N)
        if curl -f -s --connect-timeout 5 --max-time 10 "$service_url/health" >/dev/null 2>&1; then
            health_status="healthy"
        else
            health_status="unhealthy"
        fi
        health_end=$(date +%s.%N)
        health_time=$(echo "scale=3; $health_end - $health_start" | bc)
    fi
    
    stage_end=$(date +%s.%N)
    stage_time=$(echo "scale=3; $stage_end - $stage_start" | bc)
    results=$(echo "$results" | jq ".stages.healthcheck = {\"time\": $stage_time, \"status\": \"$health_status\", \"response_time\": $health_time}")
    
    # Calculate total time
    end_time=$(date +%s.%N)
    total_time=$(echo "scale=3; $end_time - $start_time" | bc)
    results=$(echo "$results" | jq ".total_time = $total_time")
    
    # Network performance
    network_latency=$(check_network_speed)
    results=$(echo "$results" | jq ".network_latency = $network_latency")
    
    log "Run #$run_number completed in ${total_time}s"
    echo "$results"
}

# Function to calculate averages and generate recommendations
analyze_results() {
    local results_file="$1"
    
    log "Analyzing benchmark results..."
    
    # Calculate averages
    local avg_total=$(jq -r '.runs[].total_time' "$results_file" | awk '{sum+=$1; count++} END {print sum/count}')
    local avg_network=$(jq -r '.runs[].network_latency' "$results_file" | awk '{sum+=$1; count++} END {print sum/count}')
    
    # Update results file with averages
    jq ".averages.total_time = $avg_total | .averages.network_latency = $avg_network" "$results_file" > "${results_file}.tmp" && mv "${results_file}.tmp" "$results_file"
    
    # Generate recommendations
    local recommendations=()
    
    # Build time recommendations
    local has_optimized=$(jq -r '.runs[0].stages.build_optimized' "$results_file" 2>/dev/null)
    if [[ "$has_optimized" != "null" ]]; then
        local regular_time=$(jq -r '.runs[0].stages.build_regular.build_time' "$results_file" 2>/dev/null || echo "0")
        local optimized_time=$(jq -r '.runs[0].stages.build_optimized.build_time' "$results_file" 2>/dev/null || echo "0")
        
        if (( $(echo "$regular_time > $optimized_time" | bc -l) )); then
            recommendations+=("Use Dockerfile.optimized for faster builds ($(echo "scale=1; ($regular_time - $optimized_time)" | bc)s improvement)")
        fi
    fi
    
    # Network recommendations
    if (( $(echo "$avg_network > 1.0" | bc -l) )); then
        recommendations+=("High network latency detected (${avg_network}s) - consider using regional builds")
    fi
    
    # Registry recommendations
    local existing_tags=$(jq -r '.runs[0].stages.registry.existing_tags' "$results_file" 2>/dev/null || echo "0")
    if [[ $existing_tags -gt 20 ]]; then
        recommendations+=("Many container images in registry ($existing_tags) - consider cleanup for faster pulls")
    fi
    
    # Performance targets
    if (( $(echo "$avg_total > 180" | bc -l) )); then
        recommendations+=("Deployment time exceeds 3 minutes - implement parallel builds and caching")
    fi
    
    # Cloud Run specific optimizations
    recommendations+=("Use min-instances=1 to avoid cold starts")
    recommendations+=("Consider using Cloud Build for parallel operations")
    recommendations+=("Implement blue-green deployment for zero-downtime releases")
    
    # Add recommendations to results
    local rec_json=""
    for rec in "${recommendations[@]}"; do
        if [[ -z "$rec_json" ]]; then
            rec_json="[\"$rec\""
        else
            rec_json="$rec_json,\"$rec\""
        fi
    done
    rec_json="$rec_json]"
    
    jq ".recommendations = $rec_json" "$results_file" > "${results_file}.tmp" && mv "${results_file}.tmp" "$results_file"
}

# Function to display results
display_results() {
    local results_file="$1"
    
    echo ""
    echo -e "${GREEN}📊 Benchmark Results Summary${NC}"
    echo "============================="
    
    # Overall performance
    local avg_total=$(jq -r '.averages.total_time' "$results_file")
    local avg_network=$(jq -r '.averages.network_latency' "$results_file")
    
    echo -e "${BLUE}⏱️  Average Performance:${NC}"
    echo "   Total Time: ${avg_total}s"
    echo "   Network Latency: ${avg_network}s"
    
    # Build comparison (if available)
    local regular_time=$(jq -r '.runs[0].stages.build_regular.build_time' "$results_file" 2>/dev/null)
    local optimized_time=$(jq -r '.runs[0].stages.build_optimized.build_time' "$results_file" 2>/dev/null)
    
    if [[ "$regular_time" != "null" && "$optimized_time" != "null" ]]; then
        echo ""
        echo -e "${BLUE}🏗️  Build Performance:${NC}"
        echo "   Regular Dockerfile: ${regular_time}s"
        echo "   Optimized Dockerfile: ${optimized_time}s"
        local improvement=$(echo "scale=1; ($regular_time - $optimized_time)" | bc)
        if (( $(echo "$improvement > 0" | bc -l) )); then
            echo -e "   ${GREEN}Improvement: ${improvement}s faster${NC}"
        fi
    fi
    
    # Recommendations
    echo ""
    echo -e "${YELLOW}💡 Optimization Recommendations:${NC}"
    jq -r '.recommendations[]' "$results_file" | while read -r rec; do
        echo "   • $rec"
    done
    
    # Performance grade
    echo ""
    if (( $(echo "$avg_total < 60" | bc -l) )); then
        echo -e "${GREEN}🏆 Performance Grade: A+ (Excellent)${NC}"
    elif (( $(echo "$avg_total < 120" | bc -l) )); then
        echo -e "${GREEN}🥈 Performance Grade: A (Good)${NC}"
    elif (( $(echo "$avg_total < 180" | bc -l) )); then
        echo -e "${YELLOW}🥉 Performance Grade: B (Acceptable)${NC}"
    else
        echo -e "${RED}📉 Performance Grade: C (Needs Improvement)${NC}"
    fi
    
    echo ""
    echo -e "${CYAN}📁 Detailed results saved to: $results_file${NC}"
}

# Main execution
main() {
    log "Starting deployment performance benchmark..."
    log "Configuration: $BENCHMARK_RUNS runs, results saved to $RESULTS_FILE"
    
    # Run benchmarks
    for ((i=1; i<=BENCHMARK_RUNS; i++)); do
        result=$(benchmark_deployment "$i")
        
        # Add to results file
        jq ".runs += [$result]" "$RESULTS_FILE" > "${RESULTS_FILE}.tmp" && mv "${RESULTS_FILE}.tmp" "$RESULTS_FILE"
        
        if [[ $i -lt $BENCHMARK_RUNS ]]; then
            log "Waiting 10 seconds before next run..."
            sleep 10
        fi
    done
    
    # Analyze results
    analyze_results "$RESULTS_FILE"
    
    # Display summary
    display_results "$RESULTS_FILE"
    
    success "Benchmark completed successfully!"
}

# Check dependencies
if ! command -v jq &> /dev/null; then
    error "jq is required but not installed. Please install jq first."
    exit 1
fi

if ! command -v bc &> /dev/null; then
    error "bc is required but not installed. Please install bc first."
    exit 1
fi

# Run main function
main "$@"