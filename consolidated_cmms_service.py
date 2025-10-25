#!/usr/bin/env python3
"""
ChatterFix Consolidated CMMS Service
Combines work orders, assets, and parts into one deployment with modular architecture
"""

import os
import uvicorn
from datetime import datetime
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Import modular routers
from modules.work_orders import router as work_orders_router
from modules.assets import router as assets_router  
from modules.parts import router as parts_router
from modules.shared import get_health_status, verify_api_key, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW

# Import AI modules
from modules.predictive_maintenance import get_predictive_maintenance_data, get_asset_risk_summary
from modules.ai_insights import get_ai_summary, get_asset_specific_insights
from modules.anomaly_detection import monitor_cmms_metrics, get_alerts

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="ChatterFix Consolidated CMMS Service",
    description="Unified work orders, assets, and parts management",
    version="1.0.0"
)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add SlowAPI middleware for rate limiting
app.add_middleware(SlowAPIMiddleware)

# Include module routers
app.include_router(work_orders_router, prefix="/work_orders", tags=["Work Orders"])
app.include_router(assets_router, prefix="/assets", tags=["Assets"])
app.include_router(parts_router, prefix="/parts", tags=["Parts"])

@app.get("/health")
@limiter.limit(f"{RATE_LIMIT_REQUESTS}/minute")
async def health_check(request: Request, authenticated: bool = Depends(verify_api_key)):
    """Consolidated health check with authentication and rate limiting"""
    return {
        "status": "healthy",
        "service": "consolidated_cmms",
        "version": "1.0.0",
        "modules": ["work_orders", "assets", "parts"],
        "rate_limit": f"{RATE_LIMIT_REQUESTS} requests per minute",
        **get_health_status()
    }

@app.get("/validate")
@limiter.limit(f"{RATE_LIMIT_REQUESTS}/minute")
async def validate_system(request: Request, authenticated: bool = Depends(verify_api_key)):
    """Comprehensive system validation endpoint for CI/CD pipeline"""
    from modules.work_orders import get_sample_data as get_work_orders_sample
    from modules.assets import get_sample_data as get_assets_sample  
    from modules.parts import get_sample_data as get_parts_sample
    
    validation_results = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "healthy",
        "service": "consolidated_cmms",
        "version": "1.0.0",
        "modules": {}
    }
    
    # Test each module's data availability
    try:
        # Work Orders validation
        wo_data = get_work_orders_sample()
        validation_results["modules"]["work_orders"] = {
            "status": "operational",
            "data_count": len(wo_data.get("work_orders", [])),
            "last_check": datetime.now().isoformat()
        }
    except Exception as e:
        validation_results["modules"]["work_orders"] = {
            "status": "error",
            "error": str(e),
            "last_check": datetime.now().isoformat()
        }
        validation_results["overall_status"] = "degraded"
    
    try:
        # Assets validation
        assets_data = get_assets_sample()
        validation_results["modules"]["assets"] = {
            "status": "operational", 
            "data_count": len(assets_data.get("assets", [])),
            "last_check": datetime.now().isoformat()
        }
    except Exception as e:
        validation_results["modules"]["assets"] = {
            "status": "error",
            "error": str(e),
            "last_check": datetime.now().isoformat()
        }
        validation_results["overall_status"] = "degraded"
    
    try:
        # Parts validation
        parts_data = get_parts_sample()
        validation_results["modules"]["parts"] = {
            "status": "operational",
            "data_count": len(parts_data.get("parts", [])),
            "last_check": datetime.now().isoformat()
        }
    except Exception as e:
        validation_results["modules"]["parts"] = {
            "status": "error", 
            "error": str(e),
            "last_check": datetime.now().isoformat()
        }
        validation_results["overall_status"] = "degraded"
    
    # Add system health info
    validation_results["system"] = get_health_status()
    
    return validation_results

@app.post("/api/analytics/log")
@limiter.limit(f"{RATE_LIMIT_REQUESTS * 2}/minute")  # Higher limit for analytics
async def log_analytics(request: Request, authenticated: bool = Depends(verify_api_key)):
    """Log anonymized usage analytics"""
    try:
        body = await request.json()
        
        # Required fields validation
        required_fields = ["endpoint", "action", "timestamp"]
        if not all(field in body for field in required_fields):
            raise HTTPException(status_code=400, detail="Missing required fields: endpoint, action, timestamp")
        
        # Anonymize and log analytics data
        analytics_entry = {
            "timestamp": body["timestamp"],
            "endpoint": body["endpoint"],
            "action": body["action"],
            "user_agent": request.headers.get("user-agent", "unknown")[:100],  # Truncate for privacy
            "ip_hash": hash(request.client.host) if request.client else None,  # Hash IP for privacy
            "session_id": body.get("session_id", "anonymous"),
            "duration_ms": body.get("duration_ms"),
            "status": body.get("status", "success")
        }
        
        # In production, this would go to BigQuery, Analytics, or a database
        # For now, we'll log it (in production you'd store this properly)
        logger.info(f"Analytics: {analytics_entry}")
        
        return {
            "success": True,
            "message": "Analytics logged successfully",
            "logged_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Analytics logging error: {e}")
        raise HTTPException(status_code=500, detail="Failed to log analytics")

