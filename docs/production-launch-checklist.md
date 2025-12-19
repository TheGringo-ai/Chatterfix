# Production Launch Checklist - ChatterFix CMMS

Complete checklist for deploying ChatterFix to Cloud Run + Firestore.

---

## 1. Environment Variables / Secrets

### Required (Critical)

| Variable | Description | Where to Set | Example |
|----------|-------------|--------------|---------|
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | Cloud Run env | `fredfix` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON | Cloud Run (auto-injected) | `/secrets/firebase-admin.json` |
| `USE_FIRESTORE` | Enable Firestore database | Cloud Run env | `true` |
| `ENVIRONMENT` | Environment mode | Cloud Run env | `production` |
| `FIREBASE_API_KEY` | Firebase Web API key | Secret Manager | `AIzaSy...` |
| `SECRET_KEY` | JWT signing secret | Secret Manager | `<random 64 char>` |

### Firebase Configuration

| Variable | Description | Where to Set |
|----------|-------------|--------------|
| `FIREBASE_APP_ID` | Firebase Web App ID | Secret Manager |
| `FIREBASE_MESSAGING_SENDER_ID` | FCM Sender ID | Cloud Run env |
| `FIREBASE_STORAGE_BUCKET` | Firebase Storage bucket | Cloud Run env |
| `FIREBASE_MEASUREMENT_ID` | Google Analytics ID | Cloud Run env |

### Cloud Scheduler (PM Automation)

| Variable | Description | Where to Set |
|----------|-------------|--------------|
| `SCHEDULER_SERVICE_ACCOUNT` | Expected scheduler SA email | Cloud Run env |
| `SCHEDULER_SECRET` | Fallback auth secret (optional) | Secret Manager |
| `CLOUD_RUN_SERVICE_URL` | Service URL for OIDC audience | Cloud Run env |

### AI Services (Optional)

| Variable | Description | Where to Set |
|----------|-------------|--------------|
| `GEMINI_API_KEY` | Gemini AI API key | Secret Manager |
| `OPENAI_API_KEY` | OpenAI API key | Secret Manager |
| `XAI_API_KEY` | xAI (Grok) API key | Secret Manager |
| `ANTHROPIC_API_KEY` | Claude API key | Secret Manager |

### Email Service (Optional)

| Variable | Description | Where to Set |
|----------|-------------|--------------|
| `SMTP_SERVER` | SMTP server hostname | Cloud Run env |
| `SMTP_PORT` | SMTP port | Cloud Run env |
| `SMTP_USERNAME` | SMTP username | Secret Manager |
| `SMTP_PASSWORD` | SMTP password | Secret Manager |
| `FROM_EMAIL` | Sender email address | Cloud Run env |

---

## 2. Firestore Rules / Permissions

### Security Model

ChatterFix uses **server-side only access** - all client requests go through the FastAPI backend.

```
┌──────────────┐     HTTPS      ┌──────────────┐   Admin SDK   ┌────────────┐
│  Web/Mobile  │ ─────────────> │  Cloud Run   │ ────────────> │  Firestore │
│   Clients    │   (No direct   │   (FastAPI)  │  (Full access │            │
└──────────────┘    Firestore)  └──────────────┘   via SA)     └────────────┘
```

### Firestore Rules (firestore.rules)

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // DENY ALL PUBLIC ACCESS
    // Only Firebase Admin SDK (service account) can access
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

### Deploy Rules

```bash
firebase deploy --only firestore:rules --project fredfix
```

### Service Account Permissions

The Cloud Run service account needs:

| Role | Purpose |
|------|---------|
| `roles/datastore.user` | Read/write Firestore documents |
| `roles/firebase.sdkAdminServiceAgent` | Firebase Admin SDK access |
| `roles/secretmanager.secretAccessor` | Access Secret Manager secrets |

```bash
# Grant Firestore access to Cloud Run service account
gcloud projects add-iam-policy-binding fredfix \
  --member="serviceAccount:SERVICE_ACCOUNT@fredfix.iam.gserviceaccount.com" \
  --role="roles/datastore.user"
```

---

## 3. Health Check Routes

### Endpoints

| Route | Purpose | Used By |
|-------|---------|---------|
| `GET /health` | Basic health check | Load balancer |
| `GET /health/liveness` | Kubernetes liveness probe | Cloud Run |
| `GET /health/readiness` | Kubernetes readiness probe | Cloud Run |
| `GET /health/detailed` | Full system diagnostics | Monitoring |
| `GET /health/environment` | Environment info | Debugging |

### Cloud Run Health Check Config

```bash
gcloud run services update chatterfix \
  --region=us-central1 \
  --startup-probe-path=/health \
  --startup-probe-period-seconds=10 \
  --startup-probe-failure-threshold=3 \
  --liveness-probe-path=/health/liveness \
  --liveness-probe-period-seconds=30
```

### Expected Responses

