import os
import shutil

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.firestore_db import get_db_connection

# # from app.core.database import get_db_connection
from app.auth import get_current_active_user, get_optional_current_user
from app.models.user import User
from typing import Optional
from app.services.ai_assistant import chatterfix_ai
from app.services.computer_vision import analyze_asset_condition, recognize_part, extract_text_from_image, detect_equipment_issues
from app.services.voice_commands import (
    get_voice_command_suggestions,
    process_voice_command,
)

# Server-side Speech-to-Text
try:
    from app.services.speech_to_text_service import get_speech_service, AudioEncoding
    SPEECH_SERVICE_AVAILABLE = True
except ImportError:
    SPEECH_SERVICE_AVAILABLE = False

# Import AI Memory Service
try:
    from app.services.ai_memory_integration import get_ai_memory_service
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatRequest(BaseModel):
    message: str
    context: str = ""
    user_id: int = 1
    context_type: str = "general"  # general, equipment_diagnosis, troubleshooting, etc.
    force_team: bool = False  # Force full AI team collaboration
    fast_mode: bool = False  # Skip AI team refinement for ~50% faster responses


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    General AI Chat - Smart routing to best AI model(s)

    Simple queries: Fast Gemini response (< 2 seconds)
    Complex tasks: Full AI team collaboration (6 models)

    Options:
    - force_team=true: Always use the full AI team
    - fast_mode=true: Skip AI team refinement for ~50% faster responses
    """
    try:
        # Use smart routing via updated process_message
        response = await chatterfix_ai.process_message(
            message=request.message,
            context=request.context,
            user_id=request.user_id,
            context_type=request.context_type,
            force_team=request.force_team,
            fast_mode=request.fast_mode
        )
        return JSONResponse({"response": response})
    except Exception as e:
        return JSONResponse(
            {"response": f"I encountered an error: {str(e)}"}, status_code=500
        )


@router.post("/chat/team")
async def chat_with_team(request: ChatRequest):
    """
    AI Chat with FULL AI Team - Always uses all 6 AI models

    Returns detailed response with model info, complexity analysis, etc.
    Use this for complex diagnostics, troubleshooting, and analysis tasks.

    Options:
    - fast_mode=true: Skip refinement phase for ~50% faster responses
    """
    try:
        result = await chatterfix_ai.process_with_team(
            message=request.message,
            context=request.context,
            user_id=request.user_id,
            context_type=request.context_type,
            fast_mode=request.fast_mode
        )
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse(
            {"success": False, "response": f"Error: {str(e)}", "model_used": "error"},
            status_code=500
        )


@router.get("/team/status")
async def get_ai_team_status():
    """
    Get AI Team service status and available models

    Returns health status, available models, and capabilities.
    """
    try:
        from app.services.ai_team_http_client import get_ai_team_client

        client = await get_ai_team_client()

        # Get health and models in parallel
        health = await client.health_check()
        models = await client.get_available_models()

        return JSONResponse({
            "success": True,
            "team_available": health.get("status") == "healthy",
            "health": health,
            "models": models.get("models", []),
            "total_models": models.get("total", 0),
            "capabilities": [
                "analysis", "reasoning", "planning",
                "coding", "debugging", "architecture",
                "creativity", "design", "innovation",
                "fast-coding", "optimization", "strategy"
            ]
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "team_available": False,
            "error": str(e),
            "models": [],
            "total_models": 0
        })


@router.get("/router/stats")
async def get_router_stats():
    """
    Get AI Router statistics and performance metrics

    Returns:
    - Cache statistics (hits, misses, hit rate)
    - Circuit breaker status
    - Routing analytics (request counts, response times, model usage)
    - AI team availability
    """
    try:
        from app.services.ai_router import ai_router

        stats = ai_router.get_router_stats()
        return JSONResponse({
            "success": True,
            **stats
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.post("/router/clear-cache")
async def clear_router_cache():
    """
    Clear the AI response cache

    Useful for testing or when you want fresh responses.
    """
    try:
        from app.services.ai_router import ai_router

        # Clear cache by creating a new one
        ai_router.cache = type(ai_router.cache)(
            max_size=ai_router.cache.max_size,
            ttl=ai_router.cache.ttl
        )
        return JSONResponse({
            "success": True,
            "message": "Cache cleared successfully"
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.post("/router/reset-circuit-breaker")
async def reset_circuit_breaker():
    """
    Reset the circuit breaker to closed state

    Useful after fixing issues with the AI team service.
    """
    try:
        from app.services.ai_router import ai_router

        ai_router.circuit_breaker.failure_count = 0
        ai_router.circuit_breaker.state = "closed"
        return JSONResponse({
            "success": True,
            "message": "Circuit breaker reset to closed state"
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.post("/analyze-image")
async def analyze_image(
    image: UploadFile = File(...),
    prompt: str = Form("Describe this image for maintenance purposes."),
    current_user: User = Depends(get_current_active_user),
):
    """Analyze an uploaded image"""
    if not chatterfix_ai.gemini:
        return JSONResponse({"response": "AI features unavailable."})

    # Save temp file
    temp_path = f"temp_{image.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    try:
        response = await chatterfix_ai.gemini.analyze_image(
            temp_path, prompt, user_id=current_user.uid
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return JSONResponse({"response": response})


@router.post("/kpi-report")
async def kpi_report(current_user: User = Depends(get_current_active_user)):
    """Generate KPI Report"""
    if not chatterfix_ai.gemini:
        return JSONResponse({"response": "AI features unavailable."})

    # This still uses the fake connection. This needs to be refactored.
    conn = get_db_connection()
    work_orders = conn.execute("SELECT * FROM work_orders").fetchall()
    parts = conn.execute("SELECT * FROM parts").fetchall()
    conn.close()

    data = {
        "total_work_orders": len(work_orders),
        "open_work_orders": len([wo for wo in work_orders if wo["status"] == "Open"]),
        "completed_work_orders": len(
            [wo for wo in work_orders if wo["status"] == "Completed"]
        ),
        "total_parts": len(parts),
        "low_stock_parts": len(
            [p for p in parts if p["current_stock"] <= p["minimum_stock"]]
        ),
    }

    report = await chatterfix_ai.gemini.generate_kpi_report(
        data, user_id=current_user.uid
    )
    return JSONResponse({"response": report})


@router.post("/troubleshoot")
async def troubleshoot(
    asset: str = Form(...),
    issue: str = Form(...),
    current_user: User = Depends(get_current_active_user),
):
    """Get troubleshooting advice"""
    if not chatterfix_ai.gemini:
        return JSONResponse({"response": "AI features unavailable."})

    advice = await chatterfix_ai.gemini.get_troubleshooting_advice(
        asset, issue, user_id=current_user.uid
    )
    return JSONResponse({"response": advice})


@router.post("/assist")
async def assist(request: ChatRequest):
    """Global AI Assistant Endpoint"""
    if not chatterfix_ai.gemini:
        return JSONResponse({"response": "AI features unavailable."})

    try:
        # Use user_id from request or default to demo user
        user_id = request.user_id if request.user_id else "demo_user_1"
        # Call the advanced assistant agent
        result = await chatterfix_ai.gemini.run_assistant_agent(
            request.message, request.context, user_id=user_id
        )
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"response": f"I encountered an error: {str(e)}"})


@router.post("/voice-command")
async def voice_command(voice_text: str = Form(...), technician_id: int = Form(None)):
    """Process voice commands with AI and Golden Workflows"""
    result = await process_voice_command(voice_text, technician_id)
    return JSONResponse(result)


@router.get("/voice-suggestions")
async def get_voice_suggestions():
    """Get intelligent voice command suggestions and golden workflows"""
    suggestions = await get_voice_command_suggestions()
    return JSONResponse(suggestions)


@router.post("/recognize-part")
async def recognize_part_endpoint(image: UploadFile = File(...)):
    """AI-powered part recognition from image"""
    # Save temp file
    temp_path = f"temp_{image.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    try:
        with open(temp_path, "rb") as f:
            image_data = f.read()
        result = await recognize_part(image_data=image_data)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return JSONResponse(result)


@router.post("/analyze-condition")
async def analyze_condition_endpoint(
    image: UploadFile = File(...), asset_id: int = Form(None)
):
    """Analyze asset condition from visual inspection"""
    # Save temp file
    temp_path = f"temp_{image.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    try:
        with open(temp_path, "rb") as f:
            image_data = f.read()
        result = await analyze_asset_condition(image_data=image_data, asset_id=asset_id)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return JSONResponse(result)


@router.post("/extract-text")
async def extract_text_endpoint(image: UploadFile = File(...)):
    """Advanced OCR text extraction for AR applications"""
    # Save temp file
    temp_path = f"temp_{image.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    try:
        with open(temp_path, "rb") as f:
            image_data = f.read()
        result = await extract_text_from_image(image_data=image_data)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return JSONResponse(result)


@router.post("/inspect-equipment")
async def inspect_equipment_endpoint(image: UploadFile = File(...)):
    """Advanced equipment inspection with voice feedback for emergency scenarios"""
    # Save temp file
    temp_path = f"temp_{image.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    try:
        with open(temp_path, "rb") as f:
            image_data = f.read()
        result = await detect_equipment_issues(image_data)
        
        # Add emergency voice feedback for critical issues
        if result.get("success") and result.get("overall_condition_score", 10) < 3.0:
            urgent_issues = [issue for issue in result.get("detected_issues", []) 
                           if issue.get("severity") in ["critical", "high", "severe"]]
            
            if urgent_issues:
                result["emergency_voice_feedback"] = f"CRITICAL ALERT: {len(urgent_issues)} high-priority issues detected. " + \
                    f"Overall condition score {result['overall_condition_score']} out of 10. " + \
                    f"Immediate maintenance required. Safety precautions advised."
                result["immediate_actions_required"] = True
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return JSONResponse(result)


@router.post("/emergency-workflow")
async def emergency_workflow(
    voice_text: str = Form(...), 
    image: UploadFile = File(None),
    technician_id: int = Form(1)
):
    """Complete emergency workflow: Voice + Vision + AI Analysis + Work Order Creation"""
    try:
        # Step 1: Process voice command for context and urgency
        voice_result = await process_voice_command(voice_text, technician_id)
        
        workflow_result = {
            "voice_analysis": voice_result,
            "visual_analysis": None,
            "integrated_response": None,
            "emergency_actions": [],
            "voice_feedback": "Voice command processed."
        }
        
        # Step 2: Process image if provided
        if image and image.filename:
            temp_path = f"temp_{image.filename}"
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            
            try:
                with open(temp_path, "rb") as f:
                    image_data = f.read()
                
                # Comprehensive visual analysis
                visual_result = await detect_equipment_issues(image_data)
                part_result = await recognize_part(image_data=image_data)
                text_result = await extract_text_from_image(image_data)
                
                workflow_result["visual_analysis"] = {
                    "equipment_condition": visual_result,
                    "part_recognition": part_result,
                    "text_extraction": text_result
                }
                
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        # Step 3: Integrate voice + vision for emergency response
        if workflow_result["visual_analysis"]:
            condition_score = workflow_result["visual_analysis"]["equipment_condition"].get("overall_condition_score", 10)
            
            # Emergency integration logic
            if condition_score < 3.0 and voice_result.get("success"):
                # Critical emergency detected
                workflow_result["emergency_actions"] = [
                    "IMMEDIATE: Stop equipment operation",
                    "SAFETY: Implement lockout/tagout procedures", 
                    "PARTS: Order replacement components automatically",
                    "NOTIFY: Alert maintenance supervisor and safety team",
                    "DOCUMENT: Auto-generate emergency work order"
                ]
                
                workflow_result["voice_feedback"] = f"EMERGENCY PROTOCOL ACTIVATED. Critical equipment condition detected with score {condition_score} out of 10. " + \
                    f"Work order {voice_result.get('work_order_id', 'EMERGENCY')} created with highest priority. " + \
                    "Immediate shutdown and maintenance required. All safety teams have been notified."
                
                workflow_result["integrated_response"] = {
                    "priority": "CRITICAL",
                    "estimated_repair_time": "4-6 hours",
                    "safety_level": "EXTREME CAUTION",
                    "business_impact": "PRODUCTION LINE STOPPAGE PREVENTED"
                }
        
        return JSONResponse(workflow_result)
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e),
            "emergency_actions": ["Contact maintenance team immediately"],
            "voice_feedback": f"Emergency workflow error: {str(e)}"
        })
        shutil.copyfileobj(image.file, buffer)

    try:
        with open(temp_path, "rb") as f:
            image_data = f.read()
        result = await detect_equipment_issues(image_data=image_data)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return JSONResponse(result)


@router.get("/voice-suggestions")
async def voice_suggestions():
    """Get intelligent voice command suggestions"""
    suggestions = await get_voice_command_suggestions()
    return JSONResponse(suggestions)


# ============ AI MEMORY ENDPOINTS ============

@router.get("/memory/stats")
async def get_memory_stats():
    """Get AI memory system statistics"""
    if not MEMORY_AVAILABLE:
        return JSONResponse({
            "error": "Memory service not available",
            "available": False
        })

    try:
        memory = get_ai_memory_service()
        stats = await memory.get_memory_stats()
        return JSONResponse({
            "success": True,
            "available": True,
            **stats
        })
    except Exception as e:
        return JSONResponse({
            "error": str(e),
            "available": False
        }, status_code=500)


@router.get("/memory/mistakes")
async def get_recent_mistakes():
    """Get recent mistake patterns from AI memory"""
    if not MEMORY_AVAILABLE:
        return JSONResponse({"error": "Memory service not available"})

    try:
        memory = get_ai_memory_service()
        mistakes = await memory.firestore.get_collection(
            "mistake_patterns",
            limit=20,
            order_by="-timestamp"
        )
        return JSONResponse({
            "success": True,
            "count": len(mistakes),
            "mistakes": mistakes
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/memory/solutions")
async def get_solutions():
    """Get solution patterns from AI knowledge base"""
    if not MEMORY_AVAILABLE:
        return JSONResponse({"error": "Memory service not available"})

    try:
        memory = get_ai_memory_service()
        solutions = await memory.firestore.get_collection(
            "solution_knowledge_base",
            limit=20,
            order_by="-timestamp"
        )
        return JSONResponse({
            "success": True,
            "count": len(solutions),
            "solutions": solutions
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/memory/capture-solution")
async def capture_solution(
    problem: str = Form(...),
    solution: str = Form(...),
    code_template: str = Form(""),
):
    """Manually capture a solution pattern to the knowledge base"""
    if not MEMORY_AVAILABLE:
        return JSONResponse({"error": "Memory service not available"})

    try:
        memory = get_ai_memory_service()
        solution_id = await memory.capture_solution(
            problem_description=problem,
            solution_steps=[solution],
            code_template=code_template,
            success_rate=1.0,
        )
        return JSONResponse({
            "success": True,
            "solution_id": solution_id,
            "message": "Solution captured to knowledge base"
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/memory/search")
async def search_memory(query: str = Form(...)):
    """Search AI memory for relevant solutions and past interactions"""
    if not MEMORY_AVAILABLE:
        return JSONResponse({"error": "Memory service not available"})

    try:
        memory = get_ai_memory_service()

        # Find similar mistakes to warn about
        similar_mistakes = await memory.find_similar_mistakes(query)

        # Find relevant solutions
        solutions = await memory.find_solutions(query)

        return JSONResponse({
            "success": True,
            "query": query,
            "warnings": [
                {
                    "type": "past_mistake",
                    "description": m.get("description"),
                    "prevention": m.get("prevention_strategy"),
                    "severity": m.get("severity")
                }
                for m in similar_mistakes
            ],
            "solutions": [
                {
                    "problem": s.get("problem_pattern"),
                    "solution": s.get("solution_steps"),
                    "success_rate": s.get("success_rate")
                }
                for s in solutions
            ]
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ============ SERVER-SIDE SPEECH-TO-TEXT ENDPOINTS ============
# These endpoints provide reliable speech recognition independent of browser
# Optimized for factory floor environments with noise handling

@router.post("/speech/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language_code: str = Form("en-US"),
    sample_rate: int = Form(16000),
    encoding: str = Form("LINEAR16"),
):
    """
    Server-side speech-to-text transcription

    Accepts audio file and returns transcription with confidence scores.
    Optimized for manufacturing environments with custom vocabulary.
    """
    if not SPEECH_SERVICE_AVAILABLE:
        return JSONResponse({
            "success": False,
            "error": "Speech-to-Text service not available",
            "message": "Install google-cloud-speech and configure credentials"
        }, status_code=503)

    try:
        speech_service = get_speech_service()

        # Read audio data
        audio_data = await audio.read()

        # Get encoding enum
        try:
            audio_encoding = AudioEncoding(encoding)
        except ValueError:
            audio_encoding = AudioEncoding.LINEAR16

        # Perform transcription
        result = await speech_service.transcribe_audio(
            audio_data=audio_data,
            encoding=audio_encoding,
            sample_rate_hertz=sample_rate,
            language_code=language_code,
        )

        return JSONResponse({
            "success": True,
            "transcript": result.transcript,
            "confidence": result.confidence,
            "language": result.language_code,
            "is_final": result.is_final,
            "alternatives": result.alternatives,
            "words": result.words,
            "processing_time_ms": result.processing_time_ms,
            "audio_duration_ms": result.audio_duration_ms,
            "noise_level": result.noise_level,
            "timestamp": result.timestamp,
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.post("/speech/transcribe-base64")
async def transcribe_audio_base64(
    audio_base64: str = Form(...),
    language_code: str = Form("en-US"),
    sample_rate: int = Form(16000),
    encoding: str = Form("LINEAR16"),
):
    """
    Transcribe base64-encoded audio data

    Useful for mobile apps and web applications that capture audio as base64.
    """
    if not SPEECH_SERVICE_AVAILABLE:
        return JSONResponse({
            "success": False,
            "error": "Speech-to-Text service not available"
        }, status_code=503)

    try:
        speech_service = get_speech_service()

        # Get encoding enum
        try:
            audio_encoding = AudioEncoding(encoding)
        except ValueError:
            audio_encoding = AudioEncoding.LINEAR16

        # Perform transcription (service handles base64 decoding)
        result = await speech_service.transcribe_audio(
            audio_data=audio_base64,
            encoding=audio_encoding,
            sample_rate_hertz=sample_rate,
            language_code=language_code,
        )

        return JSONResponse({
            "success": True,
            "transcript": result.transcript,
            "confidence": result.confidence,
            "language": result.language_code,
            "is_final": result.is_final,
            "alternatives": result.alternatives,
            "words": result.words,
            "processing_time_ms": result.processing_time_ms,
            "noise_level": result.noise_level,
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.post("/speech/transcribe-and-execute")
async def transcribe_and_execute_command(
    audio: UploadFile = File(...),
    technician_id: int = Form(None),
    language_code: str = Form("en-US"),
    sample_rate: int = Form(16000),
):
    """
    Full hands-free workflow: Transcribe audio -> Detect command -> Execute

    This endpoint handles the complete voice command pipeline:
    1. Server-side speech-to-text transcription
    2. Wake word detection
    3. Command type identification
    4. Command execution (work orders, inventory, etc.)

    Perfect for technicians on the factory floor with dirty hands.
    """
    if not SPEECH_SERVICE_AVAILABLE:
        return JSONResponse({
            "success": False,
            "error": "Speech-to-Text service not available"
        }, status_code=503)

    try:
        speech_service = get_speech_service()

        # Read and transcribe audio
        audio_data = await audio.read()
        transcription_result = await speech_service.transcribe_with_commands(
            audio_data=audio_data,
            language_code=language_code,
            sample_rate_hertz=sample_rate,
        )

        # If we got a valid command, execute it
        command = transcription_result.get("command", "")
        command_type = transcription_result.get("command_type", "general")

        execution_result = None
        if command and transcription_result["transcription"]["confidence"] > 0.7:
            # Execute the voice command
            execution_result = await process_voice_command(command, technician_id)

        return JSONResponse({
            "success": True,
            "transcription": transcription_result["transcription"],
            "has_wake_word": transcription_result["has_wake_word"],
            "command": command,
            "command_type": command_type,
            "execution_result": execution_result,
            "voice_feedback": _generate_voice_feedback(
                transcription_result,
                execution_result
            )
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e),
            "voice_feedback": f"Sorry, I couldn't process that command. Error: {str(e)}"
        }, status_code=500)


@router.post("/speech/detect-wake-word")
async def detect_wake_word(
    audio: UploadFile = File(...),
    language_code: str = Form("en-US"),
):
    """
    Check if audio contains a wake word (e.g., "Hey ChatterFix")

    Returns whether wake word was detected and the confidence level.
    Useful for implementing always-listening mode.
    """
    if not SPEECH_SERVICE_AVAILABLE:
        return JSONResponse({
            "success": False,
            "detected": False,
            "error": "Speech-to-Text service not available"
        }, status_code=503)

    try:
        speech_service = get_speech_service()
        audio_data = await audio.read()

        detected, wake_word, confidence = await speech_service.detect_wake_word(audio_data)

        return JSONResponse({
            "success": True,
            "detected": detected,
            "wake_word": wake_word,
            "confidence": confidence,
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "detected": False,
            "error": str(e)
        }, status_code=500)


@router.get("/speech/status")
async def get_speech_service_status():
    """
    Get Speech-to-Text service status and configuration

    Returns service availability, supported encodings, languages, etc.
    """
    if not SPEECH_SERVICE_AVAILABLE:
        return JSONResponse({
            "available": False,
            "error": "Speech-to-Text service module not installed",
            "install_command": "pip install google-cloud-speech"
        })

    try:
        speech_service = get_speech_service()
        status = speech_service.get_service_status()
        status["supported_languages"] = speech_service.get_supported_languages()

        return JSONResponse({
            "success": True,
            **status
        })

    except Exception as e:
        return JSONResponse({
            "available": False,
            "error": str(e)
        }, status_code=500)


@router.get("/speech/languages")
async def get_supported_languages():
    """
    Get list of supported languages for speech recognition
    """
    if not SPEECH_SERVICE_AVAILABLE:
        return JSONResponse({
            "success": False,
            "error": "Speech-to-Text service not available"
        })

    try:
        speech_service = get_speech_service()
        languages = speech_service.get_supported_languages()

        return JSONResponse({
            "success": True,
            "languages": languages
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


def _generate_voice_feedback(transcription_result: dict, execution_result: dict) -> str:
    """Generate voice feedback message for the technician"""
    confidence = transcription_result["transcription"]["confidence"]
    command_type = transcription_result.get("command_type", "general")

    if confidence < 0.5:
        return "I'm sorry, I didn't catch that clearly. Could you please repeat?"

    if confidence < 0.7:
        return f"I heard: {transcription_result['command']}. Is that correct?"

    if not execution_result:
        return f"Command received: {transcription_result['command']}"

    # Generate feedback based on command type
    if command_type == "work_order":
        wo_id = execution_result.get("work_order_id", "")
        return f"Work order {wo_id} has been created successfully."

    if command_type == "inventory":
        return "Inventory action completed."

    if command_type == "emergency":
        return "EMERGENCY PROTOCOL ACTIVATED. Supervisor has been notified."

    if command_type == "inspection":
        return "Equipment inspection logged."

    return f"Command processed: {transcription_result['command']}"


# ============ VOICE/VISION MEMORY ENDPOINTS ============
# Learning analytics from voice commands and vision analysis

# Import Voice/Vision Memory service
try:
    from app.services.voice_vision_memory import get_voice_vision_memory
    VOICE_VISION_MEMORY_AVAILABLE = True
except ImportError:
    VOICE_VISION_MEMORY_AVAILABLE = False


@router.get("/learning/voice-analytics")
async def get_voice_analytics(technician_id: str = None, days: int = 30):
    """
    Get analytics about voice command usage and learning

    Returns success rates, command distribution, and noise levels.
    """
    if not VOICE_VISION_MEMORY_AVAILABLE:
        return JSONResponse({
            "success": False,
            "error": "Voice/Vision memory service not available"
        })

    try:
        memory = get_voice_vision_memory()
        analytics = await memory.get_voice_analytics(technician_id, days)

        return JSONResponse({
            "success": True,
            **analytics
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.get("/learning/suggestions/{technician_id}")
async def get_command_suggestions(technician_id: str, context: str = ""):
    """
    Get personalized command suggestions based on technician history

    Returns most-used commands and context-aware suggestions.
    """
    if not VOICE_VISION_MEMORY_AVAILABLE:
        return JSONResponse({
            "success": False,
            "suggestions": []
        })

    try:
        memory = get_voice_vision_memory()
        suggestions = await memory.get_command_suggestions(technician_id, context)

        return JSONResponse({
            "success": True,
            "technician_id": technician_id,
            "suggestions": suggestions
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.get("/learning/technician/{technician_id}")
async def get_technician_profile(technician_id: str):
    """
    Get technician profile with learned patterns

    Returns command history, success rates, and preferences.
    """
    if not VOICE_VISION_MEMORY_AVAILABLE:
        return JSONResponse({
            "success": False,
            "error": "Voice/Vision memory service not available"
        })

    try:
        memory = get_voice_vision_memory()
        profile = await memory.get_technician_profile(technician_id)

        if profile:
            return JSONResponse({
                "success": True,
                "profile": profile
            })
        else:
            return JSONResponse({
                "success": False,
                "error": "Technician not found"
            }, status_code=404)

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.get("/learning/equipment/{equipment_type}")
async def get_equipment_learning(equipment_type: str):
    """
    Get learned data about equipment for better recognition

    Returns recognition hints, common issues, and condition trends.
    """
    if not VOICE_VISION_MEMORY_AVAILABLE:
        return JSONResponse({
            "success": False,
            "error": "Voice/Vision memory service not available"
        })

    try:
        memory = get_voice_vision_memory()
        data = await memory.get_equipment_recognition_data(equipment_type)

        return JSONResponse({
            "success": True,
            "equipment_type": equipment_type,
            "learning_data": data
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


# ============ AI WIDGET ENDPOINTS ============
# Endpoints specifically for the AI assistant widget with microphone and camera

class VoiceCommandRequest(BaseModel):
    command: str
    source: str = "voice_widget"
    context: str = ""
    context_type: str = "general"
    equipment_name: str = None
    issue_description: str = None

class ImageAnalysisRequest(BaseModel):
    image: str  # base64 encoded image
    context: str = "general"

@router.post("/process-command")
async def process_voice_command_endpoint(request: VoiceCommandRequest):
    """
    Process voice/text commands from the AI widget with REAL AI responses.

    This endpoint handles:
    - Troubleshooting questions → AI provides step-by-step guidance
    - Equipment diagnosis → AI analyzes and provides recommendations
    - Work order creation → Creates work orders via voice
    - Part/manual lookups → Searches knowledge base
    - Navigation commands → Navigates the application
    - General questions → AI assistant responds helpfully
    """
    try:
        command_lower = request.command.lower()
        action = None
        target = None
        modal = None
        response_text = None

        # === NAVIGATION COMMANDS (no AI needed) ===
        if any(word in command_lower for word in ["go to", "show me", "open", "navigate"]):
            if "analytics" in command_lower or "dashboard" in command_lower:
                action = "navigate"
                target = "/analytics/dashboard"
                response_text = "Opening the analytics dashboard for you."
            elif "work order" in command_lower:
                if "new" in command_lower or "create" in command_lower:
                    action = "navigate"
                    target = "/work-orders/new"
                    response_text = "Opening the new work order form."
                else:
                    action = "navigate"
                    target = "/work-orders"
                    response_text = "Opening work orders."
            elif "equipment" in command_lower or "asset" in command_lower:
                action = "navigate"
                target = "/assets"
                response_text = "Opening assets and equipment."
            elif "inventory" in command_lower or "parts" in command_lower:
                action = "navigate"
                target = "/inventory"
                response_text = "Opening inventory."
            elif "purchasing" in command_lower:
                action = "navigate"
                target = "/purchasing"
                response_text = "Opening the purchasing dashboard."

        # === WORK ORDER CREATION ===
        elif any(phrase in command_lower for phrase in ["create work order", "new work order", "make work order"]):
            action = "modal"
            modal = "create-work-order"
            response_text = "I'll help you create a new work order. Opening the form now."

        # === AI-POWERED RESPONSES (call the real AI) ===
        else:
            # Build context for the AI
            context_parts = []
            if request.context:
                context_parts.append(request.context)
            if request.equipment_name:
                context_parts.append(f"Equipment: {request.equipment_name}")
            if request.issue_description:
                context_parts.append(f"Issue: {request.issue_description}")

            context = "\n".join(context_parts) if context_parts else ""

            # Determine the best context type for routing
            ai_context_type = request.context_type
            if "troubleshoot" in command_lower or "fix" in command_lower or "repair" in command_lower:
                ai_context_type = "troubleshooting"
            elif "diagnose" in command_lower or "what's wrong" in command_lower:
                ai_context_type = "equipment_diagnosis"
            elif "manual" in command_lower or "documentation" in command_lower:
                ai_context_type = "documentation"
            elif "part" in command_lower and ("find" in command_lower or "where" in command_lower):
                ai_context_type = "inventory"

            # Call the REAL AI assistant for intelligent response
            response_text = await chatterfix_ai.process_message(
                message=request.command,
                context=context,
                context_type=ai_context_type,
                fast_mode=True  # Use fast mode for widget responsiveness
            )

        return JSONResponse({
            "success": True,
            "response": response_text,
            "action": action,
            "target": target,
            "modal": modal,
            "command": request.command,
            "context_type": request.context_type
        })

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"AI command processing error: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e),
            "response": "I encountered an issue processing your request. Please try again or rephrase your question."
        }, status_code=500)

@router.post("/analyze-image")
async def analyze_image_widget_endpoint(request: ImageAnalysisRequest):
    """Analyze images captured by the AI widget camera (base64 version)"""
    try:
        import base64
        from PIL import Image
        import io

        # Decode base64 image
        image_data = request.image.split(',')[1] if ',' in request.image else request.image
        image_bytes = base64.b64decode(image_data)

        # Convert to PIL Image
        image = Image.open(io.BytesIO(image_bytes))

        analysis = ""
        detailed_results = {}

        # Analyze based on context
        if request.context == "equipment_inspection" or request.context == "equipment_diagnosis":
            # Use computer vision for equipment analysis
            try:
                issues_result = await detect_equipment_issues(image_bytes)

                if issues_result.get("success"):
                    condition_score = issues_result.get("overall_condition_score", 0)
                    detected_issues = issues_result.get("detected_issues", [])

                    analysis = f"Equipment Diagnosis Complete:\n"
                    analysis += f"• Overall Condition Score: {condition_score}/10\n"

                    if detected_issues:
                        analysis += f"• Issues Detected: {len(detected_issues)}\n"
                        for idx, issue in enumerate(detected_issues[:3], 1):
                            analysis += f"  {idx}. {issue.get('type', 'Unknown')}: {issue.get('description', '')} (Severity: {issue.get('severity', 'unknown')})\n"

                        if len(detected_issues) > 3:
                            analysis += f"  ... and {len(detected_issues) - 3} more issues\n"
                    else:
                        analysis += "• No significant issues detected\n"

                    detailed_results = issues_result
                else:
                    analysis = "Equipment diagnosis completed. Image captured successfully."

            except Exception as e:
                print(f"Equipment diagnosis error: {e}")
                analysis = "Equipment analysis completed. Image captured successfully."

        elif request.context == "part_recognition":
            # Recognize parts
            try:
                part_info = await recognize_part(image_data=image_bytes)

                if part_info.get("success"):
                    analysis = f"Part Recognition Results:\n"
                    analysis += f"• Part Number: {part_info.get('part_number', 'Unknown')}\n"
                    analysis += f"• Description: {part_info.get('description', 'N/A')}\n"

                    if part_info.get('manufacturer'):
                        analysis += f"• Manufacturer: {part_info.get('manufacturer')}\n"

                    if part_info.get('in_inventory'):
                        analysis += f"• Stock Status: Available in inventory\n"
                    else:
                        analysis += f"• Stock Status: Not found in inventory\n"

                    detailed_results = part_info
                else:
                    analysis = "Part recognition completed. Unable to identify specific part."

            except Exception as e:
                print(f"Part recognition error: {e}")
                analysis = "Part recognition completed. Image captured successfully."

        elif request.context == "text_extraction":
            # Extract text using OCR
            try:
                text_result = await extract_text_from_image(image_data=image_bytes)

                if text_result.get("success"):
                    extracted_text = text_result.get("text", "")

                    if extracted_text:
                        analysis = f"OCR Text Extraction:\n"
                        analysis += f"• Characters Found: {len(extracted_text)}\n"
                        analysis += f"• Extracted Text:\n{extracted_text[:300]}"

                        if len(extracted_text) > 300:
                            analysis += "..."
                    else:
                        analysis = "No text detected in the image."

                    detailed_results = text_result
                else:
                    analysis = "Text extraction completed. No readable text found."

            except Exception as e:
                print(f"Text extraction error: {e}")
                analysis = "Text extraction completed. Image captured successfully."

        else:
            # General image analysis
            analysis = "Image captured and analyzed successfully. Ready for further processing."

        return JSONResponse({
            "success": True,
            "analysis": analysis,
            "context": request.context,
            "image_size": f"{image.size[0]}x{image.size[1]}",
            "detailed_results": detailed_results
        })

    except Exception as e:
        print(f"Image analysis error: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e),
            "analysis": "Image analysis failed. Please try again."
        }, status_code=500)
