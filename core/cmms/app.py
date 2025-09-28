#!/usr/bin/env python3
"""
ChatterFix CMMS Enterprise - Mars-Level AI Platform
🚀 The Most Advanced AI-Powered CMMS with:
- Enterprise AI Brain (Multi-AI Orchestration)
- Quantum Analytics Engine (Real-time Processing)
- Autonomous Operations (Self-healing & Zero-trust)
- Neural Architecture Search & Federated Learning
- Digital Twins & Edge Computing
- Mars-Level Performance & Intelligence
"""

from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import json
import httpx
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Protocol
import jwt
import bcrypt
import asyncio
import time

# Import enhanced database
try:
    from enhanced_database import init_enhanced_database
    ENHANCED_DB_AVAILABLE = True
except ImportError:
    ENHANCED_DB_AVAILABLE = False

# Import data toggle system
try:
    from admin import admin_manager, get_system_mode, get_database_path, can_switch_mode
    from data_toggle_system import data_toggle_system, switch_data_mode, reset_demo_data, get_system_overview
    DATA_TOGGLE_AVAILABLE = True
    print("✅ Data Toggle System loaded successfully")
except ImportError as e:
    DATA_TOGGLE_AVAILABLE = False
    print(f"⚠️  Data Toggle System not available: {e}")
    # Fallback functions
    def get_system_mode(): return "production"
    def get_database_path(mode=None): return "./data/cmms_enhanced.db"

# Import AI brain integration for data mode
try:
    from ai_brain_integration import ai_brain_integration, get_ai_mode_analysis, get_smart_mode_suggestion, get_ai_recommendations
    AI_BRAIN_INTEGRATION_AVAILABLE = True
    print("✅ AI Brain Data Mode Integration loaded successfully")
except ImportError as e:
    AI_BRAIN_INTEGRATION_AVAILABLE = False
    print(f"⚠️  AI Brain Integration not available: {e}")
    # Fallback functions
    def get_ai_mode_analysis(): return {"error": "AI Brain integration not available"}
    def get_smart_mode_suggestion(): return {"error": "AI Brain integration not available"}
    def get_ai_recommendations(): return []

# Import AI collaboration system
try:
    from ai_collaboration_integration import integrate_ai_collaboration
    AI_COLLABORATION_AVAILABLE = True
    print("✅ AI Collaboration System loaded successfully")
except ImportError as e:
    AI_COLLABORATION_AVAILABLE = False
    print(f"⚠️  AI Collaboration System not available: {e}")

# Protocol for request-like objects
class RequestLike(Protocol):
    async def json(self) -> Dict[str, Any]:
        ...

