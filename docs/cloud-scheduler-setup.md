# Cloud Scheduler Setup for PM Automation

This document describes how to configure Cloud Scheduler to trigger daily PM (Preventive Maintenance) work order generation.

## Architecture Overview

```
┌─────────────────┐         OIDC Token          ┌──────────────────┐
│ Cloud Scheduler │ ──────────────────────────> │    Cloud Run     │
│  (2:00 AM UTC)  │     POST /scheduled/...     │  (ChatterFix)    │
└─────────────────┘                             └──────────────────┘
        │                                               │
        │ Uses Service Account                          │
        ▼                                               ▼
┌─────────────────┐                             ┌──────────────────┐
│  Service Acct   │                             │    Firestore     │
│ pm-scheduler@   │                             │   (PM Rules,     │
│ fredfix.iam...  │                             │  Work Orders)    │
└─────────────────┘                             └──────────────────┘
```

## Prerequisites

- Google Cloud Project: `fredfix`
- Cloud Run service deployed at `https://chatterfix.com`
- `gcloud` CLI installed and authenticated

## Step 1: Create Service Account

Create a dedicated service account for the scheduler:

```bash
# Set project
export PROJECT_ID="fredfix"
gcloud config set project $PROJECT_ID

# Create service account
gcloud iam service-accounts create pm-scheduler \
  --display-name="PM Scheduler Service Account" \
  --description="Service account for Cloud Scheduler PM automation jobs"

# Note the email: pm-scheduler@fredfix.iam.gserviceaccount.com
```

## Step 2: Grant Cloud Run Invoker Permission

Allow the service account to invoke Cloud Run:

```bash
# Grant Cloud Run Invoker role to the service account
gcloud run services add-iam-policy-binding chatterfix \
  --region=us-central1 \
  --member="serviceAccount:pm-scheduler@fredfix.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

## Step 3: Create Cloud Scheduler Jobs

### Daily PM Generation (2:00 AM UTC)

```bash
gcloud scheduler jobs create http pm-daily-generation \
  --location=us-central1 \
  --schedule="0 2 * * *" \
  --time-zone="UTC" \
  --uri="https://chatterfix.com/scheduled/pm-generation?days_ahead=30" \
  --http-method=POST \
  --oidc-service-account-email="pm-scheduler@fredfix.iam.gserviceaccount.com" \
  --oidc-token-audience="https://chatterfix.com" \
  --description="Daily PM work order generation at 2:00 AM UTC" \
  --attempt-deadline="600s"
```

### Meter Threshold Check (Every 4 hours)

```bash
gcloud scheduler jobs create http meter-threshold-check \
  --location=us-central1 \
  --schedule="0 */4 * * *" \
  --time-zone="UTC" \
  --uri="https://chatterfix.com/scheduled/meter-threshold-check" \
  --http-method=POST \
  --oidc-service-account-email="pm-scheduler@fredfix.iam.gserviceaccount.com" \
  --oidc-token-audience="https://chatterfix.com" \
  --description="Check meter thresholds every 4 hours" \
  --attempt-deadline="300s"
```

## Step 4: Set Environment Variables (Optional)

For additional security, set environment variables on Cloud Run:

```bash
gcloud run services update chatterfix \
  --region=us-central1 \
  --set-env-vars="SCHEDULER_SERVICE_ACCOUNT=pm-scheduler@fredfix.iam.gserviceaccount.com" \
  --set-env-vars="CLOUD_RUN_SERVICE_URL=https://chatterfix.com"
```

## Verify Setup

### Check Scheduler Jobs

```bash
# List all scheduler jobs
gcloud scheduler jobs list --location=us-central1

# Describe specific job
gcloud scheduler jobs describe pm-daily-generation --location=us-central1
```

### Check Service Account Permissions

```bash
# List IAM bindings for Cloud Run service
gcloud run services get-iam-policy chatterfix --region=us-central1
```

---

## Manual Testing Runbook

### Method 1: Using Cloud Scheduler (Recommended)

Trigger the job manually from Cloud Console or CLI:

```bash
# Trigger PM generation immediately
gcloud scheduler jobs run pm-daily-generation --location=us-central1

# Check execution status
gcloud scheduler jobs describe pm-daily-generation --location=us-central1
```

### Method 2: Using curl with Service Account Token

Generate an identity token and call the endpoint:

```bash
# Get identity token (requires gcloud authenticated as project owner)
TOKEN=$(gcloud auth print-identity-token --audiences="https://chatterfix.com")

