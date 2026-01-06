"""
PM Scheduler Endpoint - Thin API Layer

Protected endpoint for Cloud Scheduler to trigger PM rule evaluation.
Uses the same auth pattern as other scheduler endpoints.

Endpoint: POST /scheduler/pm/run
"""

import logging
import os
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import JSONResponse

from app.services.pm_scheduler_runner import run_pm_scheduler

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])
logger = logging.getLogger(__name__)

# Scheduler auth (same pattern as health.py)
SCHEDULER_SECRET = os.getenv("SCHEDULER_SECRET", None)


def _verify_scheduler_auth(
    authorization: Optional[str],
    x_scheduler_secret: Optional[str],
) -> bool:
    """
    Verify Cloud Scheduler authentication.

    Methods:
    1. OIDC token from Cloud Scheduler (production)
    2. X-Scheduler-Secret header (testing)
    3. Allow all in development
    """
    env = os.getenv("ENVIRONMENT", "development").lower()

    # Development mode - allow unauthenticated
    if env in ["development", "dev", "local"]:
        return True

    # OIDC Bearer token (Cloud Scheduler with OIDC)
    if authorization and authorization.startswith("Bearer "):
        # Cloud Run validates OIDC tokens via IAM
        return True

    # Secret header fallback
    if SCHEDULER_SECRET and x_scheduler_secret == SCHEDULER_SECRET:
        return True

    return False


@router.post("/pm/run")
async def run_pm_scheduler_endpoint(
    dry_run: bool = Query(True, description="If true, evaluate but don't create WOs"),
    batch_size: int = Query(200, description="Max rules to process", le=500),
    org_id: Optional[str] = Query(None, description="Filter to specific org"),
    authorization: Optional[str] = Header(None),
    x_scheduler_secret: Optional[str] = Header(None, alias="X-Scheduler-Secret"),
):
    """
    Run PM scheduler to evaluate rules and create work orders.

    This endpoint:
    1. Fetches active PM rules (paged by batch_size)
    2. Evaluates each rule using pure evaluator
    3. Creates work orders for triggered rules (if not dry_run)
    4. Updates rule metadata after trigger
    5. Logs evaluation results

    Idempotency:
    - Work orders use deterministic IDs (pm_{rule_id}_{YYYYMMDD})
    - Safe to call multiple times - duplicates are prevented

    Security:
    - Requires Cloud Scheduler OIDC token or X-Scheduler-Secret header
    - Allowed without auth in development mode

    Returns:
        Summary with counts: rules_checked, should_trigger, created, blocked, wait, errors
    """
    # Verify authentication
    if not _verify_scheduler_auth(authorization, x_scheduler_secret):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized - Cloud Scheduler OIDC token or valid secret required",
        )

    try:
        logger.info(f"PM Scheduler run starting: dry_run={dry_run}, batch_size={batch_size}, org_id={org_id}")

        result = await run_pm_scheduler(
            batch_size=batch_size,
            dry_run=dry_run,
            org_id=org_id,
        )

        return JSONResponse(content={
            "status": "success",
            "summary": result.to_dict(),
        })

    except Exception as e:
        logger.error(f"PM Scheduler run failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"PM Scheduler failed: {str(e)}",
        )


@router.get("/pm/status")
async def pm_scheduler_status(
    authorization: Optional[str] = Header(None),
    x_scheduler_secret: Optional[str] = Header(None, alias="X-Scheduler-Secret"),
):
    """
    Get PM scheduler status and recent run info.

    Returns:
        Status info including last run, next scheduled, rule counts
    """
    if not _verify_scheduler_auth(authorization, x_scheduler_secret):
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        from app.core.firestore_db import get_firestore_manager
        from datetime import datetime, timezone

        firestore = get_firestore_manager()

        # Get recent evaluations
        recent_evals = await firestore.get_collection(
            "pm_evaluations",
            order_by="-evaluated_at",
            limit=10,
        )

        # Get active rule count
        orgs = await firestore.get_collection("organizations", limit=100)
        total_active_rules = 0
        for org in orgs:
            if not org.get("is_demo"):
                org_id = org.get("id")
                if org_id:
                    rules = await firestore.get_pm_schedule_rules(org_id, is_active=True)
                    total_active_rules += len(rules)

        return JSONResponse(content={
            "status": "healthy",
            "total_active_rules": total_active_rules,
            "recent_evaluations": len(recent_evals),
            "last_evaluation": recent_evals[0] if recent_evals else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    except Exception as e:
        logger.error(f"PM Scheduler status failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)},
        )
