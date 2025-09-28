#!/bin/bash
# ChatterFix CMMS Mars-Level AI Platform - Universal Cloud Deployment Script
# 🚀 Deploy to AWS, GCP, or Azure with enterprise-grade configuration

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="chatterfix-cmms"
IMAGE_NAME="chatterfix/cmms-mars-level"
VERSION="4.0.0"
REGION_DEFAULT="us-west-2"

# Usage function
usage() {
    echo -e "${BLUE}🚀 ChatterFix CMMS Mars-Level AI Platform - Cloud Deployment${NC}"
    echo ""
    echo "Usage: $0 [PLATFORM] [OPTIONS]"
    echo ""
    echo "PLATFORMS:"
    echo "  aws       Deploy to AWS (ECS + ECR)"
    echo "  gcp       Deploy to Google Cloud (Cloud Run + Container Registry)"
    echo "  azure     Deploy to Azure (Container Instances + Container Registry)"
    echo "  docker    Local Docker deployment"
    echo ""
    echo "OPTIONS:"
    echo "  -r, --region REGION    Deployment region (default: $REGION_DEFAULT)"
    echo "  -e, --env ENV         Environment (production/staging, default: production)"
    echo "  -d, --domain DOMAIN   Custom domain name"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 aws -r us-east-1 -d cmms.yourcompany.com"
    echo "  $0 gcp -r us-central1 -e staging"
    echo "  $0 azure -r eastus"
    echo ""
}

# Parse command line arguments
PLATFORM=""
REGION="$REGION_DEFAULT"
ENVIRONMENT="production"
DOMAIN=""

while [[ $# -gt 0 ]]; do
    case $1 in
        aws|gcp|azure|docker)
            PLATFORM="$1"
            shift
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -d|--domain)
            DOMAIN="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            exit 1
            ;;
    esac
done

if [[ -z "$PLATFORM" ]]; then
    echo -e "${RED}Error: Platform is required${NC}"
    usage
    exit 1
fi

echo -e "${BLUE}🚀 Starting ChatterFix CMMS Mars-Level AI Platform deployment...${NC}"
echo -e "${YELLOW}Platform: $PLATFORM${NC}"
echo -e "${YELLOW}Region: $REGION${NC}"
echo -e "${YELLOW}Environment: $ENVIRONMENT${NC}"
[[ -n "$DOMAIN" ]] && echo -e "${YELLOW}Domain: $DOMAIN${NC}"

# Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}📋 Checking prerequisites...${NC}"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is required but not installed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker found${NC}"
    
    # Check platform-specific tools
    case $PLATFORM in
        aws)
            if ! command -v aws &> /dev/null; then
                echo -e "${RED}❌ AWS CLI is required but not installed${NC}"
                echo "Install with: curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip' && unzip awscliv2.zip && sudo ./aws/install"
                exit 1
            fi
            echo -e "${GREEN}✅ AWS CLI found${NC}"
            ;;
        gcp)
            if ! command -v gcloud &> /dev/null; then
                echo -e "${RED}❌ Google Cloud CLI is required but not installed${NC}"
                echo "Install with: curl https://sdk.cloud.google.com | bash"
                exit 1
            fi
            echo -e "${GREEN}✅ Google Cloud CLI found${NC}"
            ;;
        azure)
            if ! command -v az &> /dev/null; then
                echo -e "${RED}❌ Azure CLI is required but not installed${NC}"
                echo "Install with: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
                exit 1
            fi
            echo -e "${GREEN}✅ Azure CLI found${NC}"
            ;;
    esac
}

# Build and tag image
build_image() {
    echo -e "${YELLOW}🔨 Building Docker image...${NC}"
    docker build -f Dockerfile.production -t "$IMAGE_NAME:$VERSION" -t "$IMAGE_NAME:latest" .
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
}