# Initialize FastAPI app with Mars-level capabilities
app = FastAPI(
    title="ChatterFix CMMS Enterprise - Mars-Level AI Platform", 
    version="4.0.0-mars-level-ai",
    description="🚀 The most advanced AI-powered CMMS with enterprise AI brain, quantum analytics, and autonomous operations"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add security middleware
try:
    from security_middleware import rate_limit_middleware, security_middleware
    app.middleware("http")(rate_limit_middleware)
    app.middleware("http")(security_middleware)
    print("✅ Security middleware enabled at startup")
except ImportError as e:
    print(f"⚠️  Security middleware not available: {e}")

# Security configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "enterprise-cloudrun-secret-2024")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Password hashing
security = HTTPBearer(auto_error=False)

# Database configuration with data toggle system support
if DATA_TOGGLE_AVAILABLE:
    DATABASE_PATH = get_database_path()  # Use current mode's database
else:
    DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/cmms_enhanced.db")  # Fallback

# Multi-AI Configuration
AI_PROVIDER = os.getenv("AI_PROVIDER", "grok")

# Grok (xAI) Configuration
XAI_API_KEY = os.getenv("XAI_API_KEY")
XAI_BASE_URL = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
XAI_MODEL = os.getenv("XAI_MODEL", "grok-4-latest")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# HuggingFace Configuration
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
HUGGINGFACE_BASE_URL = "https://api-inference.huggingface.co/models"
HUGGINGFACE_MODEL = os.getenv("HUGGINGFACE_MODEL", "microsoft/DialoGPT-large")

# Ollama Configuration (Local)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# Cloud Run Configuration
PORT = int(os.getenv("PORT", 8080))

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize enterprise database with enhanced schema and realistic data"""
    if ENHANCED_DB_AVAILABLE:
        # Use enhanced database with TechFlow Manufacturing Corp data
        init_enhanced_database()
        print("✅ Enhanced enterprise database initialized with TechFlow Manufacturing Corp data")
    else:
        # Fallback to basic database if enhanced version is not available
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create basic users table for enterprise authentication
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'viewer',
                is_active BOOLEAN DEFAULT TRUE,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                department TEXT,
                full_name TEXT
            )
        ''')
        
        # Create default admin user if not exists
        admin_password = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8')
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, email, password_hash, role, full_name, department)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ("admin", "admin@chatterfix.com", admin_password, "admin", "System Administrator", "IT"))
        
        conn.commit()
        conn.close()
        print("⚠️ Using basic database (enhanced version not available)")

# Multi-AI Processing Functions
async def process_with_grok(message: str, context: str) -> Dict[str, Any]:
    """Process message with Grok API"""
    try:
        system_prompt = f"""You are an AI assistant for ChatterFix CMMS Enterprise. 
Context: {context}
Provide helpful responses about maintenance, work orders, assets, and parts management."""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{XAI_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {XAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": XAI_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.7
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                grok_response = response.json()
                return {
                    "provider": "grok",
                    "response": grok_response["choices"][0]["message"]["content"],
                    "success": True
                }
    except Exception as e:
        logger.error(f"Grok API error: {str(e)}")
    
    return {"provider": "grok", "success": False, "error": "Grok API unavailable"}

async def process_with_openai(message: str, context: str) -> Dict[str, Any]:
    """Process message with OpenAI API"""
    if not OPENAI_API_KEY:
        return {"provider": "openai", "success": False, "error": "OpenAI API key not configured"}
    
    try:
        system_prompt = f"""You are an AI assistant for ChatterFix CMMS Enterprise.
Context: {context}
Provide helpful responses about maintenance, work orders, assets, and parts management."""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OPENAI_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": OPENAI_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.7
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                openai_response = response.json()
                return {
                    "provider": "openai",
                    "response": openai_response["choices"][0]["message"]["content"],
                    "success": True
                }
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
    
    return {"provider": "openai", "success": False, "error": "OpenAI API unavailable"}

async def process_with_huggingface(message: str, context: str) -> Dict[str, Any]:
    """Process message with HuggingFace API"""
    if not HUGGINGFACE_API_KEY:
        return {"provider": "huggingface", "success": False, "error": "HuggingFace API key not configured"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{HUGGINGFACE_BASE_URL}/{HUGGINGFACE_MODEL}",
                headers={
                    "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "inputs": f"Context: {context}\nUser: {message}\nAssistant:",
                    "parameters": {
                        "max_length": 1000,
                        "temperature": 0.7
                    }
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                hf_response = response.json()
                generated_text = hf_response[0]["generated_text"] if isinstance(hf_response, list) else hf_response.get("generated_text", "")
                return {
                    "provider": "huggingface",
                    "response": generated_text,
                    "success": True
                }
    except Exception as e:
        logger.error(f"HuggingFace API error: {str(e)}")
    
    return {"provider": "huggingface", "success": False, "error": "HuggingFace API unavailable"}

async def process_with_ollama(message: str, context: str) -> Dict[str, Any]:
    """Process message with local Ollama API"""
    try:
        async with httpx.AsyncClient() as client:
            system_prompt = f"""You are an AI assistant for ChatterFix CMMS Enterprise. 
Context: {context}

Provide helpful responses about maintenance, work orders, assets, and parts management."""

            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    "stream": False
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                ollama_response = response.json()
                return {
                    "provider": "ollama",
                    "response": ollama_response["message"]["content"],
                    "success": True
                }
    except Exception as e:
        logger.error(f"Ollama API error: {str(e)}")
    
    return {"provider": "ollama", "success": False, "error": "Ollama API unavailable"}

async def process_ai_message_multi(message: str, context: str, preferred_provider: Optional[str] = None) -> Dict[str, Any]:
    """Process message with multiple AI providers (fallback support)"""
    provider = preferred_provider or AI_PROVIDER
    
    # Try preferred provider first
    if provider == "grok":
        result = await process_with_grok(message, context)
        if result["success"]:
            return result
    elif provider == "openai":
        result = await process_with_openai(message, context)
        if result["success"]:
            return result
    elif provider == "huggingface":
        result = await process_with_huggingface(message, context)
        if result["success"]:
            return result
    elif provider == "ollama":
        result = await process_with_ollama(message, context)
        if result["success"]:
            return result
    
    # Fallback to other providers
    providers = ["ollama", "grok", "openai", "huggingface"]
    for fallback_provider in providers:
        if fallback_provider != provider:
            if fallback_provider == "grok":
                result = await process_with_grok(message, context)
            elif fallback_provider == "openai":
                result = await process_with_openai(message, context)
            elif fallback_provider == "huggingface":
                result = await process_with_huggingface(message, context)
            elif fallback_provider == "ollama":
                result = await process_with_ollama(message, context)
            
            if result["success"]:
                result["fallback"] = True
                return result
    
    # Final fallback
    return {
        "provider": "fallback",
        "response": "I'm here to help with your CMMS Enterprise needs! I can assist with work orders, asset management, parts inventory, and maintenance procedures. Please try again in a moment.",
        "success": True,
        "fallback": True
    }

# Authentication functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except jwt.PyJWTError:
        return None

def get_current_user(username: str = Depends(verify_token)):
    """Get current authenticated user"""
    if not username:
        return None
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND is_active = TRUE", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return dict(user)
    return None

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and enhanced features"""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    init_database()
    
    # Initialize enhanced features (CSV import/export, bulk operations)
    try:
        from enhanced_api_endpoints import add_enhanced_endpoints, setup_enhanced_features
        add_enhanced_endpoints(app)
        setup_enhanced_features(app)
        logger.info("✅ Enhanced competitive features loaded successfully!")
    except ImportError as e:
        logger.warning(f"⚠️  Enhanced features module not found: {e}")
    
    # Initialize advanced media and AI admin features (Whisper, OCR, Photo uploads)
    try:
        from advanced_endpoints import setup_advanced_features
        setup_advanced_features(app)
        logger.info("✅ Advanced media and AI admin features loaded successfully!")
    except ImportError as e:
        logger.warning(f"⚠️  Advanced features module not found: {e}")
    
    # Initialize AI collaboration system
    if AI_COLLABORATION_AVAILABLE:
        try:
            integrate_ai_collaboration(app)
            logger.info("✅ AI Collaboration System integrated successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to integrate AI Collaboration System: {e}")
    
    # Initialize advanced media system (Whisper voice, OCR, image uploads)
    try:
        from advanced_media_system import AdvancedMediaSystem
        media_system = AdvancedMediaSystem()
        app.state.media_system = media_system
        
        @app.post("/api/media/upload")
        async def upload_media_file(request: Request):
            """Upload and process media files with AI analysis"""
            try:
                form = await request.form()
                file = form.get("file")
                reference_type = form.get("reference_type", "general")
                reference_id = form.get("reference_id", "0")
                
                if not file or not hasattr(file, 'file'):
                    return {"success": False, "error": "No file provided"}
                
                # Read file data
                file_data = await file.read()
                filename = getattr(file, 'filename', 'uploaded_file')
                
                # Upload image with AI analysis
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    result = await media_system.upload_image(
                        file_data, filename, reference_type, int(reference_id)
                    )
                else:
                    return {"success": False, "error": "Unsupported file type"}
                
                return {"success": True, "data": result}
                
            except Exception as e:
                logger.error(f"Media upload error: {e}")
                return {"success": False, "error": str(e)}
        
        @app.post("/api/voice/transcribe")
        async def transcribe_voice(request: Request):
            """Convert voice to text using Whisper"""
            try:
                form = await request.form()
                audio_file = form.get("audio")
                
                if not audio_file or not hasattr(audio_file, 'file'):
                    return {"success": False, "error": "No audio file provided"}
                
                # Read audio data
                audio_data = await audio_file.read()
                filename = getattr(audio_file, 'filename', 'audio.wav')
                
                # Upload and transcribe audio
                result = await media_system.upload_audio_for_transcription(
                    audio_data, filename, "voice_command", 0
                )
                
                return {"success": True, "transcription": result.get("transcription", "")}
                
            except Exception as e:
                logger.error(f"Voice transcription error: {e}")
                return {"success": False, "error": str(e)}
        
        @app.post("/api/ocr/process")
        async def process_ocr(request: Request):
            """Extract text from images using OCR"""
            try:
                form = await request.form()
                image_file = form.get("image")
                
                if not image_file or not hasattr(image_file, 'file'):
                    return {"success": False, "error": "No image file provided"}
                
                # Read image data and upload first
                image_data = await image_file.read()
                filename = getattr(image_file, 'filename', 'document.jpg')
                
                # Upload image first
                upload_result = await media_system.upload_image(
                    image_data, filename, "document", 0
                )
                
                if upload_result and upload_result.get("media_file"):
                    # Extract text using OCR
                    media_file_id = upload_result["media_file"]["id"]
                    extracted_text = await media_system.extract_text_from_image(media_file_id)
                    return {"success": True, "extracted_text": extracted_text}
                else:
                    return {"success": False, "error": "Failed to upload image"}
                
            except Exception as e:
                logger.error(f"OCR processing error: {e}")
                return {"success": False, "error": str(e)}
        
        logger.info("✅ Advanced media system with Whisper, OCR, and photo uploads integrated!")
    except ImportError as e:
        logger.warning(f"⚠️  Advanced media system not available: {e}")
    
    # Initialize voice work order processor
    try:
        from core.cmms.voice_workorder_enhanced import VoiceWorkOrderProcessor
        voice_processor = VoiceWorkOrderProcessor()
        app.state.voice_processor = voice_processor
        
        @app.post("/api/voice/create-workorder")
        async def create_workorder_from_voice(request: Request):
            """Create work order from voice command with AI assistance"""
            try:
                body = await request.json()
                voice_text = body.get("transcription", "")
                
                if not voice_text:
                    return {"success": False, "error": "No voice transcription provided"}
                
                # Process voice command to create work order
                work_order = await voice_processor.process_voice_command(voice_text)
                return {"success": True, "work_order": work_order}
                
            except Exception as e:
                logger.error(f"Voice work order creation error: {e}")
                return {"success": False, "error": str(e)}
        
        @app.post("/api/ai/technician-assist")
        async def ai_technician_assistance(request: Request):
            """AI assistance for technicians with parts, directions, and technical advice"""
            try:
                body = await request.json()
                question = body.get("question", "")
                context = body.get("context", {})
                provider = body.get("provider", "multi")  # multi, openai, grok, ollama
                
                if not question:
                    return {"success": False, "error": "No question provided"}
                
                # Enhanced prompt for technician assistance
                enhanced_prompt = f"""
                As an expert CMMS technician assistant, provide helpful guidance for:
                
                QUESTION: {question}
                
                CONTEXT: {json.dumps(context) if context else 'General maintenance query'}
                
                Please provide:
                1. IMMEDIATE STEPS: What to do right now
                2. SAFETY CONSIDERATIONS: Any safety concerns or precautions
                3. REQUIRED PARTS/TOOLS: List specific parts numbers, tools needed
                4. STEP-BY-STEP INSTRUCTIONS: Clear, numbered steps
                5. TROUBLESHOOTING TIPS: Common issues and solutions
                6. PREVENTIVE MEASURES: How to avoid this issue in the future
                
                Keep responses practical, clear, and safety-focused for field technicians.
                """
                
                # Try multiple AI providers for best response
                ai_response = await process_ai_message_multi(enhanced_prompt, json.dumps(context), provider)
                
                return {
                    "success": True,
                    "assistance": ai_response.get("response", ""),
                    "provider": ai_response.get("provider", "unknown"),
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"AI technician assistance error: {e}")
                return {"success": False, "error": str(e)}
        
        @app.post("/api/ai/parts-recommendation")
        async def ai_parts_recommendation(request: Request):
            """AI-powered parts recommendation based on equipment and issue"""
            try:
                body = await request.json()
                equipment = body.get("equipment", "")
                issue = body.get("issue", "")
                symptoms = body.get("symptoms", "")
                provider = body.get("provider", "grok")  # Grok is good for technical analysis
                
                parts_prompt = f"""
                As a parts specialist for CMMS, analyze this maintenance issue:
                
                EQUIPMENT: {equipment}
                ISSUE: {issue}
                SYMPTOMS: {symptoms}
                
                Provide a detailed parts analysis including:
                1. LIKELY FAILED PARTS: Most probable components that need replacement
                2. PART NUMBERS: Specific OEM part numbers if available
                3. ALTERNATIVE PARTS: Compatible alternatives or generic equivalents
                4. URGENCY LEVEL: Critical, High, Medium, Low priority
                5. ESTIMATED COSTS: Rough cost estimates for parts
                6. DIAGNOSTIC STEPS: How to confirm which parts actually need replacement
                7. INSTALLATION NOTES: Special tools or procedures needed
                
                Focus on accuracy and practical field recommendations.
                """
                
                ai_response = await process_ai_message_multi(parts_prompt, "", provider)
                
                return {
                    "success": True,
                    "parts_recommendation": ai_response.get("response", ""),
                    "provider": ai_response.get("provider", "unknown"),
                    "urgency": "medium",  # Could be enhanced to parse from AI response
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"AI parts recommendation error: {e}")
                return {"success": False, "error": str(e)}
        
        logger.info("✅ Voice work order processor integrated!")
    except ImportError as e:
        logger.warning(f"⚠️  Voice work order processor not available: {e}")
    
    logger.info(f"🚀 ChatterFix CMMS Enterprise v3.0 - AI-Powered Competitive Edition started on port {PORT}")

# =================== DATA TOGGLE SYSTEM API ENDPOINTS ===================
if DATA_TOGGLE_AVAILABLE:
    
    @app.get("/api/admin/system-status")
    async def get_system_status(user: dict = Depends(get_current_user)):
        """Get current system status and data mode information"""
        try:
            if not user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Get comprehensive system overview
            overview = get_system_overview()
            
            return {
                "success": True,
                "status": overview,
                "user": {
                    "id": user.get("id"),
                    "username": user.get("username"),
                    "role": user.get("role"),
                    "full_name": user.get("full_name")
                }
            }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/api/admin/switch-mode")
    async def switch_system_mode(request: Request, user: dict = Depends(get_current_user)):
        """Switch between demo and production data modes"""
        try:
            if not user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Parse request body
            body = await request.json()
            target_mode = body.get("mode")
            create_backup = body.get("backup", True)
            
            if not target_mode:
                return {"success": False, "error": "Mode parameter required"}
            
            # Switch mode using data toggle system
            result = switch_data_mode(
                new_mode=target_mode,
                user_id=user.get("id"),
                user_role=user.get("role"),
                backup=create_backup
            )
            
            if result["success"]:
                # Update global DATABASE_PATH for immediate effect
                global DATABASE_PATH
                DATABASE_PATH = get_database_path(target_mode)
                logger.info(f"Database path updated to: {DATABASE_PATH}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error switching mode: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/api/admin/reset-demo")
    async def reset_demo_data_endpoint(request: Request, user: dict = Depends(get_current_user)):
        """Reset demo database to original TechFlow Manufacturing Corp data"""
        try:
            if not user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Parse request body
            body = await request.json()
            confirm = body.get("confirm", False)
            
            # Reset demo data
            result = reset_demo_data(user_id=user.get("id"), confirm=confirm)
            return result
            
        except Exception as e:
            logger.error(f"Error resetting demo data: {e}")
            return {"success": False, "error": str(e)}
    
    @app.get("/api/admin/system-overview")
    async def get_system_overview_endpoint(user: dict = Depends(get_current_user)):
        """Get comprehensive system overview for admin dashboard"""
        try:
            if not user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Get system overview
            overview = get_system_overview()
            return {"success": True, "overview": overview}
            
        except Exception as e:
            logger.error(f"Error getting system overview: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/api/admin/create-backup")
    async def create_backup_endpoint(request: Request, user: dict = Depends(get_current_user)):
        """Create backup of current database"""
        try:
            if not user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Parse request body
            body = await request.json()
            mode = body.get("mode", get_system_mode())
            reason = body.get("reason", "manual_backup")
            
            # Create backup
            if admin_manager.backup_database(mode, reason):
                return {
                    "success": True,
                    "message": f"Backup created successfully for {mode} mode",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": "Failed to create backup"}
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return {"success": False, "error": str(e)}
    
    @app.get("/api/admin/company-setup")
    async def get_company_setup_endpoint(user: dict = Depends(get_current_user)):
        """Get company setup wizard data"""
        try:
            if not user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Get company setup wizard data
            wizard_data = data_toggle_system.get_company_setup_wizard_data()
            return {"success": True, "wizard": wizard_data}
            
        except Exception as e:
            logger.error(f"Error getting company setup data: {e}")
            return {"success": False, "error": str(e)}
    
    @app.post("/api/admin/company-setup")
    async def update_company_setup_endpoint(request: Request, user: dict = Depends(get_current_user)):
        """Update company setup configuration"""
        try:
            if not user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Parse request body
            body = await request.json()
            setup_data = body.get("setup", {})
            
            # Update company setup
            result = admin_manager.update_company_setup(setup_data)
            return result
            
        except Exception as e:
            logger.error(f"Error updating company setup: {e}")
            return {"success": False, "error": str(e)}
    
    @app.get("/api/admin/data-mode")
    async def get_current_data_mode():
        """Get current data mode (demo/production) - public endpoint"""
        try:
            mode = get_system_mode()
            features = admin_manager.get_demo_features() if mode == "demo" else {}
            
            return {
                "success": True,
                "mode": mode,
                "features": features,
                "database_path": get_database_path(mode)
            }
        except Exception as e:
            logger.error(f"Error getting data mode: {e}")
            return {"success": False, "error": str(e)}
    
    # AI Brain Integration Endpoints
    if AI_BRAIN_INTEGRATION_AVAILABLE:
        
        @app.get("/api/admin/ai-analysis")
        async def get_ai_mode_analysis_endpoint(user: dict = Depends(get_current_user)):
            """Get AI analysis of data mode usage patterns"""
            try:
                if not user:
                    raise HTTPException(status_code=401, detail="Authentication required")
                
                analysis = get_ai_mode_analysis()
                return {"success": True, "analysis": analysis}
                
            except Exception as e:
                logger.error(f"Error getting AI analysis: {e}")
                return {"success": False, "error": str(e)}
        
        @app.get("/api/admin/ai-suggestions")
        async def get_ai_suggestions_endpoint(user: dict = Depends(get_current_user)):
            """Get AI-powered mode suggestions and recommendations"""
            try:
                if not user:
                    raise HTTPException(status_code=401, detail="Authentication required")
                
                suggestion = get_smart_mode_suggestion()
                recommendations = get_ai_recommendations()
                
                return {
                    "success": True,
                    "suggestion": suggestion,
                    "recommendations": recommendations
                }
                
            except Exception as e:
                logger.error(f"Error getting AI suggestions: {e}")
                return {"success": False, "error": str(e)}
        
        @app.post("/api/admin/ai-optimize")
        async def optimize_system_with_ai(request: Request, user: dict = Depends(get_current_user)):
            """Use AI to optimize system configuration"""
            try:
                if not user:
                    raise HTTPException(status_code=401, detail="Authentication required")
                
                # Get optimization request
                body = await request.json()
                auto_apply = body.get("auto_apply", False)
                
                # Get AI analysis and suggestions
                analysis = get_ai_mode_analysis()
                suggestion = get_smart_mode_suggestion()
                
                optimization_result = {
                    "analysis": analysis,
                    "suggestion": suggestion,
                    "applied_changes": []
                }
                
                # If auto-apply is enabled and confidence is high, apply suggestions
                if auto_apply and suggestion.get("confidence", 0) > 0.8:
                    suggested_mode = suggestion.get("suggested_mode")
                    current_mode = suggestion.get("current_mode")
                    
                    if suggested_mode != current_mode:
                        # Apply mode switch
                        switch_result = switch_data_mode(
                            new_mode=suggested_mode,
                            user_id=user.get("id"),
                            user_role=user.get("role"),
                            backup=True
                        )
                        
                        if switch_result["success"]:
                            optimization_result["applied_changes"].append({
                                "type": "mode_switch",
                                "from": current_mode,
                                "to": suggested_mode,
                                "result": switch_result
                            })
                
                return {"success": True, "optimization": optimization_result}
                
            except Exception as e:
                logger.error(f"Error optimizing system with AI: {e}")
                return {"success": False, "error": str(e)}

# Authentication routes
@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Enterprise login page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - ChatterFix CMMS Enterprise</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #212121 0%, #434A54 50%, #2E4053 100%);
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .login-container {
            background: rgba(33,33,33,0.3);
            padding: 40px;
            border-radius: 20px;
            backdrop-filter: blur(20px);
            box-shadow: 0 8px 32px rgba(46,64,83,0.4), 0 0 0 1px rgba(102,102,102,0.3);
            width: 100%;
            max-width: 400px;
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo h1 {
            margin: 0;
            font-size: 2em;
            font-weight: 700;
        }
        .cloud-badge {
            background: linear-gradient(45deg, #434A54, #8B9467);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7em;
            font-weight: 600;
            margin-left: 10px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
        }
        input {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 10px;
            background: rgba(46,64,83,0.4);
            color: white;
            font-size: 16px;
            box-sizing: border-box;
        }
        input::placeholder {
            color: rgba(255,255,255,0.7);
        }
        button {
            width: 100%;
            padding: 15px;
            border: none;
            border-radius: 10px;
            background: white;
            color: #2E4053;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(46,64,83,0.4), 0 0 0 1px rgba(102,102,102,0.2);
        }
        .demo-info {
            margin-top: 20px;
            text-align: center;
            font-size: 14px;
            opacity: 0.8;
        }
        .ai-info {
            margin-top: 15px;
            text-align: center;
            font-size: 12px;
            opacity: 0.7;
            border-top: 1px solid rgba(255,255,255,0.2);
            padding-top: 15px;
        }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="logo">
                <h1>🔧 ChatterFix</h1>
                <p>Enterprise CMMS<span class="cloud-badge">CLOUD RUN</span></p>
            </div>
            
            <form id="loginForm">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" placeholder="Enter username" required>
                </div>
                
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" placeholder="Enter password" required>
                </div>
                
                <button type="submit">Login to Enterprise</button>
            </form>
            
            <div class="demo-info">
                <strong>Demo Credentials:</strong><br>
                Username: admin<br>
                Password: admin123
            </div>
            
            <div class="ai-info">
                🤖 Multi-AI Integration<br>
                Grok • OpenAI • HuggingFace
            </div>
        </div>
        
        <script>
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            alert('Enterprise login ready - redirecting to dashboard');
            window.location.href = '/';
        });
        </script>
    </body>
    </html>
    """

@app.post("/api/login")
async def login(username: str = Form(...), password: str = Form(...)):
    """Authenticate user and return JWT token"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND is_active = TRUE", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(data={"sub": user['username'], "role": user['role']})
    return {"access_token": access_token, "token_type": "bearer", "user": {"username": user['username'], "role": user['role']}}

# Main dashboard
@app.get("/", response_class=HTMLResponse)
async def dashboard(current_user: Optional[dict] = Depends(get_current_user)):
    """Enterprise dashboard with Cloud Run optimizations"""
    
    # Get demo user for development if no auth
    if not current_user:
        current_user = {"username": "demo", "role": "admin", "full_name": "Demo User"}
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ChatterFix CMMS Enterprise - Cloud Run</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="/static/css/data-mode.css">
        <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #212121 0%, #434A54 50%, #2E4053 100%);
            min-height: 100vh;
        }}
        .header {{
            background: rgba(33,33,33,0.3);
            padding: 20px;
            backdrop-filter: blur(20px);
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: white;
        }}
        .logo {{
            font-size: 1.5em;
            font-weight: 700;
        }}
        .cloud-badge {{
            background: linear-gradient(45deg, #434A54, #8B9467);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7em;
            font-weight: 600;
            margin-left: 10px;
        }}
        .user-info {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        .nav {{
            background: rgba(33,33,33,0.2);
            padding: 15px 20px;
            display: flex;
            gap: 20px;
        }}
        .nav a {{
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 10px;
            transition: all 0.3s ease;
        }}
        .nav a:hover {{
            background: rgba(33,33,33,0.3);
        }}
        .dashboard {{
            padding: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }}
        .card {{
            background: rgba(33,33,33,0.3);
            padding: 25px;
            border-radius: 20px;
            backdrop-filter: blur(20px);
            color: white;
            box-shadow: 0 8px 32px rgba(46,64,83,0.4), 0 0 0 1px rgba(102,102,102,0.3);
        }}
        .card h3 {{
            margin: 0 0 15px 0;
            font-size: 1.2em;
        }}
        .metric {{
            font-size: 2em;
            font-weight: 700;
            margin: 10px 0;
        }}
        .enterprise-badge {{
            background: linear-gradient(45deg, #2E4053, #666666);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
        }}
        .ai-providers {{
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }}
        .ai-badge {{
            padding: 4px 8px;
            border-radius: 10px;
            font-size: 0.7em;
            font-weight: 500;
        }}
        .ai-grok {{ background: #1C3445; }}
        .ai-openai {{ background: #456789; }}
        .ai-hf {{ background: #2F4E7F; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="logo">🔧 ChatterFix CMMS <span class="enterprise-badge">ENTERPRISE</span><span class="cloud-badge">CLOUD RUN</span></div>
            <div class="user-info">
                <span>Welcome, {current_user['full_name'] or current_user['username']} ({current_user['role'].title()})</span>
                <a href="/login" style="color: white;">Login</a>
            </div>
        </div>
        
        <div class="nav">
            <a href="/">🏠 Dashboard</a>
            <a href="/work-orders">📋 Work Orders</a>
            <a href="/assets">⚙️ Assets</a>
            <a href="/parts">🔩 Parts</a>
            <a href="/reports">📊 Reports</a>
            <a href="/ui/ai-command-center">🧠 AI Command Center</a>
            <a href="/login">🔐 Login</a>
        </div>
        
        <div class="dashboard">
            <div class="card">
                <h3>📊 Work Orders</h3>
                <div class="metric">5</div>
                <p>Active work orders</p>
            </div>
            
            <div class="card">
                <h3>🏭 Critical Assets</h3>
                <div class="metric">3</div>
                <p>Require immediate attention</p>
            </div>
            
            <div class="card">
                <h3>📦 Low Stock Alert</h3>
                <div class="metric">2</div>
                <p>Parts below minimum stock</p>
            </div>
            
            <div class="card">
                <h3>🤖 Multi-AI Assistant</h3>
                <div class="metric">Active</div>
                <div class="ai-providers">
                    <span class="ai-badge ai-grok">Grok</span>
                    <span class="ai-badge ai-openai">OpenAI</span>
                    <span class="ai-badge ai-hf">HuggingFace</span>
                </div>
            </div>
            
            <div class="card">
                <h3>🔐 Enterprise Features</h3>
                <div class="metric">✅</div>
                <p>Authentication, RBAC, Multi-AI</p>
            </div>
            
            <div class="card">
                <h3>☁️ Cloud Infrastructure</h3>
                <div class="metric">Optimized</div>
                <p>Auto-scaling, serverless, global</p>
            </div>
        </div>
        
        <!-- CMMS Core Functions -->
        <script src="/static/js/cmms-functions.js"></script>
        <!-- Data Mode Toggle System -->
        <script src="/static/js/data-mode-toggle.js"></script>
        <!-- AI Assistant Integration -->
        <script src="/ai-inject.js"></script>
        
        <!-- Global Click Handler System with Auto-Detection -->
        <script>
        // Enhanced Click Handler System with Automatic Detection
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('🔧 ChatterFix CMMS: Initializing enhanced click handler system...');
            
            // Global automatic click handler attachment system
            window.ChatterFixAutoHandlers = {{
                
                // Attach click handlers to all existing cards
                initializeAllCards: function() {{
                    this.initializeWorkOrderCards();
                    this.initializeAssetCards();
                    this.initializePartCards();
                    console.log('🚀 All existing cards initialized with click handlers');
                }},
                
                // Initialize work order cards
                initializeWorkOrderCards: function() {{
                    document.querySelectorAll('.work-order-card').forEach((card, index) => {{
                        if (!card.onclick) {{
                            const cardId = this.extractCardId(card) || (index + 1);
                            card.onclick = () => {{
                                console.log('🔧 Work Order card clicked:', cardId);
                                if (window.showWorkOrderDetails) {{
                                    showWorkOrderDetails(cardId);
                                }} else {{
                                    console.error('❌ showWorkOrderDetails function not available');
                                }}
                            }};
                            card.style.cursor = 'pointer';
                            console.log('✅ Work order card ' + cardId + ' handler attached');
                        }}
                    }});
                }},
                
                // Initialize asset cards
                initializeAssetCards: function() {{
                    document.querySelectorAll('.asset-card').forEach((card, index) => {{
                        if (!card.onclick) {{
                            const cardId = this.extractCardId(card) || (index + 1);
                            card.onclick = () => {{
                                console.log('🏭 Asset card clicked:', cardId);
                                if (window.showAssetDetails) {{
                                    showAssetDetails(cardId);
                                }} else {{
                                    console.error('❌ showAssetDetails function not available');
                                }}
                            }};
                            card.style.cursor = 'pointer';
                            console.log('✅ Asset card ' + cardId + ' handler attached');
                        }}
                    }});
                }},
                
                // Initialize part cards
                initializePartCards: function() {{
                    document.querySelectorAll('.part-card').forEach((card, index) => {{
                        if (!card.onclick) {{
                            const cardId = this.extractCardId(card) || (index + 1);
                            card.onclick = () => {{
                                console.log('🔩 Parts card clicked:', cardId);
                                if (window.showPartsDetails) {{
                                    showPartsDetails(cardId);
                                }} else {{
                                    console.error('❌ showPartsDetails function not available');
                                }}
                            }};
                            card.style.cursor = 'pointer';
                            console.log('✅ Parts card ' + cardId + ' handler attached');
                        }}
                    }});
                }},
                
                // Extract card ID from data attributes or content
                extractCardId: function(card) {{
                    // Try to get ID from data attribute
                    if (card.dataset.id) return parseInt(card.dataset.id);
                    
                    // Try to extract from onclick attribute if it exists
                    if (card.getAttribute('onclick')) {{
                        const match = card.getAttribute('onclick').match(/\\d+/);
                        if (match) return parseInt(match[0]);
                    }}
                    
                    // Try to extract from button onclick
                    const button = card.querySelector('button[onclick]');
                    if (button) {{
                        const match = button.getAttribute('onclick').match(/\\d+/);
                        if (match) return parseInt(match[0]);
                    }}
                    
                    return null;
                }},
                
                // Monitor for new cards being added to the DOM
                startDOMObserver: function() {{
                    const observer = new MutationObserver((mutations) => {{
                        let newCardsFound = false;
                        
                        mutations.forEach((mutation) => {{
                            if (mutation.type === 'childList') {{
                                mutation.addedNodes.forEach((node) => {{
                                    if (node.nodeType === 1) {{ // Element node
                                        // Check if the added node is a card
                                        if (this.isCard(node)) {{
                                            console.log('🔍 New card detected:', node.className);
                                            this.attachHandlerToCard(node);
                                            newCardsFound = true;
                                        }}
                                        
                                        // Check if the added node contains cards
                                        const cards = node.querySelectorAll && node.querySelectorAll('.work-order-card, .asset-card, .part-card');
                                        if (cards && cards.length > 0) {{
                                            console.log('🔍 Container with ' + cards.length + ' new cards detected');
                                            cards.forEach(card => {{
                                                this.attachHandlerToCard(card);
                                                newCardsFound = true;
                                            }});
                                        }}
                                    }}
                                }});
                            }}
                        }});
                        
                        if (newCardsFound) {{
                            console.log('🔄 New cards processed, handlers attached automatically');
                        }}
                    }});
                    
                    // Start observing the document with configured parameters
                    observer.observe(document.body, {{
                        childList: true,
                        subtree: true,
                        attributes: false
                    }});
                    
                    console.log('👁️ DOM observer started - will auto-attach handlers to new cards');
                }},
                
                // Check if a node is a card
                isCard: function(node) {{
                    return node.classList && (
                        node.classList.contains('work-order-card') ||
                        node.classList.contains('asset-card') ||
                        node.classList.contains('part-card')
                    );
                }},
                
                // Attach handler to a specific card
                attachHandlerToCard: function(card) {{
                    if (!card.onclick) {{
                        const cardId = this.extractCardId(card);
                        
                        if (card.classList.contains('work-order-card')) {{
                            card.onclick = () => {{
                                console.log('🔧 Auto-attached: Work Order card clicked:', cardId);
                                if (window.showWorkOrderDetails) showWorkOrderDetails(cardId);
                            }};
                        }} else if (card.classList.contains('asset-card')) {{
                            card.onclick = () => {{
                                console.log('🏭 Auto-attached: Asset card clicked:', cardId);
                                if (window.showAssetDetails) showAssetDetails(cardId);
                            }};
                        }} else if (card.classList.contains('part-card')) {{
                            card.onclick = () => {{
                                console.log('🔩 Auto-attached: Parts card clicked:', cardId);
                                if (window.showPartsDetails) showPartsDetails(cardId);
                            }};
                        }}
                        
                        card.style.cursor = 'pointer';
                        console.log('✅ Auto-attached handler to ' + card.className + ' with ID:', cardId);
                    }}
                }}
            }};
            
            // Initialize system
            window.ChatterFixAutoHandlers.initializeAllCards();
            window.ChatterFixAutoHandlers.startDOMObserver();
            
            // Expose globally for manual triggering
            window.refreshClickHandlers = () => window.ChatterFixAutoHandlers.initializeAllCards();
            
            console.log('🚀 ChatterFix CMMS: Enhanced auto-detection click handler system ready!');
        }});
        </script>
    </body>
    </html>
    """

# Asset detail page
@app.get("/asset/{asset_id}", response_class=HTMLResponse)
async def asset_detail(asset_id: int):
    """Individual asset detail page"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM assets WHERE id = ?", (asset_id,))
    asset = cursor.fetchone()
    conn.close()
    
    if not asset:
        # Return a demo asset if not found
        asset = {
            'id': asset_id,
            'name': f'Asset #{asset_id}',
            'asset_type': 'Equipment',
            'location': 'Production Floor',
            'status': 'Active',
            'criticality': 'Medium',
            'manufacturer': 'Demo Corp',
            'model': f'Model-{asset_id}'
        }
    else:
        asset = dict(asset)
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{asset['name']} - ChatterFix CMMS Enterprise</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #212121 0%, #434A54 50%, #2E4053 100%);
            min-height: 100vh;
            color: white;
        }}
        .container {{
            padding: 30px;
            max-width: 800px;
            margin: 0 auto;
        }}
        .asset-header {{
            background: rgba(33,33,33,0.3);
            padding: 30px;
            border-radius: 20px;
            backdrop-filter: blur(20px);
            margin-bottom: 20px;
        }}
        .asset-title {{
            font-size: 2em;
            margin-bottom: 10px;
        }}
        .asset-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .info-card {{
            background: rgba(33,33,33,0.2);
            padding: 15px;
            border-radius: 10px;
        }}
        .nav-link {{
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background: rgba(33,33,33,0.3);
            color: white;
            text-decoration: none;
            border-radius: 10px;
        }}
        .enterprise-badge {{
            background: linear-gradient(45deg, #2E4053, #666666);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
        }}
        .cloud-badge {{
            background: linear-gradient(45deg, #434A54, #8B9467);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
        }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="asset-header">
                <div class="asset-title">🏭 {asset['name']} <span class="enterprise-badge">ENTERPRISE</span> <span class="cloud-badge">CLOUD</span></div>
                <p>Asset ID: {asset['id']} | Enterprise Asset Management | Cloud Run Optimized</p>
            </div>
            
            <div class="asset-info">
                <div class="info-card">
                    <h3>Type</h3>
                    <p>{asset['asset_type']}</p>
                </div>
                <div class="info-card">
                    <h3>Location</h3>
                    <p>{asset['location']}</p>
                </div>
                <div class="info-card">
                    <h3>Status</h3>
                    <p>{asset['status']}</p>
                </div>
                <div class="info-card">
                    <h3>Criticality</h3>
                    <p>{asset['criticality']}</p>
                </div>
                <div class="info-card">
                    <h3>Manufacturer</h3>
                    <p>{asset.get('manufacturer', 'N/A')}</p>
                </div>
                <div class="info-card">
                    <h3>Model</h3>
                    <p>{asset.get('model', 'N/A')}</p>
                </div>
            </div>
            
            <a href="/assets" class="nav-link">← Back to Assets</a>
            <a href="/" class="nav-link">🏠 Dashboard</a>
        </div>
        
        <!-- CMMS Core Functions -->
        <script src="/static/js/cmms-functions.js"></script>
        <!-- Data Mode Toggle System -->
        <script src="/static/js/data-mode-toggle.js"></script>
        <!-- AI Assistant Integration -->
        <script src="/ai-inject.js"></script>
    </body>
    </html>
    """

# Additional pages (simplified for Cloud Run)
@app.get("/assets", response_class=HTMLResponse)
async def assets_page():
    return """<!DOCTYPE html>
    <html>
    <head>
        <title>Assets - ChatterFix CMMS Enterprise</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #212121 0%, #434A54 50%, #2E4053 100%);
            min-height: 100vh;
        }
        .header {
            background: rgba(33,33,33,0.3);
            padding: 20px;
            backdrop-filter: blur(20px);
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: white;
        }
        .logo {
            font-size: 1.5em;
            font-weight: 700;
        }
        .enterprise-badge {
            background: linear-gradient(45deg, #2E4053, #666666);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
        }
        .cloud-badge {
            background: linear-gradient(45deg, #434A54, #8B9467);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7em;
            font-weight: 600;
            margin-left: 10px;
        }
        .nav {
            background: rgba(33,33,33,0.2);
            padding: 15px 20px;
            display: flex;
            gap: 20px;
        }
        .nav a {
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 10px;
            transition: all 0.3s ease;
        }
        .nav a:hover, .nav a.active {
            background: rgba(33,33,33,0.3);
        }
        .content {
            padding: 30px;
            max-width: 1200px;
            margin: 0 auto;
        }
        .page-header {
            color: white;
            margin-bottom: 30px;
        }
        .page-header h1 {
            font-size: 2.5em;
            margin: 0;
        }
        .page-header p {
            font-size: 1.2em;
            opacity: 0.8;
        }
        .assets-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }
        .asset-card {
            background: rgba(33,33,33,0.3);
            padding: 25px;
            border-radius: 20px;
            backdrop-filter: blur(20px);
            color: white;
            box-shadow: 0 8px 32px rgba(46,64,83,0.4), 0 0 0 1px rgba(102,102,102,0.3);
        }
        .asset-card h3 {
            margin: 0 0 15px 0;
            font-size: 1.3em;
        }
        .asset-status {
            padding: 6px 12px;
            border-radius: 15px;
            font-size: 0.9em;
            font-weight: 500;
            margin-bottom: 15px;
            display: inline-block;
        }
        .status-operational { background: #456789; }
        .status-maintenance { background: #455A64; }
        .status-critical { background: #1C3445; }
        .btn {
            background: rgba(46,64,83,0.4);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 10px;
            cursor: pointer;
            margin-top: 15px;
            font-weight: 500;
            text-decoration: none;
            display: inline-block;
        }
        .btn:hover {
            background: rgba(67,74,84,0.5);
        }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="logo">🔧 ChatterFix CMMS <span class="enterprise-badge">ENTERPRISE</span><span class="cloud-badge">CLOUD RUN</span></div>
            <div class="user-info">
                <span>Welcome, Demo User (Admin)</span>
                <a href="/login" style="color: white;">Login</a>
            </div>
        </div>
        
        <div class="nav">
            <a href="/">🏠 Dashboard</a>
            <a href="/work-orders">📋 Work Orders</a>
            <a href="/assets" class="active">⚙️ Assets</a>
            <a href="/parts">🔩 Parts</a>
            <a href="/reports">📊 Reports</a>
            <a href="/ui/ai-command-center">🧠 AI Command Center</a>
            <a href="/login">🔐 Login</a>
        </div>
        
        <div class="content">
            <div class="page-header">
                <h1>🏭 Assets</h1>
                <p>Enterprise asset management with predictive maintenance</p>
            </div>
            
            <div class="assets-grid">
                <div class="asset-card" onclick="showAssetDetails(1)" style="cursor: pointer; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 12px 40px rgba(46,64,83,0.6)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 8px 32px rgba(46,64,83,0.4)'">
                    <h3>Main Water Pump #1</h3>
                    <div class="asset-status status-operational">Operational</div>
                    <p><strong>Type:</strong> Centrifugal Pump</p>
                    <p><strong>Model:</strong> Grundfos CR 32-4</p>
                    <p><strong>Location:</strong> Pump Room A</p>
                    <p><strong>Last Maintenance:</strong> 2025-09-15</p>
                    <p><strong>Next Service:</strong> 2025-12-15</p>
                    <a href="/asset/1" class="btn">🔧 Manage Asset</a>
                </div>
                
                <div class="asset-card" onclick="showAssetDetails(2)" style="cursor: pointer; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 12px 40px rgba(46,64,83,0.6)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 8px 32px rgba(46,64,83,0.4)'">
                    <h3>HVAC System Zone A</h3>
                    <div class="asset-status status-maintenance">Maintenance Due</div>
                    <p><strong>Type:</strong> Air Handling Unit</p>
                    <p><strong>Model:</strong> Carrier 50HJQ</p>
                    <p><strong>Location:</strong> Roof Level 3</p>
                    <p><strong>Last Maintenance:</strong> 2025-06-20</p>
                    <p><strong>Next Service:</strong> 2025-09-30</p>
                    <a href="/asset/2" class="btn">🔧 Manage Asset</a>
                </div>
                
                <div class="asset-card" onclick="showAssetDetails(3)" style="cursor: pointer; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 12px 40px rgba(46,64,83,0.6)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 8px 32px rgba(46,64,83,0.4)'">
                    <h3>Conveyor System #3</h3>
                    <div class="asset-status status-operational">Operational</div>
                    <p><strong>Type:</strong> Belt Conveyor</p>
                    <p><strong>Model:</strong> FlexLink X45</p>
                    <p><strong>Location:</strong> Production Line C</p>
                    <p><strong>Last Maintenance:</strong> 2025-09-20</p>
                    <p><strong>Next Service:</strong> 2025-10-20</p>
                    <a href="/asset/3" class="btn">🔧 Manage Asset</a>
                </div>
                
                <div class="asset-card" onclick="showAssetDetails(4)" style="cursor: pointer; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 12px 40px rgba(46,64,83,0.6)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 8px 32px rgba(46,64,83,0.4)'">
                    <h3>Backup Generator #1</h3>
                    <div class="asset-status status-critical">Critical Alert</div>
                    <p><strong>Type:</strong> Diesel Generator</p>
                    <p><strong>Model:</strong> Caterpillar C15</p>
                    <p><strong>Location:</strong> Generator Room</p>
                    <p><strong>Last Maintenance:</strong> 2025-08-10</p>
                    <p><strong>Next Service:</strong> Overdue</p>
                    <a href="/asset/4" class="btn">🔧 Manage Asset</a>
                </div>
                
                <div class="asset-card" onclick="showAssetDetails(5)" style="cursor: pointer; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 12px 40px rgba(46,64,83,0.6)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 8px 32px rgba(46,64,83,0.4)'">
                    <h3>Safety Station #2</h3>
                    <div class="asset-status status-operational">Operational</div>
                    <p><strong>Type:</strong> Emergency Equipment</p>
                    <p><strong>Model:</strong> SafetyFirst Pro</p>
                    <p><strong>Location:</strong> Production Floor B</p>
                    <p><strong>Last Maintenance:</strong> 2025-09-01</p>
                    <p><strong>Next Service:</strong> 2025-12-01</p>
                    <a href="/asset/5" class="btn">🔧 Manage Asset</a>
                </div>
                
                <div class="asset-card" onclick="showAssetDetails(6)" style="cursor: pointer; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 12px 40px rgba(46,64,83,0.6)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 8px 32px rgba(46,64,83,0.4)'">
                    <h3>Compressor Unit #2</h3>
                    <div class="asset-status status-maintenance">Maintenance Due</div>
                    <p><strong>Type:</strong> Air Compressor</p>
                    <p><strong>Model:</strong> Atlas Copco GA22</p>
                    <p><strong>Location:</strong> Utility Room</p>
                    <p><strong>Last Maintenance:</strong> 2025-07-15</p>
                    <p><strong>Next Service:</strong> 2025-10-15</p>
                    <a href="/asset/6" class="btn">🔧 Manage Asset</a>
                </div>
            </div>
        </div>
        
        <!-- Assets CRUD Functionality -->
        <script>
        // Assets CRUD Functionality
        document.addEventListener('DOMContentLoaded', function() {
            console.log('🏭 Assets CRUD System Loading...');
            
            // Sample assets data (following Llama3's recommendations)
            let assets = [
                {id: 1, name: 'Main Water Pump #1', type: 'Pump', location: 'Facility A - Basement', condition: 'good', manufacturer: 'Grundfos', model: 'CR150', serialNumber: 'GF-2023-001', purchaseDate: '2023-01-15', lastMaintenance: '2025-09-01', nextMaintenance: '2025-12-01', cost: 15000, warranty: '2026-01-15'},
                {id: 2, name: 'HVAC System Zone A', type: 'HVAC', location: 'Building 1 - Roof', condition: 'warning', manufacturer: 'Carrier', model: 'AC-500X', serialNumber: 'CR-2022-045', purchaseDate: '2022-03-20', lastMaintenance: '2025-08-15', nextMaintenance: '2025-11-15', cost: 45000, warranty: '2025-03-20'},
                {id: 3, name: 'Conveyor System #3', type: 'Conveyor', location: 'Production Floor B', condition: 'excellent', manufacturer: 'FlexLink', model: 'CV-1000', serialNumber: 'FL-2024-012', purchaseDate: '2024-02-10', lastMaintenance: '2025-09-10', nextMaintenance: '2025-10-10', cost: 28000, warranty: '2027-02-10'},
                {id: 4, name: 'Backup Generator #1', type: 'Generator', location: 'Utility Room', condition: 'good', manufacturer: 'Caterpillar', model: 'C18', serialNumber: 'CAT-2023-078', purchaseDate: '2023-06-01', lastMaintenance: '2025-09-20', nextMaintenance: '2025-10-20', cost: 75000, warranty: '2028-06-01'},
                {id: 5, name: 'Safety Station #2', type: 'Safety Equipment', location: 'Assembly Line 2', condition: 'good', manufacturer: 'Honeywell', model: 'SS-200', serialNumber: 'HW-2023-156', purchaseDate: '2023-04-12', lastMaintenance: '2025-09-05', nextMaintenance: '2025-12-05', cost: 3500, warranty: '2026-04-12'},
                {id: 6, name: 'Compressor Unit #1', type: 'Compressor', location: 'Equipment Room A', condition: 'warning', manufacturer: 'Atlas Copco', model: 'GA55', serialNumber: 'AC-2022-234', purchaseDate: '2022-11-08', lastMaintenance: '2025-08-25', nextMaintenance: '2025-11-25', cost: 32000, warranty: '2025-11-08'}
            ];
            
            // Create modal for Assets CRUD operations
            function createAssetModal() {
                const modal = document.createElement('div');
                modal.id = 'asset-modal';
                modal.innerHTML = `
                    <div style="
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        background: rgba(0,0,0,0.8);
                        z-index: 2000;
                        display: none;
                        justify-content: center;
                        align-items: center;
                    ">
                        <div style="
                            background: linear-gradient(135deg, #212121 0%, #434A54 50%, #2E4053 100%);
                            padding: 30px;
                            border-radius: 20px;
                            width: 90%;
                            max-width: 700px;
                            max-height: 85vh;
                            overflow-y: auto;
                            color: white;
                            box-shadow: 0 20px 60px rgba(46,64,83,0.6);
                        ">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                                <h2 id="asset-modal-title" style="margin: 0;">Asset Details</h2>
                                <button onclick="closeAssetModal()" style="
                                    background: none;
                                    border: none;
                                    color: white;
                                    font-size: 24px;
                                    cursor: pointer;
                                    padding: 5px;
                                ">×</button>
                            </div>
                            <div id="asset-modal-content"></div>
                            <div style="margin-top: 20px; display: flex; gap: 10px; justify-content: flex-end;">
                                <button onclick="closeAssetModal()" style="
                                    background: rgba(102,102,102,0.3);
                                    color: white;
                                    border: none;
                                    padding: 10px 20px;
                                    border-radius: 10px;
                                    cursor: pointer;
                                ">Cancel</button>
                                <button id="asset-modal-action-btn" style="
                                    background: linear-gradient(45deg, #2E4053, #666666);
                                    color: white;
                                    border: none;
                                    padding: 10px 20px;
                                    border-radius: 10px;
                                    cursor: pointer;
                                    font-weight: 600;
                                ">Save</button>
                            </div>
                        </div>
                    </div>
                `;
                document.body.appendChild(modal);
            }
            
            // Enhanced modal initialization system
            window.ensureModalExists = function(modalId, createFunction) {
                let modal = document.getElementById(modalId);
                if (!modal) {
                    console.log(`🔨 Creating ${modalId}...`);
                    createFunction();
                    modal = document.getElementById(modalId);
                }
                
                if (!modal) {
                    console.error(`❌ Failed to create ${modalId}!`);
                    return false;
                }
                return true;
            };

            // Show asset details with enhanced error handling
            window.showAssetDetails = function(id) {
                console.log('🏭 Opening asset details for ID:', id);
                
                // Ensure modal exists
                if (!ensureModalExists('asset-modal', createAssetModal)) {
                    alert('Error: Unable to open asset details. Please refresh the page.');
                    return;
                }
                
                const asset = assets.find(a => a.id === parseInt(id));
                if (!asset) {
                    console.error('Asset not found:', id);
                    alert('Asset not found. Please refresh the page.');
                    return;
                }
                
                const modal = document.getElementById('asset-modal');
                const title = document.getElementById('asset-modal-title');
                const content = document.getElementById('asset-modal-content');
                const actionBtn = document.getElementById('asset-modal-action-btn');
                
                title.textContent = asset.name;
                
                const conditionColor = asset.condition === 'excellent' ? '#87CEEB' : 
                                     asset.condition === 'good' ? '#456789' : 
                                     asset.condition === 'warning' ? '#455A64' : '#1C3445';
                
                content.innerHTML = `
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; line-height: 1.8;">
                        <div>
                            <p><strong>🏭 Asset Type:</strong> ${asset.type}</p>
                            <p><strong>📍 Location:</strong> ${asset.location}</p>
                            <p><strong>🏭 Manufacturer:</strong> ${asset.manufacturer}</p>
                            <p><strong>📋 Model:</strong> ${asset.model}</p>
                            <p><strong>🔢 Serial Number:</strong> ${asset.serialNumber}</p>
                            <p><strong>📅 Purchase Date:</strong> ${asset.purchaseDate}</p>
                        </div>
                        <div>
                            <p><strong>💰 Purchase Cost:</strong> $${asset.cost.toLocaleString()}</p>
                            <p><strong>🛡️ Warranty Until:</strong> ${asset.warranty}</p>
                            <p><strong>🔧 Last Maintenance:</strong> ${asset.lastMaintenance}</p>
                            <p><strong>📅 Next Maintenance:</strong> ${asset.nextMaintenance}</p>
                            <p><strong>📊 Condition:</strong> <span style="background: ${conditionColor}; padding: 4px 12px; border-radius: 15px; font-size: 0.9em;">${asset.condition.charAt(0).toUpperCase() + asset.condition.slice(1)}</span></p>
                        </div>
                    </div>
                    <div style="margin: 20px 0; padding: 15px; background: rgba(46,64,83,0.4); border-radius: 10px; border-left: 4px solid #8B9467;">
                        <strong style="color: #8B9467;">🤖 AI Asset Insight:</strong> This ${asset.type.toLowerCase()} is in ${asset.condition} condition. 
                        ${asset.condition === 'warning' ? 'Consider scheduling maintenance soon.' : 
                          asset.condition === 'excellent' ? 'Asset is performing optimally.' : 
                          'Asset is operating within normal parameters.'}
                        Next maintenance due: ${asset.nextMaintenance}
                    </div>
                `;
                
                actionBtn.textContent = 'Edit Asset';
                actionBtn.onclick = () => editAsset(id);
                
                modal.style.display = 'flex';
            };
            
            // Edit asset
            window.editAsset = function(id) {
                const asset = assets.find(a => a.id === parseInt(id));
                if (!asset) return;
                
                const content = document.getElementById('asset-modal-content');
                const actionBtn = document.getElementById('asset-modal-action-btn');
                
                content.innerHTML = `
                    <form id="asset-edit-form" style="display: grid; gap: 15px;">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Asset Name:</label>
                                <input type="text" id="edit-asset-name" value="${asset.name}" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Asset Type:</label>
                                <select id="edit-asset-type" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                                    <option value="Pump" ${asset.type === 'Pump' ? 'selected' : ''}>Pump</option>
                                    <option value="HVAC" ${asset.type === 'HVAC' ? 'selected' : ''}>HVAC</option>
                                    <option value="Conveyor" ${asset.type === 'Conveyor' ? 'selected' : ''}>Conveyor</option>
                                    <option value="Generator" ${asset.type === 'Generator' ? 'selected' : ''}>Generator</option>
                                    <option value="Compressor" ${asset.type === 'Compressor' ? 'selected' : ''}>Compressor</option>
                                    <option value="Safety Equipment" ${asset.type === 'Safety Equipment' ? 'selected' : ''}>Safety Equipment</option>
                                    <option value="Motor" ${asset.type === 'Motor' ? 'selected' : ''}>Motor</option>
                                    <option value="Other" ${asset.type === 'Other' ? 'selected' : ''}>Other</option>
                                </select>
                            </div>
                        </div>
                        <div>
                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">Location:</label>
                            <input type="text" id="edit-asset-location" value="${asset.location}" style="
                                width: 100%;
                                padding: 10px;
                                border: 1px solid rgba(102,102,102,0.3);
                                border-radius: 8px;
                                background: rgba(46,64,83,0.4);
                                color: white;
                                outline: none;
                            ">
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;">
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Manufacturer:</label>
                                <input type="text" id="edit-asset-manufacturer" value="${asset.manufacturer}" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Model:</label>
                                <input type="text" id="edit-asset-model" value="${asset.model}" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Serial Number:</label>
                                <input type="text" id="edit-asset-serial" value="${asset.serialNumber}" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;">
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Purchase Date:</label>
                                <input type="date" id="edit-asset-purchase" value="${asset.purchaseDate}" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Purchase Cost ($):</label>
                                <input type="number" id="edit-asset-cost" value="${asset.cost}" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Warranty Until:</label>
                                <input type="date" id="edit-asset-warranty" value="${asset.warranty}" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;">
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Condition:</label>
                                <select id="edit-asset-condition" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                                    <option value="excellent" ${asset.condition === 'excellent' ? 'selected' : ''}>Excellent</option>
                                    <option value="good" ${asset.condition === 'good' ? 'selected' : ''}>Good</option>
                                    <option value="warning" ${asset.condition === 'warning' ? 'selected' : ''}>Warning</option>
                                    <option value="critical" ${asset.condition === 'critical' ? 'selected' : ''}>Critical</option>
                                </select>
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Last Maintenance:</label>
                                <input type="date" id="edit-asset-last-maintenance" value="${asset.lastMaintenance}" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Next Maintenance:</label>
                                <input type="date" id="edit-asset-next-maintenance" value="${asset.nextMaintenance}" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                            </div>
                        </div>
                    </form>
                    <div style="margin: 20px 0; padding: 15px; background: rgba(28,52,69,0.4); border-radius: 10px; border-left: 4px solid #8B9467;">
                        <button onclick="deleteAsset(${id})" style="
                            background: linear-gradient(45deg, #8B2635, #A73C4A);
                            color: white;
                            border: none;
                            padding: 8px 16px;
                            border-radius: 8px;
                            cursor: pointer;
                            font-weight: 600;
                        ">🗑️ Delete Asset</button>
                    </div>
                `;
                
                actionBtn.textContent = 'Save Changes';
                actionBtn.onclick = () => saveAsset(id);
            };
            
            // Save asset changes
            window.saveAsset = async function(id) {
                try {
                    const formData = {
                        name: document.getElementById('edit-asset-name').value,
                        type: document.getElementById('edit-asset-type').value,
                        location: document.getElementById('edit-asset-location').value,
                        manufacturer: document.getElementById('edit-asset-manufacturer').value,
                        model: document.getElementById('edit-asset-model').value,
                        serialNumber: document.getElementById('edit-asset-serial').value,
                        purchaseDate: document.getElementById('edit-asset-purchase').value,
                        cost: parseFloat(document.getElementById('edit-asset-cost').value),
                        warranty: document.getElementById('edit-asset-warranty').value,
                        condition: document.getElementById('edit-asset-condition').value,
                        lastMaintenance: document.getElementById('edit-asset-last-maintenance').value,
                        nextMaintenance: document.getElementById('edit-asset-next-maintenance').value
                    };
                    
                    const response = await fetch(`/api/assets/${id}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(formData)
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        alert('✅ Asset updated successfully!');
                        closeAssetModal();
                        location.reload();
                    } else {
                        alert('❌ Error updating asset: ' + result.error);
                    }
                } catch (error) {
                    alert('❌ Network error: ' + error.message);
                }
            };
            
            // Delete asset
            window.deleteAsset = async function(id) {
                if (confirm('⚠️ Are you sure you want to delete this asset? This action cannot be undone.')) {
                    try {
                        const response = await fetch(`/api/assets/${id}`, {
                            method: 'DELETE',
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            alert('🗑️ Asset deleted successfully!');
                            closeAssetModal();
                            location.reload();
                        } else {
                            alert('❌ Error deleting asset: ' + result.error);
                        }
                    } catch (error) {
                        alert('❌ Network error: ' + error.message);
                    }
                }
            };
            
            // Close modal
            window.closeAssetModal = function() {
                const modal = document.getElementById('asset-modal');
                modal.style.display = 'none';
            };
            
            // Add click handlers to existing buttons
            document.querySelectorAll('.btn').forEach((btn, index) => {
                btn.onclick = () => showAssetDetails(index + 1);
                btn.style.cursor = 'pointer';
                btn.innerHTML = '🏭 View & Edit Asset';
            });
            
            // Enhanced initialization system
            window.initializeAssetSystem = function() {
                try {
                    console.log('🏭 Initializing Asset Management System...');
                    
                    // Create the modal
                    createAssetModal();
                    
                    // Add enhanced click handlers to all asset cards
                    document.querySelectorAll('.asset-card').forEach((card, index) => {
                        if (!card.onclick) {
                            const assetId = index + 1;
                            card.onclick = () => {
                                console.log(`Asset card ${assetId} clicked`);
                                showAssetDetails(assetId);
                            };
                            card.style.cursor = 'pointer';
                            console.log(`✅ Enhanced click handler added to asset card ${assetId}`);
                        }
                    });
                    
                    // Add enhanced click handlers to asset buttons
                    document.querySelectorAll('.asset-card .btn').forEach((btn, index) => {
                        if (!btn.onclick || btn.onclick.toString().includes('index + 1')) {
                            const assetId = index + 1;
                            btn.onclick = (e) => {
                                e.stopPropagation();
                                console.log(`Asset button ${assetId} clicked`);
                                showAssetDetails(assetId);
                            };
                            btn.style.cursor = 'pointer';
                            btn.innerHTML = '🏭 View & Edit Asset';
                            console.log(`✅ Enhanced click handler added to asset button ${assetId}`);
                        }
                    });
                    
                    console.log('✅ Assets CRUD System Ready!');
                    return true;
                } catch (error) {
                    console.error('❌ Error initializing asset system:', error);
                    return false;
                }
            };
            
            // Initialize when DOM is ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initializeAssetSystem);
            } else {
                initializeAssetSystem();
            }
        });
        </script>
        
        <!-- CMMS Core Functions -->
        <script src="/static/js/cmms-functions.js"></script>
        <!-- AI Assistant Integration -->
        <script src="/ai-inject.js"></script>
    </body>
    </html>"""

# Add redirect for workorders (no dash) to work-orders (with dash)
@app.get("/workorders", response_class=HTMLResponse)
async def workorders_redirect():
    return RedirectResponse(url="/work-orders", status_code=301)

@app.get("/work-orders", response_class=HTMLResponse)
async def work_orders_page():
    return """<!DOCTYPE html>
    <html>
    <head>
        <title>Work Orders - ChatterFix CMMS Enterprise</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #212121 0%, #434A54 50%, #2E4053 100%);
            min-height: 100vh;
        }
        .header {
            background: rgba(33,33,33,0.3);
            padding: 20px;
            backdrop-filter: blur(20px);
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: white;
        }
        .logo {
            font-size: 1.5em;
            font-weight: 700;
        }
        .enterprise-badge {
            background: linear-gradient(45deg, #2E4053, #666666);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
        }
        .cloud-badge {
            background: linear-gradient(45deg, #434A54, #8B9467);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7em;
            font-weight: 600;
            margin-left: 10px;
        }
        .nav {
            background: rgba(33,33,33,0.2);
            padding: 15px 20px;
            display: flex;
            gap: 20px;
        }
        .nav a {
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 10px;
            transition: all 0.3s ease;
        }
        .nav a:hover, .nav a.active {
            background: rgba(33,33,33,0.3);
        }
        .content {
            padding: 30px;
            max-width: 1200px;
            margin: 0 auto;
        }
        .page-header {
            color: white;
            margin-bottom: 30px;
        }
        .page-header h1 {
            font-size: 2.5em;
            margin: 0;
        }
        .page-header p {
            font-size: 1.2em;
            opacity: 0.8;
        }
        .work-orders-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }
        .work-order-card {
            background: rgba(33,33,33,0.3);
            padding: 25px;
            border-radius: 20px;
            backdrop-filter: blur(20px);
            color: white;
            box-shadow: 0 8px 32px rgba(46,64,83,0.4), 0 0 0 1px rgba(102,102,102,0.3);
        }
        .work-order-card h3 {
            margin: 0 0 15px 0;
            font-size: 1.3em;
        }
        .priority {
            padding: 4px 12px;
            border-radius: 10px;
            font-size: 0.8em;
            font-weight: 600;
            margin-bottom: 10px;
            display: inline-block;
        }
        .priority-high { background: #1C3445; }
        .priority-medium { background: #2F4E7F; }
        .priority-low { background: #456789; }
        .status {
            padding: 6px 12px;
            border-radius: 15px;
            font-size: 0.9em;
            font-weight: 500;
            margin-top: 10px;
            display: inline-block;
        }
        .status-open { background: #3498db; }
        .status-progress { background: #455A64; }
        .status-completed { background: #456789; }
        .btn {
            background: rgba(46,64,83,0.4);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 10px;
            cursor: pointer;
            margin-top: 15px;
            font-weight: 500;
        }
        .btn:hover {
            background: rgba(67,74,84,0.5);
        }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="logo">🔧 ChatterFix CMMS <span class="enterprise-badge">ENTERPRISE</span><span class="cloud-badge">CLOUD RUN</span></div>
            <div class="user-info">
                <span>Welcome, Demo User (Admin)</span>
                <a href="/login" style="color: white;">Login</a>
            </div>
        </div>
        
        <div class="nav">
            <a href="/">🏠 Dashboard</a>
            <a href="/work-orders" class="active">📋 Work Orders</a>
            <a href="/assets">⚙️ Assets</a>
            <a href="/parts">🔩 Parts</a>
            <a href="/reports">📊 Reports</a>
            <a href="/ui/ai-command-center">🧠 AI Command Center</a>
            <a href="/login">🔐 Login</a>
        </div>
        
        <div class="content">
            <div class="page-header">
                <h1>🔧 Work Orders</h1>
                <p>Enterprise work order management with AI-powered insights</p>
                <div style="margin-top: 15px;">
                    <button class="btn" onclick="createNewWorkOrder()" style="background: linear-gradient(45deg, #2E4053, #8B9467); color: white; font-weight: 600;">
                        + Create New Work Order
                    </button>
                    <button class="btn" onclick="createNewAsset()" style="background: linear-gradient(45deg, #434A54, #666666); color: white; font-weight: 600; margin-left: 10px;">
                        + Create New Asset
                    </button>
                    <button class="btn" onclick="createNewPart()" style="background: linear-gradient(45deg, #456789, #2F4E7F); color: white; font-weight: 600; margin-left: 10px;">
                        + Create New Part
                    </button>
                </div>
            </div>
            
            <div class="work-orders-grid">
                <div class="work-order-card" onclick="showWorkOrderDetails(1)" style="cursor: pointer; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 12px 40px rgba(46,64,83,0.6)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 8px 32px rgba(46,64,83,0.4)'">
                    <h3>WO-001: Pump Maintenance</h3>
                    <div class="priority priority-high">High Priority</div>
                    <p><strong>Asset:</strong> Main Water Pump #1</p>
                    <p><strong>Description:</strong> Scheduled maintenance and inspection</p>
                    <p><strong>Assigned:</strong> John Technician</p>
                    <p><strong>Due Date:</strong> 2025-09-30</p>
                    <div class="status status-open">Open</div>
                    <button class="btn" onclick="event.stopPropagation(); showWorkOrderDetails(1)">🔧 Manage Work Order</button>
                </div>
                
                <div class="work-order-card" onclick="showWorkOrderDetails(2)" style="cursor: pointer; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 12px 40px rgba(46,64,83,0.6)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 8px 32px rgba(46,64,83,0.4)'">
                    <h3>WO-002: HVAC Filter Replace</h3>
                    <div class="priority priority-medium">Medium Priority</div>
                    <p><strong>Asset:</strong> HVAC System Zone A</p>
                    <p><strong>Description:</strong> Replace air filters quarterly</p>
                    <p><strong>Assigned:</strong> Mike Maintenance</p>
                    <p><strong>Due Date:</strong> 2025-10-05</p>
                    <div class="status status-progress">In Progress</div>
                    <button class="btn" onclick="event.stopPropagation(); showWorkOrderDetails(2)">🔧 Manage Work Order</button>
                </div>
                
                <div class="work-order-card" onclick="showWorkOrderDetails(3)" style="cursor: pointer; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 12px 40px rgba(46,64,83,0.6)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 8px 32px rgba(46,64,83,0.4)'">
                    <h3>WO-003: Conveyor Belt Check</h3>
                    <div class="priority priority-low">Low Priority</div>
                    <p><strong>Asset:</strong> Conveyor System #3</p>
                    <p><strong>Description:</strong> Weekly safety inspection</p>
                    <p><strong>Assigned:</strong> Sarah Inspector</p>
                    <p><strong>Due Date:</strong> 2025-10-10</p>
                    <div class="status status-completed">Completed</div>
                    <button class="btn" onclick="event.stopPropagation(); showWorkOrderDetails(3)">🔧 Manage Work Order</button>
                </div>
                
                <div class="work-order-card" onclick="showWorkOrderDetails(4)" style="cursor: pointer; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 12px 40px rgba(46,64,83,0.6)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 8px 32px rgba(46,64,83,0.4)'">
                    <h3>WO-004: Emergency Generator Test</h3>
                    <div class="priority priority-high">High Priority</div>
                    <p><strong>Asset:</strong> Backup Generator #1</p>
                    <p><strong>Description:</strong> Monthly load test required</p>
                    <p><strong>Assigned:</strong> Tom Electric</p>
                    <p><strong>Due Date:</strong> 2025-09-28</p>
                    <div class="status status-open">Open</div>
                    <button class="btn" onclick="event.stopPropagation(); showWorkOrderDetails(4)">🔧 Manage Work Order</button>
                </div>
                
                <div class="work-order-card" onclick="showWorkOrderDetails(5)" style="cursor: pointer; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 12px 40px rgba(46,64,83,0.6)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 8px 32px rgba(46,64,83,0.4)'">
                    <h3>WO-005: Safety Equipment Check</h3>
                    <div class="priority priority-medium">Medium Priority</div>
                    <p><strong>Asset:</strong> Safety Station #2</p>
                    <p><strong>Description:</strong> Inspect fire extinguishers and emergency equipment</p>
                    <p><strong>Assigned:</strong> Lisa Safety</p>
                    <p><strong>Due Date:</strong> 2025-10-01</p>
                    <div class="status status-open">Open</div>
                    <button class="btn" onclick="event.stopPropagation(); showWorkOrderDetails(5)">🔧 Manage Work Order</button>
                </div>
            </div>
        </div>
        
        <!-- CRUD Functionality -->
        <script>
        // Global variables and functions accessible to onclick handlers
        let workOrders = [];
        let checkedOutParts = [];
        let timeEntries = [];
        let timerStart = null;
        let timerInterval = null;
        let isDrawing = false;
        let signatureCanvas = null;
        let signatureCtx = null;

        // Global functions accessible to HTML onclick handlers
        window.showWorkOrderDetails = async function(id) {
            console.log('🔧 Opening work order details for ID:', id);
            
            // Ensure work orders are loaded
            if (!workOrders || workOrders.length === 0) {
                console.log('📋 Loading work orders from database...');
                await loadWorkOrders();
            }
            
            const workOrder = workOrders.find(wo => wo.id === parseInt(id));
            if (!workOrder) {
                console.error('❌ Work order not found:', id);
                console.log('Available work orders:', workOrders);
                alert('Work order not found. Please try again.');
                return;
            }
            
            console.log('✅ Found work order:', workOrder);
            
            // Ensure modal exists
            let modal = document.getElementById('work-order-modal');
            if (!modal) {
                console.log('🔨 Creating modal...');
                createModal();
                modal = document.getElementById('work-order-modal');
            }
            
            if (!modal) {
                console.error('❌ Failed to create modal!');
                alert('Error: Unable to open work order details. Please refresh the page.');
                return;
            }
            
            // Get AI insights for this work order
            let aiInsights = null;
            try {
                const aiResponse = await fetch('/global-ai/process-message', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        message: `Analyze work order: ${workOrder.title} - ${workOrder.description}. Priority: ${workOrder.priority}. Status: ${workOrder.status}. Provide insights on urgency, risks, and recommendations.`,
                        context: {
                            action: 'analyze_work_order',
                            work_order_id: id,
                            work_order_data: workOrder
                        }
                    })
                });
                const aiResult = await aiResponse.json();
                if (aiResult.success) {
                    aiInsights = aiResult.response;
                }
            } catch (error) {
                console.error('Failed to get AI insights:', error);
                aiInsights = 'AI analysis temporarily unavailable';
            }
            
            const title = document.getElementById('modal-title');
            const content = document.getElementById('modal-content');
            
            if (!title || !content) {
                console.error('❌ Modal elements not found!');
                alert('Error: Modal is corrupted. Please refresh the page.');
                return;
            }
            
            title.textContent = workOrder.title;
            content.innerHTML = `
                <!-- AI Insights Panel -->
                <div style="background: linear-gradient(135deg, rgba(139, 148, 103, 0.2), rgba(46, 64, 83, 0.3)); border-radius: 12px; padding: 15px; margin-bottom: 20px; border-left: 4px solid #8B9467;">
                    <h4 style="margin: 0 0 10px 0; color: #8B9467; display: flex; align-items: center; gap: 8px;">
                        🤖 AI Brain Analysis
                    </h4>
                    <div style="color: rgba(255,255,255,0.9); font-size: 14px; line-height: 1.6;">
                        ${aiInsights || 'Loading AI insights...'}
                    </div>
                </div>
                
                <!-- Work Order Details -->
                <div style="line-height: 1.8;">
                    <p><strong>📋 Priority:</strong> <span style="color: ${workOrder.priority === 'high' ? '#e74c3c' : workOrder.priority === 'medium' ? '#f39c12' : '#2ecc71'}">${workOrder.priority}</span></p>
                    <p><strong>🔧 Status:</strong> ${workOrder.status}</p>
                    <p><strong>👤 Assigned:</strong> ${workOrder.assigned || 'Unassigned'}</p>
                    <p><strong>📅 Due Date:</strong> ${workOrder.dueDate || 'Not set'}</p>
                    <p><strong>📄 Description:</strong> ${workOrder.description}</p>
                </div>
            `;
            
            modal.style.display = 'flex';
            console.log('✅ Modal opened successfully for work order:', id);
        };
        
        
        
        
        
        // Global loadWorkOrders function
        window.loadWorkOrders = async function() {
            try {
                const response = await fetch('/api/work-orders-list');
                const result = await response.json();
                if (result.success) {
                    workOrders = result.work_orders;
                    console.log('📋 Loaded', workOrders.length, 'work orders from database');
                } else {
                    console.error('Failed to load work orders:', result.error);
                    // Fallback to sample data
                    workOrders = [
                        {id: 1, title: 'WO-001: Pump Maintenance', priority: 'high', asset: 'Main Water Pump #1', description: 'Scheduled maintenance and inspection', assigned: 'John Technician', dueDate: '2025-09-30', status: 'open'},
                        {id: 2, title: 'WO-002: HVAC Filter Replace', priority: 'medium', asset: 'HVAC System Zone A', description: 'Replace air filters quarterly', assigned: 'Mike Maintenance', dueDate: '2025-10-05', status: 'progress'}
                    ];
                }
            } catch (error) {
                console.error('Error loading work orders:', error);
                // Fallback to sample data
                workOrders = [
                    {id: 1, title: 'WO-001: Pump Maintenance', priority: 'high', asset: 'Main Water Pump #1', description: 'Scheduled maintenance and inspection', assigned: 'John Technician', dueDate: '2025-09-30', status: 'open'}
                ];
            }
        };

        // Work Order CRUD Functionality
        document.addEventListener('DOMContentLoaded', function() {
            console.log('🔧 Work Orders CRUD System Loading...');
            
            
            // Create modal for CRUD operations
            function createModal() {
                const modal = document.createElement('div');
                modal.id = 'work-order-modal';
                modal.innerHTML = `
                    <div style="
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        background: rgba(0,0,0,0.8);
                        z-index: 2000;
                        display: none;
                        justify-content: center;
                        align-items: center;
                    ">
                        <div style="
                            background: linear-gradient(135deg, #212121 0%, #434A54 50%, #2E4053 100%);
                            padding: 30px;
                            border-radius: 20px;
                            width: 90%;
                            max-width: 600px;
                            max-height: 80vh;
                            overflow-y: auto;
                            color: white;
                            box-shadow: 0 20px 60px rgba(46,64,83,0.6);
                        ">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                                <h2 id="modal-title" style="margin: 0;">Work Order Details</h2>
                                <button onclick="closeModal()" style="
                                    background: none;
                                    border: none;
                                    color: white;
                                    font-size: 24px;
                                    cursor: pointer;
                                    padding: 5px;
                                ">×</button>
                            </div>
                            <div id="modal-content"></div>
                            <div style="margin-top: 20px; display: flex; gap: 10px; justify-content: flex-end;">
                                <button onclick="closeModal()" style="
                                    background: rgba(102,102,102,0.3);
                                    color: white;
                                    border: none;
                                    padding: 10px 20px;
                                    border-radius: 10px;
                                    cursor: pointer;
                                ">Cancel</button>
                                <button id="modal-action-btn" style="
                                    background: linear-gradient(45deg, #2E4053, #666666);
                                    color: white;
                                    border: none;
                                    padding: 10px 20px;
                                    border-radius: 10px;
                                    cursor: pointer;
                                    font-weight: 600;
                                ">Save</button>
                            </div>
                        </div>
                    </div>
                `;
                document.body.appendChild(modal);
            }
            
        // Duplicate showWorkOrderDetails function removed - using global version
                const workOrder = workOrders.find(wo => wo.id === parseInt(id));
                if (!workOrder) {
                    console.error('Work order not found:', id);
                    return;
                }
                
                // Get AI insights for this work order
                let aiInsights = null;
                try {
                    const aiResponse = await fetch('/global-ai/process-message', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            message: `Analyze work order: ${workOrder.title} - ${workOrder.description}. Priority: ${workOrder.priority}. Status: ${workOrder.status}. Provide insights on urgency, risks, and recommendations.`,
                            context: {
                                action: 'analyze_work_order',
                                work_order_id: id,
                                work_order_data: workOrder
                            }
                        })
                    });
                    const aiResult = await aiResponse.json();
                    if (aiResult.success) {
                        aiInsights = aiResult.response;
                    }
                } catch (error) {
                    console.error('Failed to get AI insights:', error);
                }
                
                const modal = document.getElementById('work-order-modal');
                const title = document.getElementById('modal-title');
                const content = document.getElementById('modal-content');
                const actionBtn = document.getElementById('modal-action-btn');
                
                title.textContent = workOrder.title;
                content.innerHTML = `
                    <!-- AI Insights Panel -->
                    ${aiInsights ? `
                    <div style="background: linear-gradient(135deg, rgba(139, 148, 103, 0.2), rgba(46, 64, 83, 0.3)); border-radius: 12px; padding: 15px; margin-bottom: 20px; border-left: 4px solid #8B9467;">
                        <h4 style="margin: 0 0 10px 0; color: #8B9467; display: flex; align-items: center; gap: 8px;">
                            🤖 AI Brain Analysis
                        </h4>
                        <div style="color: rgba(255,255,255,0.9); font-size: 14px; line-height: 1.6;">
                            ${aiInsights}
                        </div>
                    </div>
                    ` : '<div style="text-align: center; padding: 10px; color: rgba(255,255,255,0.6);">🤖 AI Brain is analyzing...</div>'}
                    
                    <!-- Tab Navigation -->
                    <div style="display: flex; margin-bottom: 20px; border-bottom: 1px solid rgba(102,102,102,0.3);">
                        <button onclick="showTab('details')" id="tab-details" class="tab-btn" style="padding: 10px 20px; border: none; background: none; color: white; cursor: pointer; border-bottom: 2px solid #8B9467;">📋 Details</button>
                        <button onclick="showTab('parts')" id="tab-parts" class="tab-btn" style="padding: 10px 20px; border: none; background: none; color: rgba(255,255,255,0.7); cursor: pointer; border-bottom: 2px solid transparent;">🔧 Parts</button>
                        <button onclick="showTab('time')" id="tab-time" class="tab-btn" style="padding: 10px 20px; border: none; background: none; color: rgba(255,255,255,0.7); cursor: pointer; border-bottom: 2px solid transparent;">⏱️ Time</button>
                        <button onclick="showTab('complete')" id="tab-complete" class="tab-btn" style="padding: 10px 20px; border: none; background: none; color: rgba(255,255,255,0.7); cursor: pointer; border-bottom: 2px solid transparent;">✅ Complete</button>
                    </div>
                    
                    <!-- Details Tab -->
                    <div id="details-tab" class="tab-content">
                        <div style="line-height: 1.8;">
                            <p><strong>🏭 Asset:</strong> ${workOrder.asset}</p>
                            <p><strong>📋 Description:</strong> ${workOrder.description}</p>
                            <p><strong>👤 Assigned:</strong> ${workOrder.assigned}</p>
                            <p><strong>📅 Due Date:</strong> ${workOrder.dueDate}</p>
                            <p><strong>⚡ Priority:</strong> <span class="priority priority-${workOrder.priority}" style="padding: 4px 12px; border-radius: 15px; font-size: 0.9em;">${workOrder.priority.charAt(0).toUpperCase() + workOrder.priority.slice(1)}</span></p>
                            <p><strong>📊 Status:</strong> <span class="status status-${workOrder.status}" style="padding: 4px 12px; border-radius: 15px; font-size: 0.9em;">${workOrder.status.charAt(0).toUpperCase() + workOrder.status.slice(1)}</span></p>
                        </div>
                        <div style="margin: 20px 0; padding: 15px; background: rgba(46,64,83,0.4); border-radius: 10px; border-left: 4px solid #8B9467;">
                            <strong style="color: #8B9467;">🤖 AI Insight:</strong> This work order is ${workOrder.priority} priority. ${workOrder.status === 'open' ? 'Consider assigning resources soon.' : workOrder.status === 'progress' ? 'Work is currently in progress.' : 'Work has been completed successfully.'}
                        </div>
                    </div>
                    
                    <!-- Parts Tab -->
                    <div id="parts-tab" class="tab-content" style="display: none;">
                        <h4 style="margin: 0 0 15px 0; color: #8B9467;">🔧 Parts Management</h4>
                        <div style="background: rgba(46,64,83,0.4); padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                            <h5 style="margin: 0 0 10px 0;">Available Parts</h5>
                            <div id="available-parts">
                                <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px; background: rgba(33,33,33,0.3); margin-bottom: 5px; border-radius: 5px;">
                                    <span>🔩 HVAC Filter (25 available)</span>
                                    <button onclick="checkoutPart('filter', 1)" style="background: #8B9467; color: white; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer;">Checkout</button>
                                </div>
                                <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px; background: rgba(33,33,33,0.3); margin-bottom: 5px; border-radius: 5px;">
                                    <span>⚙️ V-Belt 15" (12 available)</span>
                                    <button onclick="checkoutPart('belt', 1)" style="background: #8B9467; color: white; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer;">Checkout</button>
                                </div>
                                <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px; background: rgba(33,33,33,0.3); margin-bottom: 5px; border-radius: 5px;">
                                    <span>🛢️ Motor Oil 15W-40 (8 available)</span>
                                    <button onclick="checkoutPart('oil', 1)" style="background: #8B9467; color: white; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer;">Checkout</button>
                                </div>
                            </div>
                        </div>
                        <div style="background: rgba(46,64,83,0.4); padding: 15px; border-radius: 10px;">
                            <h5 style="margin: 0 0 10px 0;">Checked Out Parts</h5>
                            <div id="checked-out-parts">
                                <p style="color: rgba(255,255,255,0.7); font-style: italic;">No parts checked out yet</p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Time Tab -->
                    <div id="time-tab" class="tab-content" style="display: none;">
                        <h4 style="margin: 0 0 15px 0; color: #8B9467;">⏱️ Time Tracking</h4>
                        <div style="background: rgba(46,64,83,0.4); padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                            <button id="time-toggle" onclick="toggleTimer()" style="background: #8B9467; color: white; border: none; padding: 10px 20px; border-radius: 10px; cursor: pointer; width: 100%; font-size: 16px;">▶️ Start Work</button>
                            <div id="timer-display" style="text-align: center; font-size: 24px; margin: 15px 0; display: none;">⏱️ 00:00:00</div>
                        </div>
                        <div style="background: rgba(46,64,83,0.4); padding: 15px; border-radius: 10px;">
                            <h5 style="margin: 0 0 10px 0;">Time Entries</h5>
                            <div id="time-entries">
                                <p style="color: rgba(255,255,255,0.7); font-style: italic;">No time entries yet</p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Complete Tab -->
                    <div id="complete-tab" class="tab-content" style="display: none;">
                        <h4 style="margin: 0 0 15px 0; color: #8B9467;">✅ Work Order Completion</h4>
                        <div style="background: rgba(46,64,83,0.4); padding: 15px; border-radius: 10px;">
                            <div style="margin-bottom: 15px;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Completion Notes:</label>
                                <textarea id="completion-notes" placeholder="Describe work completed, any issues found, recommendations..." style="
                                    width: 100%;
                                    height: 80px;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(33,33,33,0.3);
                                    color: white;
                                    outline: none;
                                    resize: vertical;
                                "></textarea>
                            </div>
                            <div style="margin-bottom: 15px;">
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Digital Signature:</label>
                                <canvas id="signature-pad" width="400" height="100" style="
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(33,33,33,0.3);
                                    cursor: crosshair;
                                    width: 100%;
                                    height: 80px;
                                "></canvas>
                                <button onclick="clearSignature()" style="background: rgba(102,102,102,0.3); color: white; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer; margin-top: 5px;">Clear</button>
                            </div>
                            <button onclick="completeWorkOrder(${id})" style="background: linear-gradient(45deg, #2E4053, #8B9467); color: white; border: none; padding: 15px 30px; border-radius: 10px; cursor: pointer; width: 100%; font-size: 16px; font-weight: 600;">🎉 Complete Work Order</button>
                        </div>
                    </div>
                `;
                
                actionBtn.textContent = 'Edit Work Order';
                actionBtn.onclick = () => editWorkOrder(id);
                
                modal.style.display = 'flex';
                
                // Initialize signature pad after modal is shown
                setTimeout(() => {
                    initSignaturePad();
                }, 100);
            };
            
        // Edit work order - GLOBAL FUNCTION
        window.editWorkOrder = function(id) {
                const workOrder = workOrders.find(wo => wo.id === parseInt(id));
                if (!workOrder) return;
                
                const content = document.getElementById('modal-content');
                const actionBtn = document.getElementById('modal-action-btn');
                
                content.innerHTML = `
                    <form id="edit-form" style="display: grid; gap: 15px;">
                        <div>
                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">Work Order Title:</label>
                            <input type="text" id="edit-title" value="${workOrder.title}" style="
                                width: 100%;
                                padding: 10px;
                                border: 1px solid rgba(102,102,102,0.3);
                                border-radius: 8px;
                                background: rgba(46,64,83,0.4);
                                color: white;
                                outline: none;
                            ">
                        </div>
                        <div>
                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">Asset:</label>
                            <input type="text" id="edit-asset" value="${workOrder.asset}" style="
                                width: 100%;
                                padding: 10px;
                                border: 1px solid rgba(102,102,102,0.3);
                                border-radius: 8px;
                                background: rgba(46,64,83,0.4);
                                color: white;
                                outline: none;
                            ">
                        </div>
                        <div>
                            <label style="display: block; margin-bottom: 5px; font-weight: 600;">Description:</label>
                            <textarea id="edit-description" rows="3" style="
                                width: 100%;
                                padding: 10px;
                                border: 1px solid rgba(102,102,102,0.3);
                                border-radius: 8px;
                                background: rgba(46,64,83,0.4);
                                color: white;
                                outline: none;
                                resize: vertical;
                            ">${workOrder.description}</textarea>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Priority:</label>
                                <select id="edit-priority" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                                    <option value="low" ${workOrder.priority === 'low' ? 'selected' : ''}>Low</option>
                                    <option value="medium" ${workOrder.priority === 'medium' ? 'selected' : ''}>Medium</option>
                                    <option value="high" ${workOrder.priority === 'high' ? 'selected' : ''}>High</option>
                                </select>
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Status:</label>
                                <select id="edit-status" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                                    <option value="open" ${workOrder.status === 'open' ? 'selected' : ''}>Open</option>
                                    <option value="progress" ${workOrder.status === 'progress' ? 'selected' : ''}>In Progress</option>
                                    <option value="completed" ${workOrder.status === 'completed' ? 'selected' : ''}>Completed</option>
                                </select>
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Assigned To:</label>
                                <input type="text" id="edit-assigned" value="${workOrder.assigned}" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Due Date:</label>
                                <input type="date" id="edit-dueDate" value="${workOrder.dueDate}" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                            </div>
                        </div>
                    </form>
                    <div style="margin: 20px 0; padding: 15px; background: rgba(28,52,69,0.4); border-radius: 10px; border-left: 4px solid #8B9467;">
                        <button onclick="deleteWorkOrder(${id})" style="
                            background: linear-gradient(45deg, #8B2635, #A73C4A);
                            color: white;
                            border: none;
                            padding: 8px 16px;
                            border-radius: 8px;
                            cursor: pointer;
                            font-weight: 600;
                        ">🗑️ Delete Work Order</button>
                    </div>
                `;
                
                actionBtn.textContent = 'Save Changes';
                actionBtn.onclick = () => saveWorkOrder(id);
            };
            
        // Save work order changes - GLOBAL FUNCTION
        window.saveWorkOrder = async function(id) {
                try {
                    const formData = {
                        title: document.getElementById('edit-title').value,
                        asset: document.getElementById('edit-asset').value,
                        description: document.getElementById('edit-description').value,
                        priority: document.getElementById('edit-priority').value,
                        status: document.getElementById('edit-status').value,
                        assigned: document.getElementById('edit-assigned').value,
                        dueDate: document.getElementById('edit-dueDate').value
                    };
                    
                    const response = await fetch(`/api/work-orders/${id}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(formData)
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        alert('✅ Work Order updated successfully!');
                        closeModal();
                        location.reload();
                    } else {
                        alert('❌ Error updating work order: ' + result.error);
                    }
                } catch (error) {
                    alert('❌ Network error: ' + error.message);
                }
            };
            
        // Delete work order - GLOBAL FUNCTION
        window.deleteWorkOrder = async function(id) {
                if (confirm('⚠️ Are you sure you want to delete this work order? This action cannot be undone.')) {
                    try {
                        const response = await fetch(`/api/work-orders/${id}`, {
                            method: 'DELETE',
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            alert('🗑️ Work Order deleted successfully!');
                            closeModal();
                            location.reload();
                        } else {
                            alert('❌ Error deleting work order: ' + result.error);
                        }
                    } catch (error) {
                        alert('❌ Network error: ' + error.message);
                    }
                }
            };
            
            
            // Button click handlers are already defined in HTML - no need to override
            
        // Tab switching functionality - GLOBAL FUNCTION
        window.showTab = function(tabName) {
                // Hide all tabs
                document.querySelectorAll('.tab-content').forEach(tab => {
                    tab.style.display = 'none';
                });
                
                // Reset all tab buttons
                document.querySelectorAll('.tab-btn').forEach(btn => {
                    btn.style.color = 'rgba(255,255,255,0.7)';
                    btn.style.borderBottomColor = 'transparent';
                });
                
                // Show selected tab
                document.getElementById(tabName + '-tab').style.display = 'block';
                document.getElementById('tab-' + tabName).style.color = 'white';
                document.getElementById('tab-' + tabName).style.borderBottomColor = '#8B9467';
            };
            
        // Parts checkout functionality - GLOBAL FUNCTION
        window.checkoutPart = function(partType, quantity) {
                const partNames = {
                    'filter': '🔩 HVAC Filter',
                    'belt': '⚙️ V-Belt 15"',
                    'oil': '🛢️ Motor Oil 15W-40'
                };
                
                checkedOutParts.push({
                    type: partType,
                    name: partNames[partType],
                    quantity: quantity,
                    time: new Date().toLocaleTimeString()
                });
                
                updateCheckedOutParts();
                
                // Show success message
                const btn = event.target;
                const originalText = btn.textContent;
                btn.textContent = '✅ Checked Out';
                btn.style.background = '#2E4053';
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.style.background = '#8B9467';
                }, 2000);
            };
            
            function updateCheckedOutParts() {
                const container = document.getElementById('checked-out-parts');
                if (checkedOutParts.length === 0) {
                    container.innerHTML = '<p style="color: rgba(255,255,255,0.7); font-style: italic;">No parts checked out yet</p>';
                } else {
                    container.innerHTML = checkedOutParts.map(part => 
                        `<div style="display: flex; justify-content: space-between; align-items: center; padding: 8px; background: rgba(139,148,103,0.3); margin-bottom: 5px; border-radius: 5px;">
                            <span>${part.name} (${part.quantity}x)</span>
                            <small style="color: rgba(255,255,255,0.7);">${part.time}</small>
                        </div>`
                    ).join('');
                }
            }
            
        // Timer functionality - GLOBAL FUNCTION
        window.toggleTimer = function() {
                const btn = document.getElementById('time-toggle');
                const display = document.getElementById('timer-display');
                
                if (timerStart === null) {
                    // Start timer
                    timerStart = new Date();
                    btn.textContent = '⏸️ Stop Work';
                    btn.style.background = '#d32f2f';
                    display.style.display = 'block';
                    
                    timerInterval = setInterval(() => {
                        const elapsed = new Date() - timerStart;
                        const hours = Math.floor(elapsed / 3600000);
                        const minutes = Math.floor((elapsed % 3600000) / 60000);
                        const seconds = Math.floor((elapsed % 60000) / 1000);
                        display.textContent = `⏱️ ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                    }, 1000);
                } else {
                    // Stop timer
                    const elapsed = new Date() - timerStart;
                    const minutes = Math.floor(elapsed / 60000);
                    
                    timeEntries.push({
                        start: timerStart.toLocaleTimeString(),
                        duration: `${Math.floor(minutes / 60)}h ${minutes % 60}m`,
                        date: timerStart.toLocaleDateString()
                    });
                    
                    clearInterval(timerInterval);
                    timerStart = null;
                    btn.textContent = '▶️ Start Work';
                    btn.style.background = '#8B9467';
                    display.style.display = 'none';
                    
                    updateTimeEntries();
                }
            };
            
            function updateTimeEntries() {
                const container = document.getElementById('time-entries');
                if (timeEntries.length === 0) {
                    container.innerHTML = '<p style="color: rgba(255,255,255,0.7); font-style: italic;">No time entries yet</p>';
                } else {
                    container.innerHTML = timeEntries.map(entry => 
                        `<div style="display: flex; justify-content: space-between; align-items: center; padding: 8px; background: rgba(139,148,103,0.3); margin-bottom: 5px; border-radius: 5px;">
                            <span>Started: ${entry.start}</span>
                            <span style="font-weight: 600;">${entry.duration}</span>
                        </div>`
                    ).join('');
                }
            }
            
        // Signature pad functionality - GLOBAL FUNCTIONS  
        function initSignaturePad() {
                signatureCanvas = document.getElementById('signature-pad');
                if (signatureCanvas) {
                    signatureCtx = signatureCanvas.getContext('2d');
                    signatureCtx.strokeStyle = '#ffffff';
                    signatureCtx.lineWidth = 2;
                    signatureCtx.lineCap = 'round';
                    
                    signatureCanvas.addEventListener('mousedown', startDrawing);
                    signatureCanvas.addEventListener('mousemove', draw);
                    signatureCanvas.addEventListener('mouseup', stopDrawing);
                    signatureCanvas.addEventListener('mouseout', stopDrawing);
                    
                    // Touch events for mobile
                    signatureCanvas.addEventListener('touchstart', handleTouch);
                    signatureCanvas.addEventListener('touchmove', handleTouch);
                    signatureCanvas.addEventListener('touchend', stopDrawing);
                }
            }
            
            function startDrawing(e) {
                isDrawing = true;
                const rect = signatureCanvas.getBoundingClientRect();
                signatureCtx.beginPath();
                signatureCtx.moveTo(e.clientX - rect.left, e.clientY - rect.top);
            }
            
            function draw(e) {
                if (!isDrawing) return;
                const rect = signatureCanvas.getBoundingClientRect();
                signatureCtx.lineTo(e.clientX - rect.left, e.clientY - rect.top);
                signatureCtx.stroke();
            }
            
            function stopDrawing() {
                isDrawing = false;
            }
            
            function handleTouch(e) {
                e.preventDefault();
                const touch = e.touches[0];
                const mouseEvent = new MouseEvent(e.type === 'touchstart' ? 'mousedown' : 
                    e.type === 'touchmove' ? 'mousemove' : 'mouseup', {
                    clientX: touch.clientX,
                    clientY: touch.clientY
                });
                signatureCanvas.dispatchEvent(mouseEvent);
            }
            
        window.clearSignature = function() {
                if (signatureCtx) {
                    signatureCtx.clearRect(0, 0, signatureCanvas.width, signatureCanvas.height);
                }
            };
            
        // Work order completion - GLOBAL FUNCTION
        window.completeWorkOrder = function(id) {
                const notes = document.getElementById('completion-notes').value;
                const hasSignature = signatureCtx && !isCanvasBlank(signatureCanvas);
                
                if (!notes.trim()) {
                    alert('Please add completion notes before completing the work order.');
                    return;
                }
                
                if (!hasSignature) {
                    alert('Please provide a digital signature before completing the work order.');
                    return;
                }
                
                // Update work order status
                const workOrder = workOrders.find(wo => wo.id === parseInt(id));
                if (workOrder) {
                    workOrder.status = 'completed';
                    workOrder.completionNotes = notes;
                    workOrder.completedBy = 'Current User';
                    workOrder.completedAt = new Date().toISOString();
                }
                
                // Close modal and refresh view
                closeModal();
                
                // Show success message
                alert(`🎉 Work Order ${workOrder.title} completed successfully!\\n\\nTime entries: ${timeEntries.length}\\nParts used: ${checkedOutParts.length}\\nNotes: ${notes.substring(0, 50)}...`);
                
                // Reset for next work order
                checkedOutParts = [];
                timeEntries = [];
                
                // Refresh the page to show updated status
                location.reload();
            };
            
            function isCanvasBlank(canvas) {
                const blank = document.createElement('canvas');
                blank.width = canvas.width;
                blank.height = canvas.height;
                return canvas.toDataURL() === blank.toDataURL();
            }
            
            // Initialize signature pad when modal is opened - HANDLED IN MAIN FUNCTION
            
            // Close modal function
            window.closeModal = function() {
                const modal = document.getElementById('work-order-modal');
                modal.style.display = 'none';
                
                // Reset timer if running
                if (timerStart !== null) {
                    clearInterval(timerInterval);
                    timerStart = null;
                }
            };
            
        // Dynamic Card Creation Functions with AI Integration - GLOBAL FUNCTIONS
        window.createNewWorkOrder = function() {
                showCreateModal('work-order', 'Create New Work Order', {
                    title: '',
                    description: '',
                    priority: 'medium',
                    status: 'open',
                    assigned: '',
                    dueDate: '',
                    asset: ''
                });
            };
            
        window.createNewAsset = function() {
                showCreateModal('asset', 'Create New Asset', {
                    name: '',
                    type: 'Equipment',
                    location: '',
                    condition: 'Good',
                    manufacturer: '',
                    model: ''
                });
            };
            
        window.createNewPart = function() {
                showCreateModal('part', 'Create New Part', {
                    name: '',
                    part_number: '',
                    category: 'General',
                    quantity: 0,
                    unit_cost: 0.0,
                    location: ''
                });
            };
            
        // Helper functions - GLOBAL SCOPE
        function showCreateModal(type, title, defaultData) {
                const modal = document.getElementById('work-order-modal');
                const modalTitle = document.getElementById('modal-title');
                const modalContent = document.getElementById('modal-content');
                
                modalTitle.textContent = title;
                
                // Generate form based on type
                let formHTML = generateCreateForm(type, defaultData);
                modalContent.innerHTML = formHTML;
                
                // Update modal buttons
                const modalFooter = modal.querySelector('.modal-footer') || createModalFooter();
                modalFooter.innerHTML = `
                    <button onclick="closeModal()" style="
                        background: rgba(102,102,102,0.3);
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 10px;
                        cursor: pointer;
                    ">Cancel</button>
                    <button onclick="saveNewItem('${type}')" style="
                        background: linear-gradient(45deg, #2E4053, #8B9467);
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 10px;
                        cursor: pointer;
                        font-weight: 600;
                    ">Create with AI Analysis</button>
                `;
                
                modal.style.display = 'flex';
            }
            
        function createModalFooter() {
                const modal = document.getElementById('work-order-modal');
                const footer = document.createElement('div');
                footer.className = 'modal-footer';
                footer.style.cssText = 'margin-top: 20px; display: flex; gap: 10px; justify-content: flex-end;';
                modal.querySelector('div > div').appendChild(footer);
                return footer;
            }
            
        function generateCreateForm(type, data) {
                const forms = {
                    'work-order': `
                        <div style="display: grid; gap: 15px;">
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Title:</label>
                                <input type="text" id="create-title" value="${data.title}" placeholder="Work order title..." style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Description:</label>
                                <textarea id="create-description" placeholder="Detailed description..." style="
                                    width: 100%;
                                    height: 80px;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                    resize: vertical;
                                ">${data.description}</textarea>
                            </div>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                                <div>
                                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Priority:</label>
                                    <select id="create-priority" style="
                                        width: 100%;
                                        padding: 10px;
                                        border: 1px solid rgba(102,102,102,0.3);
                                        border-radius: 8px;
                                        background: rgba(46,64,83,0.4);
                                        color: white;
                                        outline: none;
                                    ">
                                        <option value="low" ${data.priority === 'low' ? 'selected' : ''}>Low</option>
                                        <option value="medium" ${data.priority === 'medium' ? 'selected' : ''}>Medium</option>
                                        <option value="high" ${data.priority === 'high' ? 'selected' : ''}>High</option>
                                        <option value="critical" ${data.priority === 'critical' ? 'selected' : ''}>Critical</option>
                                    </select>
                                </div>
                                <div>
                                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Assigned To:</label>
                                    <input type="text" id="create-assigned" value="${data.assigned}" placeholder="Technician name..." style="
                                        width: 100%;
                                        padding: 10px;
                                        border: 1px solid rgba(102,102,102,0.3);
                                        border-radius: 8px;
                                        background: rgba(46,64,83,0.4);
                                        color: white;
                                        outline: none;
                                    ">
                                </div>
                            </div>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                                <div>
                                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Asset:</label>
                                    <input type="text" id="create-asset" value="${data.asset}" placeholder="Related asset..." style="
                                        width: 100%;
                                        padding: 10px;
                                        border: 1px solid rgba(102,102,102,0.3);
                                        border-radius: 8px;
                                        background: rgba(46,64,83,0.4);
                                        color: white;
                                        outline: none;
                                    ">
                                </div>
                                <div>
                                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Due Date:</label>
                                    <input type="date" id="create-dueDate" value="${data.dueDate}" style="
                                        width: 100%;
                                        padding: 10px;
                                        border: 1px solid rgba(102,102,102,0.3);
                                        border-radius: 8px;
                                        background: rgba(46,64,83,0.4);
                                        color: white;
                                        outline: none;
                                    ">
                                </div>
                            </div>
                        </div>
                    `,
                    'asset': `
                        <div style="display: grid; gap: 15px;">
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Asset Name:</label>
                                <input type="text" id="create-name" value="${data.name}" placeholder="Asset name..." style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                            </div>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                                <div>
                                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Type:</label>
                                    <select id="create-type" style="
                                        width: 100%;
                                        padding: 10px;
                                        border: 1px solid rgba(102,102,102,0.3);
                                        border-radius: 8px;
                                        background: rgba(46,64,83,0.4);
                                        color: white;
                                        outline: none;
                                    ">
                                        <option value="Equipment" ${data.type === 'Equipment' ? 'selected' : ''}>Equipment</option>
                                        <option value="Pump" ${data.type === 'Pump' ? 'selected' : ''}>Pump</option>
                                        <option value="HVAC" ${data.type === 'HVAC' ? 'selected' : ''}>HVAC</option>
                                        <option value="Conveyor" ${data.type === 'Conveyor' ? 'selected' : ''}>Conveyor</option>
                                        <option value="Generator" ${data.type === 'Generator' ? 'selected' : ''}>Generator</option>
                                        <option value="Safety Equipment" ${data.type === 'Safety Equipment' ? 'selected' : ''}>Safety Equipment</option>
                                    </select>
                                </div>
                                <div>
                                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Location:</label>
                                    <input type="text" id="create-location" value="${data.location}" placeholder="Asset location..." style="
                                        width: 100%;
                                        padding: 10px;
                                        border: 1px solid rgba(102,102,102,0.3);
                                        border-radius: 8px;
                                        background: rgba(46,64,83,0.4);
                                        color: white;
                                        outline: none;
                                    ">
                                </div>
                            </div>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                                <div>
                                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Manufacturer:</label>
                                    <input type="text" id="create-manufacturer" value="${data.manufacturer}" placeholder="Manufacturer..." style="
                                        width: 100%;
                                        padding: 10px;
                                        border: 1px solid rgba(102,102,102,0.3);
                                        border-radius: 8px;
                                        background: rgba(46,64,83,0.4);
                                        color: white;
                                        outline: none;
                                    ">
                                </div>
                                <div>
                                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Model:</label>
                                    <input type="text" id="create-model" value="${data.model}" placeholder="Model number..." style="
                                        width: 100%;
                                        padding: 10px;
                                        border: 1px solid rgba(102,102,102,0.3);
                                        border-radius: 8px;
                                        background: rgba(46,64,83,0.4);
                                        color: white;
                                        outline: none;
                                    ">
                                </div>
                            </div>
                        </div>
                    `,
                    'part': `
                        <div style="display: grid; gap: 15px;">
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                                <div>
                                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Part Name:</label>
                                    <input type="text" id="create-name" value="${data.name}" placeholder="Part name..." style="
                                        width: 100%;
                                        padding: 10px;
                                        border: 1px solid rgba(102,102,102,0.3);
                                        border-radius: 8px;
                                        background: rgba(46,64,83,0.4);
                                        color: white;
                                        outline: none;
                                    ">
                                </div>
                                <div>
                                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Part Number:</label>
                                    <input type="text" id="create-part_number" value="${data.part_number}" placeholder="Part number..." style="
                                        width: 100%;
                                        padding: 10px;
                                        border: 1px solid rgba(102,102,102,0.3);
                                        border-radius: 8px;
                                        background: rgba(46,64,83,0.4);
                                        color: white;
                                        outline: none;
                                    ">
                                </div>
                            </div>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                                <div>
                                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Category:</label>
                                    <select id="create-category" style="
                                        width: 100%;
                                        padding: 10px;
                                        border: 1px solid rgba(102,102,102,0.3);
                                        border-radius: 8px;
                                        background: rgba(46,64,83,0.4);
                                        color: white;
                                        outline: none;
                                    ">
                                        <option value="General" ${data.category === 'General' ? 'selected' : ''}>General</option>
                                        <option value="Seals" ${data.category === 'Seals' ? 'selected' : ''}>Seals</option>
                                        <option value="Filters" ${data.category === 'Filters' ? 'selected' : ''}>Filters</option>
                                        <option value="Belts" ${data.category === 'Belts' ? 'selected' : ''}>Belts</option>
                                        <option value="Bearings" ${data.category === 'Bearings' ? 'selected' : ''}>Bearings</option>
                                        <option value="Lubricants" ${data.category === 'Lubricants' ? 'selected' : ''}>Lubricants</option>
                                        <option value="Electrical" ${data.category === 'Electrical' ? 'selected' : ''}>Electrical</option>
                                    </select>
                                </div>
                                <div>
                                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Location:</label>
                                    <input type="text" id="create-location" value="${data.location}" placeholder="Storage location..." style="
                                        width: 100%;
                                        padding: 10px;
                                        border: 1px solid rgba(102,102,102,0.3);
                                        border-radius: 8px;
                                        background: rgba(46,64,83,0.4);
                                        color: white;
                                        outline: none;
                                    ">
                                </div>
                            </div>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                                <div>
                                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Quantity:</label>
                                    <input type="number" id="create-quantity" value="${data.quantity}" min="0" style="
                                        width: 100%;
                                        padding: 10px;
                                        border: 1px solid rgba(102,102,102,0.3);
                                        border-radius: 8px;
                                        background: rgba(46,64,83,0.4);
                                        color: white;
                                        outline: none;
                                    ">
                                </div>
                                <div>
                                    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Unit Cost ($):</label>
                                    <input type="number" id="create-unit_cost" value="${data.unit_cost}" min="0" step="0.01" style="
                                        width: 100%;
                                        padding: 10px;
                                        border: 1px solid rgba(102,102,102,0.3);
                                        border-radius: 8px;
                                        background: rgba(46,64,83,0.4);
                                        color: white;
                                        outline: none;
                                    ">
                                </div>
                            </div>
                        </div>
                    `
                };
                
                return forms[type] || '<p>Form not available</p>';
            }
            
            async function saveNewItem(type) {
                const formData = collectFormData(type);
                
                try {
                    // Show loading state
                    const saveBtn = document.querySelector('[onclick="saveNewItem(\\'${type}\\')"]');
                    const originalText = saveBtn.textContent;
                    saveBtn.textContent = '🤖 Creating with AI...';
                    saveBtn.disabled = true;
                    
                    // Call API to create with AI analysis
                    const response = await fetch(`/api/${type}s`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(formData)
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        // Create new card dynamically
                        const newCard = createDynamicCard(type, result[type]);
                        addCardToGrid(type, newCard);
                        
                        // Show AI insights if available
                        if (result[type].ai_insights) {
                            showAIInsights(result[type].ai_insights);
                        }
                        
                        closeModal();
                        alert(`✅ ${type.charAt(0).toUpperCase() + type.slice(1)} created successfully with AI analysis!`);
                    } else {
                        alert(`❌ Error creating ${type}: ` + result.error);
                    }
                } catch (error) {
                    alert(`❌ Network error: ` + error.message);
                } finally {
                    saveBtn.textContent = originalText;
                    saveBtn.disabled = false;
                }
            }
            
            function collectFormData(type) {
                const data = {};
                const form = document.querySelector('#modal-content');
                
                // Collect all input values
                form.querySelectorAll('input, select, textarea').forEach(field => {
                    const fieldName = field.id.replace('create-', '');
                    data[fieldName] = field.value;
                });
                
                return data;
            }
            
            function createDynamicCard(type, data) {
                console.log(`🔨 Creating new ${type} card with ID: ${data.id || 'auto-generated'}`);
                
                const card = document.createElement('div');
                card.className = `${type}-card`;
                card.style.cssText = 'cursor: pointer; transition: all 0.3s ease;';
                
                // Enhanced click handler with error handling
                card.onclick = () => {
                    console.log(`✅ ${type} card clicked - ID: ${data.id}`);
                    try {
                        if (type === 'work-order') {
                            if (window.showWorkOrderDetails) {
                                showWorkOrderDetails(data.id);
                            } else {
                                console.error('❌ showWorkOrderDetails function not found');
                                alert('Unable to open work order details. Please refresh the page.');
                            }
                        } else if (type === 'asset') {
                            if (window.showAssetDetails) {
                                showAssetDetails(data.id);
                            } else {
                                console.error('❌ showAssetDetails function not found');
                                alert('Unable to open asset details. Please refresh the page.');
                            }
                        } else if (type === 'part') {
                            if (window.showPartsDetails) {
                                showPartsDetails(data.id);
                            } else {
                                console.error('❌ showPartsDetails function not found');
                                alert('Unable to open parts details. Please refresh the page.');
                            }
                        }
                    } catch (error) {
                        console.error(`❌ Error opening ${type} details:`, error);
                        alert(`Error opening ${type} details. Please try again.`);
                    }
                };
                
                // Add hover effects
                card.onmouseover = () => {
                    card.style.transform = 'translateY(-5px)';
                    card.style.boxShadow = '0 12px 40px rgba(46,64,83,0.6)';
                };
                card.onmouseout = () => {
                    card.style.transform = 'translateY(0)';
                    card.style.boxShadow = '0 8px 32px rgba(46,64,83,0.4)';
                };
                
                // Add AI badge if insights available
                if (data.ai_insights && data.ai_insights.urgency_level === 'high') {
                    const aiBadge = document.createElement('div');
                    aiBadge.className = 'ai-badge';
                    aiBadge.textContent = '🚨 AI: Urgent';
                    aiBadge.style.cssText = `
                        position: absolute;
                        top: 8px;
                        right: 8px;
                        background: linear-gradient(45deg, #e74c3c, #c0392b);
                        color: white;
                        padding: 4px 8px;
                        border-radius: 12px;
                        font-size: 11px;
                        font-weight: bold;
                        z-index: 10;
                    `;
                    card.style.position = 'relative';
                    card.appendChild(aiBadge);
                }
                
                // Generate card content based on type
                card.innerHTML = generateCardContent(type, data);
                
                return card;
            }
            
            function generateCardContent(type, data) {
                if (type === 'work-order') {
                    return `
                        <h3>WO-${data.id.toString().padStart(3, '0')}: ${data.title}</h3>
                        <div class="priority priority-${data.priority}">${data.priority.charAt(0).toUpperCase() + data.priority.slice(1)} Priority</div>
                        <p><strong>Asset:</strong> ${data.asset || 'N/A'}</p>
                        <p><strong>Description:</strong> ${data.description}</p>
                        <p><strong>Assigned:</strong> ${data.assigned || 'Unassigned'}</p>
                        <p><strong>Due Date:</strong> ${data.dueDate || 'Not set'}</p>
                        <div class="status status-${data.status}">${data.status.charAt(0).toUpperCase() + data.status.slice(1)}</div>
                        <button class="btn" onclick="event.stopPropagation(); showWorkOrderDetails(${data.id})">🔧 Manage Work Order</button>
                    `;
                } else if (type === 'asset') {
                    return `
                        <h3>${data.name}</h3>
                        <div class="asset-status status-operational">Operational</div>
                        <p><strong>Type:</strong> ${data.type}</p>
                        <p><strong>Location:</strong> ${data.location}</p>
                        <p><strong>Manufacturer:</strong> ${data.manufacturer || 'N/A'}</p>
                        <p><strong>Model:</strong> ${data.model || 'N/A'}</p>
                        <button class="btn" onclick="event.stopPropagation(); showAssetDetails(${data.id})">🔧 Manage Asset</button>
                    `;
                } else if (type === 'part') {
                    return `
                        <h3>${data.name}</h3>
                        <div class="stock-status stock-good">In Stock</div>
                        <p><strong>Part Number:</strong> ${data.part_number}</p>
                        <p><strong>Category:</strong> ${data.category}</p>
                        <p><strong>Current Stock:</strong> ${data.quantity} units</p>
                        <p><strong>Unit Cost:</strong> $${data.unit_cost}</p>
                        <p><strong>Location:</strong> ${data.location || 'N/A'}</p>
                        <button class="btn" onclick="event.stopPropagation(); showPartsDetails(${data.id})">🔧 Manage Part</button>
                    `;
                }
            }
            
            function addCardToGrid(type, card) {
                console.log(`📋 Adding ${type} card to grid...`);
                
                let grid;
                let gridSelector;
                
                if (type === 'work-order') {
                    gridSelector = '.work-orders-grid';
                    grid = document.querySelector(gridSelector);
                } else if (type === 'asset') {
                    gridSelector = '.assets-grid';
                    grid = document.querySelector(gridSelector);
                } else if (type === 'part') {
                    gridSelector = '.parts-grid';
                    grid = document.querySelector(gridSelector);
                }
                
                if (grid) {
                    grid.appendChild(card);
                    console.log(`✅ ${type} card successfully added to grid`);
                    
                    // Trigger re-initialization of click handlers if needed
                    setTimeout(() => {
                        if (window.ChatterFixDebug && window.ChatterFixDebug.testAllClickHandlers) {
                            window.ChatterFixDebug.testAllClickHandlers();
                        }
                    }, 100);
                } else {
                    console.error(`❌ Grid not found for ${type}: ${gridSelector}`);
                    console.log('🔍 Available grids:', document.querySelectorAll('[class*="grid"]').length);
                }
            }
            
            function showAIInsights(insights) {
                if (insights.recommendations && insights.recommendations.length > 0) {
                    setTimeout(() => {
                        alert(`🤖 AI Recommendations:\\n\\n${insights.recommendations.join('\\n')}`);
                    }, 1000);
                }
            }
            
            // Enhanced initialization system for work orders
            window.initializeWorkOrderSystem = function() {
                try {
                    console.log('🔧 Initializing Work Order Management System...');
                    
                    // Create modal if it doesn't exist
                    if (!document.getElementById('work-order-modal')) {
                        createModal();
                        console.log('✅ Work order modal created');
                    }
                    
                    // CRITICAL FIX: Replace static cards with dynamic cards from database
                    if (workOrders && workOrders.length > 0) {
                        console.log('🔄 Replacing static cards with dynamic database cards...');
                        const grid = document.querySelector('.work-orders-grid');
                        if (grid) {
                            // Clear existing static cards
                            grid.innerHTML = '';
                            
                            // Create dynamic cards from database
                            workOrders.slice(0, 10).forEach((workOrder, index) => { // Show first 10 work orders
                                const priorityClass = workOrder.priority ? `priority-${workOrder.priority.toLowerCase()}` : 'priority-medium';
                                const statusClass = workOrder.status ? `status-${workOrder.status.toLowerCase().replace(' ', '-')}` : 'status-open';
                                
                                const cardHTML = `
                                    <div class="work-order-card" onclick="showWorkOrderDetails(${workOrder.id})" style="cursor: pointer; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 12px 40px rgba(46,64,83,0.6)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 8px 32px rgba(46,64,83,0.4)'">
                                        <h3>${workOrder.title || 'Untitled Work Order'}</h3>
                                        <div class="priority ${priorityClass}">${workOrder.priority || 'Medium'} Priority</div>
                                        <p><strong>Asset:</strong> ${workOrder.asset || 'Database Asset'}</p>
                                        <p><strong>Description:</strong> ${workOrder.description || 'No description available'}</p>
                                        <p><strong>Assigned:</strong> ${workOrder.assigned || 'Unassigned'}</p>
                                        <p><strong>Due Date:</strong> ${workOrder.dueDate || 'Not set'}</p>
                                        <div class="status ${statusClass}">${workOrder.status || 'Open'}</div>
                                        <button class="btn" onclick="event.stopPropagation(); showWorkOrderDetails(${workOrder.id})">🔧 Manage Work Order</button>
                                    </div>
                                `;
                                grid.innerHTML += cardHTML;
                                console.log(`✅ Created dynamic card for work order ID ${workOrder.id}: ${workOrder.title}`);
                            });
                            
                            console.log(`🎯 Successfully replaced static cards with ${Math.min(workOrders.length, 10)} dynamic cards using actual database IDs`);
                        }
                    } else {
                        console.warn('⚠️ No work orders loaded from database, keeping static cards');
                        // Add enhanced click handlers to static cards (fallback)
                        document.querySelectorAll('.work-order-card').forEach((card, index) => {
                            if (!card.onclick) {
                                const workOrderId = index + 1;
                                card.onclick = () => {
                                    console.log(`Work order card ${workOrderId} clicked`);
                                    showWorkOrderDetails(workOrderId);
                                };
                                card.style.cursor = 'pointer';
                                console.log(`✅ Enhanced click handler added to work order card ${workOrderId}`);
                            }
                        });
                        
                        // Add enhanced click handlers to work order buttons (fallback)
                        document.querySelectorAll('.work-order-card .btn').forEach((btn, index) => {
                            if (!btn.onclick || btn.onclick.toString().includes('showWorkOrderDetails')) {
                                const workOrderId = index + 1;
                                btn.onclick = (e) => {
                                    e.stopPropagation();
                                    console.log(`Work order button ${workOrderId} clicked`);
                                    showWorkOrderDetails(workOrderId);
                                };
                                btn.style.cursor = 'pointer';
                                console.log(`✅ Enhanced click handler added to work order button ${workOrderId}`);
                            }
                        });
                    }
                    
                    console.log('✅ Work Orders CRUD System Ready!');
                    return true;
                } catch (error) {
                    console.error('❌ Error initializing work order system:', error);
                    return false;
                }
            };

            // Load work orders from database and initialize system
            loadWorkOrders().then(() => {
                console.log('✅ Work orders loaded and ready for AI-powered interaction');
                initializeWorkOrderSystem();
            }).catch(error => {
                console.error('❌ Failed to load work orders:', error);
                // Still try to initialize the system even if loading fails
                initializeWorkOrderSystem();
            });
            
            // Initialize when DOM is ready (fallback)
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initializeWorkOrderSystem);
            } else {
                setTimeout(initializeWorkOrderSystem, 100);
            }
        });
        </script>
        
        <!-- CMMS Core Functions -->
        <script src="/static/js/cmms-functions.js"></script>
        <!-- AI Assistant Integration -->
        <script src="/ai-inject.js"></script>
    </body>
    </html>"""

@app.get("/parts", response_class=HTMLResponse)
async def parts_page():
    return """<!DOCTYPE html>
    <html>
    <head>
        <title>Parts - ChatterFix CMMS Enterprise</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #212121 0%, #434A54 50%, #2E4053 100%);
            min-height: 100vh;
        }
        .header {
            background: rgba(33,33,33,0.3);
            padding: 20px;
            backdrop-filter: blur(20px);
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: white;
        }
        .logo {
            font-size: 1.5em;
            font-weight: 700;
        }
        .enterprise-badge {
            background: linear-gradient(45deg, #2E4053, #666666);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
        }
        .cloud-badge {
            background: linear-gradient(45deg, #434A54, #8B9467);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7em;
            font-weight: 600;
            margin-left: 10px;
        }
        .nav {
            background: rgba(33,33,33,0.2);
            padding: 15px 20px;
            display: flex;
            gap: 20px;
        }
        .nav a {
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 10px;
            transition: all 0.3s ease;
        }
        .nav a:hover, .nav a.active {
            background: rgba(33,33,33,0.3);
        }
        .content {
            padding: 30px;
            max-width: 1200px;
            margin: 0 auto;
        }
        .page-header {
            color: white;
            margin-bottom: 30px;
        }
        .page-header h1 {
            font-size: 2.5em;
            margin: 0;
        }
        .page-header p {
            font-size: 1.2em;
            opacity: 0.8;
        }
        .parts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }
        .part-card {
            background: rgba(33,33,33,0.3);
            padding: 25px;
            border-radius: 20px;
            backdrop-filter: blur(20px);
            color: white;
            box-shadow: 0 8px 32px rgba(46,64,83,0.4), 0 0 0 1px rgba(102,102,102,0.3);
        }
        .part-card h3 {
            margin: 0 0 15px 0;
            font-size: 1.3em;
        }
        .stock-status {
            padding: 6px 12px;
            border-radius: 15px;
            font-size: 0.9em;
            font-weight: 500;
            margin-bottom: 15px;
            display: inline-block;
        }
        .stock-good { background: #456789; }
        .stock-low { background: #455A64; }
        .stock-critical { background: #1C3445; }
        .btn {
            background: rgba(46,64,83,0.4);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 10px;
            cursor: pointer;
            margin-top: 15px;
            font-weight: 500;
        }
        .btn:hover {
            background: rgba(67,74,84,0.5);
        }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="logo">🔧 ChatterFix CMMS <span class="enterprise-badge">ENTERPRISE</span><span class="cloud-badge">CLOUD RUN</span></div>
            <div class="user-info">
                <span>Welcome, Demo User (Admin)</span>
                <a href="/login" style="color: white;">Login</a>
            </div>
        </div>
        
        <div class="nav">
            <a href="/">🏠 Dashboard</a>
            <a href="/work-orders">📋 Work Orders</a>
            <a href="/assets">⚙️ Assets</a>
            <a href="/parts" class="active">🔩 Parts</a>
            <a href="/reports">📊 Reports</a>
            <a href="/ui/ai-command-center">🧠 AI Command Center</a>
            <a href="/login">🔐 Login</a>
        </div>
        
        <div class="content">
            <div class="page-header">
                <h1>📦 Parts & Inventory</h1>
                <p>Enterprise inventory management with automated reordering</p>
            </div>
            
            <div class="parts-grid">
                <div class="part-card" onclick="showPartsDetails(1)" style="cursor: pointer; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 12px 40px rgba(46,64,83,0.6)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 8px 32px rgba(46,64,83,0.4)'">
                    <h3>Pump Impeller - Model CR32</h3>
                    <div class="stock-status stock-good">In Stock</div>
                    <p><strong>Part Number:</strong> GF-CR32-IMP-001</p>
                    <p><strong>Category:</strong> Pump Components</p>
                    <p><strong>Current Stock:</strong> 8 units</p>
                    <p><strong>Min Stock Level:</strong> 3 units</p>
                    <p><strong>Unit Cost:</strong> $245.00</p>
                    <p><strong>Location:</strong> Warehouse A, Bin 15</p>
                    <button class="btn" onclick="event.stopPropagation(); showPartsDetails(1)">🔧 Manage Part</button>
                </div>
                
                <div class="part-card" onclick="showPartsDetails(2)" style="cursor: pointer; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 12px 40px rgba(46,64,83,0.6)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 8px 32px rgba(46,64,83,0.4)'">
                    <h3>HVAC Filter - HEPA Grade</h3>
                    <div class="stock-status stock-low">Low Stock</div>
                    <p><strong>Part Number:</strong> CR-HJQ-HEPA-24x24</p>
                    <p><strong>Category:</strong> Filtration</p>
                    <p><strong>Current Stock:</strong> 2 units</p>
                    <p><strong>Min Stock Level:</strong> 5 units</p>
                    <p><strong>Unit Cost:</strong> $89.50</p>
                    <p><strong>Location:</strong> Warehouse B, Bin 7</p>
                    <button class="btn" onclick="event.stopPropagation(); showPartsDetails(2)">📦 Manage Part</button>
                </div>
                
                <div class="part-card" onclick="showPartsDetails(3)" style="cursor: pointer; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 12px 40px rgba(46,64,83,0.6)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 8px 32px rgba(46,64,83,0.4)'">
                    <h3>Conveyor Belt - Heavy Duty</h3>
                    <div class="stock-status stock-good">In Stock</div>
                    <p><strong>Part Number:</strong> FL-X45-BELT-10M</p>
                    <p><strong>Category:</strong> Conveyor Parts</p>
                    <p><strong>Current Stock:</strong> 150 meters</p>
                    <p><strong>Min Stock Level:</strong> 50 meters</p>
                    <p><strong>Unit Cost:</strong> $12.75/meter</p>
                    <p><strong>Location:</strong> Warehouse C, Roll Storage</p>
                    <button class="btn" onclick="event.stopPropagation(); showPartsDetails(3)">🔧 Manage Part</button>
                </div>
                
                <div class="part-card" onclick="showPartsDetails(4)" style="cursor: pointer; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 12px 40px rgba(46,64,83,0.6)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 8px 32px rgba(46,64,83,0.4)'">
                    <h3>Generator Oil Filter</h3>
                    <div class="stock-status stock-critical">Critical Low</div>
                    <p><strong>Part Number:</strong> CAT-C15-OF-123</p>
                    <p><strong>Category:</strong> Generator Parts</p>
                    <p><strong>Current Stock:</strong> 0 units</p>
                    <p><strong>Min Stock Level:</strong> 4 units</p>
                    <p><strong>Unit Cost:</strong> $67.25</p>
                    <p><strong>Location:</strong> Out of Stock</p>
                    <button class="btn" onclick="event.stopPropagation(); showPartsDetails(4)">🔧 Manage Part</button>
                </div>
                
                <div class="part-card" onclick="showPartsDetails(5)" style="cursor: pointer; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 12px 40px rgba(46,64,83,0.6)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 8px 32px rgba(46,64,83,0.4)'">
                    <h3>Safety Valve - 150 PSI</h3>
                    <div class="stock-status stock-good">In Stock</div>
                    <p><strong>Part Number:</strong> SV-150-PSI-001</p>
                    <p><strong>Category:</strong> Safety Equipment</p>
                    <p><strong>Current Stock:</strong> 6 units</p>
                    <p><strong>Min Stock Level:</strong> 2 units</p>
                    <p><strong>Unit Cost:</strong> $156.00</p>
                    <p><strong>Location:</strong> Warehouse A, Bin 22</p>
                    <button class="btn" onclick="event.stopPropagation(); showPartsDetails(5)">🔧 Manage Part</button>
                </div>
                
                <div class="part-card" onclick="showPartsDetails(6)" style="cursor: pointer; transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 12px 40px rgba(46,64,83,0.6)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 8px 32px rgba(46,64,83,0.4)'">
                    <h3>Bearing Set - SKF 6308</h3>
                    <div class="stock-status stock-low">Low Stock</div>
                    <p><strong>Part Number:</strong> SKF-6308-2RS1</p>
                    <p><strong>Category:</strong> Bearings & Seals</p>
                    <p><strong>Current Stock:</strong> 3 units</p>
                    <p><strong>Min Stock Level:</strong> 8 units</p>
                    <p><strong>Unit Cost:</strong> $34.50</p>
                    <p><strong>Location:</strong> Warehouse A, Bin 8</p>
                    <button class="btn" onclick="event.stopPropagation(); showPartsDetails(6)">🔧 Manage Part</button>
                </div>
            </div>
        </div>
        
        <!-- Parts Inventory CRUD Functionality -->
        <script>
        // Parts Inventory CRUD Functionality  
        document.addEventListener('DOMContentLoaded', function() {
            console.log('🔩 Parts Inventory CRUD System Loading...');
            
            // Sample parts data (following Llama3's inventory management recommendations)
            let parts = [
                {id: 1, partNumber: 'PUMP-SEAL-001', name: 'Pump Seal Kit', category: 'Seals', description: 'Complete seal kit for main water pumps', quantity: 25, minStock: 5, maxStock: 50, unitCost: 125.50, supplier: 'AquaTech Supply', supplierPartNo: 'ATS-PSK-125', location: 'Warehouse A, Bin 12', leadTime: 7, lastOrdered: '2025-08-15', status: 'in-stock'},
                {id: 2, partNumber: 'FILTER-AIR-002', name: 'HVAC Air Filter', category: 'Filters', description: 'High-efficiency air filter for HVAC systems', quantity: 4, minStock: 8, maxStock: 24, unitCost: 89.25, supplier: 'CleanAir Solutions', supplierPartNo: 'CAS-HE24-089', location: 'Warehouse B, Bin 3', leadTime: 3, lastOrdered: '2025-09-01', status: 'low-stock'},
                {id: 3, partNumber: 'BELT-CONV-003', name: 'Conveyor Belt', category: 'Belts', description: 'Industrial conveyor belt 48" x 300ft', quantity: 2, minStock: 2, maxStock: 6, unitCost: 450.00, supplier: 'Industrial Motion', supplierPartNo: 'IM-CB48-300', location: 'Warehouse C, Floor Storage', leadTime: 14, lastOrdered: '2025-07-20', status: 'critical'},
                {id: 4, partNumber: 'BEARING-001', name: 'Ball Bearing Set', category: 'Bearings', description: 'High-performance ball bearings for rotating equipment', quantity: 15, minStock: 10, maxStock: 30, unitCost: 67.80, supplier: 'Precision Parts Co', supplierPartNo: 'PPC-BB-6780', location: 'Warehouse A, Bin 5', leadTime: 5, lastOrdered: '2025-08-28', status: 'in-stock'},
                {id: 5, partNumber: 'LUBRI-001', name: 'Industrial Lubricant', category: 'Lubricants', description: 'High-temp synthetic lubricant 5-gallon', quantity: 8, minStock: 6, maxStock: 18, unitCost: 156.30, supplier: 'LubeTech Pro', supplierPartNo: 'LTP-HTL-5G', location: 'Chemical Storage', leadTime: 10, lastOrdered: '2025-09-10', status: 'in-stock'},
                {id: 6, partNumber: 'ELECTRIC-WIRE-001', name: 'Electrical Wire 12AWG', category: 'Electrical', description: '12AWG copper wire 500ft spool', quantity: 3, minStock: 8, maxStock: 20, unitCost: 234.50, supplier: 'ElectroMax Supply', supplierPartNo: 'EMS-12AWG-500', location: 'Warehouse A, Bin 8', leadTime: 4, lastOrdered: '2025-08-05', status: 'low-stock'}
            ];
            
            // Create modal for Parts CRUD operations
            function createPartsModal() {
                const modal = document.createElement('div');
                modal.id = 'parts-modal';
                modal.innerHTML = `
                    <div style="
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        background: rgba(0,0,0,0.8);
                        z-index: 2000;
                        display: none;
                        justify-content: center;
                        align-items: center;
                    ">
                        <div style="
                            background: linear-gradient(135deg, #212121 0%, #434A54 50%, #2E4053 100%);
                            padding: 30px;
                            border-radius: 20px;
                            width: 90%;
                            max-width: 800px;
                            max-height: 85vh;
                            overflow-y: auto;
                            color: white;
                            box-shadow: 0 20px 60px rgba(46,64,83,0.6);
                        ">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                                <h2 id="parts-modal-title" style="margin: 0;">Parts Inventory Details</h2>
                                <button onclick="closePartsModal()" style="
                                    background: none;
                                    border: none;
                                    color: white;
                                    font-size: 24px;
                                    cursor: pointer;
                                    padding: 5px;
                                ">×</button>
                            </div>
                            <div id="parts-modal-content"></div>
                            <div style="margin-top: 20px; display: flex; gap: 10px; justify-content: flex-end;">
                                <button onclick="closePartsModal()" style="
                                    background: rgba(102,102,102,0.3);
                                    color: white;
                                    border: none;
                                    padding: 10px 20px;
                                    border-radius: 10px;
                                    cursor: pointer;
                                ">Cancel</button>
                                <button id="parts-modal-action-btn" style="
                                    background: linear-gradient(45deg, #2E4053, #666666);
                                    color: white;
                                    border: none;
                                    padding: 10px 20px;
                                    border-radius: 10px;
                                    cursor: pointer;
                                    font-weight: 600;
                                ">Save</button>
                            </div>
                        </div>
                    </div>
                `;
                document.body.appendChild(modal);
            }
            
            // Show parts details with enhanced error handling
            window.showPartsDetails = function(id) {
                console.log('🔩 Opening parts details for ID:', id);
                
                // Ensure modal exists
                if (!ensureModalExists('parts-modal', createPartsModal)) {
                    alert('Error: Unable to open parts details. Please refresh the page.');
                    return;
                }
                
                const part = parts.find(p => p.id === parseInt(id));
                if (!part) {
                    console.error('Part not found:', id);
                    alert('Part not found. Please refresh the page.');
                    return;
                }
                
                const modal = document.getElementById('parts-modal');
                const title = document.getElementById('parts-modal-title');
                const content = document.getElementById('parts-modal-content');
                const actionBtn = document.getElementById('parts-modal-action-btn');
                
                title.textContent = part.name;
                
                const stockColor = part.status === 'in-stock' ? '#87CEEB' : 
                                 part.status === 'low-stock' ? '#455A64' : '#1C3445';
                
                const inventoryAlert = part.status === 'critical' ? 'CRITICAL: Immediate reorder required!' :
                                     part.status === 'low-stock' ? 'WARNING: Stock below minimum level' :
                                     'Inventory levels normal';
                
                content.innerHTML = `
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; line-height: 1.8;">
                        <div>
                            <p><strong>🔢 Part Number:</strong> ${part.partNumber}</p>
                            <p><strong>📦 Category:</strong> ${part.category}</p>
                            <p><strong>📋 Description:</strong> ${part.description}</p>
                            <p><strong>📍 Location:</strong> ${part.location}</p>
                            <p><strong>🏢 Supplier:</strong> ${part.supplier}</p>
                            <p><strong>🔗 Supplier Part #:</strong> ${part.supplierPartNo}</p>
                        </div>
                        <div>
                            <p><strong>📊 Current Stock:</strong> ${part.quantity} units</p>
                            <p><strong>⬇️ Min Stock:</strong> ${part.minStock} units</p>
                            <p><strong>⬆️ Max Stock:</strong> ${part.maxStock} units</p>
                            <p><strong>💰 Unit Cost:</strong> $${part.unitCost.toFixed(2)}</p>
                            <p><strong>🚛 Lead Time:</strong> ${part.leadTime} days</p>
                            <p><strong>📅 Last Ordered:</strong> ${part.lastOrdered}</p>
                            <p><strong>📊 Status:</strong> <span style="background: ${stockColor}; padding: 4px 12px; border-radius: 15px; font-size: 0.9em;">${part.status.replace('-', ' ').toUpperCase()}</span></p>
                        </div>
                    </div>
                    <div style="margin: 20px 0; padding: 15px; background: rgba(46,64,83,0.4); border-radius: 10px; border-left: 4px solid #8B9467;">
                        <strong style="color: #8B9467;">🤖 AI Inventory Insight:</strong> ${inventoryAlert}
                        <br/>Current stock: ${part.quantity} units. Reorder when below ${part.minStock} units.
                        Total inventory value: $${(part.quantity * part.unitCost).toFixed(2)}
                    </div>
                    <div style="margin: 20px 0; padding: 15px; background: rgba(67,74,84,0.4); border-radius: 10px; display: flex; gap: 10px;">
                        <button onclick="reorderPart(${id})" style="
                            background: linear-gradient(45deg, #434A54, #8B9467);
                            color: white;
                            border: none;
                            padding: 10px 20px;
                            border-radius: 8px;
                            cursor: pointer;
                            font-weight: 600;
                        ">📦 Reorder Part</button>
                        <button onclick="adjustStock(${id})" style="
                            background: linear-gradient(45deg, #456789, #2E4053);
                            color: white;
                            border: none;
                            padding: 10px 20px;
                            border-radius: 8px;
                            cursor: pointer;
                            font-weight: 600;
                        ">📊 Adjust Stock</button>
                    </div>
                `;
                
                actionBtn.textContent = 'Edit Part';
                actionBtn.onclick = () => editPart(id);
                
                modal.style.display = 'flex';
            };
            
            // Reorder part functionality
            window.reorderPart = function(id) {
                const part = parts.find(p => p.id === parseInt(id));
                if (!part) return;
                
                const reorderQty = part.maxStock - part.quantity;
                const cost = (reorderQty * part.unitCost).toFixed(2);
                
                if (confirm(`🚛 Reorder ${part.name}?\\n\\nQuantity to order: ${reorderQty} units\\nEstimated cost: $${cost}\\nLead time: ${part.leadTime} days\\n\\nProceed with order?`)) {
                    part.quantity = part.maxStock;
                    part.lastOrdered = new Date().toISOString().split('T')[0];
                    part.status = 'in-stock';
                    alert('✅ Reorder processed successfully! Stock level updated.');
                    closePartsModal();
                    location.reload();
                }
            };
            
            // Adjust stock functionality
            window.adjustStock = function(id) {
                const part = parts.find(p => p.id === parseInt(id));
                if (!part) return;
                
                const newQty = prompt(`📊 Adjust stock for ${part.name}\\n\\nCurrent quantity: ${part.quantity} units\\nEnter new quantity:`, part.quantity);
                if (newQty !== null && !isNaN(newQty) && newQty >= 0) {
                    part.quantity = parseInt(newQty);
                    part.status = part.quantity <= part.minStock ? 
                                 (part.quantity === 0 ? 'critical' : 'low-stock') : 'in-stock';
                    alert('✅ Stock level adjusted successfully!');
                    closePartsModal();
                    location.reload();
                }
            };
            
            // Edit part
            window.editPart = function(id) {
                const part = parts.find(p => p.id === parseInt(id));
                if (!part) return;
                
                const content = document.getElementById('parts-modal-content');
                const actionBtn = document.getElementById('parts-modal-action-btn');
                
                content.innerHTML = `
                    <form id="parts-edit-form" style="display: grid; gap: 15px;">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Part Number:</label>
                                <input type="text" id="edit-part-number" value="${part.partNumber}" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Part Name:</label>
                                <input type="text" id="edit-part-name" value="${part.name}" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 15px;">
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Category:</label>
                                <select id="edit-part-category" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                                    <option value="Seals" ${part.category === 'Seals' ? 'selected' : ''}>Seals</option>
                                    <option value="Filters" ${part.category === 'Filters' ? 'selected' : ''}>Filters</option>
                                    <option value="Belts" ${part.category === 'Belts' ? 'selected' : ''}>Belts</option>
                                    <option value="Bearings" ${part.category === 'Bearings' ? 'selected' : ''}>Bearings</option>
                                    <option value="Lubricants" ${part.category === 'Lubricants' ? 'selected' : ''}>Lubricants</option>
                                    <option value="Electrical" ${part.category === 'Electrical' ? 'selected' : ''}>Electrical</option>
                                    <option value="Fasteners" ${part.category === 'Fasteners' ? 'selected' : ''}>Fasteners</option>
                                    <option value="Other" ${part.category === 'Other' ? 'selected' : ''}>Other</option>
                                </select>
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Description:</label>
                                <input type="text" id="edit-part-description" value="${part.description}" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 15px;">
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Current Stock:</label>
                                <input type="number" id="edit-part-quantity" value="${part.quantity}" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Min Stock:</label>
                                <input type="number" id="edit-part-min" value="${part.minStock}" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Max Stock:</label>
                                <input type="number" id="edit-part-max" value="${part.maxStock}" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Unit Cost ($):</label>
                                <input type="number" step="0.01" id="edit-part-cost" value="${part.unitCost}" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Supplier:</label>
                                <input type="text" id="edit-part-supplier" value="${part.supplier}" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Supplier Part #:</label>
                                <input type="text" id="edit-part-supplier-part" value="${part.supplierPartNo}" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Storage Location:</label>
                                <input type="text" id="edit-part-location" value="${part.location}" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                            </div>
                            <div>
                                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Lead Time (days):</label>
                                <input type="number" id="edit-part-leadtime" value="${part.leadTime}" style="
                                    width: 100%;
                                    padding: 10px;
                                    border: 1px solid rgba(102,102,102,0.3);
                                    border-radius: 8px;
                                    background: rgba(46,64,83,0.4);
                                    color: white;
                                    outline: none;
                                ">
                            </div>
                        </div>
                    </form>
                    <div style="margin: 20px 0; padding: 15px; background: rgba(28,52,69,0.4); border-radius: 10px; border-left: 4px solid #8B9467;">
                        <button onclick="deletePart(${id})" style="
                            background: linear-gradient(45deg, #8B2635, #A73C4A);
                            color: white;
                            border: none;
                            padding: 8px 16px;
                            border-radius: 8px;
                            cursor: pointer;
                            font-weight: 600;
                        ">🗑️ Delete Part</button>
                    </div>
                `;
                
                actionBtn.textContent = 'Save Changes';
                actionBtn.onclick = () => savePart(id);
            };
            
            // Save part changes
            window.savePart = async function(id) {
                try {
                    const quantity = parseInt(document.getElementById('edit-part-quantity').value);
                    const minStock = parseInt(document.getElementById('edit-part-min').value);
                    const maxStock = parseInt(document.getElementById('edit-part-max').value);
                    
                    const formData = {
                        partNumber: document.getElementById('edit-part-number').value,
                        name: document.getElementById('edit-part-name').value,
                        category: document.getElementById('edit-part-category').value,
                        quantity: quantity,
                        minStock: minStock,
                        maxStock: maxStock,
                        unitCost: parseFloat(document.getElementById('edit-part-cost').value),
                        supplier: document.getElementById('edit-part-supplier').value,
                        location: document.getElementById('edit-part-location').value,
                        leadTime: document.getElementById('edit-part-leadtime').value,
                        status: quantity <= minStock ? (quantity === 0 ? 'critical' : 'low-stock') : 'in-stock'
                    };
                    
                    const response = await fetch(`/api/parts/${id}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(formData)
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        alert('✅ Part updated successfully!');
                        closePartsModal();
                        location.reload();
                    } else {
                        alert('❌ Error updating part: ' + result.error);
                    }
                } catch (error) {
                    alert('❌ Network error: ' + error.message);
                }
            };
            
            // Delete part
            window.deletePart = async function(id) {
                if (confirm('⚠️ Are you sure you want to delete this part? This action cannot be undone.')) {
                    try {
                        const response = await fetch(`/api/parts/${id}`, {
                            method: 'DELETE',
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            alert('🗑️ Part deleted successfully!');
                            closePartsModal();
                            location.reload();
                        } else {
                            alert('❌ Error deleting part: ' + result.error);
                        }
                    } catch (error) {
                        alert('❌ Network error: ' + error.message);
                    }
                }
            };
            
            // Close modal
            window.closePartsModal = function() {
                const modal = document.getElementById('parts-modal');
                modal.style.display = 'none';
            };
            
            // Add click handlers to existing buttons
            document.querySelectorAll('.btn').forEach((btn, index) => {
                btn.onclick = () => showPartsDetails(index + 1);
                btn.style.cursor = 'pointer';
                btn.innerHTML = '🔩 Manage Inventory';
            });
            
            // Enhanced initialization system for parts
            window.initializePartsSystem = function() {
                try {
                    console.log('🔩 Initializing Parts Management System...');
                    
                    // Create the modal
                    createPartsModal();
                    
                    // Add enhanced click handlers to all part cards
                    document.querySelectorAll('.part-card').forEach((card, index) => {
                        if (!card.onclick) {
                            const partId = index + 1;
                            card.onclick = () => {
                                console.log(`Part card ${partId} clicked`);
                                showPartsDetails(partId);
                            };
                            card.style.cursor = 'pointer';
                            console.log(`✅ Enhanced click handler added to part card ${partId}`);
                        }
                    });
                    
                    // Add enhanced click handlers to parts buttons
                    document.querySelectorAll('.part-card .btn').forEach((btn, index) => {
                        if (!btn.onclick || btn.onclick.toString().includes('index + 1')) {
                            const partId = index + 1;
                            btn.onclick = (e) => {
                                e.stopPropagation();
                                console.log(`Part button ${partId} clicked`);
                                showPartsDetails(partId);
                            };
                            btn.style.cursor = 'pointer';
                            btn.innerHTML = '🔩 Manage Inventory';
                            console.log(`✅ Enhanced click handler added to part button ${partId}`);
                        }
                    });
                    
                    console.log('✅ Parts Inventory CRUD System Ready!');
                    return true;
                } catch (error) {
                    console.error('❌ Error initializing parts system:', error);
                    return false;
                }
            };
            
            // Initialize when DOM is ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initializePartsSystem);
            } else {
                initializePartsSystem();
            }
        });
        </script>
        
        <!-- CMMS Core Functions -->
        <script src="/static/js/cmms-functions.js"></script>
        <!-- AI Assistant Integration -->
        <script src="/ai-inject.js"></script>
    </body>
    </html>"""

@app.get("/reports", response_class=HTMLResponse)
async def reports_page():
    return """<!DOCTYPE html>
    <html>
    <head>
        <title>📊 Enterprise Reports - ChatterFix CMMS</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
        body {
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #212121 0%, #434A54 50%, #2E4053 100%);
            min-height: 100vh;
        }
        .header {
            background: rgba(33,33,33,0.3);
            padding: 20px;
            backdrop-filter: blur(20px);
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: white;
            box-shadow: 0 8px 32px rgba(46,64,83,0.4), 0 0 0 1px rgba(102,102,102,0.3);
        }
        .logo {
            font-size: 1.5em;
            font-weight: 700;
        }
        .enterprise-badge {
            background: linear-gradient(45deg, #2E4053, #666666);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
        }
        .cloud-badge {
            background: linear-gradient(45deg, #434A54, #8B9467);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7em;
            font-weight: 600;
            margin-left: 10px;
        }
        .nav {
            background: rgba(33,33,33,0.2);
            padding: 15px 20px;
            display: flex;
            gap: 20px;
        }
        .nav a {
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 10px;
            transition: all 0.3s ease;
        }
        .nav a:hover, .nav a.active {
            background: rgba(33,33,33,0.3);
        }
        .content {
            padding: 30px;
            max-width: 1400px;
            margin: 0 auto;
        }
        .page-header {
            color: white;
            margin-bottom: 30px;
            text-align: center;
        }
        .page-header h1 {
            font-size: 2.8em;
            margin: 0;
            background: linear-gradient(45deg, #434A54, #8B9467);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .page-header p {
            font-size: 1.3em;
            opacity: 0.9;
            margin: 10px 0;
        }
        .ai-providers {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin: 20px 0;
        }
        .ai-provider {
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
            color: white;
        }
        .ai-grok { background: #1C3445; }
        .ai-openai { background: #456789; }
        .ai-hf { background: #2F4E7F; }
        .reports-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 25px;
            margin-top: 30px;
        }
        .report-card {
            background: rgba(33,33,33,0.3);
            padding: 30px;
            border-radius: 20px;
            backdrop-filter: blur(20px);
            color: white;
            box-shadow: 0 8px 32px rgba(46,64,83,0.4), 0 0 0 1px rgba(102,102,102,0.3);
            transition: all 0.3s ease;
        }
        .report-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(46,64,83,0.5), 0 0 0 1px rgba(102,102,102,0.4);
        }
        .report-card h3 {
            margin: 0 0 15px 0;
            font-size: 1.4em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .report-icon {
            font-size: 1.2em;
        }
        .report-desc {
            opacity: 0.8;
            margin-bottom: 20px;
            line-height: 1.6;
        }
        .ai-insight {
            background: rgba(46,64,83,0.4);
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
            border-left: 4px solid #8B9467;
        }
        .ai-insight strong {
            color: #8B9467;
        }
        .generate-btn {
            background: linear-gradient(45deg, #2E4053, #666666);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 10px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            width: 100%;
        }
        .generate-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(46,64,83,0.4), 0 0 0 1px rgba(102,102,102,0.2);
        }
        .status-indicator {
            padding: 6px 12px;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: 500;
            display: inline-block;
            margin-bottom: 10px;
        }
        .status-active { background: #456789; }
        .status-generating { background: #455A64; }
        .filter-section {
            background: rgba(33,33,33,0.3);
            padding: 20px;
            border-radius: 15px;
            backdrop-filter: blur(20px);
            margin-bottom: 30px;
            display: flex;
            gap: 20px;
            align-items: center;
            flex-wrap: wrap;
        }
        .filter-item {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        .filter-item label {
            color: white;
            font-weight: 500;
            font-size: 0.9em;
        }
        .filter-item select, .filter-item input {
            padding: 8px 12px;
            border: 1px solid rgba(102,102,102,0.3);
            border-radius: 8px;
            background: rgba(46,64,83,0.4);
            color: white;
            outline: none;
        }
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <div class="logo">🔧 ChatterFix CMMS</div>
                <span class="enterprise-badge">ENTERPRISE</span>
                <span class="cloud-badge">CLOUD RUN</span>
            </div>
            <div>
                <span class="ai-provider ai-grok">GROK</span>
                <span class="ai-provider ai-openai">OPENAI</span>
                <span class="ai-provider ai-hf">HUGGINGFACE</span>
            </div>
        </div>
        
        <div class="nav">
            <a href="/">🏠 Dashboard</a>
            <a href="/work-orders">📋 Work Orders</a>
            <a href="/assets">⚙️ Assets</a>
            <a href="/parts">🔩 Parts</a>
            <a href="/reports" class="active">📊 Reports</a>
        </div>
        
        <div class="content">
            <div class="page-header">
                <h1>📊 Enterprise Analytics & Reports</h1>
                <p>AI-Powered Insights for Industrial Operations</p>
                <div class="ai-providers">
                    <div class="ai-provider ai-grok">🚀 Grok Intelligence</div>
                    <div class="ai-provider ai-openai">🧠 OpenAI Analytics</div>
                    <div class="ai-provider ai-hf">🤖 HuggingFace ML</div>
                </div>
            </div>
            
            <div class="filter-section">
                <div class="filter-item">
                    <label>Department</label>
                    <select>
                        <option>All Departments</option>
                        <option>Manufacturing</option>
                        <option>Maintenance</option>
                        <option>Quality Control</option>
                    </select>
                </div>
                <div class="filter-item">
                    <label>Date Range</label>
                    <input type="date" value="2024-01-01">
                </div>
                <div class="filter-item">
                    <label>Asset Type</label>
                    <select>
                        <option>All Assets</option>
                        <option>Pumps</option>
                        <option>Motors</option>
                        <option>Conveyors</option>
                    </select>
                </div>
            </div>
            
            <div class="reports-grid">
                <div class="report-card">
                    <h3><span class="report-icon">🔮</span>Predictive Maintenance</h3>
                    <div class="status-indicator status-active">AI Active</div>
                    <p class="report-desc">AI-powered forecast of equipment failures and maintenance schedules using machine learning algorithms.</p>
                    <div class="ai-insight">
                        <strong>AI Insight:</strong> 3 critical assets require attention within 7 days. Predictive model confidence: 94.7%
                    </div>
                    <button class="generate-btn">🚀 Generate with Grok AI</button>
                </div>
                
                <div class="report-card">
                    <h3><span class="report-icon">📈</span>Maintenance History</h3>
                    <div class="status-indicator status-active">Analytics Ready</div>
                    <p class="report-desc">Comprehensive equipment maintenance history with AI-powered trend analysis and cost optimization.</p>
                    <div class="ai-insight">
                        <strong>OpenAI Analysis:</strong> 23% cost reduction possible through optimized scheduling patterns.
                    </div>
                    <button class="generate-btn">🧠 Generate with OpenAI</button>
                </div>
                
                <div class="report-card">
                    <h3><span class="report-icon">⚡</span>Equipment Performance</h3>
                    <div class="status-indicator status-generating">Generating...</div>
                    <p class="report-desc">Real-time equipment performance metrics with AI-powered anomaly detection and efficiency analysis.</p>
                    <div class="ai-insight">
                        <strong>HuggingFace ML:</strong> Detected 5 performance anomalies in Sector B. Investigating...
                    </div>
                    <button class="generate-btn">🤖 Generate with HuggingFace</button>
                </div>
                
                <div class="report-card">
                    <h3><span class="report-icon">🔗</span>Supply Chain Analytics</h3>
                    <div class="status-indicator status-active">Multi-AI Active</div>
                    <p class="report-desc">Intelligent supply chain optimization with inventory forecasting and procurement analytics.</p>
                    <div class="ai-insight">
                        <strong>Multi-AI Consensus:</strong> Optimal reorder point for critical parts: 72 hours lead time.
                    </div>
                    <button class="generate-btn">🌟 Generate with All AIs</button>
                </div>
                
                <div class="report-card">
                    <h3><span class="report-icon">💰</span>Cost Analysis</h3>
                    <div class="status-indicator status-active">Financial AI</div>
                    <p class="report-desc">Advanced financial analytics with predictive cost modeling and budget optimization insights.</p>
                    <div class="ai-insight">
                        <strong>Financial AI:</strong> Q4 maintenance budget projected to be 12% under budget with current trends.
                    </div>
                    <button class="generate-btn">💼 Generate Financial Report</button>
                </div>
                
                <div class="report-card">
                    <h3><span class="report-icon">🛡️</span>Safety & Compliance</h3>
                    <div class="status-indicator status-active">Compliance Ready</div>
                    <p class="report-desc">AI-driven safety compliance monitoring with regulatory reporting and risk assessment.</p>
                    <div class="ai-insight">
                        <strong>Safety AI:</strong> 100% compliance achieved. Next audit: 45 days. Zero safety incidents detected.
                    </div>
                    <button class="generate-btn">🛡️ Generate Safety Report</button>
                </div>
            </div>
        </div>
        
        <!-- CMMS Core Functions -->
        <script src="/static/js/cmms-functions.js"></script>
        <!-- Data Mode Toggle System -->
        <script src="/static/js/data-mode-toggle.js"></script>
        <!-- AI Assistant Integration -->
        <script src="/ai-inject.js"></script>
    </body>
    </html>"""

# API Routes
@app.get("/api/work-orders-list")
async def get_work_orders_list():
    """Get all work orders formatted for CRUD interface"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, description, status, priority, assigned_to, created_date, due_date
            FROM work_orders
            ORDER BY 
                CASE priority 
                    WHEN 'Critical' THEN 1 
                    WHEN 'High' THEN 2 
                    WHEN 'Medium' THEN 3 
                    WHEN 'Low' THEN 4 
                END,
                created_date DESC
        ''')
        work_orders = []
        for row in cursor.fetchall():
            work_orders.append({
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'status': row[3],
                'priority': row[4],
                'assigned': row[5],
                'dueDate': row[7],
                'asset': 'Database Asset'  # TODO: Join with assets table
            })
        conn.close()
        return {"success": True, "work_orders": work_orders}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/work-orders")
async def get_work_orders():
    """Get all work orders from database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, description, status, priority, assigned_to, created_date, due_date
            FROM work_orders 
            ORDER BY created_date DESC
        ''')
        work_orders = []
        for row in cursor.fetchall():
            work_orders.append({
                "id": row["id"],
                "title": row["title"],
                "description": row["description"],
                "status": row["status"],
                "priority": row["priority"],
                "assigned": row["assigned_to"],
                "created_date": row["created_date"],
                "due_date": row["due_date"]
            })
        conn.close()
        return {"work_orders": work_orders}
    except Exception as e:
        logger.error(f"Error fetching work orders: {e}")
        return {"work_orders": [], "error": str(e)}

@app.get("/api/assets")
async def get_assets():
    return {"assets": []}

@app.get("/api/assets/{asset_id}")
async def get_asset(asset_id: int):
    return {"id": asset_id, "name": f"Asset #{asset_id}", "type": "Equipment"}

@app.get("/api/parts")
async def get_parts():
    return {"parts": []}

# AI-Enhanced CRUD API Endpoints for Work Orders
@app.post("/api/work-orders")
async def create_work_order(request: Request):
    """Create a new work order with AI analysis"""
    try:
        body = await request.json()
        
        # Get AI insights before creation
        ai_insights = await get_ai_insights("work_order", body)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO work_orders (title, description, status, priority, assigned_to, due_date, asset_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            body.get("title", "New Work Order"),
            body.get("description", ""),
            body.get("status", "open"),
            body.get("priority", "medium"),
            body.get("assigned", ""),
            body.get("dueDate", ""),
            body.get("asset", "")
        ))
        
        work_order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        work_order = {
            "id": work_order_id,
            "title": body.get("title", "New Work Order"),
            "description": body.get("description", ""),
            "priority": body.get("priority", "medium"),
            "status": body.get("status", "open"),
            "ai_insights": ai_insights,
            "assigned": body.get("assigned", ""),
            "dueDate": body.get("dueDate", ""),
            "asset": body.get("asset", "")
        }
        return {"success": True, "work_order": work_order}
    except Exception as e:
        logger.error(f"Error creating work order: {e}")
        return {"success": False, "error": str(e)}

@app.put("/api/work-orders/{work_order_id}")
async def update_work_order(work_order_id: int, request: Request):
    """Update an existing work order"""
    try:
        body = await request.json()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE work_orders 
            SET title = ?, description = ?, status = ?, priority = ?, assigned_to = ?, due_date = ?, asset_id = ?
            WHERE id = ?
        ''', (
            body.get("title", ""),
            body.get("description", ""),
            body.get("status", "open"),
            body.get("priority", "medium"),
            body.get("assigned", ""),
            body.get("dueDate", ""),
            body.get("asset", ""),
            work_order_id
        ))
        
        conn.commit()
        conn.close()
        
        work_order = {
            "id": work_order_id,
            "title": body.get("title", ""),
            "description": body.get("description", ""),
            "priority": body.get("priority", "medium"),
            "status": body.get("status", "open"),
            "assigned": body.get("assigned", ""),
            "dueDate": body.get("dueDate", ""),
            "asset": body.get("asset", "")
        }
        return {"success": True, "work_order": work_order}
    except Exception as e:
        logger.error(f"Error updating work order {work_order_id}: {e}")
        return {"success": False, "error": str(e)}

@app.delete("/api/work-orders/{work_order_id}")
async def delete_work_order(work_order_id: int):
    """Delete a work order"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM work_orders WHERE id = ?', (work_order_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return {"success": False, "error": f"Work order {work_order_id} not found"}
        
        conn.commit()
        conn.close()
        return {"success": True, "message": f"Work order {work_order_id} deleted"}
    except Exception as e:
        logger.error(f"Error deleting work order {work_order_id}: {e}")
        return {"success": False, "error": str(e)}

# Work Order Completion Endpoint
@app.post("/api/work-orders/{work_order_id}/complete")
async def complete_work_order(work_order_id: int, request: Request):
    """Mark a work order as completed with completion details"""
    try:
        body = await request.json()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        completion_notes = body.get("notes", "")
        completed_by = body.get("completed_by", "")
        parts_used = body.get("parts_used", "")
        
        cursor.execute('''
            UPDATE work_orders 
            SET status = 'completed', 
                completion_date = CURRENT_TIMESTAMP,
                completion_notes = ?,
                completed_by = ?,
                parts_used = ?
            WHERE id = ?
        ''', (completion_notes, completed_by, parts_used, work_order_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return {"success": False, "error": f"Work order {work_order_id} not found"}
        
        conn.commit()
        conn.close()
        return {"success": True, "message": f"Work order {work_order_id} marked as completed"}
    except Exception as e:
        logger.error(f"Error completing work order {work_order_id}: {e}")
        return {"success": False, "error": str(e)}

# AI Insights Function
async def get_ai_insights(item_type: str, data: dict) -> dict:
    """Get AI insights for any CMMS item"""
    try:
        # Use the existing global AI endpoint
        prompt = f"""
        Analyze this {item_type} and provide insights:
        {json.dumps(data, indent=2)}
        
        Please provide:
        1. Risk assessment (0-1 scale)
        2. Urgency level (low/medium/high)
        3. Specific recommendations
        4. Predicted issues
        5. Suggested actions
        
        Return analysis in a structured format.
        """
        
        # Call the global AI processor with proper request format
        from fastapi import Request
        import io
        
        # Create a mock request object for AI processing
        class MockRequest:
            def __init__(self, json_data):
                self._json = json_data
                
            async def json(self):
                return self._json
        
        mock_request = MockRequest({
            "message": prompt,
            "context": {
                "action": "analyze_item",
                "item_type": item_type,
                "item_data": data
            }
        })
        
        ai_response = await process_ai_message(mock_request)
        
        # Parse AI response into structured format
        insights = parse_ai_insights(ai_response.get("response", ""))
        
        return insights
        
    except Exception as e:
        logger.error(f"AI insights failed: {e}")
        return {"error": str(e), "risk_score": 0.0, "urgency_level": "medium"}

def parse_ai_insights(ai_response: str) -> dict:
    """Parse AI response into structured insights"""
    insights = {
        "risk_score": 0.0,
        "urgency_level": "medium",
        "recommendations": [],
        "predicted_issues": [],
        "suggested_actions": []
    }
    
    try:
        # Extract recommendations
        if "urgent" in ai_response.lower() or "critical" in ai_response.lower():
            insights["urgency_level"] = "high"
            insights["risk_score"] = 0.8
        elif "important" in ai_response.lower() or "priority" in ai_response.lower():
            insights["urgency_level"] = "medium"
            insights["risk_score"] = 0.5
        else:
            insights["urgency_level"] = "low"
            insights["risk_score"] = 0.2
            
        # Extract recommendations using simple parsing
        lines = ai_response.split('\n')
        for line in lines:
            if 'recommend' in line.lower():
                insights["recommendations"].append(line.strip())
            elif 'issue' in line.lower() or 'problem' in line.lower():
                insights["predicted_issues"].append(line.strip())
            elif 'suggest' in line.lower() or 'action' in line.lower():
                insights["suggested_actions"].append(line.strip())
                
    except Exception as e:
        logger.error(f"Error parsing AI insights: {e}")
    
    return insights

# Work Order Parts Management
@app.get("/api/work-orders/{work_order_id}/parts")
async def get_work_order_parts(work_order_id: int):
    """Get parts associated with work order"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # For now, return demo data since we need to set up the work_order_parts table
        demo_parts = [
            {
                "part_id": 1,
                "name": "HVAC Filter",
                "part_number": "HF-001",
                "quantity_requested": 2,
                "quantity_used": 1,
                "unit_cost": 25.50,
                "available_stock": 15
            },
            {
                "part_id": 2,
                "name": "Belt Drive",
                "part_number": "BD-150",
                "quantity_requested": 1,
                "quantity_used": 0,
                "unit_cost": 45.00,
                "available_stock": 8
            }
        ]
        
        conn.close()
        return demo_parts
        
    except Exception as e:
        logger.error(f"Error fetching work order parts: {e}")
        return []

@app.post("/api/work-orders/{work_order_id}/parts")
async def add_work_order_part(work_order_id: int, request: Request):
    """Add part to work order"""
    try:
        data = await request.json()
        
        # For now, just return success
        # In production, you'd insert into work_order_parts table
        
        return {"success": True, "message": "Part added to work order"}
        
    except Exception as e:
        logger.error(f"Error adding part to work order: {e}")
        return {"success": False, "error": str(e)}



# CRUD API Endpoints for Assets
@app.post("/api/assets")
async def create_asset(request: Request):
    """Create a new asset"""
    try:
        body = await request.json()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert asset into database
        cursor.execute('''
            INSERT INTO assets (name, asset_type, location, manufacturer, model, status, criticality, last_maintenance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            body.get("name", "New Asset"),
            body.get("type", "Equipment"),
            body.get("location", ""),
            body.get("manufacturer", ""),
            body.get("model", ""),
            body.get("condition", "Active"),
            body.get("criticality", "Medium"),
            body.get("lastMaintenance", None)
        ))
        
        asset_id = cursor.lastrowid
        conn.commit()
        
        # Get the created asset
        cursor.execute('SELECT * FROM assets WHERE id = ?', (asset_id,))
        asset_row = cursor.fetchone()
        conn.close()
        
        if asset_row:
            asset = {
                "id": asset_row["id"],
                "name": asset_row["name"],
                "type": asset_row["asset_type"],
                "location": asset_row["location"],
                "manufacturer": asset_row["manufacturer"],
                "model": asset_row["model"],
                "condition": asset_row["status"],
                "criticality": asset_row["criticality"],
                "lastMaintenance": asset_row["last_maintenance"]
            }
            return {"success": True, "asset": asset}
        else:
            return {"success": False, "error": "Failed to create asset"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/assets/{asset_id}")
async def update_asset(asset_id: int, request: Request):
    """Update an existing asset"""
    try:
        body = await request.json()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update asset in database
        cursor.execute('''
            UPDATE assets 
            SET name = ?, asset_type = ?, location = ?, manufacturer = ?, model = ?, status = ?, criticality = ?, last_maintenance = ?
            WHERE id = ?
        ''', (
            body.get("name"),
            body.get("type"),
            body.get("location"),
            body.get("manufacturer"),
            body.get("model"),
            body.get("condition"),
            body.get("criticality"),
            body.get("lastMaintenance"),
            asset_id
        ))
        
        conn.commit()
        
        # Get the updated asset
        cursor.execute('SELECT * FROM assets WHERE id = ?', (asset_id,))
        asset_row = cursor.fetchone()
        conn.close()
        
        if asset_row:
            asset = {
                "id": asset_row["id"],
                "name": asset_row["name"],
                "type": asset_row["asset_type"],
                "location": asset_row["location"],
                "manufacturer": asset_row["manufacturer"],
                "model": asset_row["model"],
                "condition": asset_row["status"],
                "criticality": asset_row["criticality"],
                "lastMaintenance": asset_row["last_maintenance"]
            }
            return {"success": True, "asset": asset}
        else:
            return {"success": False, "error": "Asset not found"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/assets/{asset_id}")
async def delete_asset(asset_id: int):
    """Delete an asset"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if asset exists
        cursor.execute('SELECT id FROM assets WHERE id = ?', (asset_id,))
        if not cursor.fetchone():
            conn.close()
            return {"success": False, "error": "Asset not found"}
        
        # Delete asset
        cursor.execute('DELETE FROM assets WHERE id = ?', (asset_id,))
        conn.commit()
        conn.close()
        
        return {"success": True, "message": f"Asset {asset_id} deleted"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# CRUD API Endpoints for Parts
@app.post("/api/parts")
async def create_part(request: Request):
    """Create a new part"""
    try:
        body = await request.json()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert part into database
        cursor.execute('''
            INSERT INTO parts (part_number, name, description, category, stock_quantity, min_stock, unit_cost, location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            body.get("partNumber", f"PN-{int(time.time())}"),
            body.get("name", "New Part"),
            body.get("description", ""),
            body.get("category", "General"),
            body.get("quantity", 0),
            body.get("minStock", 5),
            body.get("unitCost", 0),
            body.get("location", "")
        ))
        
        part_id = cursor.lastrowid
        conn.commit()
        
        # Get the created part
        cursor.execute('SELECT * FROM parts WHERE id = ?', (part_id,))
        part_row = cursor.fetchone()
        conn.close()
        
        if part_row:
            part = {
                "id": part_row["id"],
                "name": part_row["name"],
                "partNumber": part_row["part_number"],
                "description": part_row["description"],
                "category": part_row["category"],
                "quantity": part_row["stock_quantity"],
                "minStock": part_row["min_stock"],
                "unitCost": part_row["unit_cost"],
                "location": part_row["location"]
            }
            return {"success": True, "part": part}
        else:
            return {"success": False, "error": "Failed to create part"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/parts/{part_id}")
async def update_part(part_id: int, request: Request):
    """Update an existing part"""
    try:
        body = await request.json()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update part in database
        cursor.execute('''
            UPDATE parts 
            SET part_number = ?, name = ?, description = ?, category = ?, stock_quantity = ?, min_stock = ?, unit_cost = ?, location = ?
            WHERE id = ?
        ''', (
            body.get("partNumber"),
            body.get("name"),
            body.get("description"),
            body.get("category"),
            body.get("quantity"),
            body.get("minStock"),
            body.get("unitCost"),
            body.get("location"),
            part_id
        ))
        
        conn.commit()
        
        # Get the updated part
        cursor.execute('SELECT * FROM parts WHERE id = ?', (part_id,))
        part_row = cursor.fetchone()
        conn.close()
        
        if part_row:
            part = {
                "id": part_row["id"],
                "name": part_row["name"],
                "partNumber": part_row["part_number"],
                "description": part_row["description"],
                "category": part_row["category"],
                "quantity": part_row["stock_quantity"],
                "minStock": part_row["min_stock"],
                "unitCost": part_row["unit_cost"],
                "location": part_row["location"]
            }
            return {"success": True, "part": part}
        else:
            return {"success": False, "error": "Part not found"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/parts/{part_id}")
async def delete_part(part_id: int):
    """Delete a part"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if part exists
        cursor.execute('SELECT id FROM parts WHERE id = ?', (part_id,))
        if not cursor.fetchone():
            conn.close()
            return {"success": False, "error": "Part not found"}
        
        # Delete part
        cursor.execute('DELETE FROM parts WHERE id = ?', (part_id,))
        conn.commit()
        conn.close()
        
        return {"success": True, "message": f"Part {part_id} deleted"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Multi-AI Assistant endpoint
@app.post("/global-ai/process-message")
async def process_ai_message(request: Request):
    """Process AI assistant messages with multiple AI providers"""
    try:
        body = await request.json()
        message = body.get("message", "")
        context = body.get("context", "")
        page_context = body.get("page_context", "")
        preferred_provider = body.get("provider", AI_PROVIDER)
        
        if not message:
            return {"success": False, "error": "No message provided"}
        
        # Process with multi-AI system
        result = await process_ai_message_multi(
            message, 
            f"Context: {context}, Page: {page_context}", 
            preferred_provider
        )
        
        return {
            "success": result["success"],
            "response": result["response"],
            "provider": result["provider"],
            "fallback": result.get("fallback", False),
            "actions": [],
            "timestamp": datetime.now().isoformat(),
            "page_context": page_context
        }
                
    except Exception as e:
        logger.error(f"AI processing error: {str(e)}")
        return {
            "success": False,
            "error": "AI service temporarily unavailable",
            "timestamp": datetime.now().isoformat()
        }

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected",
        "ai_assistant": "multi-provider-active",
        "version": "enterprise-2.0.0-cloudrun",
        "features": ["authentication", "rbac", "asset_details", "login_page", "multi_ai"],
        "providers": ["grok", "openai", "huggingface"],
        "platform": "cloud-run"
    }


# 🚀 MARS-LEVEL AI BRAIN INTEGRATION
# Import and integrate the most advanced AI systems

try:
    # Enterprise AI Brain - Multi-AI Orchestration
    from enterprise_ai_brain import ai_brain_router, ai_brain
    app.include_router(ai_brain_router)
    print("🧠 Enterprise AI Brain activated - Mars-level multi-AI orchestration ready!")
except ImportError as e:
    print(f"⚠️  Enterprise AI Brain not available: {e}")

try:
    # Quantum Analytics Engine - Real-time Processing
    from quantum_analytics_engine import quantum_router, quantum_engine
    app.include_router(quantum_router)
    print("🔬 Quantum Analytics Engine activated - Mars-level real-time processing ready!")
except ImportError as e:
    print(f"⚠️  Quantum Analytics Engine not available: {e}")

try:
    # Autonomous Operations System - Self-healing & Zero-trust
    from autonomous_operations import autonomous_router, autonomous_system
    app.include_router(autonomous_router)
    print("🤖 Autonomous Operations activated - Mars-level autonomous intelligence ready!")
except ImportError as e:
    print(f"⚠️  Autonomous Operations not available: {e}")

try:
    # Mars-Level UI Dashboard - Advanced AI Management Interface
    from mars_level_ui_dashboard import ui_router
    app.include_router(ui_router)
    print("🎨 Mars-Level UI Dashboard activated - Advanced AI management interface ready!")
except ImportError as e:
    print(f"⚠️  Mars-Level UI Dashboard not available: {e}")

# Serve AI Inject JavaScript file
@app.get("/ai-inject.js", response_class=HTMLResponse)
async def get_ai_inject_js():
    """Serve the AI assistant injection script"""
    try:
        with open("ai-inject.js", "r") as f:
            js_content = f.read()
        return HTMLResponse(content=js_content, media_type="application/javascript")
    except FileNotFoundError:
        return HTMLResponse(content="console.error('AI inject script not found');", media_type="application/javascript")


print("🚀🚀🚀 CHATTERFIX CMMS MARS-LEVEL AI PLATFORM INITIALIZED 🚀🚀🚀")
print("     The most advanced AI-powered CMMS with enterprise-grade intelligence")
print("     Featuring: AI Brain, Quantum Analytics, Autonomous Operations")
print("     Ready for Mars-level performance! 🔥")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)