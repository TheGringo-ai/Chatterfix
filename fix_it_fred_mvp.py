#!/usr/bin/env python3
"""
Fix It Fred MVP - AI Brain for Everyone
DIY, Car Maintenance, Home Projects, Workshop Planning & More
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
    title="Fix It Fred MVP",
    description="AI-Powered Assistant for DIY, Maintenance, and Projects",
    version="1.0.0"
)

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Fix It Fred AI Brain Integration
FIX_IT_FRED_BRAIN_URL = "http://localhost:9000"
FALLBACK_AI_URL = "http://localhost:8081"

class ChatRequest(BaseModel):
    message: str
    user_type: Optional[str] = "diy"  # diy, car_owner, homeowner, pro_tech, workshop
    context: Optional[str] = None
    project_type: Optional[str] = None

class Project(BaseModel):
    title: str
    description: str
    category: str  # car, home, workshop, electronics, etc.
    difficulty: str = "medium"
    estimated_time: Optional[str] = None

# Sample data for demonstration
sample_data = {
    "projects": [
        {"id": 1, "title": "Oil Change", "category": "car", "difficulty": "easy", "status": "planned", "estimated_time": "30 min"},
        {"id": 2, "title": "Kitchen Faucet Repair", "category": "home", "difficulty": "medium", "status": "in_progress", "estimated_time": "2 hours"},
        {"id": 3, "title": "Workshop Organization", "category": "workshop", "difficulty": "easy", "status": "completed", "estimated_time": "4 hours"},
        {"id": 4, "title": "Replace Brake Pads", "category": "car", "difficulty": "hard", "status": "planned", "estimated_time": "3 hours"},
    ],
    "reminders": [
        {"type": "car", "task": "Oil change due", "due": "Next week", "priority": "medium"},
        {"type": "home", "task": "HVAC filter replacement", "due": "This month", "priority": "low"},
        {"type": "workshop", "task": "Tool calibration", "due": "Overdue", "priority": "high"},
    ],
    "stats": {
        "projects_completed": 12,
        "money_saved": 2847,
        "skills_learned": 8,
        "time_invested": 45
    }
}

# Fix It Fred AI Helper
async def get_fix_it_fred_help(message: str, user_type: str, context: str = None, project_type: str = None):
    """Get help from Fix It Fred AI brain"""
    try:
        response = requests.post(
            f"{FIX_IT_FRED_BRAIN_URL}/api/ai/chat",
            json={
                "message": message,
                "user_type": user_type,
                "context": context or f"Fix It Fred {user_type} assistance",
                "project_type": project_type,
                "system": "fix_it_fred_mvp"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("response", "Fix It Fred is here to help!"),
                "recommendations": data.get("recommendations", []),
                "safety_tips": data.get("safety_tips", []),
                "tools_needed": data.get("tools_needed", []),
                "estimated_time": data.get("estimated_time"),
                "difficulty": data.get("difficulty"),
                "cost_estimate": data.get("cost_estimate")
            }
        else:
            # Fallback response
            return {
                "success": True,
                "response": f"I'm Fix It Fred! I'd be happy to help with your {project_type or user_type} project. Could you provide more details about what you're working on?",
                "recommendations": ["Provide more project details", "Check safety requirements", "Gather necessary tools"],
                "agent_type": "fix_it_fred_fallback"
            }
            
    except Exception as e:
        logger.error(f"Fix It Fred error: {e}")
        return {
            "success": True,
            "response": "Hi! I'm Fix It Fred, your AI assistant for DIY projects, car maintenance, and home repairs. How can I help you today?",
            "agent_type": "fix_it_fred_offline"
        }

# Main Fix It Fred Dashboard
@app.get("/", response_class=HTMLResponse)
async def fix_it_fred_dashboard(request: Request):
    """Main Fix It Fred Dashboard for everyone"""
    return templates.TemplateResponse("fix_it_fred_dashboard.html", {
        "request": request,
        "projects": sample_data["projects"],
        "reminders": sample_data["reminders"],
        "stats": sample_data["stats"],
        "page_title": "Fix It Fred - Your AI Assistant"
    })

# Car Maintenance Interface
@app.get("/car", response_class=HTMLResponse)
async def car_maintenance(request: Request):
    """Car maintenance and automotive help"""
    car_projects = [p for p in sample_data["projects"] if p["category"] == "car"]
    return templates.TemplateResponse("fix_it_fred_car.html", {
        "request": request,
        "car_projects": car_projects,
        "stats": sample_data["stats"],
        "page_title": "Fix It Fred - Car Maintenance"
    })

# Home Projects Interface
@app.get("/home", response_class=HTMLResponse)
async def home_projects(request: Request):
    """Home improvement and repair projects"""
    home_projects = [p for p in sample_data["projects"] if p["category"] == "home"]
    return templates.TemplateResponse("fix_it_fred_home.html", {
        "request": request,
        "home_projects": home_projects,
        "stats": sample_data["stats"],
        "page_title": "Fix It Fred - Home Projects"
    })

# Workshop & Tools Interface
@app.get("/workshop", response_class=HTMLResponse)
async def workshop_tools(request: Request):
    """Workshop organization and tool management"""
    workshop_projects = [p for p in sample_data["projects"] if p["category"] == "workshop"]
    return templates.TemplateResponse("fix_it_fred_workshop.html", {
        "request": request,
        "workshop_projects": workshop_projects,
        "stats": sample_data["stats"],
        "page_title": "Fix It Fred - Workshop & Tools"
    })

# DIY Projects Interface
@app.get("/diy", response_class=HTMLResponse)
async def diy_projects(request: Request):
    """DIY projects and maker activities"""
    return templates.TemplateResponse("fix_it_fred_diy.html", {
        "request": request,
        "projects": sample_data["projects"],
        "stats": sample_data["stats"],
        "page_title": "Fix It Fred - DIY Projects"
    })

# Professional Technician Interface (Bridge to ChatterFix)
@app.get("/pro", response_class=HTMLResponse)
async def pro_tech_interface(request: Request):
    """Professional technician tools - bridge to ChatterFix CMMS"""
    return templates.TemplateResponse("fix_it_fred_pro.html", {
        "request": request,
        "projects": sample_data["projects"],
        "stats": sample_data["stats"],
        "page_title": "Fix It Fred - Professional Tools"
    })

# AI Chat API
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Fix It Fred AI chat endpoint for all user types"""
    try:
        ai_response = await get_fix_it_fred_help(
            message=request.message,
            user_type=request.user_type,
            context=request.context,
            project_type=request.project_type
        )
        
        return {
            "success": True,
            "response": ai_response["response"],
            "recommendations": ai_response.get("recommendations", []),
            "safety_tips": ai_response.get("safety_tips", []),
            "tools_needed": ai_response.get("tools_needed", []),
            "estimated_time": ai_response.get("estimated_time"),
            "difficulty": ai_response.get("difficulty"),
            "cost_estimate": ai_response.get("cost_estimate"),
            "agent_type": "fix_it_fred",
            "user_type": request.user_type
        }
            
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"success": False, "error": str(e)}

