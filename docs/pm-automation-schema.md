# PM Automation Firestore Schema

## Overview

This document defines the Firestore schema for the PM (Preventive Maintenance) automation system. All collections enforce multi-tenant data isolation via `organization_id`.

---

## Collections

### 1. `pm_templates/{template_id}`

Maintenance task templates that define what work needs to be done. Can be global (organization_id = null) or organization-specific.

#### Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Auto | Document ID (auto-generated) |
| `organization_id` | string \| null | Yes | Owner org ID, or null for global templates |
| `name` | string | Yes | Template name |
| `description` | string | Yes | Detailed description |
| `maintenance_type` | string | Yes | Enum: `preventive`, `predictive`, `condition_based`, `usage_based`, `time_based`, `seasonal`, `regulatory` |
| `triggers` | array | Yes | Array of trigger conditions |
| `triggers[].trigger_type` | string | Yes | Enum: `calendar`, `runtime_hours`, `production_cycles`, `vibration_threshold`, `temperature_threshold`, `pressure_threshold`, `oil_analysis`, `wear_measurement`, `seasonal_change`, `regulatory_deadline` |
| `triggers[].threshold_value` | number | Yes | Value that triggers maintenance |
| `triggers[].warning_threshold` | number | Yes | Value that triggers warning |
| `triggers[].description` | string | Yes | Human-readable trigger description |
| `triggers[].unit` | string | Yes | Unit of measurement |
| `required_skills` | array[string] | Yes | Skills needed to perform work |
| `estimated_duration` | number | Yes | Hours to complete |
| `required_parts` | array[string] | No | Parts needed |
| `required_tools` | array[string] | No | Tools needed |
| `safety_requirements` | array[string] | No | Safety requirements |
| `procedures` | array[string] | No | Step-by-step procedures |
| `criticality` | number | Yes | 1-5 scale (5 = most critical) |
| `can_be_deferred` | boolean | Yes | Whether task can be postponed |
| `max_deferral_days` | number | No | Max days task can be deferred |
| `created_at` | timestamp | Auto | Creation timestamp |
| `updated_at` | timestamp | Auto | Last update timestamp |
| `created_by` | string | No | User ID who created template |

#### Example Document

```json
{
  "id": "tpl_hydraulic_monthly_001",
  "organization_id": null,
  "name": "Hydraulic System Monthly Maintenance",
  "description": "Comprehensive monthly hydraulic maintenance including filter changes and pressure testing",
  "maintenance_type": "preventive",
  "triggers": [
    {
      "trigger_type": "calendar",
      "threshold_value": 30,
      "warning_threshold": 25,
      "description": "Monthly maintenance schedule",
      "unit": "days"
    },
    {
      "trigger_type": "runtime_hours",
      "threshold_value": 720,
      "warning_threshold": 600,
      "description": "Runtime hours threshold",
      "unit": "hours"
    }
  ],
  "required_skills": ["hydraulics", "mechanical", "safety_inspection"],
  "estimated_duration": 4.0,
  "required_parts": ["hydraulic_filter", "o_rings", "hydraulic_fluid"],
  "required_tools": ["pressure_gauge", "torque_wrench", "filter_wrench"],
  "safety_requirements": ["safety_glasses", "gloves", "lockout_tagout"],
  "procedures": [
    "Lockout/tagout the system",
    "Drain hydraulic reservoir",
    "Change hydraulic filters",
    "Test relief valves",
    "Check cylinder seals",
    "Refill with proper fluid",
    "Calibrate pressure sensors",
    "Update maintenance records"
  ],
  "criticality": 5,
  "can_be_deferred": true,
  "max_deferral_days": 7,
  "created_at": "2024-12-18T10:00:00Z",
  "updated_at": "2024-12-18T10:00:00Z",
  "created_by": null
}
```

---

### 2. `pm_schedule_rules/{rule_id}`

Per-asset scheduling rules that determine when maintenance should occur.

#### Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Auto | Document ID (auto-generated) |
| `organization_id` | string | **Yes** | Owner organization ID |
| `asset_id` | string | Yes | FK to assets collection |
| `asset_name` | string | No | Denormalized asset name for display |
| `template_id` | string | Yes | FK to pm_templates collection |
| `template_name` | string | No | Denormalized template name |
| `schedule_type` | string | Yes | Enum: `time_based`, `condition_based`, `usage_based`, `seasonal` |
| `interval_value` | number | Yes | Interval between maintenance |
| `interval_unit` | string | Yes | Enum: `days`, `weeks`, `months`, `hours`, `cycles` |
| `start_date` | timestamp | Yes | When scheduling begins |
| `end_date` | timestamp | No | When scheduling ends (null = indefinite) |
| `is_active` | boolean | Yes | Whether rule is active |
| `last_generated` | timestamp | No | Last time WO was generated |
| `next_due` | timestamp | No | Next scheduled maintenance date |
| `seasonal_adjustments` | map | No | Season-specific multipliers |
| `created_at` | timestamp | Auto | Creation timestamp |
| `updated_at` | timestamp | Auto | Last update timestamp |
| `created_by` | string | No | User ID who created rule |

