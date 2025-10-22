# ChatterFix Developer Checklist

## 📁 Repository Structure - Where Code Belongs

### Frontend Development
- **React Components**: `frontend/src/components/`
- **Pages & Views**: `frontend/src/pages/`
- **Utilities**: `frontend/utils/`
- **Storybook Docs**: `frontend/storybook/`

### Backend Development  
- **API Endpoints**: `backend/app/api/`
  - Work Orders: `backend/app/api/work_orders.py`
  - Assets: `backend/app/api/assets.py`
  - Parts: `backend/app/api/parts.py`
- **Business Logic**: `backend/app/services/`
- **Database**: `backend/app/database/`
- **Utilities**: `backend/app/utils/`
- **Main Entry**: `backend/app/main.py`

### AI Services
- **Core AI Services**: `ai/services/`
  - Fix It Fred: `ai/services/fix_it_fred_service.py`
  - AI Brain: `ai/services/ai_brain_service.py`
  - Predictive Intelligence: `ai/services/predictive_intelligence_service.py`
- **AI Assistants**: `ai/assistants/`
- **Provider Integrations**: `ai/providers/`
- **AI Gateways**: `ai/gateway/`

### Infrastructure & DevOps
- **Kubernetes**: `infra/k8s/`
- **Docker**: `infra/docker/`
- **Deployment Scripts**: `infra/scripts/deploy/`
- **Development Tools**: `infra/scripts/dev/`
- **Monitoring**: `infra/monitoring/`
- **Configuration**: `infra/config/`

### Documentation
- **Architecture**: `docs/architecture/`
- **API Docs**: `docs/api/`
- **Feature Guides**: `docs/features/`
- **Maintenance**: `docs/maintenance/`

---

## 🏗️ Naming Conventions

### Files
- **Python**: `snake_case.py`
- **TypeScript/React**: `PascalCase.tsx` for components, `camelCase.ts` for utilities
- **Configuration**: `kebab-case.yml`, `snake_case.env`
- **Scripts**: `kebab-case.sh`

### Directories
- **All lowercase**: `services/`, `components/`, `utils/`
- **Hyphenated**: `api-docs/`, `test-results/`

### API Endpoints
- **RESTful**: `/api/work_orders`, `/api/assets/{id}`
- **AI Endpoints**: `/api/ai/chat`, `/api/predict/failures`
- **Health Checks**: `/health`, `/status`

---

## 🧪 Testing Requirements Before PRs

### Backend Testing
```bash
# Run from project root
cd backend/app
python -m pytest tests/ -v
python -m pytest tests/test_api.py::test_work_orders
```

### Frontend Testing  
```bash
cd frontend/
npm test
npm run lint
npm run type-check
```

### AI Services Testing
```bash
# Test AI service health endpoints
curl http://localhost:9001/health
python -c "from ai.services.fix_it_fred_service import call_ollama; print('✅ AI imports OK')"
```

### Integration Testing
```bash
# Full stack health check
python infra/scripts/testing/run-tests.sh
```

---

## 🚀 Local Development Setup

### 1. Backend Services
```bash
# Install dependencies
cd backend/app
pip install -r requirements.txt

# Start main API server
python main.py --port 8000

# Health check
curl http://localhost:8000/health
```

### 2. AI Services
```bash
# Start Fix It Fred AI
python ai/services/fix_it_fred_service.py

# Test AI endpoint
curl -X POST http://localhost:9001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I fix a pump?", "provider": "ollama"}'
```

### 3. Frontend Development
```bash
cd frontend/
npm install
npm run dev

# Build for production
npm run build
```

### 4. Database Setup
```bash
# Initialize PostgreSQL (if needed)
python backend/app/database/postgresql_init.py

# Run migrations
alembic upgrade head
```

---

## 🔄 Branch and Tag Workflow

### Branch Strategy
- **main**: Production-ready code
- **main-clean**: Clean development branch
- **feature/feature-name**: New features
- **fix/issue-description**: Bug fixes
- **refactor/component-name**: Code improvements

