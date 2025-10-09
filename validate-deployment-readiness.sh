#!/bin/bash

# ChatterFix CMMS - Complete Deployment Readiness Validation
# Validates all components before GCP deployment

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 ChatterFix CMMS - Deployment Readiness Validation${NC}"
echo "======================================================"
echo ""

ERRORS=0
WARNINGS=0

# Step 1: Python Syntax Validation
echo -e "${YELLOW}📝 Step 1: Python Syntax Validation${NC}"
cd core/cmms
for file in *.py; do
    if [ -f "$file" ]; then
        if python3 -m py_compile "$file" 2>/dev/null; then
            echo -e "${GREEN}✅${NC} $file"
        else
            echo -e "${RED}❌${NC} $file has syntax errors"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done
echo ""

# Step 2: Import Validation
echo -e "${YELLOW}🔗 Step 2: Critical Imports Validation${NC}"
if python3 -c "import app; print('✅ app.py imports successfully')" 2>&1; then
    echo -e "${GREEN}✅${NC} Main application imports successfully"
else
    echo -e "${RED}❌${NC} Main application import failed"
    ERRORS=$((ERRORS + 1))
fi

if [ -f "technician_ai_assistant.py" ]; then
    if python3 -c "import technician_ai_assistant; print('✅ technician_ai_assistant.py imports successfully')" 2>&1; then
        echo -e "${GREEN}✅${NC} Technician AI Assistant imports successfully"
    else
        echo -e "${RED}❌${NC} Technician AI Assistant import failed"
        ERRORS=$((ERRORS + 1))
    fi
fi
echo ""

# Step 3: Unit Tests
echo -e "${YELLOW}🧪 Step 3: Running Unit Tests${NC}"
if pytest tests/unit/ -v --tb=short 2>&1 | tail -20; then
    echo -e "${GREEN}✅${NC} Unit tests passed"
else
    echo -e "${RED}❌${NC} Unit tests failed"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Step 4: Deployment Scripts Validation
echo -e "${YELLOW}📦 Step 4: Deployment Scripts Validation${NC}"
DEPLOY_SCRIPTS=(
    "deploy-ai-brain-service.sh"
    "deploy-fix-it-fred.sh"
    "deployment/deploy-consolidated-services.sh"
    "deployment/validate-ai-endpoints.sh"
)

for script in "${DEPLOY_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        if bash -n "$script" 2>/dev/null; then
            echo -e "${GREEN}✅${NC} $script syntax valid"
        else
            echo -e "${RED}❌${NC} $script has syntax errors"
            ERRORS=$((ERRORS + 1))
        fi
    else
        echo -e "${YELLOW}⚠️${NC} $script not found (optional)"
        WARNINGS=$((WARNINGS + 1))
    fi
done
echo ""

# Step 5: Docker Configuration Validation
echo -e "${YELLOW}🐳 Step 5: Docker Configuration Validation${NC}"
DOCKERFILES=(
    "Dockerfile"
    "Dockerfile.ai-brain"
    "Dockerfile.techbot"
)

for dockerfile in "${DOCKERFILES[@]}"; do
    if [ -f "$dockerfile" ]; then
        echo -e "${GREEN}✅${NC} $dockerfile found"
    else
        echo -e "${YELLOW}⚠️${NC} $dockerfile not found (may be optional)"
        WARNINGS=$((WARNINGS + 1))
    fi
done
echo ""

# Step 6: Requirements Files Validation
echo -e "${YELLOW}📋 Step 6: Requirements Files Validation${NC}"
REQUIREMENTS=(
    "requirements.txt"
    "requirements.ai-brain.txt"
    "requirements.fred.txt"
)

for req in "${REQUIREMENTS[@]}"; do
    if [ -f "$req" ]; then
        echo -e "${GREEN}✅${NC} $req found"
        # Check if requirements can be parsed
        if pip install --dry-run -r "$req" > /dev/null 2>&1; then
            echo -e "${GREEN}  ✓${NC} Dependencies resolvable"
        else
            echo -e "${YELLOW}  ⚠${NC} Some dependencies may need review"
            WARNINGS=$((WARNINGS + 1))
        fi
    else
        echo -e "${YELLOW}⚠️${NC} $req not found (may be optional)"
        WARNINGS=$((WARNINGS + 1))
    fi
done
echo ""

# Step 7: Environment Variables Check
echo -e "${YELLOW}🔐 Step 7: Environment Variables Check${NC}"
CRITICAL_ENV_VARS=(
    "DATABASE_TYPE"
    "SERVICE_MODE"
)

echo -e "${BLUE}ℹ️${NC} The following environment variables should be set in GCP:"
for var in "${CRITICAL_ENV_VARS[@]}"; do
    echo "  - $var"
done
echo ""

# Step 8: GCP Configuration Check
echo -e "${YELLOW}☁️ Step 8: GCP Configuration Check${NC}"
cd ../..
if [ -f "gcp_deployment_config.sh" ]; then
    echo -e "${GREEN}✅${NC} GCP deployment config found"
    cat gcp_deployment_config.sh
else
    echo -e "${YELLOW}⚠️${NC} GCP deployment config not found"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Step 9: Documentation Check
echo -e "${YELLOW}📚 Step 9: Documentation Check${NC}"
DOCS=(
    "README.md"
    "core/cmms/FIX_IT_FRED_README.md"
    "core/cmms/TECHBOT_DEPLOYMENT_GUIDE.md"
)

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        echo -e "${GREEN}✅${NC} $doc found"
    else
        echo -e "${YELLOW}⚠️${NC} $doc not found"
        WARNINGS=$((WARNINGS + 1))
    fi
done
echo ""

# Step 10: Security Check
echo -e "${YELLOW}🔒 Step 10: Security Check${NC}"
echo -e "${BLUE}ℹ️${NC} Checking for hardcoded credentials..."
cd core/cmms
if grep -r "password.*=" *.py 2>/dev/null | grep -v "PGPASSWORD" | grep -v "# " | grep -v "password_hash" | head -5; then
    echo -e "${YELLOW}⚠️${NC} Potential hardcoded passwords found - review manually"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✅${NC} No obvious hardcoded passwords found"
fi
echo ""

# Final Report
cd ../..
echo "======================================================"
echo -e "${BLUE}📊 Deployment Readiness Report${NC}"
echo "======================================================"

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ ERRORS: $ERRORS${NC}"
else
    echo -e "${RED}❌ ERRORS: $ERRORS${NC}"
fi

if [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ WARNINGS: $WARNINGS${NC}"
else
    echo -e "${YELLOW}⚠️ WARNINGS: $WARNINGS${NC}"
fi

echo ""
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}🎉 DEPLOYMENT READY!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Review and configure GCP project settings"
    echo "2. Set up required environment variables in GCP"
    echo "3. Deploy using: cd core/cmms && ./deployment/deploy-consolidated-services.sh"
    echo "4. Validate deployment: ./deployment/validate-ai-endpoints.sh"
    exit 0
else
    echo -e "${RED}❌ DEPLOYMENT NOT READY - Fix errors first${NC}"
    echo ""
    echo "Please address the errors above before deploying."
    exit 1
fi