#### Example Document

```json
{
  "id": "rule_press001_monthly",
  "organization_id": "org_acme_manufacturing",
  "asset_id": "asset_hydraulic_press_001",
  "asset_name": "Hydraulic Press #1 - Building A",
  "template_id": "tpl_hydraulic_monthly_001",
  "template_name": "Hydraulic System Monthly Maintenance",
  "schedule_type": "time_based",
  "interval_value": 30,
  "interval_unit": "days",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": null,
  "is_active": true,
  "last_generated": "2024-12-01T06:00:00Z",
  "next_due": "2024-12-31T06:00:00Z",
  "seasonal_adjustments": {
    "summer": 0.8,
    "winter": 1.2
  },
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-12-01T06:00:00Z",
  "created_by": "user_john_smith"
}
```

---

### 3. `asset_meters/{meter_id}`

Tracks asset usage metrics and condition readings for usage-based and condition-based maintenance.

#### Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Auto | Document ID (auto-generated) |
| `organization_id` | string | **Yes** | Owner organization ID |
| `asset_id` | string | Yes | FK to assets collection |
| `asset_name` | string | No | Denormalized asset name |
| `meter_type` | string | Yes | Enum: `runtime_hours`, `production_cycles`, `operation_cycles`, `vibration`, `temperature`, `pressure`, `oil_level`, `wear` |
| `current_value` | number | Yes | Current meter reading |
| `previous_value` | number | No | Previous reading (for delta calc) |
| `last_reading_date` | timestamp | Yes | When last reading was taken |
| `last_reading_source` | string | No | Enum: `manual`, `iot`, `api` |
| `reading_frequency` | number | No | Expected days between readings |
| `unit` | string | Yes | Unit of measurement |
| `is_automated` | boolean | Yes | IoT sensor vs manual reading |
| `threshold_warning` | number | No | Warning threshold value |
| `threshold_critical` | number | No | Critical threshold value |
| `reset_on_maintenance` | boolean | No | Reset to 0 after maintenance |
| `created_at` | timestamp | Auto | Creation timestamp |
| `updated_at` | timestamp | Auto | Last update timestamp |

#### Example Document

```json
{
  "id": "meter_press001_cycles",
  "organization_id": "org_acme_manufacturing",
  "asset_id": "asset_hydraulic_press_001",
  "asset_name": "Hydraulic Press #1 - Building A",
  "meter_type": "operation_cycles",
  "current_value": 23456,
  "previous_value": 23100,
  "last_reading_date": "2024-12-18T14:30:00Z",
  "last_reading_source": "iot",
  "reading_frequency": 1,
  "unit": "cycles",
  "is_automated": true,
  "threshold_warning": 25000,
  "threshold_critical": 30000,
  "reset_on_maintenance": false,
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-12-18T14:30:00Z"
}
```

#### Example: Vibration Meter

```json
{
  "id": "meter_motor005_vibration",
  "organization_id": "org_acme_manufacturing",
  "asset_id": "asset_motor_drive_005",
  "asset_name": "Motor Drive #5 - Line 2",
  "meter_type": "vibration",
  "current_value": 4.2,
  "previous_value": 3.8,
  "last_reading_date": "2024-12-18T14:30:00Z",
  "last_reading_source": "iot",
  "reading_frequency": 1,
  "unit": "mm/s",
  "is_automated": true,
  "threshold_warning": 4.5,
  "threshold_critical": 7.1,
  "reset_on_maintenance": false,
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-12-18T14:30:00Z"
}
```

---

### 4. `pm_generated_orders/{order_id}`

Tracks PM-generated work orders for auditing, preventing duplicates, and linking to actual work orders.

#### Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Auto | Document ID (auto-generated) |
| `organization_id` | string | **Yes** | Owner organization ID |
| `idempotency_key` | string | **Yes** | Unique key to prevent duplicates |
| `work_order_id` | string | No | FK to work_orders (null until created) |
| `template_id` | string | Yes | FK to pm_templates |
| `rule_id` | string | Yes | FK to pm_schedule_rules |
| `asset_id` | string | Yes | FK to assets |
| `asset_name` | string | No | Denormalized asset name |
| `trigger_reason` | string | Yes | Why maintenance was triggered |
| `trigger_type` | string | Yes | Enum: `scheduled`, `condition`, `usage`, `manual` |
| `trigger_value` | number | No | Meter value that triggered (if applicable) |
| `generated_date` | timestamp | Yes | When PM order was generated |
| `due_date` | timestamp | Yes | When maintenance is due |
| `status` | string | Yes | Enum: `pending`, `work_order_created`, `deferred`, `cancelled`, `completed` |
| `deferral_count` | number | No | Times this has been deferred |
| `deferred_until` | timestamp | No | New due date if deferred |
| `deferred_by` | string | No | User who deferred |
| `deferral_reason` | string | No | Why it was deferred |
| `created_at` | timestamp | Auto | Creation timestamp |
| `updated_at` | timestamp | Auto | Last update timestamp |

