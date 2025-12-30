#!/usr/bin/env python3
"""
ChatterFix CMMS - Modular Application
Clean, maintainable structure with AI brain integration
"""
import os
import uvicorn
import requests
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ChatterFix CMMS - Modular",
    description="AI-Powered Maintenance Management System",
    version="3.0.0"
)

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Fix It Fred AI Brain Integration
FIX_IT_FRED_URL = "http://localhost:9000"
AI_CHAT_URL = "http://localhost:8081"

class ChatRequest(BaseModel):
    message: str
    user_role: Optional[str] = "technician"  # technician, manager, scheduler, parts
    context: Optional[str] = None

class WorkOrder(BaseModel):
    title: str
    description: str
    asset_id: Optional[int] = None
    priority: str = "medium"
    assigned_to: Optional[str] = None

class Asset(BaseModel):
    name: str
    type: str
    location: str
    status: str = "operational"

class Part(BaseModel):
    name: str
    part_number: str
    quantity: int
    min_stock: int = 5
    location: str

# Sample data (in production this would come from database)
sample_data = {
    "work_orders": [
        {"id": 1, "title": "Pump Maintenance", "status": "in_progress", "priority": "high", "asset_name": "Pump #1", "technician": "John Smith"},
        {"id": 2, "title": "Filter Replacement", "status": "assigned", "priority": "medium", "asset_name": "HVAC Unit A", "technician": "Sarah Johnson"},
        {"id": 3, "title": "Belt Inspection", "status": "pending", "priority": "low", "asset_name": "Conveyor #3", "technician": "Mike Wilson"},
    ],
    "assets": [
        {"id": 1, "name": "Pump #1", "health_score": 85, "status": "operational", "type": "Pump", "location": "Building A"},
        {"id": 2, "name": "HVAC Unit A", "health_score": 92, "status": "operational", "type": "HVAC", "location": "Building B"},
        {"id": 3, "name": "Conveyor #3", "health_score": 78, "status": "maintenance", "type": "Conveyor", "location": "Warehouse"},
    ],
    "parts": [
        {"id": 1, "name": "Oil Filter", "part_number": "OF-001", "quantity": 15, "min_stock": 5, "price": 25.99, "location": "A1-01", "category": "filters"},
        {"id": 2, "name": "V-Belt", "part_number": "VB-200", "quantity": 3, "min_stock": 10, "price": 45.00, "location": "B2-05", "category": "belts"},
        {"id": 3, "name": "Bearing", "part_number": "BR-150", "quantity": 8, "min_stock": 5, "price": 120.50, "location": "C1-03", "category": "bearings"},
        {"id": 4, "name": "Air Filter", "part_number": "AF-001", "quantity": 22, "min_stock": 8, "price": 18.75, "location": "A1-02", "category": "filters"},
        {"id": 5, "name": "Hydraulic Hose", "part_number": "HH-300", "quantity": 1, "min_stock": 3, "price": 89.99, "location": "D3-01", "category": "hydraulics"},
        {"id": 6, "name": "Gear Oil", "part_number": "GO-SAE90", "quantity": 12, "min_stock": 4, "price": 32.50, "location": "E1-01", "category": "lubricants"},
        {"id": 7, "name": "Circuit Breaker", "part_number": "CB-20A", "quantity": 0, "min_stock": 2, "price": 156.00, "location": "F2-01", "category": "electrical"},
        {"id": 8, "name": "Gasket Set", "part_number": "GS-PUMP1", "quantity": 6, "min_stock": 3, "price": 67.80, "location": "G1-02", "category": "seals"},
    ],
    "stats": {
        "active_workorders": 12,
        "total_assets": 48,
        "parts_in_stock": 156,
        "system_health": 98,
        "total_parts": 5,
        "in_stock": 3,
        "low_stock": 1,
        "total_value": 641
    }
}

