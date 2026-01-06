"""
PM Scheduler Runner - Thin Integration Layer

This module connects the pure evaluator to Firestore and work order creation.
It is intentionally minimal - all logic is in pm_rule_evaluator.py.

Flow:
1. Fetch active PM rules (paged)
2. For each rule: load minimal asset state
3. Call evaluator (pure function)
4. If SHOULD_TRIGGER: create WO with idempotent ID
5. Update rule metadata
6. Log evaluation result

Key design:
- Idempotent: deterministic WO IDs prevent duplicates
- Minimal reads: only fetch what evaluator needs
- Dry run: validate without creating WOs
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.core.firestore_db import get_firestore_manager
from app.services.pm_rule_evaluator import (
    AssetState,
    EvaluationResult,
    TimeBasedRule,
    TriggerDecision,
    evaluate_time_rule,
)

logger = logging.getLogger(__name__)


@dataclass
class RunnerResult:
    """Result of a scheduler run."""
    rules_checked: int = 0
    should_trigger: int = 0
    created: int = 0
    blocked: int = 0
    wait: int = 0
    errors: int = 0
    dry_run: bool = False
    duration_ms: float = 0.0
    details: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rules_checked": self.rules_checked,
            "should_trigger": self.should_trigger,
            "created": self.created,
            "blocked": self.blocked,
            "wait": self.wait,
            "errors": self.errors,
            "dry_run": self.dry_run,
            "duration_ms": round(self.duration_ms, 2),
            "details": self.details[:50],  # Limit response size
        }


def _generate_idempotent_wo_id(rule_id: str, due_date: datetime) -> str:
    """
    Generate deterministic work order ID.

    Format: pm_{rule_id}_{YYYYMMDD}

    This prevents duplicate WOs even if scheduler runs twice.
    """
    date_str = due_date.strftime("%Y%m%d")
    # Sanitize rule_id (remove special chars)
    safe_rule_id = "".join(c if c.isalnum() or c == "_" else "_" for c in rule_id)
    return f"pm_{safe_rule_id}_{date_str}"


async def _load_asset_state(
    firestore,
    asset_id: str,
    rule_id: str,
    org_id: str,
) -> AssetState:
    """
    Load minimal asset state for evaluation.

    Only fetches what the evaluator needs:
    - asset.status
    - has_pending_pm_work_order (via query)
    - current_meter_values (if needed)
    """
    # Get asset status
    asset_status = "operational"
    try:
        asset = await firestore.get_org_asset(asset_id, org_id)
        if asset:
            asset_status = asset.get("status", "operational")
    except Exception as e:
        logger.warning(f"Could not load asset {asset_id}: {e}")

    # Check for pending PM work order for this rule
    # Query: work_orders where pm_rule_id == X AND status in ["Open","In Progress"]
    has_pending = False
    try:
        pending_wos = await firestore.get_collection(
            "work_orders",
            filters=[
                {"field": "pm_rule_id", "operator": "==", "value": rule_id},
                {"field": "organization_id", "operator": "==", "value": org_id},
            ],
            limit=5,
        )
        # Check if any are still open
        for wo in pending_wos:
            status = wo.get("status", "")
            if status in ["Open", "In Progress", "Pending"]:
                has_pending = True
                break
    except Exception as e:
        logger.warning(f"Could not check pending WOs for rule {rule_id}: {e}")

    return AssetState(
        asset_id=asset_id,
        status=asset_status,
        has_pending_pm_work_order=has_pending,
    )


async def _create_pm_work_order(
    firestore,
    rule: Dict[str, Any],
    result: EvaluationResult,
    org_id: str,
    now: datetime,
) -> Optional[str]:
    """
    Create PM work order with idempotent ID.

    Returns work order ID if created, None if already exists.
    """
    rule_id = rule.get("id", "unknown")
    due_date = result.next_due or now

    # Generate deterministic ID
    wo_id = _generate_idempotent_wo_id(rule_id, due_date)

    # Check if already exists (idempotency check)
    existing = await firestore.get_document("work_orders", wo_id)
    if existing:
        logger.info(f"WO {wo_id} already exists - skipping (idempotent)")
        return None

    # Build work order data
    wo_data = {
        "id": wo_id,
        "title": rule.get("title", f"PM - {rule.get('asset_id', 'Unknown')}"),
        "description": rule.get("description", "Scheduled preventive maintenance"),
        "priority": rule.get("priority", "Medium"),
        "status": "Open",
        "work_order_type": "Preventive",
        "asset_id": rule.get("asset_id"),
        "organization_id": org_id,
        "due_date": due_date.isoformat(),
        "estimated_hours": rule.get("estimated_hours", 1.0),
        "pm_rule_id": rule_id,
        "pm_trigger_reason": result.trigger_reason.value if result.trigger_reason else "scheduled",
        "pm_generated_at": now.isoformat(),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    # Add checklist if present
    if rule.get("checklist"):
        wo_data["checklist"] = rule.get("checklist")

    # Create with specific ID (idempotent)
    try:
        await firestore.create_document("work_orders", wo_data, doc_id=wo_id)
        logger.info(f"Created PM work order {wo_id} for rule {rule_id}")
        return wo_id
    except Exception as e:
        logger.error(f"Failed to create WO {wo_id}: {e}")
        return None


async def _update_rule_after_trigger(
    firestore,
    rule_id: str,
    org_id: str,
    now: datetime,
    next_due: Optional[datetime],
    created_wo_id: Optional[str] = None,
) -> bool:
    """
    Update rule metadata after evaluation/trigger.

    This is CRITICAL for the due-only query to work correctly.
    If next_due is not updated, the rule will be picked up again next run.

    Fields updated:
    - last_evaluated_at: When we last looked at this rule
    - last_triggered_at: When we last created a WO (if triggered)
    - next_due: The next target date (MUST be updated for due-only query)
    - last_work_order_id: Reference to created WO
    - updated_at: General timestamp
    """
    try:
        update_data = {
            "last_evaluated_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        if created_wo_id:
            update_data["last_triggered_at"] = now.isoformat()
            update_data["last_work_order_id"] = created_wo_id

        if next_due:
            # Use consistent field name "next_due" (not "next_due_date")
            update_data["next_due"] = next_due.isoformat()

        # Use org-scoped update
        await firestore.update_pm_schedule_rule(rule_id, update_data, org_id)
        logger.debug(f"Updated rule {rule_id}: next_due={next_due.isoformat() if next_due else 'None'}")
        return True
    except Exception as e:
        logger.error(f"Failed to update rule {rule_id}: {e}")
        return False


async def _update_rule_after_evaluation(
    firestore,
    rule_id: str,
    org_id: str,
    result: EvaluationResult,
    now: datetime,
) -> bool:
    """
    Update rule after evaluation (even if not triggered).

    For blocked rules, store the blocked reason.
    This helps with debugging and monitoring.
    """
    try:
        update_data = {
            "last_evaluated_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        if result.blocked_reason:
            update_data["blocked_reason"] = result.blocked_reason.value
            update_data["blocked_at"] = now.isoformat()

        await firestore.update_pm_schedule_rule(rule_id, update_data, org_id)
        return True
    except Exception as e:
        logger.warning(f"Failed to update evaluation status for rule {rule_id}: {e}")
        return False


async def _log_evaluation(
    firestore,
    rule_id: str,
    org_id: str,
    result: EvaluationResult,
    wo_id: Optional[str],
    latency_ms: float,
    now: datetime,
) -> None:
    """Log evaluation result for debugging and audit."""
    try:
        log_data = {
            "rule_id": rule_id,
            "organization_id": org_id,
            "decision": result.decision.value,
            "trigger_reason": result.trigger_reason.value if result.trigger_reason else None,
            "blocked_reason": result.blocked_reason.value if result.blocked_reason else None,
            "message": result.message,
            "created_wo_id": wo_id,
            "latency_ms": round(latency_ms, 2),
            "evaluated_at": now.isoformat(),
        }
        # Use timestamp-based ID
        log_id = f"{rule_id}_{int(now.timestamp())}"
        await firestore.create_document("pm_evaluations", log_data, doc_id=log_id)
    except Exception as e:
        # Don't fail the run for logging errors
        logger.warning(f"Failed to log evaluation for {rule_id}: {e}")


async def process_rule(
    firestore,
    rule: Dict[str, Any],
    now: datetime,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Process a single PM rule.

    1. Load asset state
    2. Call evaluator
    3. If SHOULD_TRIGGER and not dry_run: create WO, update rule
    4. Log result

    Returns dict with rule_id, decision, created_wo_id, latency_ms
    """
    start_time = time.time()
    rule_id = rule.get("id", "unknown")
    org_id = rule.get("organization_id", "unknown")
    asset_id = rule.get("asset_id", "unknown")

    try:
        # 1. Load minimal asset state
        asset_state = await _load_asset_state(firestore, asset_id, rule_id, org_id)

        # 2. Convert rule to TimeBasedRule and evaluate
        time_rule = TimeBasedRule.from_dict(rule)
        result = evaluate_time_rule(time_rule, asset_state, now)

        latency_ms = (time.time() - start_time) * 1000
        created_wo_id = None

        # 3. Handle SHOULD_TRIGGER
        if result.decision == TriggerDecision.SHOULD_TRIGGER and not dry_run:
            created_wo_id = await _create_pm_work_order(
                firestore, rule, result, org_id, now
            )

            # Calculate next due for time-based rules
            interval_days = rule.get("interval_days", 30)
            next_due = now + timedelta(days=interval_days)

            # ALWAYS update rule state after trigger attempt
            # This moves next_due forward so rule won't be picked up again
            await _update_rule_after_trigger(
                firestore, rule_id, org_id, now, next_due, created_wo_id
            )
        elif result.decision == TriggerDecision.BLOCKED and not dry_run:
            # Update blocked reason in rule
            await _update_rule_after_evaluation(
                firestore, rule_id, org_id, result, now
            )

        # 4. Log evaluation
        await _log_evaluation(
            firestore, rule_id, org_id, result, created_wo_id, latency_ms, now
        )

        return {
            "rule_id": rule_id,
            "asset_id": asset_id,
            "decision": result.decision.value,
            "trigger_reason": result.trigger_reason.value if result.trigger_reason else None,
            "blocked_reason": result.blocked_reason.value if result.blocked_reason else None,
            "message": result.message,
            "created_wo_id": created_wo_id,
            "latency_ms": round(latency_ms, 2),
        }

    except Exception as e:
        logger.error(f"Error processing rule {rule_id}: {e}")
        return {
            "rule_id": rule_id,
            "asset_id": asset_id,
            "decision": "error",
            "error": str(e),
            "latency_ms": round((time.time() - start_time) * 1000, 2),
        }


