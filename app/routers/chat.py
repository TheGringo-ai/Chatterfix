"""
Fix-it-Fred Chat Router
Provides AI-powered maintenance consulting endpoints
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.ai_service import get_maintenance_solution

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Fix-it-Fred AI"])

class MaintenanceConsultationRequest(BaseModel):
    """Request model for maintenance consultation"""
    problem_description: str = Field(
        ..., 
        description="Detailed description of the maintenance issue",
        example="Hydraulic pump is overheating and making loud noises"
    )
    equipment_type: Optional[str] = Field(
        None,
        description="Type of equipment (pump, motor, conveyor, etc.)",
        example="Hydraulic Pump"
    )
    priority: Optional[str] = Field(
        None,
        description="Issue priority level",
        example="High"
    )
    location: Optional[str] = Field(
        None,
        description="Equipment location",
        example="Production Line A"
    )

class MaintenanceConsultationResponse(BaseModel):
    """Response model for maintenance consultation"""
    success: bool
    fred_says: Optional[str] = None
    problem: str
    equipment_type: Optional[str] = None
    priority: Optional[str] = None
    model_used: Optional[str] = None
    response_type: str
    error: Optional[str] = None
    note: Optional[str] = None

@router.post("/consult", response_model=MaintenanceConsultationResponse)
async def consult_fix_it_fred(request: MaintenanceConsultationRequest):
    """
    🔧 Consult Fix-it-Fred for maintenance solutions
    
    Send a maintenance problem to Fred, our veteran AI maintenance technician.
    Fred will provide safety-first, practical solutions with prevention tips.
    
    **Example Problems to Try:**
    - "Conveyor belt is vibrating excessively during operation"
    - "Electric motor is running hot and tripping breakers"  
    - "Hydraulic pump pressure is dropping unexpectedly"
    - "Air compressor is cycling too frequently"
    """
    try:
        logger.info(f"Fix-it-Fred consultation request: {request.problem_description[:50]}...")
        
        # Get AI-powered solution from Fix-it-Fred
        solution = await get_maintenance_solution(
            problem_description=request.problem_description,
            equipment_type=request.equipment_type,
            priority=request.priority
        )
        
        # Log the consultation for analytics
        logger.info(f"Fix-it-Fred response generated (type: {solution.get('response_type')})")
        
        return MaintenanceConsultationResponse(**solution)
        
    except Exception as e:
        logger.error(f"Error in Fix-it-Fred consultation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Fred encountered an error: {str(e)}"
        )

@router.get("/health")
async def fred_health_check():
    """
    🔧 Check Fix-it-Fred's availability status
    """
    try:
        from app.services.ai_service import fix_it_fred_service
        
        has_openai = fix_it_fred_service.client is not None
        
        return {
            "fred_status": "ready" if has_openai else "demo_mode",
            "ai_enabled": has_openai,
            "message": "Fred is ready to help!" if has_openai else "Fred is in demo mode - configure OPENAI_API_KEY for full AI",
            "capabilities": [
                "Safety-first troubleshooting",
                "Root cause analysis", 
                "Preventive maintenance tips",
                "Tool recommendations",
                "Escalation guidance"
            ]
        }
        
    except Exception as e:
        logger.error(f"Fred health check failed: {e}")
        return {
            "fred_status": "error",
            "ai_enabled": False,
            "message": f"Fred is having issues: {str(e)}"
        }

@router.get("/examples")
async def get_consultation_examples():
    """
    🔧 Get example maintenance problems to consult Fred about
    """
    return {
        "examples": [
            {
                "category": "Mechanical",
                "problems": [
                    "Conveyor belt is making grinding noises",
                    "Bearing temperature is running high on motor #3", 
                    "Gearbox oil is leaking from the seal",
                    "Chain drive is skipping teeth under load"
                ]
            },
            {
                "category": "Hydraulic", 
                "problems": [
                    "Hydraulic pump pressure keeps dropping",
                    "Cylinder is moving too slowly",
                    "Hydraulic fluid is foaming excessively",
                    "Relief valve is chattering during operation"
                ]
            },
            {
                "category": "Electrical",
                "problems": [
                    "Motor starter is tripping on overload",
                    "VFD showing communication faults",
                    "Control panel breaker keeps tripping",
                    "Sensor readings are erratic and unstable"
                ]
            },
            {
                "category": "HVAC",
                "problems": [
                    "Air handler fan is vibrating severely", 
                    "Chiller is short cycling frequently",
                    "Ductwork has excessive condensation",
                    "Building pressure is not maintaining setpoint"
                ]
            }
        ],
        "tips": [
            "Be specific about symptoms and conditions",
            "Include equipment type and model if known", 
            "Mention when the problem started",
            "Note any recent maintenance or changes"
        ]
    }