#### Idempotency Key Format

The `idempotency_key` prevents duplicate work orders from being created:

```
{organization_id}_{rule_id}_{due_date_YYYYMMDD}
```

Example: `org_acme_manufacturing_rule_press001_monthly_20241231`

#### Example Document

```json
{
  "id": "pmgen_abc123xyz",
  "organization_id": "org_acme_manufacturing",
  "idempotency_key": "org_acme_manufacturing_rule_press001_monthly_20241231",
  "work_order_id": "wo_def456uvw",
  "template_id": "tpl_hydraulic_monthly_001",
  "rule_id": "rule_press001_monthly",
  "asset_id": "asset_hydraulic_press_001",
  "asset_name": "Hydraulic Press #1 - Building A",
  "trigger_reason": "Scheduled time_based maintenance - 30 day interval",
  "trigger_type": "scheduled",
  "trigger_value": null,
  "generated_date": "2024-12-18T06:00:00Z",
  "due_date": "2024-12-31T06:00:00Z",
  "status": "work_order_created",
  "deferral_count": 0,
  "deferred_until": null,
  "deferred_by": null,
  "deferral_reason": null,
  "created_at": "2024-12-18T06:00:00Z",
  "updated_at": "2024-12-18T06:00:05Z"
}
```

#### Example: Condition-Based Trigger

```json
{
  "id": "pmgen_condition_789",
  "organization_id": "org_acme_manufacturing",
  "idempotency_key": "org_acme_manufacturing_condition_motor005_vibration_20241218",
  "work_order_id": "wo_urgent_001",
  "template_id": "tpl_motor_condition_001",
  "rule_id": "condition_motor005",
  "asset_id": "asset_motor_drive_005",
  "asset_name": "Motor Drive #5 - Line 2",
  "trigger_reason": "Condition threshold exceeded: vibration = 7.5 mm/s (critical: 7.1)",
  "trigger_type": "condition",
  "trigger_value": 7.5,
  "generated_date": "2024-12-18T14:35:00Z",
  "due_date": "2024-12-19T14:35:00Z",
  "status": "work_order_created",
  "deferral_count": 0,
  "deferred_until": null,
  "deferred_by": null,
  "deferral_reason": null,
  "created_at": "2024-12-18T14:35:00Z",
  "updated_at": "2024-12-18T14:35:02Z"
}
```

---

## Composite Indexes

Add these to `firestore.indexes.json`:

```json
{
  "indexes": [
    {
      "collectionGroup": "pm_templates",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "organization_id", "order": "ASCENDING" },
        { "fieldPath": "name", "order": "ASCENDING" }
      ]
    },
    {
      "collectionGroup": "pm_templates",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "organization_id", "order": "ASCENDING" },
        { "fieldPath": "maintenance_type", "order": "ASCENDING" }
      ]
    },
    {
      "collectionGroup": "pm_schedule_rules",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "organization_id", "order": "ASCENDING" },
        { "fieldPath": "is_active", "order": "ASCENDING" },
        { "fieldPath": "next_due", "order": "ASCENDING" }
      ]
    },
    {
      "collectionGroup": "pm_schedule_rules",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "organization_id", "order": "ASCENDING" },
        { "fieldPath": "asset_id", "order": "ASCENDING" }
      ]
    },
    {
      "collectionGroup": "pm_schedule_rules",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "organization_id", "order": "ASCENDING" },
        { "fieldPath": "next_due", "order": "ASCENDING" }
      ]
    },
    {
      "collectionGroup": "asset_meters",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "organization_id", "order": "ASCENDING" },
        { "fieldPath": "asset_id", "order": "ASCENDING" }
      ]
    },
    {
      "collectionGroup": "asset_meters",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "organization_id", "order": "ASCENDING" },
        { "fieldPath": "meter_type", "order": "ASCENDING" }
      ]
    },
    {
      "collectionGroup": "pm_generated_orders",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "organization_id", "order": "ASCENDING" },
        { "fieldPath": "status", "order": "ASCENDING" },
        { "fieldPath": "generated_date", "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "pm_generated_orders",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "organization_id", "order": "ASCENDING" },
        { "fieldPath": "generated_date", "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "pm_generated_orders",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "organization_id", "order": "ASCENDING" },
        { "fieldPath": "rule_id", "order": "ASCENDING" }
      ]
    },
    {
      "collectionGroup": "pm_generated_orders",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "organization_id", "order": "ASCENDING" },
        { "fieldPath": "asset_id", "order": "ASCENDING" }
      ]
    },
    {
      "collectionGroup": "pm_generated_orders",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "idempotency_key", "order": "ASCENDING" }
      ]
    }
  ],
  "fieldOverrides": []
}
```