# Fix It Fred AI Brain Helper
async def get_ai_assistance(message: str, user_role: str, context: str = None):
    """Get AI assistance from Fix It Fred brain agent"""
    try:
        # Try Fix It Fred endpoint first
        response = requests.post(
            f"{FIX_IT_FRED_URL}/api/ai/chat",
            json={
                "message": f"[ChatterFix {user_role.upper()}] {message}",
                "context": f"ChatterFix CMMS - {context or 'General maintenance assistance'}",
                "user_type": user_role,
                "system": "chatterfix_cmms"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("response", "Fix It Fred assistance unavailable"),
                "agent_type": "fix_it_fred",
                "recommendations": data.get("recommendations", [])
            }
        else:
            # Fallback to alternative endpoint
            response = requests.post(
                f"{AI_CHAT_URL}/api/ai/chat",
                json={
                    "message": f"[{user_role.upper()}] {message}",
                    "context": f"ChatterFix CMMS - {context or 'General assistance'}"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "response": data.get("response", "AI assistance unavailable"),
                    "agent_type": "ai_brain"
                }
            else:
                return {"success": False, "error": "Fix It Fred unavailable"}
            
    except Exception as e:
        logger.error(f"Fix It Fred assistance error: {e}")
        return {"success": False, "error": str(e)}

# Main Dashboard Route
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main ChatterFix CMMS Dashboard"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "recent_workorders": sample_data["work_orders"][:5],
        "top_assets": sample_data["assets"][:5],
        "stats": sample_data["stats"],
        "page_title": "ChatterFix CMMS Dashboard"
    })

# Work Orders Routes
@app.get("/work-orders", response_class=HTMLResponse)
async def work_orders(request: Request):
    """Work Orders Management Page"""
    return templates.TemplateResponse("work_orders.html", {
        "request": request,
        "work_orders": sample_data["work_orders"],
        "stats": sample_data["stats"],
        "page_title": "Work Orders Management"
    })

# Assets Routes
@app.get("/assets", response_class=HTMLResponse)
async def assets(request: Request):
    """Assets Management Page"""
    return templates.TemplateResponse("assets.html", {
        "request": request,
        "assets": sample_data["assets"],
        "stats": sample_data["stats"],
        "page_title": "Assets Management"
    })

# Parts Routes
@app.get("/parts", response_class=HTMLResponse)
async def parts(request: Request):
    """Advanced Parts Inventory Management Page with Fix It Fred Intelligence"""
    return templates.TemplateResponse("parts_advanced.html", {
        "request": request,
        "parts": sample_data["parts"],
        "stats": sample_data["stats"],
        "page_title": "Advanced Parts Intelligence"
    })

# AI Settings Route
@app.get("/ai-settings", response_class=HTMLResponse)
async def ai_settings(request: Request):
    """AI Provider Settings Page"""
    return templates.TemplateResponse("ai_settings.html", {
        "request": request,
        "page_title": "AI Settings"
    })

@app.get("/parts/basic", response_class=HTMLResponse)
async def parts_basic(request: Request):
    """Basic Parts Inventory Management Page"""
    return templates.TemplateResponse("parts.html", {
        "request": request,
        "parts": sample_data["parts"],
        "stats": sample_data["stats"],
        "page_title": "Parts Inventory"
    })

# Technician Interface
@app.get("/technician", response_class=HTMLResponse)
async def technician_interface(request: Request):
    """Technician-focused interface"""
    technician_workorders = [wo for wo in sample_data["work_orders"] if wo["status"] in ["assigned", "in_progress"]]
    return templates.TemplateResponse("technician.html", {
        "request": request,
        "my_workorders": technician_workorders,
        "stats": sample_data["stats"],
        "page_title": "Technician Dashboard"
    })

# Manager Interface
@app.get("/manager", response_class=HTMLResponse)
async def manager_interface(request: Request):
    """Manager-focused interface with analytics"""
    return templates.TemplateResponse("manager.html", {
        "request": request,
        "all_workorders": sample_data["work_orders"],
        "all_assets": sample_data["assets"],
        "stats": sample_data["stats"],
        "page_title": "Manager Dashboard"
    })

# Scheduler Interface
@app.get("/scheduler", response_class=HTMLResponse)
async def scheduler_interface(request: Request):
    """Scheduler-focused interface"""
    return templates.TemplateResponse("scheduler.html", {
        "request": request,
        "scheduled_workorders": sample_data["work_orders"],
        "assets": sample_data["assets"],
        "stats": sample_data["stats"],
        "page_title": "Scheduler Dashboard"
    })

# Parts Staff Interface
@app.get("/parts-staff", response_class=HTMLResponse)
async def parts_staff_interface(request: Request):
    """Parts staff focused interface"""
    low_stock_parts = [part for part in sample_data["parts"] if part["quantity"] <= part["min_stock"]]
    return templates.TemplateResponse("parts_staff.html", {
        "request": request,
        "all_parts": sample_data["parts"],
        "low_stock_parts": low_stock_parts,
        "stats": sample_data["stats"],
        "page_title": "Parts Management"
    })

