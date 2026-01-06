# ChatterFix Company Onboarding Guide

## Overview

ChatterFix supports two onboarding paths:

| Path | Who Uses It | What Happens |
|------|-------------|--------------|
| **Self-Service** | Customers signing up via web | User creates account, org auto-created with 30-day trial |
| **Admin Bootstrap** | Sales/Admin provisioning enterprise accounts | API creates org with specific tier and rate limits |

---

## 1. Self-Service Onboarding (Recommended for Most Users)

### How It Works

Customers sign up themselves at `https://chatterfix.com/landing` or `/signup`:

1. **User fills out signup form:**
   - Full name
   - Email
   - Password (8+ characters)
   - Company name (optional)

2. **System automatically creates:**
   - Firebase Auth user account
   - Organization (with auto-generated slug ID)
   - User document linked to organization
   - Default asset categories (HVAC, Electrical, Plumbing, etc.)
   - Default locations (Main Building, Warehouse)

3. **User gets:**
   - 30-day free trial with full features
   - Owner role in their organization
   - Immediate access to dashboard

### Trial Period

- **Duration:** 30 days from signup
- **Features:** Full access to all features
- **After Trial:** Prompts to upgrade to paid plan

### Adding Team Members

After signup, owners can invite team members:
1. Go to **Organization > Team** in the dashboard
2. Click **Invite Member**
3. Enter email and select role (Manager, Technician, etc.)
4. Invitee receives email with signup link
5. When they sign up, they're automatically added to the organization

---

## 2. Admin/Enterprise Bootstrap (API)

### When to Use

- Enterprise deals requiring specific tiers
- Pre-provisioning accounts for large deployments
- Migrating existing customers with specific rate limits
- Demo accounts for sales presentations

### API Endpoint

```
POST /api/v1/orgs/{org_id}/bootstrap
```

### Request Body

```json
{
  "org_name": "Acme Manufacturing",
  "owner_email": "admin@acme.com",
  "owner_user_id": "firebase_uid_here",
  "owner_name": "John Smith",
  "tier": "professional",
  "timezone": "America/Chicago",
  "include_sample_data": false
}
```

### Parameters

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `org_name` | Yes | - | Company display name |
| `owner_email` | Yes | - | Primary contact email |
| `owner_user_id` | No | auto-generated | Firebase UID (if user exists) |
| `owner_name` | No | "" | Owner's display name |
| `tier` | No | "free" | Subscription tier (see below) |
| `timezone` | No | "UTC" | Organization timezone |
| `include_sample_data` | No | false | Seed demo assets, work orders, PM rules |

### Subscription Tiers

| Tier | AI Requests/Day | Work Orders/Day | Assets | Team Members |
|------|-----------------|-----------------|--------|--------------|
| `free` | 25 | 50 | 25 | 3 |
| `starter` | 100 | 200 | 100 | 10 |
| `professional` | 500 | 1000 | 500 | 50 |
| `enterprise` | Unlimited | Unlimited | Unlimited | Unlimited |

### Query Parameters

| Param | Default | Description |
|-------|---------|-------------|
| `force` | false | Overwrite existing org if true |

### Example: Create Enterprise Account

```bash
curl -X POST "https://chatterfix.com/api/v1/orgs/acme-corp/bootstrap?force=false" \
  -H "Content-Type: application/json" \
  -d '{
    "org_name": "Acme Corporation",
    "owner_email": "cto@acme.com",
    "owner_name": "Jane Doe",
    "tier": "enterprise",
    "timezone": "America/New_York",
    "include_sample_data": true
  }'
```

### Response

```json
{
  "success": true,
  "org_id": "acme-corp",
  "org_name": "Acme Corporation",
  "tier": "enterprise",
  "documents_created": [
    "organizations/acme-corp",
    "rate_limits/acme-corp",
    "users/auto_generated_uid"
  ],
  "sample_data_created": {
    "assets": 5,
    "pm_rules": 3
  },
  "message": "Organization bootstrapped successfully"
}
```

---

## 3. Check Organization Status

### Endpoint

```
GET /api/v1/orgs/{org_id}/status
```

### Response

```json
{
  "org_id": "acme-corp",
  "name": "Acme Corporation",
  "tier": "enterprise",
  "status": "ready",
  "subscription_status": "active",
  "rate_limits": {
    "ai_requests_per_day": -1,
    "work_orders_per_day": -1,
    "max_assets": -1,
    "max_team_members": -1
  },
  "counts": {
    "assets": 5,
    "work_orders": 12,
    "pm_rules": 3,
    "team_members": 8
  },
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

## 4. Delete Organization (Danger Zone)

### Endpoint

```
DELETE /api/v1/orgs/{org_id}?confirm=true
```

**WARNING:** This permanently deletes ALL organization data including:
- Organization record
- All work orders
- All assets
- All PM rules
- All inventory parts
- All vendors
- All team member associations
- Rate limits

### Query Parameters

| Param | Required | Description |
|-------|----------|-------------|
| `confirm` | Yes | Must be `true` to proceed |

### Example

```bash
curl -X DELETE "https://chatterfix.com/api/v1/orgs/test-org?confirm=true"
```

---

## 5. Onboarding Checklist

### For Self-Service Customers

- [ ] Sign up at `/landing` with company email
- [ ] Verify email (if email verification enabled)
- [ ] Complete profile in Settings
- [ ] Add first asset
- [ ] Create first work order
- [ ] Invite team members
- [ ] Set up PM schedules (optional)
- [ ] Configure notification preferences

### For Enterprise Deployments

- [ ] Sales provides org_id and tier requirements
- [ ] Admin runs bootstrap API with appropriate tier
- [ ] Create Firebase Auth user for owner (or let bootstrap auto-create)
- [ ] Share login credentials with customer
- [ ] Customer completes profile
- [ ] Bulk import assets (if migrating)
- [ ] Set up integrations (if applicable)
- [ ] Training session for team

---

## 6. Troubleshooting

### "Organization already exists" Error

If bootstrapping fails because org exists:
1. Check if org should be overwritten: add `?force=true`
2. Or delete first: `DELETE /api/v1/orgs/{org_id}?confirm=true`

### User Can't Access Organization

1. Verify user's `organization_id` in Firestore users collection
2. Check organization exists in organizations collection
3. Verify user is in organization's `members` array

### Rate Limits Not Working

1. Check `rate_limits` collection has document with org_id
2. Verify tier matches expected limits
3. Self-service signups don't create rate_limits doc by default (uses trial mode)

### Converting Demo to Real Account

Demo accounts (created via anonymous auth) can be converted:
1. User clicks "Create Account" in demo
2. System calls `convert_demo_to_real()`
3. All demo data is preserved
4. Demo timer is removed

---

## 7. Quick Reference

### Signup URL
```
https://chatterfix.com/landing
```

### Bootstrap API
```
POST /api/v1/orgs/{org_id}/bootstrap
```

### Status Check
```
GET /api/v1/orgs/{org_id}/status
```

### Delete Org
```
DELETE /api/v1/orgs/{org_id}?confirm=true
```

### Support
- Technical issues: support@chatterfix.com
- Enterprise sales: enterprise@chatterfix.com
