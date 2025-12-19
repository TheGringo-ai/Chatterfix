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


def _verify_scheduler_auth(authorization: Optional[str]) -> bool:
    """
    Verify Cloud Scheduler OIDC token.

    In production, Cloud Scheduler sends an OIDC token in the Authorization header.
    For local development, we allow requests without auth or with a dev token.
    """
    env = os.getenv("ENVIRONMENT", "development").lower()

    # In development, allow unauthenticated requests for testing
    if env in ["development", "dev", "local"]:
        return True

    # In production, require authorization header
    if not authorization:
        return False

    # Cloud Scheduler sends "Bearer <token>"
    if authorization.startswith("Bearer "):
        # In a full implementation, verify the OIDC token with Google
        # For now, we trust that Cloud Run's built-in auth handles this
        return True

    return False


@router.post("/scheduled/pm-generation")
async def scheduled_pm_generation(
    days_ahead: int = Query(30, description="Days to generate PM for"),
    dry_run: bool = Query(False, description="If true, don't create actual work orders"),
    authorization: Optional[str] = Header(None),
):
    """
    Cloud Scheduler endpoint for automated PM work order generation.

    This endpoint iterates through all organizations with active PM rules
    and generates work orders for due maintenance tasks.

    Security: Protected by Cloud Run IAM + OIDC token from Cloud Scheduler.

    Setup Cloud Scheduler job:
    ```bash
    gcloud scheduler jobs create http pm-daily-generation \
      --location=us-central1 \
      --schedule="0 6 * * *" \
      --uri="https://chatterfix.com/scheduled/pm-generation" \
      --http-method=POST \
      --oidc-service-account-email=YOUR_SA@PROJECT.iam.gserviceaccount.com \
      --oidc-token-audience="https://chatterfix.com"
    ```
    """
    start_time = time.time()

    # Verify scheduler authentication
    if not _verify_scheduler_auth(authorization):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized - Cloud Scheduler OIDC token required",
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
):
    """
    Cloud Scheduler endpoint for checking meter thresholds and triggering alerts.

    This endpoint checks all asset meters across organizations for threshold
    violations and can trigger condition-based maintenance work orders.

    Setup Cloud Scheduler job (every 4 hours):
    ```bash
    gcloud scheduler jobs create http meter-threshold-check \
      --location=us-central1 \
      --schedule="0 */4 * * *" \
      --uri="https://chatterfix.com/scheduled/meter-threshold-check" \
      --http-method=POST \
      --oidc-service-account-email=YOUR_SA@PROJECT.iam.gserviceaccount.com
    ```
    """
    start_time = time.time()

    if not _verify_scheduler_auth(authorization):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized - Cloud Scheduler OIDC token required",
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