---

## Idempotency Strategy

### Problem
Cloud Scheduler or manual triggers could generate duplicate work orders for the same maintenance event.

### Solution: Idempotency Key

1. **Generate a unique key** for each PM order based on:
   - `organization_id`
   - `rule_id` (or `condition_{asset_id}_{meter_type}` for condition-based)
   - `due_date` (truncated to day: YYYYMMDD)

2. **Check before creating** - Query `pm_generated_orders` for existing `idempotency_key`:

```python
async def generate_pm_order_idempotent(
    organization_id: str,
    rule_id: str,
    due_date: datetime,
    order_data: dict
) -> Optional[str]:
    """Generate PM order only if idempotency key doesn't exist."""

    # Build idempotency key
    due_date_str = due_date.strftime("%Y%m%d")
    idempotency_key = f"{organization_id}_{rule_id}_{due_date_str}"

    # Check for existing order with this key
    existing = await firestore_manager.get_collection(
        "pm_generated_orders",
        filters=[
            {"field": "idempotency_key", "operator": "==", "value": idempotency_key}
        ],
        limit=1
    )

    if existing:
        logger.info(f"Skipping duplicate: {idempotency_key}")
        return None  # Already exists

    # Create new PM generated order
    order_data["idempotency_key"] = idempotency_key
    order_data["organization_id"] = organization_id

    pm_order_id = await firestore_manager.create_document(
        "pm_generated_orders", order_data
    )

    return pm_order_id
```

### Idempotency Key Formats

| Trigger Type | Key Format | Example |
|--------------|------------|---------|
| Scheduled (time-based) | `{org}_{rule_id}_{YYYYMMDD}` | `org_acme_rule_press001_monthly_20241231` |
| Condition-based | `{org}_condition_{asset}_{meter}_{YYYYMMDD}` | `org_acme_condition_motor005_vibration_20241218` |
| Usage-based | `{org}_usage_{asset}_{meter}_{threshold}` | `org_acme_usage_conveyor001_cycles_100000` |
| Manual | `{org}_manual_{asset}_{timestamp}` | `org_acme_manual_press001_1734523800` |

### Edge Cases

1. **Multiple triggers same day**: For condition-based, include meter type in key
2. **Deferred orders**: Keep original idempotency_key, update `deferred_until`
3. **Cancelled and re-triggered**: Check status, allow if `cancelled`
4. **Usage resets**: Include threshold value in key for usage-based

---

## Query Patterns

### Get Active PM Rules Due Soon

```python
rules = await firestore_manager.get_org_collection(
    "pm_schedule_rules",
    organization_id,
    additional_filters=[
        {"field": "is_active", "operator": "==", "value": True},
        {"field": "next_due", "operator": "<=", "value": due_date}
    ],
    order_by="next_due"
)
```

### Get Meters Exceeding Threshold

```python
# Firestore can't compare two fields, so fetch and filter in code
meters = await firestore_manager.get_asset_meters(organization_id)
critical = [
    m for m in meters
    if m.get("threshold_critical")
    and m.get("current_value", 0) >= m["threshold_critical"]
]
```

### Check for Duplicate PM Order

```python
existing = await firestore_manager.get_collection(
    "pm_generated_orders",
    filters=[
        {"field": "idempotency_key", "operator": "==", "value": idempotency_key}
    ],
    limit=1
)
```

### Get PM History for Asset

```python
history = await firestore_manager.get_org_collection(
    "pm_generated_orders",
    organization_id,
    additional_filters=[
        {"field": "asset_id", "operator": "==", "value": asset_id}
    ],
    order_by="-generated_date",
    limit=50
)
```

---

## Data Relationships

```
organizations
    └── pm_templates (organization_id or null for global)
    └── pm_schedule_rules (organization_id)
            └── references pm_templates.id
            └── references assets.id
    └── asset_meters (organization_id)
            └── references assets.id
    └── pm_generated_orders (organization_id)
            └── references pm_templates.id
            └── references pm_schedule_rules.id
            └── references assets.id
            └── references work_orders.id
```

---

## Security Rules

All PM collections use the same security model as other org-scoped data:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // All access denied - backend service account only
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

Access is controlled via:
1. Firebase Admin SDK (bypasses rules)
2. Backend API endpoints with authentication
3. Organization ID filtering in all queries