# Project Management API
@app.post("/api/projects")
async def create_project(project: Project):
    """Create new project with Fix It Fred AI assistance"""
    try:
        # Get AI guidance for the project
        ai_response = await get_fix_it_fred_help(
            message=f"Help me plan this project: {project.title} - {project.description}",
            user_type="diy",
            context="Project planning",
            project_type=project.category
        )
        
        # Create project
        new_id = len(sample_data["projects"]) + 1
        new_project = {
            "id": new_id,
            "title": project.title,
            "description": project.description,
            "category": project.category,
            "difficulty": project.difficulty,
            "status": "planned",
            "estimated_time": project.estimated_time or ai_response.get("estimated_time", "TBD"),
            "ai_guidance": ai_response.get("response"),
            "tools_needed": ai_response.get("tools_needed", []),
            "safety_tips": ai_response.get("safety_tips", [])
        }
        
        sample_data["projects"].append(new_project)
        
        return {"success": True, "project": new_project, "ai_guidance": ai_response}
        
    except Exception as e:
        logger.error(f"Project creation error: {e}")
        return {"success": False, "error": str(e)}

# Quick Help API
@app.get("/api/quick-help/{category}")
async def quick_help(category: str, question: str = None):
    """Quick help for common questions"""
    try:
        if not question:
            # Provide category-specific quick tips
            quick_tips = {
                "car": "I can help with oil changes, brake repairs, tire maintenance, engine diagnostics, and more!",
                "home": "I assist with plumbing fixes, electrical repairs, HVAC maintenance, and home improvements!",
                "workshop": "I help organize tools, plan projects, manage inventory, and optimize your workspace!",
                "diy": "I guide through DIY projects, recommend tools, provide step-by-step instructions, and safety tips!"
            }
            return {"success": True, "response": quick_tips.get(category, "How can I help you today?")}
        
        ai_response = await get_fix_it_fred_help(
            message=question,
            user_type="diy",
            context=f"Quick help - {category}",
            project_type=category
        )
        
        return ai_response
        
    except Exception as e:
        logger.error(f"Quick help error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Fix It Fred MVP",
        "version": "1.0.0",
        "modules": ["car", "home", "workshop", "diy", "pro"],
        "ai_brain": "fix_it_fred",
        "target_audience": "Everyone - DIY enthusiasts, car owners, homeowners, professionals"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8082)))