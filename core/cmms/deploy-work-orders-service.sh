#!/bin/bash

# Deploy Work Orders Service
set -e

echo "🛠️ Deploying Work Orders Service..."

# Create a temporary directory with just the work orders service files
rm -rf /tmp/work-orders-deploy
mkdir -p /tmp/work-orders-deploy
cp work_orders_service.py /tmp/work-orders-deploy/
cp work_orders_service_requirements.txt /tmp/work-orders-deploy/requirements.txt
cp Dockerfile.work_orders /tmp/work-orders-deploy/Dockerfile

# Deploy from the temp directory
cd /tmp/work-orders-deploy
gcloud run deploy chatterfix-work-orders \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 5 \
    --min-instances 1 \
    --set-env-vars "SERVICE_NAME=work-orders,DATABASE_URL=postgresql://yoyofred:%40Gringo420@136.112.167.114/chatterfix_cmms" \
    --quiet

# Return to original directory
cd -

echo "✅ Work Orders Service deployed successfully!"