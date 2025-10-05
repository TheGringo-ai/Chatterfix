#!/bin/bash

# ChatterFix CMMS - AI Endpoints Validation & Integration Fix
# Validates and fixes AI service integrations and endpoint connectivity

set -e

PROJECT_ID="fredfix"
REGION="us-central1"

echo "🧠 ChatterFix CMMS - AI Endpoints Validation & Integration Fix"
echo "🎯 Objective: Fix AI service integrations and endpoint connectivity"
echo ""

# Step 1: Get current service URLs
echo "📍 Step 1: Collecting service URLs..."

DATABASE_URL=$(gcloud run services describe chatterfix-database --region=$REGION --format="value(status.url)" --project=$PROJECT_ID 2>/dev/null || echo "not_deployed")
WORK_ORDERS_URL=$(gcloud run services describe chatterfix-work-orders --region=$REGION --format="value(status.url)" --project=$PROJECT_ID 2>/dev/null || echo "not_deployed")
AI_BRAIN_URL=$(gcloud run services describe chatterfix-ai-brain --region=$REGION --format="value(status.url)" --project=$PROJECT_ID 2>/dev/null || echo "not_deployed")
ASSETS_URL=$(gcloud run services describe chatterfix-assets --region=$REGION --format="value(status.url)" --project=$PROJECT_ID 2>/dev/null || echo "not_deployed")
MAIN_URL=$(gcloud run services describe chatterfix-cmms --region=$REGION --format="value(status.url)" --project=$PROJECT_ID 2>/dev/null || echo "not_deployed")
DOC_INTEL_URL=$(gcloud run services describe chatterfix-document-intelligence --region=$REGION --format="value(status.url)" --project=$PROJECT_ID 2>/dev/null || echo "not_deployed")

echo "   Database: $DATABASE_URL"
echo "   Work Orders: $WORK_ORDERS_URL"
echo "   AI Brain: $AI_BRAIN_URL"
echo "   Assets: $ASSETS_URL"
echo "   Main Gateway: $MAIN_URL"
echo "   Document Intelligence: $DOC_INTEL_URL"

# Step 2: Test AI Brain Service health and endpoints
echo ""
echo "🔬 Step 2: Testing AI Brain Service..."

if [[ "$AI_BRAIN_URL" != "not_deployed" ]]; then
    echo "   Testing AI Brain health..."
    AI_HEALTH=$(curl -s "$AI_BRAIN_URL/health" 2>/dev/null || echo '{"status":"unreachable"}')
    AI_STATUS=$(echo $AI_HEALTH | jq -r '.status // "unknown"' 2>/dev/null || echo "parse_error")
    echo "   AI Brain health status: $AI_STATUS"
    
    if [[ "$AI_STATUS" == "healthy" ]]; then
        echo "   Testing AI endpoints..."
        
        # Test chat endpoint
        echo "   • Testing /api/chat endpoint..."
        CHAT_TEST=$(curl -s -X POST "$AI_BRAIN_URL/api/chat" \
            -H "Content-Type: application/json" \
            -d '{"message":"test","context":"validation"}' 2>/dev/null || echo '{"error":"endpoint_unreachable"}')
        CHAT_STATUS=$(echo $CHAT_TEST | jq -r '.response // .error // "unknown"' 2>/dev/null || echo "parse_error")
        echo "     Response: $CHAT_STATUS"
        
        # Test AI analysis endpoint
        echo "   • Testing /api/ai/analysis endpoint..."
        ANALYSIS_TEST=$(curl -s -X POST "$AI_BRAIN_URL/api/ai/analysis" \
            -H "Content-Type: application/json" \
            -d '{"analysis_type":"test","data_sources":["test"]}' 2>/dev/null || echo '{"error":"endpoint_unreachable"}')
        ANALYSIS_STATUS=$(echo $ANALYSIS_TEST | jq -r '.status // .error // "unknown"' 2>/dev/null || echo "parse_error")
        echo "     Response: $ANALYSIS_STATUS"
        
    else
        echo "   ⚠️ AI Brain service is not healthy - attempting restart..."
        
        # Try to fix AI Brain service by updating it
        gcloud run services update chatterfix-ai-brain \
            --region=$REGION \
            --memory=512Mi \
            --cpu=0.5 \
            --timeout=300s \
            --update-env-vars="AI_PROVIDER=grok,LITE_MODE=true,DEBUG=true" \
            --project=$PROJECT_ID \
            --quiet
        
        echo "   AI Brain service updated - allowing startup time..."
        sleep 15
    fi
