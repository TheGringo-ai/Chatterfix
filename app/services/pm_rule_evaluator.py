"""
PM Rule Evaluator - Pure Function, No Side Effects

This module provides deterministic rule evaluation.
It answers: "Should this rule trigger right now, and why?"

Key design principles:
- Pure functions only - no database writes, no state mutation
- Returns decision + reason for every evaluation
- Handles conflict rules (breakdown, manual completion, out of service)
- Easily testable and auditable

Usage:
    result = evaluate_time_rule(rule, asset_state, now)
    if result.decision == TriggerDecision.SHOULD_TRIGGER:
        # Create work order
    elif result.decision == TriggerDecision.BLOCKED:
        # Log blocked reason
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# ==========================================
# ENUMS
# ==========================================


class TriggerDecision(Enum):
    """Result of rule evaluation."""
    SHOULD_TRIGGER = "should_trigger"
    WAIT = "wait"
    BLOCKED = "blocked"


class BlockedReason(Enum):
    """Why a rule is blocked from triggering."""
    NONE = "none"
    ASSET_BREAKDOWN = "asset_breakdown"
    ASSET_OUT_OF_SERVICE = "asset_out_of_service"
    ALREADY_COMPLETED_IN_WINDOW = "already_completed_in_window"
    RULE_PAUSED = "rule_paused"
    RULE_DISABLED = "rule_disabled"
    PENDING_WORK_ORDER_EXISTS = "pending_work_order_exists"
    COOLDOWN_PERIOD = "cooldown_period"


class TriggerReason(Enum):
    """Why a rule should trigger."""
    DUE_BY_TIME = "due_by_time"
    OVERDUE = "overdue"
    WITHIN_TOLERANCE = "within_tolerance"
    DUE_BY_USAGE = "due_by_usage"
    THRESHOLD_EXCEEDED = "threshold_exceeded"
    CONDITION_MET = "condition_met"


class RuleStatus(Enum):
    """Status of a PM rule."""
    ACTIVE = "active"
    PAUSED = "paused"
    BLOCKED = "blocked"


# ==========================================
# DATA CLASSES
# ==========================================


@dataclass
class EvaluationResult:
    """
    Result of evaluating a PM rule.

    This is the ONLY output of the evaluator.
    It tells you what to do and why.
    """
    decision: TriggerDecision
    trigger_reason: Optional[TriggerReason] = None
    blocked_reason: Optional[BlockedReason] = None
    next_due: Optional[datetime] = None
    days_until_due: Optional[int] = None
    days_overdue: Optional[int] = None
    confidence: float = 1.0
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "trigger_reason": self.trigger_reason.value if self.trigger_reason else None,
            "blocked_reason": self.blocked_reason.value if self.blocked_reason else None,
            "next_due": self.next_due.isoformat() if self.next_due else None,
            "days_until_due": self.days_until_due,
            "days_overdue": self.days_overdue,
            "confidence": self.confidence,
            "message": self.message,
        }


@dataclass
class AssetState:
    """
    Current state of an asset.

    This is the ONLY input about the asset.
    Evaluator does not query databases.
    """
    asset_id: str
    status: str = "operational"  # operational, breakdown, out_of_service, maintenance
    has_pending_pm_work_order: bool = False
    last_pm_completed_at: Optional[datetime] = None
    last_breakdown_at: Optional[datetime] = None
    breakdown_resolved_at: Optional[datetime] = None
    current_meter_values: Optional[Dict[str, float]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssetState":
        return cls(
            asset_id=data.get("asset_id", "unknown"),
            status=data.get("status", "operational"),
            has_pending_pm_work_order=data.get("has_pending_pm_work_order", False),
            last_pm_completed_at=_parse_datetime(data.get("last_pm_completed_at")),
            last_breakdown_at=_parse_datetime(data.get("last_breakdown_at")),
            breakdown_resolved_at=_parse_datetime(data.get("breakdown_resolved_at")),
            current_meter_values=data.get("current_meter_values"),
        )


@dataclass
class TimeBasedRule:
    """
    Time-based PM rule configuration.

    Examples:
    - Every 30 days
    - Every Monday
    - First business day of month
    """
    rule_id: str
    asset_id: str
    interval_days: int
    anchor_date: datetime
    tolerance_days: int = 3  # +/- days window
    status: RuleStatus = RuleStatus.ACTIVE
    blocked_reason: Optional[str] = None
    last_triggered_at: Optional[datetime] = None
    next_due: Optional[datetime] = None
    cooldown_hours: int = 24  # Min hours between triggers

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimeBasedRule":
        status_str = data.get("status", "active")
        if isinstance(status_str, str):
            try:
                status = RuleStatus(status_str)
            except ValueError:
                status = RuleStatus.ACTIVE
        else:
            status = status_str

        # Handle multiple field name conventions
        next_due = _parse_datetime(
            data.get("next_due") or
            data.get("next_due_date") or
            data.get("next_due_at")
        )

        anchor = _parse_datetime(
            data.get("anchor_date") or
            data.get("start_date") or
            data.get("created_at")
        ) or datetime.now(timezone.utc)

        return cls(
            rule_id=data.get("id", data.get("rule_id", "unknown")),
            asset_id=data.get("asset_id", "unknown"),
            interval_days=data.get("interval_days", data.get("interval_value", 30)),
            anchor_date=anchor,
            tolerance_days=data.get("tolerance_days", 3),
            status=status,
            blocked_reason=data.get("blocked_reason"),
            last_triggered_at=_parse_datetime(data.get("last_triggered_at", data.get("last_generated"))),
            next_due=next_due,
            cooldown_hours=data.get("cooldown_hours", 24),
        )


@dataclass
class UsageBasedRule:
    """
    Usage-based PM rule configuration.

    Examples:
    - Every 500 runtime hours
    - Every 10,000 cycles
    """
    rule_id: str
    asset_id: str
    meter_type: str  # "runtime_hours", "cycles", "units"
    threshold: float
    last_trigger_value: float = 0.0
    status: RuleStatus = RuleStatus.ACTIVE
    blocked_reason: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UsageBasedRule":
        status_str = data.get("status", "active")
        if isinstance(status_str, str):
            try:
                status = RuleStatus(status_str)
            except ValueError:
                status = RuleStatus.ACTIVE
        else:
            status = status_str

        return cls(
            rule_id=data.get("id", data.get("rule_id", "unknown")),
            asset_id=data.get("asset_id", "unknown"),
            meter_type=data.get("meter_type", data.get("interval_unit", "runtime_hours")),
            threshold=float(data.get("threshold", data.get("interval_value", 500))),
            last_trigger_value=float(data.get("last_trigger_value", 0.0)),
            status=status,
            blocked_reason=data.get("blocked_reason"),
        )


# ==========================================
# PURE EVALUATION FUNCTIONS
# ==========================================


def evaluate_time_rule(
    rule: TimeBasedRule,
    asset_state: AssetState,
    now: Optional[datetime] = None,
) -> EvaluationResult:
    """
    Evaluate a time-based PM rule.

    This is a PURE FUNCTION:
    - Takes rule + asset state + current time
    - Returns decision + reason
    - Does NOT modify anything
    - Does NOT query databases

    Args:
        rule: The time-based PM rule to evaluate
        asset_state: Current state of the asset
        now: Current time (defaults to UTC now)

    Returns:
        EvaluationResult with decision and reason
    """
    now = _ensure_utc(now) or datetime.now(timezone.utc)

    # ========================================
    # STEP 1: Check rule status
    # ========================================
    if rule.status == RuleStatus.PAUSED:
        return EvaluationResult(
            decision=TriggerDecision.BLOCKED,
            blocked_reason=BlockedReason.RULE_PAUSED,
            message=f"Rule {rule.rule_id} is paused",
        )

    if rule.status == RuleStatus.BLOCKED:
        return EvaluationResult(
            decision=TriggerDecision.BLOCKED,
            blocked_reason=BlockedReason.RULE_DISABLED,
            message=f"Rule {rule.rule_id} is blocked: {rule.blocked_reason}",
        )

    # ========================================
    # STEP 2: Check asset status (conflicts)
    # ========================================

    # Breakdown overrides PM
    if asset_state.status == "breakdown":
        return EvaluationResult(
            decision=TriggerDecision.BLOCKED,
            blocked_reason=BlockedReason.ASSET_BREAKDOWN,
            message=f"Asset {asset_state.asset_id} is in breakdown - PM postponed",
        )

    # Asset out of service - PM paused
    if asset_state.status == "out_of_service":
        return EvaluationResult(
            decision=TriggerDecision.BLOCKED,
            blocked_reason=BlockedReason.ASSET_OUT_OF_SERVICE,
            message=f"Asset {asset_state.asset_id} is out of service - PM paused",
        )

    # Already has pending PM work order - don't double-fire
    if asset_state.has_pending_pm_work_order:
        return EvaluationResult(
            decision=TriggerDecision.BLOCKED,
            blocked_reason=BlockedReason.PENDING_WORK_ORDER_EXISTS,
            message=f"Asset {asset_state.asset_id} already has pending PM work order",
        )

    # ========================================
    # STEP 3: Check cooldown period
    # ========================================
    if rule.last_triggered_at:
        cooldown_end = rule.last_triggered_at + timedelta(hours=rule.cooldown_hours)
        if now < cooldown_end:
            hours_remaining = (cooldown_end - now).total_seconds() / 3600
            return EvaluationResult(
                decision=TriggerDecision.BLOCKED,
                blocked_reason=BlockedReason.COOLDOWN_PERIOD,
                message=f"Cooldown period: {hours_remaining:.1f} hours remaining",
            )

    # ========================================
    # STEP 4: Check if recently completed (manual reset)
    # ========================================
    if asset_state.last_pm_completed_at:
        days_since_completion = (now - asset_state.last_pm_completed_at).days
        if days_since_completion < rule.interval_days - rule.tolerance_days:
            next_due = asset_state.last_pm_completed_at + timedelta(days=rule.interval_days)
            days_until = (next_due - now).days
            return EvaluationResult(
                decision=TriggerDecision.WAIT,
                next_due=next_due,
                days_until_due=days_until,
                message=f"PM completed {days_since_completion} days ago, next due in {days_until} days",
            )

    # ========================================
    # STEP 5: Calculate due date
    # ========================================
    if rule.next_due:
        next_due = rule.next_due
    elif rule.last_triggered_at:
        next_due = rule.last_triggered_at + timedelta(days=rule.interval_days)
    else:
        next_due = rule.anchor_date + timedelta(days=rule.interval_days)

    days_until_due = (next_due - now).days

    # ========================================
    # STEP 6: Make decision
    # ========================================

    # Already overdue
    if days_until_due < 0:
        days_overdue = abs(days_until_due)
        return EvaluationResult(
            decision=TriggerDecision.SHOULD_TRIGGER,
            trigger_reason=TriggerReason.OVERDUE,
            next_due=next_due,
            days_overdue=days_overdue,
            confidence=1.0,
            message=f"PM is {days_overdue} days overdue",
        )

    # Due today
    if days_until_due == 0:
        return EvaluationResult(
            decision=TriggerDecision.SHOULD_TRIGGER,
            trigger_reason=TriggerReason.DUE_BY_TIME,
            next_due=next_due,
            days_until_due=0,
            confidence=1.0,
            message="PM is due today",
        )

    # Within tolerance window (can trigger early)
    if days_until_due <= rule.tolerance_days:
        return EvaluationResult(
            decision=TriggerDecision.SHOULD_TRIGGER,
            trigger_reason=TriggerReason.WITHIN_TOLERANCE,
            next_due=next_due,
            days_until_due=days_until_due,
            confidence=0.9,
            message=f"PM due in {days_until_due} days (within {rule.tolerance_days}-day tolerance)",
        )

    # Not yet due
    return EvaluationResult(
        decision=TriggerDecision.WAIT,
        next_due=next_due,
        days_until_due=days_until_due,
        message=f"PM not due yet - {days_until_due} days remaining",
    )


def evaluate_usage_rule(
    rule: UsageBasedRule,
    asset_state: AssetState,
    now: Optional[datetime] = None,
) -> EvaluationResult:
    """
    Evaluate a usage-based PM rule.

    Pure function - no side effects.

    Args:
        rule: The usage-based PM rule to evaluate
        asset_state: Current state of the asset (must include meter values)
        now: Current time (for logging only)

    Returns:
        EvaluationResult with decision and reason
    """
    now = _ensure_utc(now) or datetime.now(timezone.utc)

    # Check rule status
    if rule.status == RuleStatus.PAUSED:
        return EvaluationResult(
            decision=TriggerDecision.BLOCKED,
            blocked_reason=BlockedReason.RULE_PAUSED,
            message=f"Rule {rule.rule_id} is paused",
        )

    if rule.status == RuleStatus.BLOCKED:
        return EvaluationResult(
            decision=TriggerDecision.BLOCKED,
            blocked_reason=BlockedReason.RULE_DISABLED,
            message=f"Rule {rule.rule_id} is blocked: {rule.blocked_reason}",
        )

    # Check asset status
    if asset_state.status == "breakdown":
        return EvaluationResult(
            decision=TriggerDecision.BLOCKED,
            blocked_reason=BlockedReason.ASSET_BREAKDOWN,
            message=f"Asset {asset_state.asset_id} is in breakdown",
        )

    if asset_state.status == "out_of_service":
        return EvaluationResult(
            decision=TriggerDecision.BLOCKED,
            blocked_reason=BlockedReason.ASSET_OUT_OF_SERVICE,
            message=f"Asset {asset_state.asset_id} is out of service",
        )

    if asset_state.has_pending_pm_work_order:
        return EvaluationResult(
            decision=TriggerDecision.BLOCKED,
            blocked_reason=BlockedReason.PENDING_WORK_ORDER_EXISTS,
            message=f"Asset already has pending PM work order",
        )

    # Get current meter value
    if not asset_state.current_meter_values:
        return EvaluationResult(
            decision=TriggerDecision.WAIT,
            message=f"No meter values available for {rule.meter_type}",
        )

    current_value = asset_state.current_meter_values.get(rule.meter_type)
    if current_value is None:
        return EvaluationResult(
            decision=TriggerDecision.WAIT,
            message=f"Meter type {rule.meter_type} not found",
        )

    # Calculate usage since last trigger
    usage_since_trigger = current_value - rule.last_trigger_value
    usage_remaining = rule.threshold - usage_since_trigger

    if usage_remaining <= 0:
        return EvaluationResult(
            decision=TriggerDecision.SHOULD_TRIGGER,
            trigger_reason=TriggerReason.DUE_BY_USAGE,
            confidence=1.0,
            message=f"Usage threshold reached: {current_value} {rule.meter_type} (threshold: {rule.threshold})",
        )

    # Check if approaching threshold (10% warning)
    if usage_remaining < rule.threshold * 0.1:
        return EvaluationResult(
            decision=TriggerDecision.WAIT,
            confidence=0.8,
            message=f"Approaching threshold: {usage_remaining:.0f} {rule.meter_type} remaining",
        )

    return EvaluationResult(
        decision=TriggerDecision.WAIT,
        message=f"Usage: {usage_since_trigger:.0f}/{rule.threshold} {rule.meter_type}",
    )


# ==========================================
# HELPER FUNCTIONS
# ==========================================


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure datetime is UTC timezone-aware."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _parse_datetime(value: Any) -> Optional[datetime]:
    """Parse datetime from various formats."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return _ensure_utc(value)
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return _ensure_utc(dt)
        except ValueError:
            return None
    return None


