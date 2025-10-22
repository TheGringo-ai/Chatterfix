# 🧭 ChatterFix CMMS — Phase 6B Claude Prompt Deck

**Objective:** Finalize enterprise analytics, automation, and investor-ready systems.  
**Team:** GPT-5 (Engineering) | Claude (Process) | Gemini (Analytics) | Fix It Fred (Ops)  
**Status:** Phase 6 ✅ | Phase 6B ⚙️ In Progress  

---

## **Prompt XXX — Revenue Intelligence Engine** 💰

Create `ai/services/revenue_intelligence.py`

**Purpose:** Automated financial intelligence layer.

**Tasks:**
- Aggregate MRR / ARR, LTV, CAC, churn trends from `backend/app/analytics/customer_success_metrics.py`
- Forecast 12-month ARR using Gemini 1.5 Flash (Prophet fallback)
- Build FastAPI endpoints:
  - `GET /api/finance/summary` – returns JSON snapshot
  - `GET /api/finance/forecast` – returns projection
- Implement Redis cache + JSON mirror `backend/app/analytics/revenue_cache.json`
- Output chart → `docs/analytics/revenue_forecast.png`
- Write doc → `docs/analytics/revenue_intelligence.md`
- Add pytest hook `pytest -k finance`

---

## **Prompt XXXI — Customer Success Dashboard (React + Realtime)** 📊

Create `frontend/src/components/DashboardCustomerSuccess.tsx`

**Requirements:**
- Live health score gauge + churn probability chart
- Table of "At-Risk Accounts" with AI recommendations from Fix It Fred
- WebSocket updates from `/ws/customer-health`
- KPIs and ROI widgets connected to Revenue Intelligence API
- Style with Material-UI + Tailwind for mobile responsiveness
- Document in `docs/features/customer_success_dashboard.md`

---

## **Prompt XXXII — Enterprise Reporting Portal** 📈

Build `frontend/src/pages/Reports.tsx`

**Tabs:**
- Financial (Revenue + Forecast)
- Customer Health (NPS, Engagement)
- System Performance (Uptime, Latency, AI Usage)

**Integrations:**
- Backend endpoints `/api/finance/*` and `/ws/customer-health`
- Export PDF/CSV buttons
- Role-based access via `enterprise_security.py`
- Write doc → `docs/features/enterprise_reporting_portal.md`

---

## **Prompt XXXIII — Investor Metrics Sync** 🔄

Update `ai/services/fix_it_fred_service.py`

**Add Cron Job:**
- Collect metrics: uptime, AI usage, MRR, lead conversion
- Write weekly summary `docs/investors/metrics_snapshot.json`
- Alert if ARR growth < 5% MoM or uptime < 99.5%
- Post summary to `/api/finance/summary` for dashboards

---

## **Prompt XXXIV — Series A Data Room Automation** 🧩

Create `infra/scripts/seriesA_data_room_sync.py`

**Automate:**
- Bundle key files: `ChatterFix_SeriesA_Deck.md`, `metrics_snapshot.json`, logs
- Encrypt + upload to GCS `gs://chatterfix-investor-room/`
- Tag release `v3.1.0-data-room`
- Auto-notify via email webhook to investor distribution list
- Document → `docs/investors/data_room_automation.md`

---

## **Prompt XXXV — Executive Launch Report** 📜

Compile all Phase 6 and 6B analytics into `docs/reports/enterprise_launch_report.md`

**Include:**
- Customer Success Metrics (highlights + charts)
- Revenue Forecast summary with growth curve
- Fix It Fred Ops metrics (uptime + autonomous events)
- ARR forecast vs actuals table
- Funding status summary and Series A progress

---

## **Prompt XXXVI — Phase 6B Tag + Deployment** 🚀

Finalize and deploy:

```bash
git tag -a v3.1.0-phase6b-final -m "🚀 Phase 6B Enterprise Finalization Complete"
git push origin v3.1.0-phase6b-final
```

- Verify CI/CD runs successfully
- Confirm services (8001–8012) healthy
- Output `docs/maintenance/PHASE6B_COMPLETION_SUMMARY.md`

---

## ✅ **Deliverables After All Prompts**

- Live Executive Dashboard Suite (financial + customer insights)
- Automated Investor Metrics and Data Room Sync
- Series A reporting pipeline integrated with Fix It Fred
- v3.1.0 Enterprise Tag – Investor-ready and production stable

---

*Ready for sequential execution by AI team for Phase 6B enterprise finalization*