@app.get("/predictive_maintenance")
@limiter.limit(f"{RATE_LIMIT_REQUESTS}/minute")
async def predictive_maintenance_endpoint(request: Request, authenticated: bool = Depends(verify_api_key)):
    """AI-powered predictive maintenance analysis"""
    try:
        # Get sample asset data for prediction
        from modules.assets import get_sample_data as get_assets_data
        assets_response = get_assets_data()
        assets = assets_response.get("assets", [])
        
        if not assets:
            return {
                "predictions": [],
                "summary": get_asset_risk_summary(),
                "message": "No assets available for analysis",
                "generated_at": datetime.now().isoformat()
            }
        
        # Generate predictions
        predictions = get_predictive_maintenance_data(assets)
        summary = get_asset_risk_summary()
        
        # Log analytics
        try:
            logger.info(f"Predictive maintenance analysis: {len(predictions)} predictions generated")
        except:
            pass
        
        return {
            "predictions": predictions,
            "summary": summary,
            "total_assets_analyzed": len(assets),
            "high_risk_assets": len([p for p in predictions if p.get("failure_risk", 0) > 0.7]),
            "generated_at": datetime.now().isoformat(),
            "model_version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Predictive maintenance error: {e}")
        raise HTTPException(status_code=500, detail=f"Predictive maintenance analysis failed: {str(e)}")

@app.get("/insights/summary")
@limiter.limit(f"{RATE_LIMIT_REQUESTS}/minute")
async def ai_insights_summary(request: Request, authenticated: bool = Depends(verify_api_key)):
    """AI-generated operational insights and summary"""
    try:
        # Get data from all modules
        from modules.work_orders import get_sample_data as get_work_orders_data
        from modules.assets import get_sample_data as get_assets_data
        from modules.parts import get_sample_data as get_parts_data
        
        work_orders_response = get_work_orders_data()
        assets_response = get_assets_data()
        parts_response = get_parts_data()
        
        work_orders = work_orders_response.get("work_orders", [])
        assets = assets_response.get("assets", [])
        parts = parts_response.get("parts", [])
        
        # Generate AI insights
        ai_summary = await get_ai_summary(work_orders, assets, parts)
        
        # Get predictive maintenance data for asset insights
        predictions = get_predictive_maintenance_data(assets)
        asset_insights = await get_asset_specific_insights(assets, predictions)
        
        return {
            "summary": ai_summary,
            "asset_insights": asset_insights,
            "data_sources": {
                "work_orders": len(work_orders),
                "assets": len(assets),
                "parts": len(parts)
            },
            "generated_at": datetime.now().isoformat(),
            "ai_powered": True
        }
        
    except Exception as e:
        logger.error(f"AI insights error: {e}")
        # Fallback response
        return {
            "summary": {
                "summary": "AI insights temporarily unavailable. Operations are continuing normally.",
                "recommendations": {
                    "immediate_actions": ["Continue standard maintenance procedures"],
                    "weekly_priorities": ["Monitor system performance"],
                    "optimization_opportunities": ["Review maintenance workflows"],
                    "cost_reduction_tips": ["Optimize resource scheduling"]
                },
                "generated_by": "fallback"
            },
            "asset_insights": [],
            "error": str(e),
            "generated_at": datetime.now().isoformat()
        }

@app.get("/alerts")
@limiter.limit(f"{RATE_LIMIT_REQUESTS}/minute")
async def anomaly_alerts(request: Request, authenticated: bool = Depends(verify_api_key)):
    """Current anomaly alerts and system status"""
    try:
        # Get current data for anomaly detection
        from modules.work_orders import get_sample_data as get_work_orders_data
        from modules.assets import get_sample_data as get_assets_data
        from modules.parts import get_sample_data as get_parts_data
        
        work_orders_response = get_work_orders_data()
        assets_response = get_assets_data()
        parts_response = get_parts_data()
        
        work_orders = work_orders_response.get("work_orders", [])
        assets = assets_response.get("assets", [])
        parts = parts_response.get("parts", [])
        
        # Monitor metrics and detect anomalies
        monitoring_result = monitor_cmms_metrics(work_orders, assets, parts)
        
        # Get current alerts
        alerts = get_alerts()
        
        return {
            "alerts": alerts,
            "anomaly_monitoring": monitoring_result,
            "system_health": {
                "overall_status": alerts.get("system_status", "normal"),
                "metrics_monitored": len(monitoring_result.get("metric_statuses", {})),
                "active_anomalies": len(monitoring_result.get("current_anomalies", []))
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Anomaly detection error: {e}")
        return {
            "alerts": {
                "alert_summary": {"critical": 0, "high": 0, "medium": 0, "total": 0},
                "system_status": "unknown",
                "message": "Anomaly detection temporarily unavailable"
            },
            "error": str(e),
            "generated_at": datetime.now().isoformat()
        }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "ChatterFix Consolidated CMMS",
        "version": "1.0.0",
        "ai_powered": True,
        "endpoints": {
            "work_orders": "/work_orders",
            "assets": "/assets", 
            "parts": "/parts",
            "health": "/health",
            "validate": "/validate",
            "predictive_maintenance": "/predictive_maintenance",
            "ai_insights": "/insights/summary",
            "anomaly_alerts": "/alerts",
            "analytics": "/api/analytics/log"
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)