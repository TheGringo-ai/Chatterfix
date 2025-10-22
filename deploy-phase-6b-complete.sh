#!/bin/bash
# 🚀 ChatterFix CMMS - Phase 6B Enterprise Deployment
# Deploys all Phase 6B services to Google Cloud Run

set -e
echo "🚀 Starting Phase 6B Enterprise Deployment to chatterfix.com..."

# Configuration
PROJECT_ID="fredfix"
REGION="us-central1"

echo "📋 Project: $PROJECT_ID"
echo "🌍 Region: $REGION"

# Set the project
gcloud config set project $PROJECT_ID

echo ""
echo "🔧 Building and deploying Phase 6B services..."

# 1. Deploy Customer Success Analytics Service
echo "📊 Deploying Customer Success Analytics Service..."
gcloud run deploy chatterfix-customer-success \
  --source backend/app/analytics \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars="SERVICE_NAME=customer-success-analytics" \
  --timeout 900 \
  --max-instances 10 \
  --min-instances 1

# 2. Deploy Revenue Intelligence Engine
echo "💰 Deploying Revenue Intelligence Engine..."
gcloud run deploy chatterfix-revenue-intelligence \
  --source ai/services \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars="SERVICE_NAME=revenue-intelligence" \
  --timeout 900 \
  --max-instances 10 \
  --min-instances 1

# 3. Deploy Series A Data Room Service
echo "📄 Deploying Series A Data Room Service..."
gcloud run deploy chatterfix-data-room \
  --source backend/app/analytics \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars="SERVICE_NAME=data-room" \
  --timeout 900 \
  --max-instances 5 \
  --min-instances 1

# 4. Deploy Enhanced Fix It Fred Service
echo "🤖 Deploying Enhanced Fix It Fred Service..."
gcloud run deploy chatterfix-fix-it-fred-enhanced \
  --source ai/services \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars="SERVICE_NAME=fix-it-fred-enhanced" \
  --timeout 900 \
  --max-instances 10 \
  --min-instances 1

# 5. Get service URLs
echo ""
echo "🌐 Getting service URLs..."
CUSTOMER_SUCCESS_URL=$(gcloud run services describe chatterfix-customer-success --region=$REGION --format="value(status.url)")
REVENUE_INTELLIGENCE_URL=$(gcloud run services describe chatterfix-revenue-intelligence --region=$REGION --format="value(status.url)")
DATA_ROOM_URL=$(gcloud run services describe chatterfix-data-room --region=$REGION --format="value(status.url)")
FIX_IT_FRED_URL=$(gcloud run services describe chatterfix-fix-it-fred-enhanced --region=$REGION --format="value(status.url)")

echo "📊 Customer Success Analytics: $CUSTOMER_SUCCESS_URL"
echo "💰 Revenue Intelligence: $REVENUE_INTELLIGENCE_URL"
echo "📄 Data Room: $DATA_ROOM_URL"
echo "🤖 Enhanced Fix It Fred: $FIX_IT_FRED_URL"

# 6. Update main ChatterFix service with Phase 6B integration
echo ""
echo "🔄 Updating main ChatterFix service with Phase 6B integration..."

# Create environment variables for service URLs
ENV_VARS="CUSTOMER_SUCCESS_URL=$CUSTOMER_SUCCESS_URL,"
ENV_VARS+="REVENUE_INTELLIGENCE_URL=$REVENUE_INTELLIGENCE_URL,"
ENV_VARS+="DATA_ROOM_URL=$DATA_ROOM_URL,"
ENV_VARS+="FIX_IT_FRED_ENHANCED_URL=$FIX_IT_FRED_URL,"
ENV_VARS+="PHASE_6B_ENABLED=true"

gcloud run services update chatterfix-cmms \
  --region $REGION \
  --set-env-vars="$ENV_VARS"

echo ""
echo "🎉 Phase 6B Enterprise Deployment Complete!"
echo ""
echo "🌟 Enterprise Features Now Live:"
echo "   • Customer Success Analytics with ML-powered churn prediction"
echo "   • Revenue Intelligence with automated forecasting"
echo "   • Series A Data Room with investor documentation"
echo "   • Enhanced AI capabilities with investor metrics"
echo ""
echo "🔗 Access your enterprise platform at: https://chatterfix.com"
echo ""
echo "📊 Service Health Checks:"
echo "   curl $CUSTOMER_SUCCESS_URL/api/customer-success/kpis"
echo "   curl $REVENUE_INTELLIGENCE_URL/api/revenue/summary"
echo "   curl $DATA_ROOM_URL/api/data-room/status"
echo "   curl $FIX_IT_FRED_URL/health"
echo ""
echo "✅ ChatterFix CMMS Phase 6B Enterprise Launch: COMPLETE"