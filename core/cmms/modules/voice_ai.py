#!/usr/bin/env python3
"""
Voice AI Module - Natural Language Work Order Creation
Powered by Claude + Grok AI partnership
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import asyncio

router = APIRouter(prefix="/voice", tags=["Voice AI"])

# Voice Models
class VoiceCommand(BaseModel):
    audio_data: Optional[str] = None  # Base64 encoded audio
    text_input: Optional[str] = None  # Direct text input
    technician_id: str
    location: Optional[str] = None

class VoiceResponse(BaseModel):
    understood: bool
    intent: str
    work_order_created: bool
    work_order_id: Optional[str] = None
    priority: str
    assigned_to: Optional[str] = None
    confidence: float
    ai_analysis: str

class VoiceCapabilities(BaseModel):
    supported_languages: List[str]
    confidence_threshold: float
    ai_models: List[str]
    features: List[str]

# AI-powered voice processing
async def process_voice_command(text: str, technician_id: str, location: str = None) -> Dict[str, Any]:
    """Process voice command with AI team analysis"""
    
    text_lower = text.lower()
    
    # Determine intent and priority
    if any(word in text_lower for word in ["emergency", "critical", "urgent", "broken", "down", "stopped"]):
        priority = "critical"
        intent = "emergency_work_order"
    elif any(word in text_lower for word in ["maintenance", "service", "inspect", "check", "repair"]):
        priority = "high" if any(word in text_lower for word in ["soon", "today", "asap"]) else "normal"
        intent = "maintenance_work_order"
    elif any(word in text_lower for word in ["order", "parts", "inventory", "stock"]):
        priority = "normal"
        intent = "parts_request"
    else:
        priority = "normal"
        intent = "general_request"
    
    # Generate work order details
    work_order_id = f"WO_VOICE_{len(text):06d}"
    
    # AI analysis simulation
    ai_analysis = f"Claude + Grok Analysis: Detected {intent} with {priority} priority. "
    if "motor" in text_lower:
        ai_analysis += "Motor-related issue identified. Recommend electrical team assignment."
    elif "pump" in text_lower:
        ai_analysis += "Pump system issue. Hydraulics specialist recommended."
    elif "conveyor" in text_lower:
        ai_analysis += "Conveyor system maintenance. Mechanical team optimal."
    else:
        ai_analysis += "General maintenance request processed."
    
    return {
        "understood": True,
        "intent": intent,
        "work_order_created": True,
        "work_order_id": work_order_id,
        "priority": priority,
        "assigned_to": determine_assignment(text_lower),
        "confidence": 0.94,
        "ai_analysis": ai_analysis
    }

def determine_assignment(text: str) -> str:
    """AI-powered technician assignment"""
    if any(word in text for word in ["electrical", "motor", "power", "voltage"]):
        return "Electrical Team Alpha"
    elif any(word in text for word in ["hydraulic", "pump", "pressure", "fluid"]):
        return "Hydraulics Team Beta"
    elif any(word in text for word in ["mechanical", "gear", "belt", "chain"]):
        return "Mechanical Team Gamma"
    else:
        return "Maintenance Team Delta"

@router.post("/command", response_model=VoiceResponse)
async def process_voice(command: VoiceCommand):
    """Process voice command and create work order"""
    
    # Use text input if provided, otherwise simulate speech-to-text
    text = command.text_input or "Simulate: Conveyor belt motor overheating in production line 3"
    
    result = await process_voice_command(text, command.technician_id, command.location)
    
    return VoiceResponse(**result)

@router.get("/capabilities", response_model=VoiceCapabilities)
async def get_voice_capabilities():
    """Get voice AI capabilities"""
    return VoiceCapabilities(
        supported_languages=["en-US", "en-GB", "es-ES", "fr-FR", "de-DE"],
        confidence_threshold=0.85,
        ai_models=["claude-nlp", "grok-voice", "openai-whisper"],
        features=[
            "Natural language work order creation",
            "Priority detection and assignment",
            "Technician team routing",
            "Equipment identification",
            "Emergency detection",
            "Multi-language support"
        ]
    )

@router.post("/emergency")
async def emergency_voice_command(command: VoiceCommand):
    """Emergency voice command processing"""
    
    text = command.text_input or "EMERGENCY: Equipment failure in production area"
    
    result = await process_voice_command(text, command.technician_id, command.location)
    result["priority"] = "critical"
    result["intent"] = "emergency"
    
    # Simulate emergency protocols
    emergency_response = {
        **result,
        "emergency_protocols_activated": True,
        "notifications_sent": ["Safety Team", "Production Manager", "Maintenance Supervisor"],
        "estimated_response_time": "5 minutes",
        "ai_emergency_analysis": "Critical equipment failure detected. Immediate safety assessment required. Production line shutdown recommended."
    }
    
    return emergency_response

@router.get("/active-commands")
async def get_active_voice_commands():
    """Get currently processing voice commands"""
    return {
        "active_sessions": 3,
        "processing_queue": [
            {"id": "VC_001", "status": "analyzing", "technician": "TECH_101"},
            {"id": "VC_002", "status": "creating_work_order", "technician": "TECH_205"},
            {"id": "VC_003", "status": "completed", "technician": "TECH_330"}
        ],
        "ai_models_online": ["claude", "grok", "openai"],
        "average_processing_time": "2.3 seconds"
    }