**`GET /health`** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2024-12-18T12:00:00.000000"
}
```

**`GET /health/detailed`** (200 OK or 207 degraded):
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "system": {
    "cpu_percent": 15.2,
    "memory_percent": 45.3,
    "disk_percent": 30.1
  },
  "database": {
    "status": "ok",
    "type": "firestore",
    "response_time_ms": 45.2
  }
}
```

---

## 4. Logging / Trace Correlation

### Structured Logging Setup

ChatterFix uses Python's `logging` module with structured JSON output.

```python
import logging
import google.cloud.logging

# Initialize Cloud Logging client (auto-configured on Cloud Run)
client = google.cloud.logging.Client()
client.setup_logging()

logger = logging.getLogger(__name__)
```

### Trace Correlation

To correlate logs with Cloud Trace spans, include the trace header:

```python
from fastapi import Request

def get_trace_header(request: Request) -> str:
    """Extract trace ID from X-Cloud-Trace-Context header."""
    trace_header = request.headers.get("X-Cloud-Trace-Context", "")
    if trace_header:
        trace_id = trace_header.split("/")[0]
        return f"projects/{PROJECT_ID}/traces/{trace_id}"
    return ""
```

### Recommended Logging Practices

1. **Use structured logging** - Log dicts, not strings:
   ```python
   logger.info({
       "message": "Work order created",
       "work_order_id": wo_id,
       "organization_id": org_id,
       "user_id": user.uid,
   })
   ```

2. **Include request context** - Add trace_id, user_id, org_id to all logs

3. **Log at appropriate levels**:
   - `INFO`: Normal operations (request completed, WO created)
   - `WARNING`: Recoverable issues (retry, fallback used)
   - `ERROR`: Failures requiring attention

### Cloud Logging Queries

```bash
# View recent errors
gcloud logging read "resource.type=cloud_run_revision \
  AND resource.labels.service_name=chatterfix \
  AND severity>=ERROR" \
  --limit=50 --format="table(timestamp,severity,textPayload)"

# View PM automation logs
gcloud logging read "resource.type=cloud_run_revision \
  AND textPayload:\"PM generation\"" \
  --limit=20
```

---

## 5. Pre-Launch Checklist

### Infrastructure

- [ ] Cloud Run service deployed with correct memory/CPU settings
- [ ] Firestore database created in correct region (us-central1)
- [ ] Secret Manager secrets created and accessible
- [ ] Custom domain mapped (chatterfix.com)
- [ ] SSL certificate provisioned (automatic with Cloud Run)

### Security

- [ ] Firestore rules deployed (deny all public access)
- [ ] Service account has minimum required permissions
- [ ] Secret Manager access configured
- [ ] CORS settings validated
- [ ] Rate limiting configured (if applicable)

### Environment

- [ ] `ENVIRONMENT=production` set
- [ ] `USE_FIRESTORE=true` set
- [ ] All required secrets accessible
- [ ] Firebase config complete (all fields)

### Monitoring

- [ ] Health check endpoints responding
- [ ] Cloud Logging receiving logs
- [ ] Error alerting configured (optional)
- [ ] Uptime monitoring configured (optional)

### Cloud Scheduler (PM Automation)

- [ ] Service account `pm-scheduler@...` created
- [ ] Cloud Run invoker role granted
- [ ] Scheduler jobs created (pm-daily-generation, meter-threshold-check)
- [ ] Manual trigger test successful

---

## 6. Deployment Commands

### Deploy to Cloud Run

```bash
# Build and deploy
gcloud builds submit --config=cloudbuild.yaml --project=fredfix

# Or direct deploy
gcloud run deploy chatterfix \
  --source . \
  --region=us-central1 \
  --project=fredfix \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --set-env-vars="ENVIRONMENT=production,USE_FIRESTORE=true" \
  --set-secrets="FIREBASE_API_KEY=FIREBASE_API_KEY:latest,SECRET_KEY=SECRET_KEY:latest"
```

### Verify Deployment

```bash
# Check service status
gcloud run services describe chatterfix --region=us-central1

# Test health endpoint
curl https://chatterfix.com/health

# Run smoke test
./scripts/smoke-test-pm.sh
```

---

## 7. Rollback Procedure

### Quick Rollback

```bash
# List revisions
gcloud run revisions list --service=chatterfix --region=us-central1

# Rollback to previous revision
gcloud run services update-traffic chatterfix \
  --region=us-central1 \
  --to-revisions=chatterfix-PREVIOUS_REVISION=100
```

### Full Rollback

```bash
# Redeploy previous git commit
git checkout HEAD~1
gcloud builds submit --config=cloudbuild.yaml --project=fredfix
```

---

## 8. Post-Launch Verification

After deployment, verify:

1. **Health endpoints**: All return 200
2. **Authentication**: Login flow works
3. **PM Automation**: Smoke test passes
4. **Cloud Scheduler**: Manual trigger succeeds
5. **Firestore**: Data persists correctly
6. **Logs**: Appearing in Cloud Logging

Run the smoke test script:

```bash
./scripts/smoke-test-pm.sh --base-url https://chatterfix.com --org-id YOUR_ORG_ID
```