### Safe Development Process
1. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-api-endpoint
   ```

2. **Make Changes in Correct Directories**
   - Backend changes → `backend/app/api/`
   - Frontend changes → `frontend/src/`
   - AI changes → `ai/services/`

3. **Test Locally**
   ```bash
   # Run relevant tests
   pytest backend/app/tests/
   npm test --prefix frontend/
   ```

4. **Commit with Clear Messages**
   ```bash
   git add backend/app/api/new_endpoint.py
   git commit -m "feat: add new asset tracking endpoint
   
   - Implements GET/POST for asset lifecycle tracking
   - Includes validation and error handling
   - Updates API documentation"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/new-api-endpoint
   # Create PR via GitHub UI
   ```

---

## 📋 Pre-PR Validation Checklist

### Code Quality
- [ ] **No new root-level files** (use proper directories)
- [ ] **Import paths updated** (no `from core.cmms.*`)
- [ ] **Naming conventions followed**
- [ ] **Documentation updated** (if needed)

### Testing
- [ ] **Local tests pass** 
- [ ] **Health endpoints respond**
- [ ] **No lint errors**
- [ ] **TypeScript compiles** (frontend)

### Architecture Compliance
- [ ] **Files in correct directories**
- [ ] **API endpoints follow RESTful patterns**
- [ ] **AI services use proper provider pattern**
- [ ] **Database changes include migrations**

### Security
- [ ] **No hardcoded secrets**
- [ ] **Environment variables used**
- [ ] **Input validation implemented**
- [ ] **Authentication/authorization checked**

---

## 🎯 Quick Commands Reference

### Development
```bash
# Backend API server
python backend/app/main.py

# AI services  
python ai/services/fix_it_fred_service.py

# Frontend dev server
npm run dev --prefix frontend/

# Database migrations
alembic upgrade head
```

### Testing
```bash
# Backend tests
pytest backend/app/tests/ -v

# Frontend tests
npm test --prefix frontend/

# AI service health
curl http://localhost:9001/health

# Full integration test
python infra/scripts/testing/run-tests.sh
```

### Deployment
```bash
# Local deployment
docker-compose up -d

# Production deployment  
./infra/scripts/deploy/deploy-production.sh

# Health check all services
./infra/monitoring/service_monitor.py --check-all
```

---

## 🚨 What NOT to Do

### ❌ Forbidden Actions
- **Don't create root-level Python files** (use proper directories)
- **Don't use legacy import paths** (`from core.cmms.*`)
- **Don't skip tests** before submitting PRs
- **Don't hardcode secrets** in any files
- **Don't modify multiple unrelated components** in one PR

### ⚠️ Proceed with Caution
- **Large architectural changes** - discuss in issues first
- **Database schema changes** - require migration scripts
- **AI model changes** - test thoroughly with all providers
- **Infrastructure changes** - validate in staging first

---

## 🆘 Getting Help

### Documentation
- **Architecture**: `docs/architecture/`
- **API Reference**: `docs/api/`
- **Troubleshooting**: `docs/maintenance/`

### Quick Help
- **Backend issues**: Check `backend/app/main.py` health endpoint
- **AI service issues**: Verify Ollama is running on port 11434
- **Frontend issues**: Check browser console and run `npm run lint`
- **Database issues**: Verify PostgreSQL connection in `backend/app/database/`

### Contact
- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For architectural questions
- **Security Issues**: Use private security reporting

---

## 🔄 Development Workflow - Post-Consolidation

### Enterprise Development Process
1. **Create feature branch from `safe-edit`**
   ```bash
   git checkout safe-edit
   git pull origin safe-edit
   git checkout -b feature/your-feature-name
   ```

2. **Run pre-commit checks locally**
   ```bash
   pip install pre-commit
   pre-commit install
   pre-commit run --all-files  # Test before committing
   ```

3. **Ensure all imports resolve**
   ```bash
   python -c "import backend.app.main; print('✅ Backend imports OK')"
   python -c "import ai.services.fix_it_fred_service; print('✅ AI imports OK')"
   pytest -q --collect-only  # Validate test discovery
   ```

4. **Open PR and wait for CI**
   - Push branch: `git push origin feature/your-feature-name`
   - Create PR via GitHub UI
   - Wait for CI to pass (architecture protection + tests)
   - Request review from team

5. **Merge only through GitHub UI**
   - **Never use CLI merges** (`git merge`) on main branches
   - Use "Squash and merge" for clean history
   - Delete feature branch after merge

### Protected Branches
- `main-clean`: Enterprise baseline (protected)
- `safe-edit`: Active development branch  
- `production`: Production deployment branch

### Architecture Protection
- ✅ `.github/workflows/protect-enterprise.yml` blocks violations
- ✅ Pre-commit hooks prevent common issues
- ✅ No new root-level Python files allowed
- ✅ Import path validation enforced

---

**Remember**: This codebase is enterprise-grade. Every change should be purposeful, tested, and documented. When in doubt, create an issue to discuss the approach first! 🚀