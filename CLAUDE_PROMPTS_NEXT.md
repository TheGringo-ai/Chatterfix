# ChatterFix - Claude Prompt Pack for Next Phase

Copy/paste these prompts one at a time to evolve ChatterFix from MVP to production-ready platform.

## 1) 🚨 Ops Hardening: Alerting & SLO Guards

```
You are SRE for ChatterFix. Add alert policies and SLO burn-rate alerts:
- 99.9% availability SLO; alert on 2%/1h and 5%/10m burn.
- P95 latency alerts per endpoint (/work_orders, /assets, /parts, /automation/*).
- Dashboards: latency, error rate, request volume, automation outcomes.
Deliver: Terraform or YAML for Monitoring, plus README runbook steps.
Commit: ops: add SLOs, burn-rate alerts, and dashboards.
```

## 2) 💰 Cost Control & Autoscaling

```
Optimize Cloud Run scaling and budgets:
- Set concurrency=40, min=1, max=10; add CPU-throttling on idle.
- Add GCP budgets + 80/100/120% alerts.
- Cache: 30s in-memory result cache; ETag support on GETs.
Deliver: gcloud/TF configs + docs. Commit: chore: scale tuning and budget guards.
```

## 3) 🔐 RBAC + JWT Auth

```
Add role-based access:
- Roles: viewer, planner, admin.
- Issue JWT via lightweight `/auth/token` (dev mode) or OIDC (prod-ready hooks).
- Enforce per-route permissions; log denials without payloads.
Commit: security: add RBAC with JWT/OIDC scaffolding + tests.
```

## 4) 💾 Data Persistence Switch (Demo ↔ Prod)

```
Implement storage adapters:
- InMemoryAdapter (demo), FirestoreAdapter, SQLAdapter (SQLAlchemy).
- ENV CHX_STORAGE_BACKEND=memory|firestore|sql; migrate on boot if sql.
- Add integration tests; seed tools for each backend.
Commit: feat: pluggable storage backends and migrations.
```

## 5) 📋 Import/Export Pipelines

```
Add CSV importers for Work Orders/Assets/Parts with schema validation.
- `/imports/*` accepts CSV; dry-run + error report; idempotent upserts.
- `/exports/*` streams CSV and PDF with consistent headers.
Commit: feat: bulk import/export with validation + docs.
```

## 6) 🔔 Webhooks & Notifications

```
Add outbound webhooks and Teams/Slack notifications:
- Events: work_order.created/updated/overdue, inventory.reorder, automation.executed.
- Signed HMAC headers; retry with backoff.
Commit: feat: webhooks + chat notifications + signatures.
```

## 7) 🧠 Prediction Feedback & Model Tuning

```
Close the loop on AI:
- `/feedback/prediction` endpoint to mark prediction helpful|unhelpful.
- Log features+label for incremental retraining; nightly job retrains.
- Model registry with version pinning and A/B compare.
Commit: feat(ai): feedback loop, scheduled retrain, model registry.
```

## 8) 📜 Compliance & Audit Pack

```
Add audit log export (daily to GCS), PII masking utilities, retention policies config.
- Admin UI to set retention per dataset (30/90/365).
Commit: chore(security): audit exports, masking, retention controls.
```

## 9) 🆘 Disaster Recovery Playbooks

```
Write DR docs + scripts:
- Cross-region deploy (us-central1 ↔ us-east1) + DNS failover.
- Backup/restore scripts for data + model artifacts.
Commit: docs(ops): DR playbooks and failover scripts.
```

## 10) 🎭 Investor Demo Mode

```
Create `DEMO_MODE=true`:
- Synthetic tenant + safe seeded data.
- One-click demo flow: triggers predictions, automation, exports.
- Branded landing and story-driven walkthrough.
Commit: feat(demo): investor-ready demo preset with scripted tour.
```

## 🚀 Usage Instructions

1. **Pick a prompt** based on your current priority
2. **Paste into Claude** exactly as written
3. **Follow the implementation** guidance
4. **Commit with the suggested message** for clean git history
5. **Move to next prompt** when ready

## 📋 Suggested Order

**Week 1**: Ops Hardening (#1) + Cost Control (#2)
**Week 2**: RBAC (#3) + Data Persistence (#4)  
**Week 3**: Import/Export (#5) + Webhooks (#6)
**Week 4**: AI Feedback (#7) + Compliance (#8)
**Month 2**: DR (#9) + Demo Mode (#10)

## 🎯 Success Metrics

Each prompt should result in:
- ✅ Working code changes
- ✅ Tests or validation scripts
- ✅ Documentation updates
- ✅ Clean commit with conventional message
- ✅ Deployment verification

---

*Ready to scale ChatterFix from Empire to Global Domination* 🌍