# ==========================================
# BATCH EVALUATION
# ==========================================


def evaluate_rules_batch(
    rules: list,
    asset_states: Dict[str, AssetState],
    now: Optional[datetime] = None,
) -> Dict[str, EvaluationResult]:
    """
    Evaluate multiple rules in batch.

    Args:
        rules: List of rule dicts (will auto-detect type)
        asset_states: Dict mapping asset_id to AssetState
        now: Current time

    Returns:
        Dict mapping rule_id to EvaluationResult
    """
    now = _ensure_utc(now) or datetime.now(timezone.utc)
    results = {}

    for rule_dict in rules:
        rule_id = rule_dict.get("id", rule_dict.get("rule_id", "unknown"))
        asset_id = rule_dict.get("asset_id", "unknown")
        schedule_type = rule_dict.get("schedule_type", "time_based")

        # Get asset state (or create default)
        asset_state = asset_states.get(asset_id, AssetState(asset_id=asset_id))

        try:
            if schedule_type == "usage_based":
                rule = UsageBasedRule.from_dict(rule_dict)
                result = evaluate_usage_rule(rule, asset_state, now)
            else:
                # Default to time-based
                rule = TimeBasedRule.from_dict(rule_dict)
                result = evaluate_time_rule(rule, asset_state, now)

            results[rule_id] = result

        except Exception as e:
            logger.error(f"Error evaluating rule {rule_id}: {e}")
            results[rule_id] = EvaluationResult(
                decision=TriggerDecision.BLOCKED,
                blocked_reason=BlockedReason.RULE_DISABLED,
                message=f"Evaluation error: {str(e)}",
            )

    return results
