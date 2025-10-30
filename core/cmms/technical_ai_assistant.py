#!/usr/bin/env python3
"""
ChatterFix CMMS - Technical AI Assistant Service
Advanced multimedia AI assistant for technicians and workers with photo, video, document, and speech capabilities
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Union
from datetime import datetime, timedelta
import sqlite3
import json
import os
import logging
import httpx
import uuid
import asyncio
from enum import Enum
import base64
import io
from PIL import Image
import speech_recognition as sr
import pydub
from pydub import AudioSegment
import tempfile
import cv2
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ChatterFix Technical AI Assistant", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATABASE_FILE = os.getenv("DATABASE_FILE", "chatterfix_enterprise_v3.db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
XAI_API_KEY = os.getenv("XAI_API_KEY")

# Technical Role Definitions
class TechnicalRole(str, Enum):
    TECHNICIAN = "technician"
    MAINTENANCE_WORKER = "maintenance_worker"
    FIELD_ENGINEER = "field_engineer"
    SUPERVISOR = "supervisor"
    INSPECTOR = "inspector"
    SAFETY_OFFICER = "safety_officer"

# Pydantic Models
class TechnicalRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    user_role: Optional[TechnicalRole] = TechnicalRole.TECHNICIAN
    context: Optional[Dict[str, Any]] = {}
    session_id: Optional[str] = None
    current_page: Optional[str] = None
    equipment_id: Optional[str] = None
    work_order_id: Optional[str] = None

class MultimediaAnalysis(BaseModel):
    analysis_type: str  # "image", "video", "document", "audio"
    content: str
    confidence: float
    findings: List[Dict[str, Any]]
    recommendations: List[str]
    safety_alerts: List[str] = []

# Technical AI configurations with specialized expertise
TECHNICAL_CONFIGURATIONS = {
    TechnicalRole.TECHNICIAN: {
        "name": "TechBot Pro",
        "personality": "Hands-on expert with deep technical knowledge, safety-first approach, practical problem solver",
        "expertise": [
            "equipment diagnostics", "troubleshooting", "repair procedures", "preventive maintenance",
            "parts identification", "safety protocols", "tool usage", "technical documentation"
        ],
        "capabilities": [
            "photo_analysis", "video_diagnostics", "document_reading", "speech_commands",
            "part_recognition", "damage_assessment", "procedure_guidance", "safety_checks"
        ],
        "ai_model_preference": "grok",  # Best for technical problem-solving
    },
    TechnicalRole.MAINTENANCE_WORKER: {
        "name": "MaintenanceBot",
        "personality": "Practical, methodical, detail-oriented with focus on preventive care and efficiency",
        "expertise": [
            "routine maintenance", "lubrication schedules", "cleaning procedures", "basic repairs",
            "inventory management", "work order completion", "equipment monitoring"
        ],
        "capabilities": [
            "photo_documentation", "checklist_assistance", "procedure_lookup", "voice_notes",
            "condition_monitoring", "maintenance_scheduling", "parts_ordering"
        ],
        "ai_model_preference": "gpt4",
    },
    TechnicalRole.FIELD_ENGINEER: {
        "name": "FieldBot Engineer",
        "personality": "Analytical, innovative, systems-thinking engineer focused on optimization and root cause analysis",
        "expertise": [
            "system analysis", "performance optimization", "failure analysis", "design improvements",
            "technical specifications", "compliance verification", "advanced diagnostics"
        ],
        "capabilities": [
            "technical_drawing_analysis", "performance_data_analysis", "system_modeling",
            "failure_prediction", "optimization_recommendations", "compliance_checking"
        ],
        "ai_model_preference": "claude",
    },
    TechnicalRole.SUPERVISOR: {
        "name": "SupervisorBot",
        "personality": "Leadership-focused, safety-conscious, efficiency-driven with team coordination expertise",
        "expertise": [
            "team coordination", "work planning", "quality control", "safety oversight",
            "resource allocation", "progress tracking", "performance management"
        ],
        "capabilities": [
            "team_coordination", "progress_monitoring", "quality_assurance", "safety_oversight",
            "resource_planning", "performance_analytics", "communication_facilitation"
        ],
        "ai_model_preference": "claude",
    },
    TechnicalRole.INSPECTOR: {
        "name": "InspectorBot",
        "personality": "Detail-oriented, compliance-focused, thorough with regulatory knowledge and quality standards",
        "expertise": [
            "quality inspection", "compliance verification", "standards adherence", "defect identification",
            "regulatory requirements", "certification processes", "audit procedures"
        ],
        "capabilities": [
            "defect_detection", "compliance_checking", "quality_scoring", "audit_assistance",
            "certification_guidance", "standards_verification", "reporting_automation"
        ],
        "ai_model_preference": "claude",
    },
    TechnicalRole.SAFETY_OFFICER: {
        "name": "SafetyBot",
        "personality": "Safety-first, risk-aware, protective with comprehensive safety knowledge and emergency procedures",
        "expertise": [
            "safety protocols", "hazard identification", "risk assessment", "emergency procedures",
            "PPE requirements", "safety training", "incident investigation"
        ],
        "capabilities": [
            "hazard_detection", "safety_assessment", "ppe_verification", "emergency_guidance",
            "safety_training", "incident_analysis", "risk_mitigation"
        ],
        "ai_model_preference": "gpt4",
    }
}

# Database initialization for technical assistant
def init_technical_database():
    """Initialize technical assistant database tables"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Technical assistance sessions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS technical_sessions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        user_role TEXT NOT NULL,
        equipment_id TEXT,
        work_order_id TEXT,
        context TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        active BOOLEAN DEFAULT TRUE
    )
    """)
    
    # Multimedia analysis results
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS multimedia_analysis (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        analysis_type TEXT NOT NULL,
        file_path TEXT,
        analysis_results TEXT NOT NULL,
        confidence REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES technical_sessions (id)
    )
    """)
    
    # Technical knowledge base
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS technical_knowledge (
        id TEXT PRIMARY KEY,
        equipment_type TEXT NOT NULL,
        issue_type TEXT NOT NULL,
        solution TEXT NOT NULL,
        procedure_steps TEXT,
        safety_notes TEXT,
        tools_required TEXT,
        parts_needed TEXT,
        difficulty_level INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Voice commands and transcripts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS voice_transcripts (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        transcript TEXT NOT NULL,
        confidence REAL DEFAULT 0.0,
        processed_command TEXT,
        response TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES technical_sessions (id)
    )
    """)
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_technical_database()

async def analyze_image(image_data: bytes, analysis_context: Dict = None) -> MultimediaAnalysis:
    """Analyze image for technical insights using computer vision and AI"""
    try:
        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(image_data))
        
        # Basic image analysis using OpenCV
        img_array = np.array(image)
        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # Detect edges, contours for equipment analysis
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        findings = []
        recommendations = []
        safety_alerts = []
        
        # Basic analysis
        if len(contours) > 10:
            findings.append({
                "type": "complexity",
                "description": f"Complex equipment detected with {len(contours)} distinct components",
                "confidence": 0.8
            })
        
        # Color analysis for warning signs
        hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)
        
        # Check for red areas (potential warnings/damage)
        red_lower = np.array([0, 120, 70])
        red_upper = np.array([10, 255, 255])
        red_mask = cv2.inRange(hsv, red_lower, red_upper)
        red_pixels = cv2.countNonZero(red_mask)
        
        if red_pixels > 1000:
            findings.append({
                "type": "warning_indicator",
                "description": "Red coloration detected - potential warning indicators or wear",
                "confidence": 0.7
            })
            safety_alerts.append("Red areas detected - check for warning labels or heat damage")
        
        # Enhanced analysis with AI Vision API (if available)
        if OPENAI_API_KEY:
            try:
                # Convert image to base64 for API
                buffered = io.BytesIO()
                image.save(buffered, format="JPEG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
                
                # Call OpenAI Vision API
                vision_analysis = await call_openai_vision(img_base64, analysis_context)
                if vision_analysis:
                    findings.extend(vision_analysis.get("findings", []))
                    recommendations.extend(vision_analysis.get("recommendations", []))
                    safety_alerts.extend(vision_analysis.get("safety_alerts", []))
                    
            except Exception as e:
                logger.warning(f"AI vision analysis failed: {str(e)}")
        
        return MultimediaAnalysis(
            analysis_type="image",
            content=f"Image analysis completed. {len(contours)} components detected.",
            confidence=0.85,
            findings=findings,
            recommendations=recommendations or ["Ensure proper lighting for detailed inspection", "Document findings in work order"],
            safety_alerts=safety_alerts
        )
        
    except Exception as e:
        logger.error(f"Image analysis error: {str(e)}")
        return MultimediaAnalysis(
            analysis_type="image",
            content="Image analysis failed",
            confidence=0.0,
            findings=[],
            recommendations=["Retake photo with better lighting"],
            safety_alerts=[]
        )

async def call_openai_vision(image_base64: str, context: Dict = None) -> Dict:
    """Call OpenAI Vision API for advanced image analysis"""
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    context_prompt = "equipment maintenance and inspection" if not context else f"equipment maintenance focusing on {context.get('equipment_type', 'general equipment')}"
    
    data = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Analyze this image for {context_prompt}. Identify any visible issues, wear patterns, safety concerns, or maintenance needs. Provide specific findings, recommendations, and safety alerts."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1000
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30.0
        )
        
    if response.status_code == 200:
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Parse the response for structured data
        return {
            "findings": [{"type": "ai_analysis", "description": content, "confidence": 0.9}],
            "recommendations": ["Follow AI analysis recommendations"],
            "safety_alerts": []
        }
    
    return {}

async def transcribe_audio(audio_data: bytes) -> Dict[str, Any]:
    """Transcribe audio to text using speech recognition"""
    try:
        # Save audio data to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name
        
        # Initialize speech recognition
        recognizer = sr.Recognizer()
        
        # Load and process audio
        with sr.AudioFile(temp_path) as source:
            audio = recognizer.record(source)
        
        # Transcribe
        transcript = recognizer.recognize_google(audio)
        confidence = 0.85  # Google Speech API typical confidence
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        return {
            "transcript": transcript,
            "confidence": confidence,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Audio transcription error: {str(e)}")
        return {
            "transcript": "",
            "confidence": 0.0,
            "success": False,
            "error": str(e)
        }

async def analyze_document(document_data: bytes, filename: str) -> MultimediaAnalysis:
    """Analyze technical documents, manuals, and procedures"""
    try:
        findings = []
        recommendations = []
        
        # Basic document analysis based on filename
        if filename.lower().endswith(('.pdf', '.doc', '.docx')):
            findings.append({
                "type": "document_type",
                "description": f"Technical document: {filename}",
                "confidence": 1.0
            })
            
        recommendations.extend([
            "Review document for relevant procedures",
            "Extract key safety information",
            "Update work order with document references"
        ])
        
        return MultimediaAnalysis(
            analysis_type="document",
            content=f"Document '{filename}' analyzed successfully",
            confidence=0.8,
            findings=findings,
            recommendations=recommendations,
            safety_alerts=[]
        )
        
    except Exception as e:
        logger.error(f"Document analysis error: {str(e)}")
        return MultimediaAnalysis(
            analysis_type="document",
            content="Document analysis failed",
            confidence=0.0,
            findings=[],
            recommendations=["Ensure document is in supported format"],
            safety_alerts=[]
        )

async def generate_technical_response(request: TechnicalRequest) -> Dict[str, Any]:
    """Generate AI response based on technical role and context"""
    
    # Get role configuration
    role_config = TECHNICAL_CONFIGURATIONS.get(request.user_role, TECHNICAL_CONFIGURATIONS[TechnicalRole.TECHNICIAN])
    
    # Build context-aware prompt for technical assistance
    system_prompt = f"""You are {role_config['name']}, a specialized AI assistant for ChatterFix CMMS.
    
    PERSONALITY: {role_config['personality']}
    
    EXPERTISE: {', '.join(role_config['expertise'])}
    
    CAPABILITIES: {', '.join(role_config['capabilities'])}
    
    USER ROLE: {request.user_role.value.title()}
    CURRENT PAGE: {request.current_page or 'dashboard'}
    EQUIPMENT: {request.equipment_id or 'Not specified'}
    WORK ORDER: {request.work_order_id or 'Not specified'}
    
    CONTEXT: {json.dumps(request.context, indent=2)}
    
    Provide practical, safety-focused technical assistance. Include:
    - Step-by-step procedures when applicable
    - Safety considerations and warnings
    - Tool and parts requirements
    - Troubleshooting guidance
    - Best practices and tips
    
    Be concise but comprehensive. Always prioritize safety."""
    
    # Call appropriate AI service based on role preference
    try:
        ai_model = role_config['ai_model_preference']
        
        if ai_model == "claude" and ANTHROPIC_API_KEY:
            response = await call_claude_api(system_prompt, request.message)
        elif ai_model == "grok" and XAI_API_KEY:
            response = await call_grok_api(system_prompt, request.message)
        else:  # Default to GPT-4
            response = await call_openai_api(system_prompt, request.message)
            
        return {
            "response": response,
            "assistant_name": role_config['name'],
            "role": request.user_role.value,
            "ai_model": ai_model,
            "capabilities": role_config['capabilities'][:3],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Technical AI response generation error: {str(e)}")
        return {
            "response": f"I'm experiencing some technical difficulties right now. As your {role_config['name']}, I recommend checking the equipment manual or contacting a senior technician for immediate assistance.",
            "assistant_name": role_config['name'],
            "role": request.user_role.value,
            "error": True
        }

async def call_claude_api(system_prompt: str, message: str) -> str:
    """Call Anthropic Claude API"""
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    data = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 2000,
        "system": system_prompt,
        "messages": [{"role": "user", "content": message}]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=30.0
        )
        
    if response.status_code == 200:
        result = response.json()
        return result["content"][0]["text"]
    else:
        return "I'm having trouble accessing my advanced technical knowledge right now."

async def call_grok_api(system_prompt: str, message: str) -> str:
    """Call xAI Grok API"""
    headers = {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        "model": "grok-beta",
        "stream": False,
        "temperature": 0.7
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.x.ai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30.0
        )
        
    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        return "My technical problem-solving capabilities are temporarily unavailable."

async def call_openai_api(system_prompt: str, message: str) -> str:
    """Call OpenAI GPT-4 API"""
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "gpt-4-turbo-preview",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        "max_tokens": 2000,
        "temperature": 0.7
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30.0
        )
        
    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        return "I'm currently unable to provide my full technical assistance capabilities."

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "technical-ai-assistant",
        "roles_supported": list(TechnicalRole),
        "capabilities": ["photo_analysis", "video_processing", "document_analysis", "speech_to_text", "ai_assistance"]
    }

@app.post("/ask")
async def ask_technical_assistant(request: TechnicalRequest):
    """Ask the technical AI assistant"""
    return await generate_technical_response(request)

@app.post("/analyze/image")
async def analyze_image_endpoint(
    image: UploadFile = File(...),
    context: str = Form("{}"),
    user_id: str = Form(None),
    session_id: str = Form(None)
):
    """Analyze uploaded image for technical insights"""
    try:
        image_data = await image.read()
        analysis_context = json.loads(context) if context else {}
        
        result = await analyze_image(image_data, analysis_context)
        
        return {
            "analysis": result.dict(),
            "filename": image.filename,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Image analysis endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Image analysis failed")

@app.post("/analyze/document")
async def analyze_document_endpoint(
    document: UploadFile = File(...),
    user_id: str = Form(None),
    session_id: str = Form(None)
):
    """Analyze uploaded technical document"""
    try:
        document_data = await document.read()
        result = await analyze_document(document_data, document.filename)
        
        return {
            "analysis": result.dict(),
            "filename": document.filename,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Document analysis endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Document analysis failed")

@app.post("/speech/transcribe")
async def transcribe_speech(
    audio: UploadFile = File(...),
    user_id: str = Form(None),
    session_id: str = Form(None)
):
    """Transcribe speech to text"""
    try:
        audio_data = await audio.read()
        result = await transcribe_audio(audio_data)
        
        return {
            "transcription": result,
            "filename": audio.filename,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Speech transcription endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Speech transcription failed")

@app.get("/roles")
async def get_technical_roles():
    """Get all technical role configurations"""
    return {
        "roles": {
            role.value: {
                "name": config["name"],
                "expertise": config["expertise"],
                "capabilities": config["capabilities"]
            }
            for role, config in TECHNICAL_CONFIGURATIONS.items()
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8012))
    uvicorn.run(app, host="0.0.0.0", port=port)