# Deploy to AWS
deploy_aws() {
    echo -e "${YELLOW}🚀 Deploying to AWS...${NC}"
    
    # Get AWS account ID
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"
    REPO_NAME="$APP_NAME-mars-level"
    
    echo -e "${YELLOW}📦 Setting up ECR repository...${NC}"
    
    # Create ECR repository if it doesn't exist
    aws ecr describe-repositories --repository-names "$REPO_NAME" --region "$REGION" 2>/dev/null || \
    aws ecr create-repository --repository-name "$REPO_NAME" --region "$REGION"
    
    # Get ECR login token
    aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ECR_URI"
    
    # Tag and push image
    docker tag "$IMAGE_NAME:$VERSION" "$ECR_URI/$REPO_NAME:$VERSION"
    docker tag "$IMAGE_NAME:$VERSION" "$ECR_URI/$REPO_NAME:latest"
    docker push "$ECR_URI/$REPO_NAME:$VERSION"
    docker push "$ECR_URI/$REPO_NAME:latest"
    
    echo -e "${YELLOW}🎯 Creating ECS resources...${NC}"
    
    # Create ECS cluster
    aws ecs create-cluster --cluster-name "$APP_NAME-cluster" --region "$REGION" 2>/dev/null || true
    
    # Create task definition
    cat > task-definition.json << EOF
{
    "family": "$APP_NAME-task",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "1024",
    "memory": "2048",
    "executionRoleArn": "arn:aws:iam::$AWS_ACCOUNT_ID:role/ecsTaskExecutionRole",
    "containerDefinitions": [
        {
            "name": "$APP_NAME",
            "image": "$ECR_URI/$REPO_NAME:$VERSION",
            "portMappings": [
                {
                    "containerPort": 8080,
                    "protocol": "tcp"
                }
            ],
            "environment": [
                {"name": "ENVIRONMENT", "value": "$ENVIRONMENT"},
                {"name": "PORT", "value": "8080"},
                {"name": "LOG_LEVEL", "value": "INFO"}
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/$APP_NAME",
                    "awslogs-region": "$REGION",
                    "awslogs-stream-prefix": "ecs"
                }
            },
            "healthCheck": {
                "command": ["CMD-SHELL", "curl -f http://localhost:8080/mars-status || exit 1"],
                "interval": 30,
                "timeout": 5,
                "retries": 3,
                "startPeriod": 60
            }
        }
    ]
}
EOF
    
    # Create CloudWatch log group
    aws logs create-log-group --log-group-name "/ecs/$APP_NAME" --region "$REGION" 2>/dev/null || true
    
    # Register task definition
    aws ecs register-task-definition --cli-input-json file://task-definition.json --region "$REGION"
    
    echo -e "${GREEN}✅ AWS deployment completed!${NC}"
    echo -e "${BLUE}📝 Next steps:${NC}"
    echo "1. Create an ECS service to run your task"
    echo "2. Set up Application Load Balancer"
    echo "3. Configure Route 53 for custom domain"
    echo "4. Add environment variables for API keys"
}

# Deploy to GCP
deploy_gcp() {
    echo -e "${YELLOW}🚀 Deploying to Google Cloud...${NC}"
    
    # Get project ID
    PROJECT_ID=$(gcloud config get-value project)
    if [[ -z "$PROJECT_ID" ]]; then
        echo -e "${RED}❌ No GCP project selected. Run: gcloud config set project YOUR_PROJECT_ID${NC}"
        exit 1
    fi
    
    # Configure Docker for GCR
    gcloud auth configure-docker --region="$REGION"
    
    # Tag and push to Container Registry
    REGISTRY_URI="$REGION-docker.pkg.dev/$PROJECT_ID/$APP_NAME"
    
    echo -e "${YELLOW}📦 Setting up Artifact Registry...${NC}"
    gcloud artifacts repositories create "$APP_NAME" --repository-format=docker --location="$REGION" 2>/dev/null || true
    
    docker tag "$IMAGE_NAME:$VERSION" "$REGISTRY_URI:$VERSION"
    docker tag "$IMAGE_NAME:$VERSION" "$REGISTRY_URI:latest"
    docker push "$REGISTRY_URI:$VERSION"
    docker push "$REGISTRY_URI:latest"
    
    echo -e "${YELLOW}🏃 Deploying to Cloud Run...${NC}"
    
    gcloud run deploy "$APP_NAME" \
        --image="$REGISTRY_URI:$VERSION" \
        --region="$REGION" \
        --platform=managed \
        --port=8080 \
        --memory=2Gi \
        --cpu=2 \
        --concurrency=100 \
        --max-instances=10 \
        --set-env-vars="ENVIRONMENT=$ENVIRONMENT,PORT=8080,LOG_LEVEL=INFO" \
        --allow-unauthenticated
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe "$APP_NAME" --region="$REGION" --format="value(status.url)")
    
    echo -e "${GREEN}✅ GCP deployment completed!${NC}"
    echo -e "${BLUE}🌐 Service URL: $SERVICE_URL${NC}"
    echo -e "${BLUE}📝 Next steps:${NC}"
    echo "1. Configure custom domain mapping"
    echo "2. Set up Cloud Armor for security"
    echo "3. Add secret environment variables"
}