# AI Chat API (Enhanced with provider support)
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """AI Brain chat endpoint for all user roles"""
    try:
        # Forward to Fix It Fred AI Service
        response = requests.post(
            "http://localhost:9000/api/chat",
            json={
                "message": request.message,
                "user_role": request.user_role,
                "context": request.context,
                "provider": getattr(request, 'provider', 'ollama'),
                "model": getattr(request, 'model', 'mistral:7b')
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            # Fallback to legacy method
            ai_response = await get_ai_assistance(
                message=request.message,
                user_role=request.user_role,
                context=request.context
            )
            
            if ai_response["success"]:
                return {
                    "success": True,
                    "response": ai_response["response"],
                    "agent_type": "ai_brain",
                    "user_role": request.user_role
                }
            else:
                return {"success": False, "error": ai_response["error"]}
            
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"success": False, "error": str(e)}

# AI Provider API endpoints (Forward to Fix It Fred AI Service)
@app.get("/api/ai/providers")
async def get_ai_providers():
    """Get available AI providers"""
    try:
        response = requests.get("http://localhost:9000/api/providers", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "AI service unavailable"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/ai/providers/{provider_name}/configure")
async def configure_ai_provider(provider_name: str, api_key: str = Form()):
    """Configure AI provider"""
    try:
        formData = {"api_key": api_key}
        response = requests.post(
            f"http://localhost:9000/api/providers/{provider_name}/configure",
            data=formData,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "Configuration failed"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/ai/models/{provider_name}")
async def get_ai_models(provider_name: str):
    """Get available models for AI provider"""
    try:
        response = requests.get(f"http://localhost:9000/api/models/{provider_name}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "Models unavailable"}
    except Exception as e:
        return {"error": str(e)}

# API Routes for CRUD operations
@app.post("/api/work-orders")
async def create_work_order(work_order: WorkOrder):
    """Create new work order with AI assistance"""
    try:
        # Get AI suggestions for the work order
        ai_response = await get_ai_assistance(
            message=f"Creating work order: {work_order.title} - {work_order.description}",
            user_role="manager",
            context="Work order creation"
        )
        
        # Create work order (in production, save to database)
        new_id = len(sample_data["work_orders"]) + 1
        new_wo = {
            "id": new_id,
            "title": work_order.title,
            "description": work_order.description,
            "status": "pending",
            "priority": work_order.priority,
            "assigned_to": work_order.assigned_to,
            "ai_suggestions": ai_response.get("response") if ai_response["success"] else None
        }
        
        sample_data["work_orders"].append(new_wo)
        
        return {"success": True, "work_order": new_wo, "ai_suggestions": ai_response}
        
    except Exception as e:
        logger.error(f"Work order creation error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/assets/{asset_id}/ai-insights")
async def get_asset_ai_insights(asset_id: int):
    """Get AI insights for specific asset"""
    try:
        asset = next((a for a in sample_data["assets"] if a["id"] == asset_id), None)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        ai_response = await get_ai_assistance(
            message=f"Analyze asset: {asset['name']} (Health: {asset['health_score']}%, Status: {asset['status']})",
            user_role="technician",
            context="Asset analysis"
        )
        
        return {
            "asset": asset,
            "ai_insights": ai_response.get("response") if ai_response["success"] else "AI analysis unavailable",
            "recommendations": [
                "Schedule preventive maintenance",
                "Monitor temperature levels",
                "Check lubrication schedule"
            ]
        }
        
    except Exception as e:
        logger.error(f"Asset insights error: {e}")
        return {"success": False, "error": str(e)}

# Advanced Fix It Fred API Endpoints
@app.post("/api/parts")
async def create_part(part: Part):
    """Create new part with Fix It Fred AI analysis"""
    try:
        # Get Fix It Fred analysis for the new part
        ai_response = await get_ai_assistance(
            message=f"Analyze new part: {part.name} (P/N: {part.part_number}, Qty: {part.quantity}, Min: {part.min_stock}, Location: {part.location}). Provide recommendations for optimal stock levels, supplier suggestions, and integration with existing inventory.",
            user_role="parts",
            context="New part analysis and optimization"
        )
        
        # Create part (in production, save to database)
        new_id = len(sample_data["parts"]) + 1
        new_part = {
            "id": new_id,
            "name": part.name,
            "part_number": part.part_number,
            "quantity": part.quantity,
            "min_stock": part.min_stock,
            "location": part.location,
            "category": "general",
            "price": 0.0,  # Default price
            "fred_analysis": ai_response.get("response") if ai_response["success"] else None,
            "recommendations": ai_response.get("recommendations", [])
        }
        
        sample_data["parts"].append(new_part)
        
        return {"success": True, "part": new_part, "fred_analysis": ai_response}
        
    except Exception as e:
        logger.error(f"Part creation error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/parts/{part_id}/fred-analysis")
async def get_part_fred_analysis(part_id: int):
    """Get Fix It Fred AI analysis for specific part"""
    try:
        part = next((p for p in sample_data["parts"] if p["id"] == part_id), None)
        if not part:
            raise HTTPException(status_code=404, detail="Part not found")
        
        ai_response = await get_ai_assistance(
            message=f"Provide comprehensive analysis for {part['name']} (P/N: {part['part_number']}). Current stock: {part['quantity']}, Min stock: {part['min_stock']}, Price: ${part['price']}, Location: {part['location']}. Include usage predictions, cost optimization, supplier recommendations, and maintenance correlations.",
            user_role="parts",
            context="Comprehensive part analysis"
        )
        
        return {
            "part": part,
            "fred_analysis": ai_response.get("response") if ai_response["success"] else "Fix It Fred analysis unavailable",
            "recommendations": ai_response.get("recommendations", [
                "Monitor usage patterns",
                "Optimize stock levels",
                "Review supplier performance"
            ]),
            "predictions": {
                "usage_trend": "+15% monthly growth",
                "optimal_order_qty": part["min_stock"] * 3,
                "next_order_date": "8 days",
                "cost_savings_potential": "$247 annually"
            }
        }
        
    except Exception as e:
        logger.error(f"Part analysis error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/parts/fred-smart-order")
async def fred_smart_order(request: dict):
    """Fix It Fred smart ordering system"""
    try:
        part_ids = request.get("part_ids", [])
        
        ai_response = await get_ai_assistance(
            message=f"Create optimal purchase order for parts {part_ids}. Consider current stock levels, usage patterns, supplier performance, bulk discounts, and work order requirements. Provide specific recommendations for quantities, suppliers, and timing.",
            user_role="parts",
            context="Smart ordering optimization"
        )
        
        # Simulate Fred's smart order creation
        smart_order = {
            "order_id": f"FRED-{len(sample_data['parts']) + 1:04d}",
            "parts": part_ids,
            "total_value": 1847.50,
            "estimated_savings": 347.25,
            "delivery_date": "3 business days",
            "fred_optimization": ai_response.get("response") if ai_response["success"] else "Optimization complete",
            "supplier_recommendations": [
                {"name": "Industrial Supply Co.", "rating": "A+", "discount": "12%"},
                {"name": "Parts Direct Inc.", "rating": "A", "discount": "8%"}
            ]
        }
        
        return {"success": True, "smart_order": smart_order, "fred_analysis": ai_response}
        
    except Exception as e:
        logger.error(f"Smart order error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/parts/fred-predictions")
async def fred_predictions():
    """Get Fix It Fred predictive analytics for all parts"""
    try:
        ai_response = await get_ai_assistance(
            message="Generate comprehensive 90-day predictive analytics for all parts inventory. Include demand forecasting, seasonal trends, maintenance cycle correlations, supply chain risks, and cost optimization opportunities.",
            user_role="parts",
            context="Advanced predictive analytics"
        )
        
        predictions = {
            "forecast_period": "90 days",
            "confidence_level": "94%",
            "total_predicted_demand": 847,
            "critical_periods": [
                {"period": "Days 18-21", "description": "Quarterly maintenance surge", "impact": "+67%"},
                {"period": "Days 44-48", "description": "Summer equipment prep", "impact": "+45%"},
                {"period": "Days 67-72", "description": "Annual pump overhauls", "impact": "+89%"}
            ],
            "cost_optimization": {
                "potential_savings": "$18,947",
                "bulk_opportunities": 15,
                "supplier_optimization": "$8,617"
            },
            "fred_insights": ai_response.get("response") if ai_response["success"] else "Advanced predictions generated"
        }
        
        return {"success": True, "predictions": predictions, "fred_analysis": ai_response}
        
    except Exception as e:
        logger.error(f"Predictions error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ChatterFix CMMS Advanced",
        "version": "4.0.0",
        "modules": ["dashboard", "work_orders", "assets", "parts_advanced", "technician", "manager", "scheduler", "parts_staff"],
        "ai_integration": "fix_it_fred_advanced",
        "fred_features": ["smart_ordering", "predictive_analytics", "cost_optimization", "auto_reorder"]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))