async def run_pm_scheduler(
    batch_size: int = 200,
    dry_run: bool = False,
    org_id: Optional[str] = None,
) -> RunnerResult:
    """
    Run PM scheduler for rules that are DUE NOW.

    This uses an indexed query to fetch only rules where:
    - is_active == True
    - next_due <= now

    This is MUCH more efficient than fetching all active rules and filtering.

    Args:
        batch_size: Max rules to process per run
        dry_run: If True, evaluate but don't create WOs
        org_id: Optional org filter (None = all orgs)

    Returns:
        RunnerResult with counts and details
    """
    start_time = time.time()
    now = datetime.now(timezone.utc)
    result = RunnerResult(dry_run=dry_run)

    try:
        firestore = get_firestore_manager()

        # =====================================================
        # KEY CHANGE: Use indexed "due-only" query
        # This drops Firestore reads from O(all_rules) to O(due_rules)
        # =====================================================

        if org_id:
            # Single org mode - use org-scoped due query
            due_rules = await firestore.get_due_pm_rules(org_id, now)
            logger.info(f"PM Scheduler (org={org_id}): Found {len(due_rules)} due rules")
        else:
            # All orgs mode - use cross-org indexed query
            due_rules = await firestore.get_all_due_pm_rules(
                due_before=now,
                limit=batch_size,
                exclude_demo_orgs=True,
            )
            logger.info(f"PM Scheduler (all orgs): Found {len(due_rules)} due rules")

        # Process only due rules (no more "wait" decisions expected)
        for rule in due_rules:
            result.rules_checked += 1

            rule_result = await process_rule(firestore, rule, now, dry_run)
            result.details.append(rule_result)

            decision = rule_result.get("decision", "error")
            if decision == "should_trigger":
                result.should_trigger += 1
                if rule_result.get("created_wo_id"):
                    result.created += 1
            elif decision == "blocked":
                result.blocked += 1
            elif decision == "wait":
                # Shouldn't happen with due-only query, but handle gracefully
                result.wait += 1
            elif decision == "error":
                result.errors += 1

        result.duration_ms = (time.time() - start_time) * 1000

        logger.info(
            f"PM Scheduler complete: checked={result.rules_checked}, "
            f"triggered={result.should_trigger}, created={result.created}, "
            f"blocked={result.blocked}, wait={result.wait}, errors={result.errors}, "
            f"duration={result.duration_ms:.0f}ms"
        )

        return result

    except Exception as e:
        logger.error(f"PM Scheduler failed: {e}")
        result.errors += 1
        result.duration_ms = (time.time() - start_time) * 1000
        return result