# Deploy to Azure
deploy_azure() {
    echo -e "${YELLOW}🚀 Deploying to Azure...${NC}"
    
    RESOURCE_GROUP="$APP_NAME-rg"
    REGISTRY_NAME="${APP_NAME//[-_]/}registry"
    CONTAINER_GROUP="$APP_NAME-group"
    
    echo -e "${YELLOW}📦 Setting up Azure Container Registry...${NC}"
    
    # Create resource group
    az group create --name "$RESOURCE_GROUP" --location "$REGION"
    
    # Create container registry
    az acr create --resource-group "$RESOURCE_GROUP" --name "$REGISTRY_NAME" --sku Basic
    
    # Login to registry
    az acr login --name "$REGISTRY_NAME"
    
    # Tag and push image
    REGISTRY_URI="$REGISTRY_NAME.azurecr.io"
    docker tag "$IMAGE_NAME:$VERSION" "$REGISTRY_URI/$APP_NAME:$VERSION"
    docker tag "$IMAGE_NAME:$VERSION" "$REGISTRY_URI/$APP_NAME:latest"
    docker push "$REGISTRY_URI/$APP_NAME:$VERSION"
    docker push "$REGISTRY_URI/$APP_NAME:latest"
    
    echo -e "${YELLOW}🏃 Creating Container Instance...${NC}"
    
    # Create container instance
    az container create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$CONTAINER_GROUP" \
        --image "$REGISTRY_URI/$APP_NAME:$VERSION" \
        --registry-login-server "$REGISTRY_URI" \
        --registry-username "$REGISTRY_NAME" \
        --registry-password "$(az acr credential show --name $REGISTRY_NAME --query passwords[0].value -o tsv)" \
        --dns-name-label "$APP_NAME-mars-level" \
        --ports 8080 \
        --memory 2 \
        --cpu 2 \
        --environment-variables ENVIRONMENT="$ENVIRONMENT" PORT=8080 LOG_LEVEL=INFO
    
    # Get FQDN
    FQDN=$(az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_GROUP" --query ipAddress.fqdn -o tsv)
    
    echo -e "${GREEN}✅ Azure deployment completed!${NC}"
    echo -e "${BLUE}🌐 Service URL: http://$FQDN:8080${NC}"
    echo -e "${BLUE}📝 Next steps:${NC}"
    echo "1. Configure Application Gateway for load balancing"
    echo "2. Set up Azure Key Vault for secrets"
    echo "3. Configure custom domain and SSL"
}

# Deploy locally
deploy_docker() {
    echo -e "${YELLOW}🚀 Starting local Docker deployment...${NC}"
    
    # Create production environment file
    if [[ ! -f ".env.production" ]]; then
        echo -e "${YELLOW}📝 Creating .env.production from template...${NC}"
        cp .env.production.template .env.production
        echo -e "${YELLOW}⚠️  Please edit .env.production with your API keys and configuration${NC}"
    fi
    
    # Start with docker-compose
    docker-compose -f docker-compose.production.yml up -d
    
    echo -e "${GREEN}✅ Local deployment completed!${NC}"
    echo -e "${BLUE}🌐 Service URL: http://localhost:8080${NC}"
    echo -e "${BLUE}📝 Services started:${NC}"
    echo "- ChatterFix CMMS: http://localhost:8080"
    echo "- Redis: localhost:6379"
    echo "- Ollama: http://localhost:11434"
    echo "- Prometheus: http://localhost:9090"
    echo "- Grafana: http://localhost:3000"
}

# Main execution
main() {
    check_prerequisites
    build_image
    
    case $PLATFORM in
        aws)
            deploy_aws
            ;;
        gcp)
            deploy_gcp
            ;;
        azure)
            deploy_azure
            ;;
        docker)
            deploy_docker
            ;;
        *)
            echo -e "${RED}Unsupported platform: $PLATFORM${NC}"
            exit 1
            ;;
    esac
    
    echo -e "${GREEN}🎉 ChatterFix CMMS Mars-Level AI Platform deployment completed!${NC}"
    echo -e "${BLUE}🚀 Your Mars-level AI platform is ready for action!${NC}"
}

# Cleanup on exit
cleanup() {
    [[ -f "task-definition.json" ]] && rm -f task-definition.json
}
trap cleanup EXIT

# Run main function
main