# Call PM generation endpoint
curl -X POST "https://chatterfix.com/scheduled/pm-generation?days_ahead=7&dry_run=true" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Call meter threshold check
curl -X POST "https://chatterfix.com/scheduled/meter-threshold-check" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

### Method 3: Using Secret Header (Development Only)

For local testing without OIDC:

```bash
# Set the secret in Cloud Run (one-time setup)
gcloud run services update chatterfix \
  --region=us-central1 \
  --set-env-vars="SCHEDULER_SECRET=your-secret-value-here"

# Call with secret header
curl -X POST "https://chatterfix.com/scheduled/pm-generation?days_ahead=7&dry_run=true" \
  -H "X-Scheduler-Secret: your-secret-value-here" \
  -H "Content-Type: application/json"
```

### Method 4: Local Development

In development mode (ENVIRONMENT=development), authentication is bypassed:

```bash
# Local server
curl -X POST "http://localhost:8000/scheduled/pm-generation?days_ahead=7&dry_run=true"
```

---

## Expected Responses

### Successful PM Generation

```json
{
  "timestamp": "2024-12-18T02:00:00.123456+00:00",
  "organizations_processed": 5,
  "total_work_orders_created": 12,
  "total_pm_orders_generated": 15,
  "dry_run": false,
  "days_ahead": 30,
  "execution_time_ms": 2345.67,
  "errors": [],
  "details": [
    {
      "organization_id": "org_abc123",
      "organization_name": "Acme Corp",
      "active_rules": 4,
      "pm_orders_generated": 3,
      "work_orders_created": 3
    }
  ]
}
```

### Successful Meter Threshold Check

```json
{
  "timestamp": "2024-12-18T02:00:00.123456+00:00",
  "organizations_checked": 5,
  "critical_alerts": 2,
  "warning_alerts": 8,
  "execution_time_ms": 1234.56,
  "details": [
    {
      "organization_id": "org_abc123",
      "organization_name": "Acme Corp",
      "critical_meters": 1,
      "warning_meters": 3
    }
  ]
}
```

### Authentication Error (401)

```json
{
  "detail": "Unauthorized - Cloud Scheduler OIDC token or valid secret required"
}
```

---

## Troubleshooting

### Job Not Running

1. Check job status:
   ```bash
   gcloud scheduler jobs describe pm-daily-generation --location=us-central1
   ```

2. Check Cloud Run logs:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=chatterfix" \
     --limit=50 --format="table(timestamp,severity,textPayload)"
   ```

### 401 Unauthorized

1. Verify service account has `roles/run.invoker`:
   ```bash
   gcloud run services get-iam-policy chatterfix --region=us-central1 | grep pm-scheduler
   ```

2. Verify OIDC audience matches service URL:
   ```bash
   gcloud scheduler jobs describe pm-daily-generation --location=us-central1 | grep audience
   ```

### 500 Internal Server Error

1. Check Cloud Run logs for detailed error
2. Verify Firestore permissions
3. Check for missing environment variables

---

## Schedule Reference

| Job | Schedule (UTC) | Cron Expression | Description |
|-----|----------------|-----------------|-------------|
| pm-daily-generation | 2:00 AM | `0 2 * * *` | Daily PM work order generation |
| meter-threshold-check | Every 4 hours | `0 */4 * * *` | Check meter thresholds |

---

## Security Considerations

1. **OIDC Authentication**: Cloud Scheduler uses OIDC tokens signed by Google. Cloud Run validates these automatically when IAM permissions are set correctly.

2. **Service Account Principle of Least Privilege**: The `pm-scheduler` service account only has `roles/run.invoker` - it cannot access Firestore directly.

3. **No Public Access**: The scheduler endpoints require authentication. They will return 401 for unauthenticated requests in production.

4. **Audit Logging**: All Cloud Run invocations are logged in Cloud Logging for audit purposes.

---

## Updating Jobs

To update a scheduler job:

```bash
# Update schedule
gcloud scheduler jobs update http pm-daily-generation \
  --location=us-central1 \
  --schedule="0 3 * * *"  # Change to 3:00 AM

# Pause job
gcloud scheduler jobs pause pm-daily-generation --location=us-central1

# Resume job
gcloud scheduler jobs resume pm-daily-generation --location=us-central1

# Delete job
gcloud scheduler jobs delete pm-daily-generation --location=us-central1
```