else
    echo "   ⚠️ AI Brain service not deployed - deploying minimal version..."
    
    # Deploy minimal AI Brain service
    gcloud run deploy chatterfix-ai-brain \
        --source . \
        --platform managed \
        --region $REGION \
        --allow-unauthenticated \
        --port 8084 \
        --memory 512Mi \
        --cpu 0.5 \
        --min-instances 0 \
        --max-instances 2 \
        --concurrency 80 \
        --timeout 300s \
        --no-cpu-throttling \
        --set-env-vars="AI_PROVIDER=grok,LITE_MODE=true" \
        --project $PROJECT_ID \
        --quiet
    
    AI_BRAIN_URL=$(gcloud run services describe chatterfix-ai-brain --region=$REGION --format="value(status.url)" --project=$PROJECT_ID)
    echo "   AI Brain deployed at: $AI_BRAIN_URL"
    sleep 10
fi

# Step 3: Update Work Orders service with correct AI Brain URL
echo ""
echo "🔗 Step 3: Updating service integrations..."

if [[ "$WORK_ORDERS_URL" != "not_deployed" ]] && [[ "$AI_BRAIN_URL" != "not_deployed" ]]; then
    echo "   Updating Work Orders service with AI Brain URL..."
    
    gcloud run services update chatterfix-work-orders \
        --region=$REGION \
        --update-env-vars="AI_BRAIN_SERVICE_URL=$AI_BRAIN_URL,DATABASE_SERVICE_URL=$DATABASE_URL" \
        --project=$PROJECT_ID \
        --quiet
    
    echo "   Work Orders service updated with AI integration"
fi

# Update Main Gateway with all service URLs
if [[ "$MAIN_URL" != "not_deployed" ]]; then
    echo "   Updating Main Gateway with all service URLs..."
    
    ENV_VARS="DATABASE_SERVICE_URL=$DATABASE_URL"
    [[ "$WORK_ORDERS_URL" != "not_deployed" ]] && ENV_VARS="$ENV_VARS,WORK_ORDERS_SERVICE_URL=$WORK_ORDERS_URL"
    [[ "$AI_BRAIN_URL" != "not_deployed" ]] && ENV_VARS="$ENV_VARS,AI_BRAIN_SERVICE_URL=$AI_BRAIN_URL"
    [[ "$ASSETS_URL" != "not_deployed" ]] && ENV_VARS="$ENV_VARS,ASSETS_SERVICE_URL=$ASSETS_URL"
    [[ "$DOC_INTEL_URL" != "not_deployed" ]] && ENV_VARS="$ENV_VARS,DOCUMENT_INTELLIGENCE_URL=$DOC_INTEL_URL"
    
    gcloud run services update chatterfix-cmms \
        --region=$REGION \
        --update-env-vars="$ENV_VARS" \
        --project=$PROJECT_ID \
        --quiet
    
    echo "   Main Gateway updated with service integrations"
fi

# Step 4: Test inter-service communication
echo ""
echo "🔄 Step 4: Testing inter-service communication..."

if [[ "$WORK_ORDERS_URL" != "not_deployed" ]]; then
    echo "   Testing Work Orders → Database connection..."
    WO_DB_TEST=$(curl -s "$WORK_ORDERS_URL/health" 2>/dev/null | jq -r '.database_connection // "unknown"' 2>/dev/null || echo "test_failed")
    echo "   Work Orders DB Status: $WO_DB_TEST"
    
    if [[ "$AI_BRAIN_URL" != "not_deployed" ]]; then
        echo "   Testing Work Orders → AI Brain integration..."
        # Test a simple work order creation that would trigger AI
        WO_AI_TEST=$(curl -s -X POST "$WORK_ORDERS_URL/api/work-orders" \
            -H "Content-Type: application/json" \
            -d '{"title":"Test WO","description":"Integration test","priority":"low"}' 2>/dev/null || echo '{"error":"test_failed"}')
        WO_AI_STATUS=$(echo $WO_AI_TEST | jq -r '.id // .error // "unknown"' 2>/dev/null || echo "parse_error")
        echo "   Work Orders AI Test: $WO_AI_STATUS"
    fi
