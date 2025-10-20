# 🧩 ChatterFix Enterprise Growth Prompt Deck (A-H)

**Phase 2: Enterprise Feature Development**  
Building on the consolidated enterprise architecture foundation.

---

## Prompt A — Authentication & RBAC Finalization

You are the ChatterFix Security Engineer.  
**Goal:** Implement full enterprise authentication.

**Tasks:**
1. Extend `backend/app/api/security.py` to support OAuth2 + JWT
2. Add RBAC roles (Admin, Manager, Technician)
3. Integrate token validation middleware into all API routers
4. Add `/api/auth/login`, `/api/auth/logout`, `/api/auth/refresh`
5. Update `frontend/src/pages/Login.tsx` and auth context
6. Document flow in `docs/api/security.md`

**Output:** Updated backend + frontend code summary + token flow diagram (Markdown only).

---

## Prompt B — Preventive Maintenance & Asset Hierarchy

You are the CMMS Core Engineer.  
**Goal:** Build enterprise-level maintenance logic.

**Tasks:**
1. Expand models:
   - `backend/app/models/asset.py` → add `parent_id` for hierarchy
   - `backend/app/models/maintenance.py` → add `recurrence_rule`, `next_due`
2. Create services:
   - `maintenance_service.py` to auto-generate PM work orders
3. Add API routes: `/api/maintenance/templates`, `/api/maintenance/schedule`
4. Update frontend maintenance dashboard to show hierarchy tree

**Output:** Schema diff + sample JSON for PM template API.

---

## Prompt C — Reporting & Dashboard Analytics

You are the ChatterFix Data Analyst Engineer.  
**Goal:** Deliver advanced KPI reporting.

**Tasks:**
1. Extend `backend/app/services/report_service.py` to compute MTBF, downtime %, cost trend
2. Add TimescaleDB queries for IoT telemetry aggregation
3. Create `/api/reports/kpi` and `/api/reports/trends`
4. Update `frontend/Dashboard.tsx` with Chart.js visuals
5. Document KPIs in `docs/features/analytics.md`

**Output:** Example API responses + dashboard wireframe (Markdown).

---

## Prompt D — Document & File Management

You are the File Systems Engineer.  
**Goal:** Add enterprise document attachments.

**Tasks:**
1. Implement `backend/app/api/documents.py` for upload/download/delete
2. Store files in GCS or S3 via `infra/config/storage.env`
3. Link uploaded files to work orders and assets
4. Frontend: add file drop zone + preview modal
5. Write `docs/features/documents.md` with API usage

**Output:** API contract + security considerations (no credentials).

---

## Prompt E — Notifications & Alerting System

You are the Automation Engineer.  
**Goal:** Provide real-time alerts and notifications.

**Tasks:**
1. Introduce background task queue (Celery or FastAPI tasks)
2. Create `notification_service.py` for email/SMS
3. Integrate SendGrid / Twilio API keys via Secret Manager
4. Add user preferences table for alert channels
5. Expose endpoints: `/api/alerts/send`, `/api/alerts/preferences`
6. Frontend toast notifications for real-time updates

**Output:** YAML diagram of notification flow + sample alert payload.

---

## Prompt F — Multi-Environment Deployment

You are the DevOps Environment Engineer.  
**Goal:** Enable separate Dev/Staging/Prod deployments.

**Tasks:**
1. Extend `infra/scripts/deploy.py` to read `.env.dev`, `.env.stage`, `.env.prod`
2. Add K8s namespace and context switching
3. Configure CI/CD matrix for multi-environment builds
4. Document environment variables in `docs/maintenance/environments.md`

**Output:** Example .env files + CI matrix snippet.

---

## Prompt G — Monitoring & Observability

You are the Site Reliability Engineer.  
**Goal:** Add unified monitoring and metrics.

**Tasks:**
1. Integrate Prometheus exporters for backend and AI services
2. Create Grafana dashboards for CPU/memory, response time, error rate
3. Add alerts to Slack/Email for service downtime
4. Include `infra/monitoring/` with docker-compose for local Grafana stack
5. Document dashboards in `docs/maintenance/monitoring.md`

**Output:** Prometheus config + Grafana JSON dashboard example.

---

## Prompt H — Fix It Fred AI Enhancements

You are the AI Systems Architect.  
**Goal:** Make Fix It Fred truly adaptive and context-aware.

**Tasks:**
1. Add context memory store (Firestore or Redis)
2. Enable session-based conversation history
3. Implement learning from past work orders & sensor patterns
4. Add `/api/ai/context` and `/api/ai/learn`
5. Support voice commands (optional Phase 2.1)
6. Update `docs/features/fix_it_fred_v2.md`

**Output:** Architecture diagram + JSON context example.

---

## ✅ Execution Guide

### Sequential Development Process
1. **Work from your `safe-edit` branch**
2. **Feed one prompt (A–H) at a time** to Claude / GPT-5 / Gemini
3. **Review outputs; commit and tag** each feature incrementally:
   - `v2.1.0-auth`, `v2.2.0-pm`, `v2.3.0-analytics`, `v2.4.0-docs`, `v2.5.0-alerts`, `v2.6.0-deployment`, `v2.7.0-monitoring`, `v2.8.0-ai`
4. **Keep `.github/workflows/protect-enterprise.yml` active**
5. **Update `CHANGELOG.md` and `docs/features/`** after every prompt

### Branch Strategy
```bash
# For each prompt
git checkout safe-edit
git pull origin safe-edit
git checkout -b feature/prompt-a-auth  # or prompt-b-pm, etc.

# After completion
git checkout safe-edit
git merge feature/prompt-a-auth
git tag v2.1.0-auth
git push origin safe-edit --tags
```

### Quality Gates
- ✅ All tests pass before merge
- ✅ Architecture protection validates structure
- ✅ Documentation updated for new features
- ✅ API endpoints follow established patterns

---

## 🎯 Expected Timeline

**Phase 2 Development Schedule:**
- **Week 1-2**: Prompt A (Authentication & RBAC)
- **Week 3-4**: Prompt B (Preventive Maintenance)
- **Week 5-6**: Prompt C (Reporting & Analytics)
- **Week 7-8**: Prompt D (Document Management)
- **Week 9-10**: Prompt E (Notifications)
- **Week 11-12**: Prompt F (Multi-Environment)
- **Week 13-14**: Prompt G (Monitoring)
- **Week 15-16**: Prompt H (AI Enhancements)

**Total Duration:** ~4 months of systematic enterprise development

---

## 🚀 Phase 2 Success Criteria

After completing all 8 prompts, ChatterFix will have:

### Enterprise Authentication
- ✅ OAuth2/JWT security with role-based access
- ✅ Multi-tenant user management
- ✅ Secure API endpoints

### Advanced CMMS Features
- ✅ Asset hierarchy and preventive maintenance
- ✅ Comprehensive reporting and analytics
- ✅ Document management and file attachments

### Production Operations
- ✅ Multi-environment deployment pipeline
- ✅ Complete monitoring and observability
- ✅ Real-time notifications and alerting

### AI Intelligence
- ✅ Context-aware Fix It Fred assistant
- ✅ Predictive maintenance capabilities
- ✅ Learning from operational data

---

**Ready to build enterprise-grade CMMS capabilities systematically! 🎯**

*Use this deck to maintain the same professional development standards established in Phase 1 consolidation.*