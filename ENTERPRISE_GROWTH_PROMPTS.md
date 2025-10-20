# 🚀 ChatterFix Enterprise Growth Cycle — Claude Prompt Deck

**Post-Consolidation Development Prompts**  
Use these prompts sequentially to build enterprise features on the stable architecture foundation.

---

## Prompt A — Authentication & RBAC Implementation

You are the ChatterFix Security Engineer.  
Build complete authentication and role-based access control on the consolidated architecture.

**Requirements:**
- Extend `backend/app/api/security.py` with OAuth2 + JWT implementation
- Implement roles: Admin, Manager, Technician with proper permissions
- Create middleware for route protection in `backend/app/services/security_middleware.py`
- Add login/logout endpoints: `/api/auth/login`, `/api/auth/logout`, `/api/auth/verify`
- Update frontend with authentication forms in `frontend/src/auth/`
- Document API security in `docs/api/authentication.md`

**Output:**
- Working JWT authentication system
- Role-based endpoint protection
- Frontend login integration
- Security documentation

---

## Prompt B — Preventive Maintenance & Asset Hierarchy

You are the ChatterFix Asset Management Specialist.  
Implement comprehensive asset hierarchy and preventive maintenance scheduling.

**Requirements:**
- Create `backend/app/models/asset_hierarchy.py` with parent-child relationships
- Build PM template system in `backend/app/models/maintenance_template.py`
- Add API endpoints: `/api/assets/hierarchy`, `/api/maintenance/templates`, `/api/maintenance/schedule`
- Implement recurring PM job scheduler using FastAPI background tasks
- Create asset tree component in `frontend/src/components/AssetTree.tsx`
- Add PM dashboard in `frontend/src/pages/PreventiveMaintenance.tsx`

**Output:**
- Asset hierarchy with parent-child relationships
- PM template system with scheduling
- Asset tree visualization
- PM scheduling dashboard

---

## Prompt C — Reporting & Analytics Dashboard

You are the ChatterFix Analytics Engineer.  
Build comprehensive KPI reporting and trend analysis capabilities.

**Requirements:**
- Create `backend/app/api/reports.py` with endpoints: `/api/reports/kpi`, `/api/reports/trends`, `/api/reports/performance`
- Implement data aggregation services in `backend/app/services/analytics_service.py`
- Build Chart.js integration in `frontend/src/components/Charts/`
- Create executive dashboard in `frontend/src/pages/ExecutiveDashboard.tsx`
- Add report export functionality (PDF, CSV)
- Document metrics in `docs/api/reporting.md`

**Output:**
- Real-time KPI endpoints
- Interactive dashboard with charts
- Report export capabilities
- Analytics documentation

---

## Prompt D — Document & File Management System

You are the ChatterFix Document Management Engineer.  
Implement secure file upload, storage, and attachment system.

**Requirements:**
- Create `backend/app/api/documents.py` with upload/download endpoints
- Implement secure file storage using local storage or cloud (configurable)
- Add file metadata tracking in `backend/app/models/document.py`
- Build file attachment system for work orders and assets
- Create drag-drop upload component in `frontend/src/components/FileUpload.tsx`
- Add document viewer in `frontend/src/components/DocumentViewer.tsx`
- Implement file security and access controls

**Output:**
- Secure file upload/download system
- Document attachment to work orders/assets
- Frontend file management interface
- Document security controls

---

## Prompt E — Notification & Communication System

You are the ChatterFix Communications Engineer.  
Build comprehensive notification system with email, SMS, and in-app alerts.

**Requirements:**
- Create `backend/app/services/notification_service.py` with multi-channel support
- Implement background job queue using FastAPI background tasks or Celery
- Add notification preferences in `backend/app/models/user_preferences.py`
- Build email templates in `backend/app/templates/email/`
- Create notification center in `frontend/src/components/NotificationCenter.tsx`
- Integrate with email providers (SendGrid, SMTP) and SMS (Twilio)
- Add real-time notifications using WebSockets

**Output:**
- Multi-channel notification system
- Background job processing
- Real-time notification delivery
- User notification preferences

---

## Prompt F — Multi-Environment Deployment Pipeline

You are the ChatterFix DevOps Engineer.  
Enhance deployment infrastructure for dev/staging/prod environments.

**Requirements:**
- Extend `infra/scripts/deploy/` with environment-specific configurations
- Create environment profiles in `infra/config/environments/`
- Build CI/CD pipeline enhancements in `.github/workflows/`
- Implement blue-green deployment strategy
- Add infrastructure monitoring in `infra/monitoring/prometheus/`
- Create environment health checks and rollback procedures
- Document deployment procedures in `docs/deployment/`

**Output:**
- Multi-environment deployment automation
- Blue-green deployment capability
- Environment monitoring
- Deployment documentation

---

## Prompt G — Monitoring & Observability Platform

You are the ChatterFix Site Reliability Engineer.  
Implement comprehensive monitoring, logging, and observability.

**Requirements:**
- Add Prometheus exporters to all services in `backend/app/`, `ai/services/`
- Create Grafana dashboards in `infra/monitoring/grafana/`
- Implement distributed tracing with OpenTelemetry
- Add log aggregation using ELK stack or similar
- Create alerting rules in `infra/monitoring/alerts/`
- Build service health dashboard in `frontend/src/pages/HealthDashboard.tsx`
- Add performance monitoring and SLA tracking

**Output:**
- Complete observability stack
- Service health monitoring
- Performance dashboards
- Automated alerting system

---

## Prompt H — AI Assistant Enhancement & Context

You are the ChatterFix AI Intelligence Engineer.  
Enhance Fix It Fred with memory, context awareness, and advanced AI capabilities.

**Requirements:**
- Implement conversation memory in `ai/services/context_service.py`
- Add user context tracking in `ai/models/user_context.py`
- Create AI endpoints: `/api/ai/context`, `/api/ai/memory`, `/api/ai/suggestions`
- Build proactive maintenance suggestions using AI analysis
- Enhance Fix It Fred with work order context awareness
- Add AI chat history in `frontend/src/components/AIChatHistory.tsx`
- Implement intelligent task automation and recommendations

**Output:**
- Context-aware AI assistant
- Proactive maintenance suggestions
- AI memory and learning capabilities
- Intelligent automation features

---

## 🎯 Execution Guidelines

### Sequential Development
1. **Start from `safe-edit` branch** for each prompt
2. **Create feature branch** per prompt: `feature/auth-rbac`, `feature/pm-scheduling`, etc.
3. **Follow architecture** - respect the directory structure
4. **Test thoroughly** - ensure all services integrate properly
5. **Document changes** - update relevant docs/api/ files

### Integration Points
- All new APIs follow FastAPI patterns in `backend/app/api/`
- Frontend components use React 18 + TypeScript in `frontend/src/`
- AI enhancements extend existing services in `ai/services/`
- Infrastructure additions go in `infra/` with proper organization

### Quality Assurance
- **Pre-commit hooks** will validate code quality
- **CI/CD pipeline** will test integration
- **Architecture protection** prevents violations
- **Documentation** required for all new APIs

---

## 🚀 Expected Outcome

After completing Prompts A-H:
- **Enterprise-grade CMMS** with full authentication, asset management, reporting
- **Production-ready deployment** with monitoring and observability  
- **AI-enhanced operations** with context-aware assistance
- **Scalable architecture** ready for multi-tenant expansion

**Development Timeline:** Each prompt represents ~1-2 weeks of focused development work.

---

**Ready to build the future of maintenance management! 🎯**