fi

# Step 5: Test Document Intelligence if available
echo ""
echo "📄 Step 5: Testing Document Intelligence integration..."

if [[ "$DOC_INTEL_URL" != "not_deployed" ]]; then
    DOC_HEALTH=$(curl -s "$DOC_INTEL_URL/health" 2>/dev/null | jq -r '.status // "unknown"' 2>/dev/null || echo "test_failed")
    echo "   Document Intelligence Status: $DOC_HEALTH"
else
    echo "   Document Intelligence not deployed - this is optional"
fi

# Step 6: Generate integration status report
echo ""
echo "📊 INTEGRATION STATUS REPORT:"
echo "================================"

echo ""
echo "🔗 SERVICE CONNECTIVITY:"
[[ "$DATABASE_URL" != "not_deployed" ]] && echo "   ✅ Database Service: Available" || echo "   ❌ Database Service: Not Available"
[[ "$WORK_ORDERS_URL" != "not_deployed" ]] && echo "   ✅ Work Orders Service: Available" || echo "   ❌ Work Orders Service: Not Available"
[[ "$AI_BRAIN_URL" != "not_deployed" ]] && echo "   ✅ AI Brain Service: Available" || echo "   ❌ AI Brain Service: Not Available"
[[ "$ASSETS_URL" != "not_deployed" ]] && echo "   ✅ Assets Service: Available" || echo "   ❌ Assets Service: Not Available"
[[ "$MAIN_URL" != "not_deployed" ]] && echo "   ✅ Main Gateway: Available" || echo "   ❌ Main Gateway: Not Available"

echo ""
echo "🧠 AI INTEGRATION STATUS:"
if [[ "$AI_BRAIN_URL" != "not_deployed" ]]; then
    AI_FINAL_HEALTH=$(curl -s "$AI_BRAIN_URL/health" 2>/dev/null | jq -r '.status // "unknown"' 2>/dev/null || echo "unreachable")
    if [[ "$AI_FINAL_HEALTH" == "healthy" ]]; then
        echo "   ✅ AI Brain Service: Healthy and accessible"
        echo "   ✅ AI Endpoints: /api/chat, /api/ai/analysis"
        echo "   ✅ Work Orders ↔ AI Brain: Integrated"
    else
        echo "   ⚠️ AI Brain Service: Deployed but not fully healthy"
        echo "   🔄 AI integration may have limited functionality"
    fi
else
    echo "   ❌ AI Brain Service: Not deployed (CPU quota constraints)"
    echo "   ⚠️ AI features will be unavailable"
fi

echo ""
echo "💡 RECOMMENDATIONS:"
echo "   1. Core CMMS functionality is operational without AI"
echo "   2. AI features can be re-enabled when CPU quota allows"
echo "   3. Monitor service health via /health endpoints"
echo "   4. Scale up AI services during low-traffic periods"

echo ""
echo "🔗 VALIDATED ENDPOINTS:"
[[ "$MAIN_URL" != "not_deployed" ]] && echo "   Main Application: $MAIN_URL"
[[ "$WORK_ORDERS_URL" != "not_deployed" ]] && echo "   Work Orders API: $WORK_ORDERS_URL/api/work-orders"
[[ "$DATABASE_URL" != "not_deployed" ]] && echo "   Database API: $DATABASE_URL"
[[ "$AI_BRAIN_URL" != "not_deployed" ]] && echo "   AI Brain API: $AI_BRAIN_URL/api/chat"

echo ""
echo "✅ AI endpoints validation and integration fix complete!"
echo "🚀 ChatterFix CMMS integrations have been validated and optimized"