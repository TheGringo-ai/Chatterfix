import logging
import os
import psutil
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import JSONResponse
import httpx

from app.core.firestore_db import get_firestore_manager
from app.services.pm_automation_engine import get_pm_automation_engine
from app.services.firestore_cost_monitor import get_cost_monitor

router = APIRouter()
logger = logging.getLogger(__name__)

# Read version from VERSION.txt
APP_VERSION = "unknown"
try:
    version_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "VERSION.txt"
    )
    with open(version_file, "r") as f:
        APP_VERSION = f.readline().strip()
except Exception as e:
    # Log warning if VERSION.txt is missing (indicates deployment issue)
    import logging

    logging.warning(f"Could not read VERSION.txt: {e}. Using 'unknown' as version.")
    APP_VERSION = "unknown"


@router.get("/health")
async def health_check():
    """Basic health check endpoint for load balancers"""
    return JSONResponse(
        {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    )


@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check endpoint for monitoring and diagnostics"""
    start_time = time.time()
    health_data: Dict[str, Any] = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "chatterfix-cmms",
        "version": APP_VERSION,
    }

    try:
        # System metrics
        health_data["system"] = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
            "load_average": os.getloadavg() if hasattr(os, "getloadavg") else None,
        }

        # Database connectivity
        health_data["database"] = await check_database_health()

        # AI Team service connectivity
        health_data["ai_team"] = await check_ai_team_health()

        # Application health
        health_data["application"] = {
            "environment": os.getenv("ENVIRONMENT", "development"),
            "port": os.getenv("PORT", "8080"),
            "workers": os.getenv("WEB_CONCURRENCY", "1"),
        }

        # Response time
        health_data["response_time_ms"] = round((time.time() - start_time) * 1000, 2)

        # Determine overall status
        issues = []
        if health_data["system"]["memory_percent"] > 90:
            issues.append("high_memory_usage")
        if health_data["system"]["cpu_percent"] > 95:
            issues.append("high_cpu_usage")
        if health_data["database"]["status"] == "error":
            issues.append("database_connection_failed")
        if health_data["ai_team"]["status"] == "error":
            issues.append("ai_team_connection_failed")

        if issues:
            health_data["status"] = "degraded"
            health_data["issues"] = issues
            return JSONResponse(
                status_code=207, content=health_data
            )  # 207 Multi-Status

        return JSONResponse(content=health_data)

    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
            },
        )


@router.get("/health/readiness")
async def readiness_check():
    """Kubernetes readiness probe endpoint"""
    try:
        # Check critical dependencies
        db_health = await check_database_health()

        if db_health["status"] == "error":
            return JSONResponse(
                status_code=503,
                content={
                    "ready": False,
                    "reason": "database_unavailable",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

        return JSONResponse({"ready": True, "timestamp": datetime.utcnow().isoformat()})

    except Exception:
        return JSONResponse(
            status_code=503,
            content={
                "ready": False,
                "reason": "service_error",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


@router.get("/health/liveness")
async def liveness_check():
    """Kubernetes liveness probe endpoint"""
    return JSONResponse({"alive": True, "timestamp": datetime.utcnow().isoformat()})


@router.get("/health/environment")
async def environment_info():
    """
    Get current environment information

    Clearly shows if you're on DEV or PROD
    """
    env = os.getenv("ENVIRONMENT", "development").lower()

    # Determine environment type
    is_production = env == "production"
    is_dev = env in ["development", "dev", "staging"]

    # Get service info
    service_url = os.getenv("K_SERVICE", "unknown")
    revision = os.getenv("K_REVISION", "unknown")

    env_info = {
        "environment": env,
        "is_production": is_production,
        "is_development": is_dev,
        "service": service_url,
        "revision": revision,
        "version": APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if is_production:
        env_info["banner"] = "🚀 PRODUCTION - chatterfix.com"
        env_info["warning"] = "Changes here affect real users!"
        env_info["urls"] = {
            "main": "https://chatterfix.com",
            "demo": "https://chatterfix.com/demo",
        }
    else:
        env_info["banner"] = "🧪 DEVELOPMENT - Testing Environment"
        env_info["info"] = "Safe to test - does not affect production"
        env_info["urls"] = {
            "main": "https://gringo-core-650169261019.us-central1.run.app",
            "demo": "https://gringo-core-650169261019.us-central1.run.app/demo",
        }
        env_info["promote_command"] = "./scripts/deploy-prod.sh"

    return JSONResponse(env_info)


async def check_database_health() -> Dict[str, Any]:
    """Check database connectivity"""
    db_info = {
        "status": "unknown",
        "type": "none",
        "response_time_ms": None,
    }

    start_time = time.time()
    try:
        if os.getenv("USE_FIRESTORE", "false").lower() == "true":
            # Firestore health check
            from app.core.db_adapter import get_db_adapter

            db_adapter = get_db_adapter()
            # Simple test to verify connection
            await db_adapter.get_all_work_orders()  # This will test the connection

            db_info["status"] = "ok"
            db_info["type"] = "firestore"
        else:
            # SQLite health check
            db_info["status"] = "ok"
            db_info["type"] = "sqlite_disabled"

        db_info["response_time_ms"] = round((time.time() - start_time) * 1000, 2)

    except Exception as e:
        db_info["status"] = "error"
        db_info["error"] = str(e)
        db_info["response_time_ms"] = round((time.time() - start_time) * 1000, 2)

    return db_info


async def check_ai_team_health() -> Dict[str, Any]:
    """Check AI Team service connectivity"""
    ai_info = {
        "status": "unknown",
        "service_url": None,
        "response_time_ms": None,
        "grpc_disabled": os.getenv("DISABLE_AI_TEAM_GRPC", "true").lower() == "true",
    }

    ai_service_url = os.getenv("AI_TEAM_SERVICE_URL")

    if not ai_service_url:
        ai_info["status"] = "disabled"
        ai_info["reason"] = "no_service_url_configured"
        return ai_info

    ai_info["service_url"] = ai_service_url
    start_time = time.time()

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{ai_service_url}/health")
            ai_info["response_time_ms"] = round((time.time() - start_time) * 1000, 2)

            if response.status_code == 200:
                ai_info["status"] = "ok"
                ai_info["service_response"] = response.json()
            else:
                ai_info["status"] = "error"
                ai_info["error"] = f"HTTP {response.status_code}"

    except Exception as e:
        ai_info["status"] = "error"
        ai_info["error"] = str(e)
        ai_info["response_time_ms"] = round((time.time() - start_time) * 1000, 2)

    return ai_info


# ========== CLOUD SCHEDULER ENDPOINTS ==========
# These endpoints are designed to be called by Cloud Scheduler with OIDC authentication

# Expected service account for scheduler (set via environment)
SCHEDULER_SERVICE_ACCOUNT = os.getenv(
    "SCHEDULER_SERVICE_ACCOUNT",
    "pm-scheduler@fredfix.iam.gserviceaccount.com"
)

# Fallback secret header for testing (should be set in production)
SCHEDULER_SECRET = os.getenv("SCHEDULER_SECRET", None)


async def _verify_oidc_token(token: str) -> dict:
    """
    Verify Google OIDC token and return claims.

    In production with Cloud Run, the platform validates the token automatically
    when IAM invoker permissions are set. This function provides additional
    verification for defense-in-depth.

    Returns:
        dict with token claims (email, aud, etc.) or empty dict if invalid
    """
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests

        # Verify the token with Google
        claims = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            audience=os.getenv("CLOUD_RUN_SERVICE_URL", "https://chatterfix.com"),
        )
        return claims
    except ImportError:
        # google-auth not installed, fall back to basic check
        logger.warning("google-auth not installed, using basic token check")
        return {"verified": "basic"}
    except Exception as e:
        logger.warning(f"OIDC token verification failed: {e}")
        return {}


def _verify_scheduler_auth(authorization: Optional[str]) -> bool:
    """
    Verify Cloud Scheduler authentication.

    Authentication methods (checked in order):
    1. OIDC token from Cloud Scheduler (preferred in production)
    2. Secret header X-Scheduler-Secret (fallback for testing)
    3. Allow all in development mode

    In production, Cloud Run IAM should be configured to only allow
    the scheduler service account to invoke these endpoints.
    """
    env = os.getenv("ENVIRONMENT", "development").lower()

    # In development, allow unauthenticated requests for testing
    if env in ["development", "dev", "local"]:
        logger.debug("Scheduler auth: allowing in development mode")
        return True

    # Check for OIDC Bearer token (Cloud Scheduler with OIDC auth)
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]  # Remove "Bearer " prefix

        # In production Cloud Run, the platform validates OIDC tokens automatically
        # when the service account has roles/run.invoker permission.
        # We trust Cloud Run's authentication here.
        #
        # For additional security, you can verify the token claims:
        # claims = await _verify_oidc_token(token)
        # if claims.get("email") == SCHEDULER_SERVICE_ACCOUNT:
        #     return True

        logger.info("Scheduler auth: OIDC token present, trusting Cloud Run IAM")
        return True

    # Check for secret header (fallback for testing or non-OIDC setups)
    # This is less secure but useful for manual testing
    if SCHEDULER_SECRET:
        # Note: This would need to be passed differently (via custom header)
        # This is a fallback mechanism
        logger.warning("Scheduler auth: checking for secret-based auth")
        return False  # Secret header not in authorization

    logger.warning("Scheduler auth: no valid authentication found")
    return False


def _verify_scheduler_secret(x_scheduler_secret: Optional[str]) -> bool:
    """
    Verify scheduler secret header (fallback authentication).

    Use this for manual testing when OIDC is not available.
    """
    if not SCHEDULER_SECRET:
        return False

    if x_scheduler_secret and x_scheduler_secret == SCHEDULER_SECRET:
        logger.info("Scheduler auth: valid secret header")
        return True

    return False


@router.post("/scheduled/pm-generation")
async def scheduled_pm_generation(
    days_ahead: int = Query(30, description="Days to generate PM for"),
    dry_run: bool = Query(False, description="If true, don't create actual work orders"),
    authorization: Optional[str] = Header(None),
    x_scheduler_secret: Optional[str] = Header(None, alias="X-Scheduler-Secret"),
):
    """
    Cloud Scheduler endpoint for automated PM work order generation.

    This endpoint iterates through all organizations with active PM rules
    and generates work orders for due maintenance tasks.

    Security: Protected by Cloud Run IAM + OIDC token from Cloud Scheduler.
    Fallback: X-Scheduler-Secret header for manual testing.

    Schedule: Daily at 2:00 AM UTC (configured in Cloud Scheduler)
    """
    start_time = time.time()

    # Verify scheduler authentication (OIDC or secret header)
    if not _verify_scheduler_auth(authorization) and not _verify_scheduler_secret(x_scheduler_secret):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized - Cloud Scheduler OIDC token or valid secret required",
        )

    try:
        firestore_manager = get_firestore_manager()
        pm_engine = get_pm_automation_engine()

        # Get all organizations
        orgs = await firestore_manager.get_collection("organizations")
        logger.info(f"PM generation starting for {len(orgs)} organizations")

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "organizations_processed": 0,
            "total_work_orders_created": 0,
            "total_pm_orders_generated": 0,
            "errors": [],
            "details": [],
        }

        end_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)

        for org in orgs:
            org_id = org.get("id")
            org_name = org.get("name", "Unknown")

            # Skip demo organizations
            if org.get("is_demo"):
                continue

            try:
                # Check if org has active PM rules
                rules = await firestore_manager.get_pm_schedule_rules(
                    org_id, is_active=True
                )

                if not rules:
                    continue  # No PM rules configured

                # Generate PM schedule
                result = await pm_engine.generate_pm_schedule(
                    org_id,
                    start_date=datetime.now(timezone.utc),
                    end_date=end_date,
                    create_work_orders=not dry_run,
                )

                results["organizations_processed"] += 1
                results["total_pm_orders_generated"] += result.get("generated_count", 0)
                results["total_work_orders_created"] += result.get(
                    "work_orders_created", 0
                )

                results["details"].append(
                    {
                        "organization_id": org_id,
                        "organization_name": org_name,
                        "active_rules": len(rules),
                        "pm_orders_generated": result.get("generated_count", 0),
                        "work_orders_created": result.get("work_orders_created", 0),
                    }
                )

                logger.info(
                    f"PM generation for {org_name}: {result.get('generated_count', 0)} orders"
                )

            except Exception as e:
                error_msg = f"Error processing org {org_name} ({org_id}): {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)

        results["execution_time_ms"] = round((time.time() - start_time) * 1000, 2)
        results["dry_run"] = dry_run
        results["days_ahead"] = days_ahead

        logger.info(
            f"PM generation complete: {results['total_work_orders_created']} WOs created "
            f"for {results['organizations_processed']} orgs in {results['execution_time_ms']}ms"
        )

        return JSONResponse(content=results)

    except Exception as e:
        logger.error(f"PM generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"PM generation failed: {str(e)}",
        )


@router.post("/scheduled/meter-threshold-check")
async def scheduled_meter_threshold_check(
    authorization: Optional[str] = Header(None),
    x_scheduler_secret: Optional[str] = Header(None, alias="X-Scheduler-Secret"),
):
    """
    Cloud Scheduler endpoint for checking meter thresholds and triggering alerts.

    This endpoint checks all asset meters across organizations for threshold
    violations and can trigger condition-based maintenance work orders.

    Schedule: Every 4 hours (configured in Cloud Scheduler)
    """
    start_time = time.time()

    if not _verify_scheduler_auth(authorization) and not _verify_scheduler_secret(x_scheduler_secret):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized - Cloud Scheduler OIDC token or valid secret required",
        )

    try:
        firestore_manager = get_firestore_manager()

        # Get all organizations
        orgs = await firestore_manager.get_collection("organizations")

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "organizations_checked": 0,
            "critical_alerts": 0,
            "warning_alerts": 0,
            "details": [],
        }

        for org in orgs:
            org_id = org.get("id")
            org_name = org.get("name", "Unknown")

            if org.get("is_demo"):
                continue

            try:
                # Check for meters exceeding thresholds
                critical = await firestore_manager.get_meters_exceeding_threshold(
                    org_id, "critical"
                )
                warning = await firestore_manager.get_meters_exceeding_threshold(
                    org_id, "warning"
                )

                if critical or warning:
                    results["organizations_checked"] += 1
                    results["critical_alerts"] += len(critical)
                    results["warning_alerts"] += len(warning)

                    results["details"].append(
                        {
                            "organization_id": org_id,
                            "organization_name": org_name,
                            "critical_meters": len(critical),
                            "warning_meters": len(warning),
                            "critical_details": [
                                {
                                    "meter_id": m.get("id"),
                                    "asset_id": m.get("asset_id"),
                                    "meter_type": m.get("meter_type"),
                                    "current_value": m.get("current_value"),
                                    "threshold": m.get("threshold_critical"),
                                }
                                for m in critical
                            ],
                        }
                    )

            except Exception as e:
                logger.error(f"Error checking meters for {org_name}: {str(e)}")

        results["execution_time_ms"] = round((time.time() - start_time) * 1000, 2)

        return JSONResponse(content=results)

    except Exception as e:
        logger.error(f"Meter threshold check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Meter threshold check failed: {str(e)}",
        )


# ========== FIRESTORE COST MONITORING ==========

@router.get("/health/firestore-costs")
async def firestore_cost_stats():
    """
    Get Firestore collection statistics and estimated costs.

    Returns:
        - Document counts per collection
        - Estimated storage sizes
        - Monthly cost estimates
        - Cost warnings if thresholds exceeded
    """
    try:
        cost_monitor = get_cost_monitor()
        stats = await cost_monitor.get_all_stats()
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"Error getting Firestore costs: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()}
        )


@router.post("/scheduled/data-cleanup")
async def scheduled_data_cleanup(
    dry_run: bool = Query(True, description="If true, only report what would be deleted"),
    authorization: Optional[str] = Header(None),
    x_scheduler_secret: Optional[str] = Header(None, alias="X-Scheduler-Secret"),
):
    """
    Cloud Scheduler endpoint for cleaning up old log data.

    Applies retention policies:
    - Critical data (users, work_orders, assets): Never deleted
    - Long-term (audit_logs, safety_incidents): 365 days
    - Medium-term (ai_conversations, team_messages): 90 days
    - Short-term (voice_logs, zone_entries): 30 days
    - Temporary (debug_logs): 7 days

    Schedule: Weekly on Sunday at 3:00 AM UTC
    """
    start_time = time.time()

    # Verify scheduler authentication
    if not _verify_scheduler_auth(authorization) and not _verify_scheduler_secret(x_scheduler_secret):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized - Cloud Scheduler OIDC token or valid secret required",
        )

    try:
        cost_monitor = get_cost_monitor()
        results = await cost_monitor.prune_old_data(dry_run=dry_run)
        results["execution_time_ms"] = round((time.time() - start_time) * 1000, 2)

        if not dry_run:
            logger.info(f"Data cleanup complete: {results['total_documents_deleted']} documents deleted")

        return JSONResponse(content=results)

    except Exception as e:
        logger.error(f"Data cleanup failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Data cleanup failed: {str(e)}",
        )


@router.get("/health/cost-summary")
async def cost_summary():
    """
    Quick cost summary with actionable recommendations.

    Returns simple metrics and warnings for dashboard display.
    """
    try:
        cost_monitor = get_cost_monitor()
        stats = await cost_monitor.get_all_stats()

        summary = stats.get("summary", {})
        warnings = stats.get("cost_warnings", [])

        # Determine status
        monthly_cost = summary.get("estimated_monthly_cost_usd", 0)
        if monthly_cost > 10:
            status = "high"
            action = "Run data cleanup: POST /scheduled/data-cleanup?dry_run=false"
        elif monthly_cost > 5:
            status = "moderate"
            action = "Monitor growth, consider cleanup"
        else:
            status = "healthy"
            action = "No action needed"

        return JSONResponse({
            "status": status,
            "monthly_cost_usd": round(monthly_cost, 2),
            "total_documents": summary.get("total_documents", 0),
            "total_size_mb": summary.get("total_size_mb", 0),
            "action": action,
            "warnings": warnings,
            "cleanup_endpoint": "/scheduled/data-cleanup?dry_run=true",
            "full_stats_endpoint": "/health/firestore-costs",
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "status": "unknown"}
        )


# ========== RATE LIMIT MANAGEMENT ==========

from app.services.rate_limit_service import (
    get_rate_limit_service,
    seed_default_rate_limits,
    DEFAULT_LIMITS
)
from pydantic import BaseModel


class RateLimitUpdate(BaseModel):
    """Request model for updating rate limits"""
    rpm: int = 120
    burst: int = 60
    plan: str = "trial"
    enabled: bool = True


@router.get("/health/rate-limits")
async def get_rate_limits():
    """
    Get current rate limit configurations.

    Returns default limits and instructions for customization.
    """
    try:
        firestore_manager = get_firestore_manager()

        # Get defaults from Firestore
        defaults = await firestore_manager.get_document("rate_limits", "defaults")

        # Get any org-specific overrides
        overrides = await firestore_manager.get_collection("rate_limits", limit=50)
        org_overrides = [o for o in overrides if o.get("id") != "defaults"]

        return JSONResponse({
            "defaults": defaults or {k: {"rpm": v.requests_per_minute, "burst": v.burst_limit, "plan": k}
                                     for k, v in DEFAULT_LIMITS.items()},
            "org_overrides": org_overrides,
            "hardcoded_fallbacks": {k: {"rpm": v.requests_per_minute, "burst": v.burst_limit}
                                    for k, v in DEFAULT_LIMITS.items()},
            "usage": {
                "to_update_defaults": "POST /health/rate-limits/defaults",
                "to_set_org_limit": "POST /health/rate-limits/org/{org_id}",
                "to_upgrade_org": "Set higher rpm/burst for paying customers",
            }
        })

    except Exception as e:
        logger.error(f"Error getting rate limits: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@router.post("/health/rate-limits/seed")
async def seed_rate_limits(
    authorization: Optional[str] = Header(None),
    x_scheduler_secret: Optional[str] = Header(None, alias="X-Scheduler-Secret"),
):
    """
    Seed default rate limits to Firestore.

    Run once to initialize, or to reset to defaults.
    """
    if not _verify_scheduler_auth(authorization) and not _verify_scheduler_secret(x_scheduler_secret):
        raise HTTPException(status_code=401, detail="Unauthorized")

    success = await seed_default_rate_limits()

    if success:
        return JSONResponse({"status": "success", "message": "Default rate limits seeded"})
    else:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Failed to seed rate limits"}
        )


@router.post("/health/rate-limits/org/{org_id}")
async def set_org_rate_limit(
    org_id: str,
    config: RateLimitUpdate,
    authorization: Optional[str] = Header(None),
    x_scheduler_secret: Optional[str] = Header(None, alias="X-Scheduler-Secret"),
):
    """
    Set custom rate limits for a specific organization.

    Use this when a company upgrades their plan.

    Example:
        POST /health/rate-limits/org/acme-corp
        {"rpm": 600, "burst": 200, "plan": "pro", "enabled": true}
    """
    if not _verify_scheduler_auth(authorization) and not _verify_scheduler_secret(x_scheduler_secret):
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        firestore_manager = get_firestore_manager()

        limit_data = {
            "org_id": org_id,
            "rpm": config.rpm,
            "burst": config.burst,
            "plan": config.plan,
            "enabled": config.enabled,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        await firestore_manager.set_document("rate_limits", org_id, limit_data)

        logger.info(f"Set rate limits for org {org_id}: {config.rpm} rpm, {config.plan} plan")

        return JSONResponse({
            "status": "success",
            "org_id": org_id,
            "config": limit_data,
            "message": f"Rate limits updated for {org_id}"
        })

    except Exception as e:
        logger.error(f"Error setting rate limits for {org_id}: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
