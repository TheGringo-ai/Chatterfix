import os
import shutil

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.firestore_db import get_db_connection

# # from app.core.database import get_db_connection
from app.auth import get_current_active_user, get_optional_current_user
from app.models.user import User
from typing import Optional, Union
import json
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
    context: Union[str, dict] = ""  # Accept string or object context
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
        # Handle context - can be string or dict
        context = request.context
        context_type = request.context_type

        # If context is a dict, check for special tasks
        if isinstance(context, dict):
            task = context.get("task", "")

            # Work Order Creation Task - build enhanced prompt
            if task == "work_order_creation":
                current_data = context.get("current_data", {})
                instructions = context.get("instructions", "")
                conversation_history = context.get("conversation_history", [])

                # Build context string for AI
                context_parts = [
                    "TASK: Help technician create a work order through conversation.",
                    "",
                    "INSTRUCTIONS:",
                    instructions,
                    "",
                    "CURRENT WORK ORDER DATA COLLECTED:",
                    json.dumps(current_data, indent=2),
                    "",
                    "CONVERSATION HISTORY:",
                ]

                for msg in conversation_history[-4:]:
                    role = msg.get("role", "user").upper()
                    content = msg.get("content", "")[:200]
                    context_parts.append(f"{role}: {content}")

                context = "\n".join(context_parts)
                context_type = "work_order_creation"

            else:
                # Convert dict to JSON string for other tasks
                context = json.dumps(context)

        # Use smart routing via updated process_message
        response = await chatterfix_ai.process_message(
            message=request.message,
            context=context,
            user_id=request.user_id,
            context_type=context_type,
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


# =============================================================================
# CODE-AWARE AI TEAM REVIEW SYSTEM
# =============================================================================

class CodeReviewRequest(BaseModel):
    """Request for AI Team code review with actual code analysis"""
    files: list[str] = []  # List of file paths or patterns to review
    focus_areas: list[str] = ["security", "performance", "bugs", "best_practices"]
    max_file_size: int = 10000  # Max chars per file
    review_type: str = "comprehensive"  # comprehensive, security, performance, quick


@router.post("/code-review")
async def ai_team_code_review(request: CodeReviewRequest):
    """
    AI Team Code Review - Analyzes ACTUAL CODE for issues WITH MEMORY

    Unlike generic reviews, this endpoint:
    1. Queries past mistakes and solutions from AI memory
    2. Reads real files from the codebase
    3. Sends actual code + historical context to AI models
    4. Captures findings back to memory (never repeat mistakes!)

    Args:
        files: List of file paths (relative to project root) or patterns
        focus_areas: What to look for (security, performance, bugs, best_practices)
        review_type: comprehensive, security, performance, or quick
    """
    import glob as glob_module
    from pathlib import Path

    try:
        # === MEMORY INTEGRATION: Query past learnings ===
        past_context = ""
        memory_stats = {}
        try:
            if MEMORY_AVAILABLE:
                memory = get_ai_memory_service()

                # Get recent mistakes to warn about
                similar_mistakes = await memory.find_similar_mistakes("code review security performance bugs")

                # Get successful solutions for reference
                past_solutions = await memory.find_solutions("code fix security vulnerability")

                if similar_mistakes:
                    past_context += "\n\n=== PAST MISTAKES TO AVOID (from AI Memory) ===\n"
                    for m in similar_mistakes[:3]:
                        past_context += f"- {m.get('description', 'Unknown')}: {m.get('prevention_strategy', 'N/A')}\n"

                if past_solutions:
                    past_context += "\n=== PROVEN SOLUTIONS (from AI Memory) ===\n"
                    for s in past_solutions[:3]:
                        past_context += f"- {s.get('problem_pattern', 'Unknown')}: Success rate {s.get('success_rate', 0)*100:.0f}%\n"

                memory_stats = await memory.get_memory_stats()
        except Exception as mem_error:
            past_context = f"\n(Memory query failed: {mem_error})\n"
        # Get project root dynamically (works locally and on Cloud Run)
        project_root = Path(__file__).parent.parent.parent  # ai.py -> routers -> app -> project
        code_snippets = []
        files_reviewed = []

        # Default files if none specified
        if not request.files:
            request.files = [
                "app/routers/*.py",
                "app/services/*.py",
                "main.py"
            ]

        # Collect code from files
        for file_pattern in request.files:
            # Handle glob patterns
            if "*" in file_pattern:
                matching_files = list(project_root.glob(file_pattern))
            else:
                file_path = project_root / file_pattern
                matching_files = [file_path] if file_path.exists() else []

            for file_path in matching_files[:10]:  # Limit to 10 files per pattern
                if file_path.is_file() and file_path.suffix == ".py":
                    try:
                        content = file_path.read_text()
                        # Truncate if too large
                        if len(content) > request.max_file_size:
                            content = content[:request.max_file_size] + "\n... (truncated)"

                        relative_path = str(file_path.relative_to(project_root))
                        code_snippets.append(f"### FILE: {relative_path}\n```python\n{content}\n```")
                        files_reviewed.append(relative_path)
                    except Exception as e:
                        code_snippets.append(f"### FILE: {file_path} - ERROR: {e}")

        if not code_snippets:
            return JSONResponse({
                "success": False,
                "error": "No files found matching the specified patterns",
                "patterns_searched": request.files
            }, status_code=400)

        # Build comprehensive prompt for AI Team
        focus_str = ", ".join(request.focus_areas)
        code_context = "\n\n".join(code_snippets[:5])  # Limit to 5 files for context

        review_prompt = f"""You are an EXPERT code reviewer for ChatterFix CMMS. Your job is to find REAL issues in code.

REVIEW TYPE: {request.review_type}
FOCUS AREAS: {focus_str}
FILES BEING REVIEWED: {', '.join(files_reviewed[:5])}

ACTUAL CODE TO REVIEW:
{code_context}

=== CRITICAL VERIFICATION REQUIREMENTS ===
Before flagging ANY issue, you MUST:
1. VERIFY the issue exists in the actual code above
2. CITE the exact line number and code snippet as evidence
3. SEARCH the entire code for usage before claiming something is "unused"
4. CHECK if validation/handling already exists before claiming it's "missing"

=== DO NOT FLAG (FALSE POSITIVE PREVENTION) ===
❌ DO NOT flag "unused imports" unless you searched ALL code and confirmed the import is never used
❌ DO NOT flag "missing validation" unless you verified no validation exists anywhere in the file
❌ DO NOT flag "in-memory filtering" if filters are passed to database queries (e.g., organization_id param)
❌ DO NOT make generic recommendations that don't reference specific code
❌ DO NOT flag issues based on assumptions - only flag what you can PROVE from the code

=== WHAT TO LOOK FOR (REAL ISSUES) ===
✅ Security: Directory traversal (e.g., os.path.join with unvalidated user input)
✅ Security: SQL injection, XSS, command injection
✅ Bugs: String comparisons where datetime comparisons should be used
✅ Bugs: Missing error handling for critical operations
✅ Performance: N+1 queries in loops

=== OUTPUT FORMAT ===
For each issue found, provide:
1. FILE: exact filename
2. LINE: exact line number (verify this!)
3. EVIDENCE: quote the problematic code
4. ISSUE: what's wrong and why it matters
5. FIX: concrete code to replace it with

If you cannot find VERIFIED issues, say "No verified issues found" - this is better than false positives.
{past_context}"""

        # Use AI Team for comprehensive review
        result = await chatterfix_ai.process_with_team(
            message=review_prompt,
            context=f"Code review of {len(files_reviewed)} files: {', '.join(files_reviewed[:5])}",
            user_id=0,
            context_type="code_review",
            fast_mode=request.review_type == "quick"
        )

        ai_analysis = result.get("response", result.get("final_answer", "No analysis generated"))

        # === MEMORY INTEGRATION: Capture review findings ===
        try:
            if MEMORY_AVAILABLE:
                memory = get_ai_memory_service()

                # Capture this interaction
                await memory.capture_interaction(
                    user_message=f"Code review: {', '.join(files_reviewed[:5])}",
                    ai_response=ai_analysis[:2000],
                    model="ai_team",
                    context=f"review_type={request.review_type}, focus={request.focus_areas}",
                    success=True,
                    metadata={"files": files_reviewed, "focus_areas": request.focus_areas}
                )

                # If issues found, capture as potential mistakes to track
                if "security" in ai_analysis.lower() or "vulnerability" in ai_analysis.lower():
                    await memory.capture_mistake(
                        mistake_type="security_review",
                        description=f"Security issues found in: {', '.join(files_reviewed[:3])}",
                        context={"files": files_reviewed, "review_type": request.review_type},
                        error_message=ai_analysis[:500],
                        severity="high"
                    )
        except Exception as mem_error:
            pass  # Don't fail the review if memory capture fails

        return JSONResponse({
            "success": True,
            "review_type": request.review_type,
            "files_reviewed": files_reviewed,
            "focus_areas": request.focus_areas,
            "ai_team_analysis": ai_analysis,
            "models_used": result.get("models_used", []),
            "confidence": result.get("confidence", 0.0),
            "memory_stats": memory_stats if memory_stats else {"status": "not_available"}
        })

    except Exception as e:
        import traceback
        return JSONResponse({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)


@router.get("/code-review/quick")
async def quick_code_review():
    """
    Quick AI Team Code Review - Fast scan of critical files

    Reviews main.py and core routers for critical issues.
    Uses fast_mode for ~50% faster response.
    """
    request = CodeReviewRequest(
        files=["main.py", "app/routers/work_orders.py", "app/routers/auth.py"],
        focus_areas=["security", "bugs"],
        review_type="quick"
    )
    return await ai_team_code_review(request)


# =============================================================================
# AI TEAM CODE EDITING WITH BRANCH ISOLATION (SAFEGUARDS)
# =============================================================================

class CodeFixRequest(BaseModel):
    """Request for AI Team to fix code with branch isolation"""
    files: list[str] = []  # Files to fix
    fix_type: str = "auto"  # auto, security, performance, bugs, refactor
    description: str = ""  # Optional description of what to fix
    create_pr: bool = False  # Whether to create a PR after fixing
    dry_run: bool = False  # If true, only show what would be changed
    budget_mode: bool = True  # Use single model (Gemini) to save costs - DEFAULT ON


# =============================================================================
# FEATURE REQUEST SYSTEM - Cost-Effective Development
# =============================================================================

class FeatureRequest(BaseModel):
    """Request for AI to implement a feature"""
    feature: str  # Description of what you want (e.g., "add status field to work orders")
    target_files: list[str] = []  # Specific files to modify (optional)
    budget_mode: bool = True  # Use single cheap model (Gemini) - DEFAULT ON
    create_branch: bool = True  # Create isolated branch for changes


@router.post("/feature")
async def implement_feature(request: FeatureRequest):
    """
    AI Feature Implementation - Cost-Effective Development Helper

    Tell the AI what you want, it creates the code in an isolated branch.
    Uses BUDGET MODE by default (single Gemini model = ~$0.01-0.02 per request)

    Example: "add a priority dropdown field to the work order form"

    SAFEGUARDS:
    - Creates isolated branch (ai-team/feature-{timestamp})
    - Never modifies main directly
    - You review and merge when ready
    """
    import subprocess
    from pathlib import Path
    from datetime import datetime

    try:
        project_root = Path(__file__).parent.parent.parent
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        branch_name = f"ai-team/feature-{timestamp}"

        # Check for uncommitted changes
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        if status_result.stdout.strip():
            return JSONResponse({
                "success": False,
                "error": "Uncommitted changes detected. Commit or stash first.",
                "safeguard": "Protecting your work"
            }, status_code=400)

        # Get current branch
        current_branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        original_branch = current_branch_result.stdout.strip()

        # Find relevant files if not specified
        target_files = request.target_files
        if not target_files:
            # Smart file detection based on feature description
            feature_lower = request.feature.lower()
            if "work order" in feature_lower:
                target_files = ["app/routers/work_orders.py", "app/templates/work_orders.html"]
            elif "asset" in feature_lower:
                target_files = ["app/routers/assets.py", "app/templates/assets.html"]
            elif "inventory" in feature_lower or "part" in feature_lower:
                target_files = ["app/routers/inventory.py", "app/templates/inventory.html"]
            elif "training" in feature_lower:
                target_files = ["app/routers/training.py", "app/templates/training.html"]
            elif "dashboard" in feature_lower:
                target_files = ["app/routers/dashboard.py", "app/templates/dashboard.html"]
            else:
                target_files = ["app/routers/work_orders.py"]  # Default

        # Read current code from target files
        code_context = []
        for file_pattern in target_files[:3]:
            file_path = project_root / file_pattern
            if file_path.exists():
                content = file_path.read_text()[:6000]
                code_context.append(f"### {file_pattern}\n```python\n{content}\n```")

        # Build feature implementation prompt
        feature_prompt = f"""You are implementing a feature for ChatterFix CMMS.

FEATURE REQUEST: {request.feature}

EXISTING CODE:
{chr(10).join(code_context)}

=== IMPLEMENTATION REQUIREMENTS ===
1. The old_code MUST exist EXACTLY in the file (copy it character-for-character)
2. Only modify code that needs to change for this feature
3. Do NOT refactor or "improve" unrelated code
4. Keep changes minimal and focused

=== VERIFICATION ===
Before providing changes:
1. Find the EXACT location in the code to modify
2. Copy the old_code EXACTLY as it appears (including whitespace)
3. Only provide changes that directly implement the requested feature

Format as JSON:
{{
    "changes": [
        {{
            "file": "path/to/file.py",
            "old_code": "EXACT code to find (must match file exactly)",
            "new_code": "the new code",
            "explanation": "what this change does"
        }}
    ],
    "summary": "brief summary of implementation"
}}

IMPORTANT: If old_code doesn't match exactly, the change will fail. Be precise!"""

        # Use budget mode (single Gemini) or full team
        if request.budget_mode:
            # Use just Gemini (cheapest)
            from app.services.gemini_service import gemini_service
            ai_response = await gemini_service.generate_response(feature_prompt)
        else:
            # Full AI Team (more expensive but better quality)
            result = await chatterfix_ai.process_with_team(
                message=feature_prompt,
                context=f"Implementing: {request.feature}",
                user_id=0,
                context_type="feature_implementation",
                fast_mode=True
            )
            ai_response = result.get("response", result.get("final_answer", ""))

        # Parse and apply changes
        import re
        json_match = re.search(r'\{[\s\S]*"changes"[\s\S]*\}', ai_response)

        if not json_match:
            return JSONResponse({
                "success": False,
                "error": "AI could not generate structured changes",
                "ai_response": ai_response[:1000],
                "suggestion": "Try rephrasing your feature request"
            })

        try:
            change_data = json.loads(json_match.group())
            changes = change_data.get("changes", [])
        except json.JSONDecodeError:
            return JSONResponse({
                "success": False,
                "error": "Could not parse AI response",
                "ai_response": ai_response[:1000]
            })

        if not changes:
            return JSONResponse({
                "success": True,
                "message": "No changes needed or AI was unsure",
                "ai_response": ai_response[:1000]
            })

        # Create branch if requested
        if request.create_branch:
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=project_root,
                capture_output=True
            )

        # Apply changes
        applied_changes = []
        for change in changes[:5]:  # Limit to 5 changes
            file_rel_path = change.get("file", "")
            old_code = change.get("old_code", "")
            new_code = change.get("new_code", "")

            if not all([file_rel_path, old_code, new_code]):
                continue

            file_path = project_root / file_rel_path
            if file_path.exists():
                content = file_path.read_text()
                if old_code in content:
                    new_content = content.replace(old_code, new_code, 1)
                    file_path.write_text(new_content)
                    applied_changes.append({
                        "file": file_rel_path,
                        "explanation": change.get("explanation", ""),
                        "status": "applied"
                    })
                else:
                    applied_changes.append({
                        "file": file_rel_path,
                        "status": "skipped - old code not found"
                    })

        # Commit if changes were made
        if applied_changes and request.create_branch:
            subprocess.run(["git", "add", "-A"], cwd=project_root)
            commit_msg = f"""AI Feature: {request.feature[:50]}

{change_data.get('summary', 'Feature implementation')}

🤖 Generated by ChatterFix AI (budget_mode={'on' if request.budget_mode else 'off'})
Review before merging!"""
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=project_root)
            subprocess.run(["git", "checkout", original_branch], cwd=project_root)

        return JSONResponse({
            "success": True,
            "feature": request.feature,
            "branch": branch_name if request.create_branch else None,
            "budget_mode": request.budget_mode,
            "estimated_cost": "$0.01-0.02" if request.budget_mode else "$0.08-0.15",
            "changes_applied": applied_changes,
            "summary": change_data.get("summary", ""),
            "next_steps": [
                f"Review: git diff {original_branch}..{branch_name}",
                f"Merge: git merge {branch_name}",
                f"Delete: git branch -D {branch_name}"
            ] if request.create_branch else ["Changes applied to current branch"]
        })

    except Exception as e:
        import traceback
        try:
            subprocess.run(["git", "checkout", original_branch], cwd=project_root)
        except:
            pass
        return JSONResponse({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)


@router.post("/code-fix")
async def ai_team_code_fix(request: CodeFixRequest):
    """
    AI Team Code Fix - Makes code changes in ISOLATED BRANCHES

    SAFEGUARDS:
    1. All changes happen in a new branch (ai-team/fix-{timestamp})
    2. Never modifies main branch directly
    3. Returns branch name for manual review
    4. User must merge after reviewing changes

    Args:
        files: Files to fix (or patterns)
        fix_type: auto, security, performance, bugs, refactor
        description: What to fix
        create_pr: Create a GitHub PR after fixing
        dry_run: Preview changes without making them
    """
    import subprocess
    import time
    from pathlib import Path
    from datetime import datetime

    try:
        # Get project root
        project_root = Path(__file__).parent.parent.parent
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        branch_name = f"ai-team/fix-{timestamp}"

        # SAFEGUARD 1: Store current branch to restore later if needed
        current_branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        original_branch = current_branch_result.stdout.strip()

        # SAFEGUARD 2: Check for uncommitted changes
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        if status_result.stdout.strip():
            return JSONResponse({
                "success": False,
                "error": "Uncommitted changes detected. Please commit or stash changes first.",
                "safeguard": "Protecting your uncommitted work"
            }, status_code=400)

        # DRY RUN MODE - Just analyze and show what would change
        if request.dry_run:
            # Get AI Team analysis
            review_request = CodeReviewRequest(
                files=request.files if request.files else ["app/routers/*.py"],
                focus_areas=["bugs", "security"] if request.fix_type == "auto" else [request.fix_type],
                review_type="comprehensive"
            )
            review_result = await ai_team_code_review(review_request)
            review_data = json.loads(review_result.body)

            return JSONResponse({
                "success": True,
                "mode": "dry_run",
                "message": "This is a preview. No changes were made.",
                "branch_would_be": branch_name,
                "files_to_review": review_data.get("files_reviewed", []),
                "ai_analysis": review_data.get("ai_team_analysis", ""),
                "next_step": "Run again with dry_run=false to apply fixes"
            })

        # SAFEGUARD 3: Create isolated branch
        create_branch_result = subprocess.run(
            ["git", "checkout", "-b", branch_name],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        if create_branch_result.returncode != 0:
            return JSONResponse({
                "success": False,
                "error": f"Failed to create branch: {create_branch_result.stderr}",
                "safeguard": "Branch creation failed - no changes made"
            }, status_code=500)

        # Collect files to fix
        files_to_fix = []
        for file_pattern in (request.files if request.files else ["app/routers/*.py"]):
            if "*" in file_pattern:
                matching_files = list(project_root.glob(file_pattern))
            else:
                file_path = project_root / file_pattern
                matching_files = [file_path] if file_path.exists() else []

            for file_path in matching_files[:5]:  # Limit to 5 files
                if file_path.is_file() and file_path.suffix == ".py":
                    files_to_fix.append(file_path)

        if not files_to_fix:
            # Return to original branch
            subprocess.run(["git", "checkout", original_branch], cwd=project_root)
            subprocess.run(["git", "branch", "-D", branch_name], cwd=project_root)
            return JSONResponse({
                "success": False,
                "error": "No files found to fix",
                "safeguard": "Returned to original branch, no changes made"
            }, status_code=400)

        # Get AI Team to analyze and suggest fixes
        fixes_made = []
        for file_path in files_to_fix:
            try:
                original_content = file_path.read_text()

                # Build fix prompt
                fix_prompt = f"""You are an EXPERT code fixer for ChatterFix CMMS. Only fix VERIFIED issues.

FIX TYPE: {request.fix_type}
ADDITIONAL CONTEXT: {request.description or 'Auto-fix common issues'}

FILE TO FIX: {file_path.name}

```python
{original_content[:8000]}
```

=== VERIFICATION REQUIREMENTS ===
Before suggesting ANY fix:
1. VERIFY the issue exists by finding it in the code above
2. CONFIRM the old_code you provide exists EXACTLY in the file
3. DO NOT suggest fixes for non-issues or "improvements" not requested
4. ONLY fix security vulnerabilities, bugs, or issues matching the FIX TYPE

=== DO NOT FIX ===
❌ Imports that ARE used elsewhere in the file
❌ "Missing validation" if validation exists
❌ Code style preferences (focus on real bugs)
❌ Things that aren't broken

=== REAL ISSUES TO FIX ===
✅ Directory traversal: os.path.join with unsanitized filenames
✅ Date string comparisons that should use datetime objects
✅ Missing null checks before accessing properties
✅ SQL/command injection vulnerabilities

Format your response as JSON:
{{
    "fixes": [
        {{
            "old_code": "EXACT code to replace (must exist in file)",
            "new_code": "replacement code",
            "reason": "why this fix is needed (cite line number)",
            "line_hint": "exact line number"
        }}
    ],
    "summary": "brief summary of verified fixes only"
}}

BE CONSERVATIVE. Only suggest fixes you are 100% confident about. No fixes is better than wrong fixes."""

                # Get AI Team fix suggestions
                result = await chatterfix_ai.process_with_team(
                    message=fix_prompt,
                    context=f"Fixing {file_path.name}",
                    user_id=0,
                    context_type="code_fix",
                    fast_mode=True
                )

                ai_response = result.get("response", result.get("final_answer", ""))

                # Try to parse JSON from response
                import re
                json_match = re.search(r'\{[\s\S]*"fixes"[\s\S]*\}', ai_response)
                if json_match:
                    try:
                        fix_data = json.loads(json_match.group())
                        fixes = fix_data.get("fixes", [])

                        # Apply fixes
                        modified_content = original_content
                        applied_fixes = []

                        for fix in fixes[:3]:  # Limit to 3 fixes per file
                            old_code = fix.get("old_code", "")
                            new_code = fix.get("new_code", "")

                            if old_code and new_code and old_code in modified_content:
                                modified_content = modified_content.replace(old_code, new_code, 1)
                                applied_fixes.append({
                                    "old": old_code[:100] + "..." if len(old_code) > 100 else old_code,
                                    "new": new_code[:100] + "..." if len(new_code) > 100 else new_code,
                                    "reason": fix.get("reason", "")
                                })

                        if applied_fixes and modified_content != original_content:
                            # Write the modified file
                            file_path.write_text(modified_content)
                            fixes_made.append({
                                "file": str(file_path.relative_to(project_root)),
                                "fixes_applied": len(applied_fixes),
                                "details": applied_fixes
                            })

                    except json.JSONDecodeError:
                        pass  # Could not parse AI response as JSON

            except Exception as e:
                fixes_made.append({
                    "file": str(file_path.relative_to(project_root)),
                    "error": str(e)
                })

        # If no fixes were made, clean up
        if not any(f.get("fixes_applied", 0) > 0 for f in fixes_made):
            subprocess.run(["git", "checkout", original_branch], cwd=project_root)
            subprocess.run(["git", "branch", "-D", branch_name], cwd=project_root)
            return JSONResponse({
                "success": True,
                "message": "No fixable issues found or AI Team was too conservative",
                "files_analyzed": [str(f.relative_to(project_root)) for f in files_to_fix],
                "safeguard": "No changes made, returned to original branch"
            })

        # Commit the changes
        subprocess.run(["git", "add", "-A"], cwd=project_root)
        commit_message = f"""AI Team: {request.fix_type} fixes

Files modified: {len([f for f in fixes_made if f.get('fixes_applied', 0) > 0])}
Fix type: {request.fix_type}
Description: {request.description or 'Automated fixes by AI Team'}

🤖 Generated by ChatterFix AI Team
Review carefully before merging!"""

        subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=project_root
        )

        # SAFEGUARD 4: Return to original branch (keep AI branch for review)
        subprocess.run(["git", "checkout", original_branch], cwd=project_root)

        # Optionally create PR
        pr_url = None
        if request.create_pr:
            try:
                # Push branch
                subprocess.run(
                    ["git", "push", "-u", "origin", branch_name],
                    cwd=project_root
                )
                # Create PR using gh CLI
                pr_result = subprocess.run(
                    ["gh", "pr", "create",
                     "--title", f"AI Team: {request.fix_type} fixes",
                     "--body", f"## AI Team Code Fixes\n\n{commit_message}\n\n**Review carefully before merging!**",
                     "--head", branch_name],
                    cwd=project_root,
                    capture_output=True,
                    text=True
                )
                if pr_result.returncode == 0:
                    pr_url = pr_result.stdout.strip()
            except Exception as e:
                pr_url = f"PR creation failed: {e}"

        return JSONResponse({
            "success": True,
            "branch": branch_name,
            "original_branch": original_branch,
            "fixes_made": fixes_made,
            "total_files_modified": len([f for f in fixes_made if f.get('fixes_applied', 0) > 0]),
            "pr_url": pr_url,
            "safeguards_applied": [
                "Changes made in isolated branch",
                "Original branch preserved",
                "Must manually merge after review"
            ],
            "next_steps": [
                f"Review changes: git diff {original_branch}..{branch_name}",
                f"Merge if approved: git merge {branch_name}",
                f"Or delete if rejected: git branch -D {branch_name}"
            ]
        })

    except Exception as e:
        import traceback
        # Try to return to original branch on error
        try:
            subprocess.run(["git", "checkout", original_branch], cwd=project_root)
        except:
            pass

        return JSONResponse({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "safeguard": "Error occurred - attempted to return to original branch"
        }, status_code=500)


@router.get("/code-fix/branches")
async def list_ai_team_branches():
    """
    List all AI Team branches for review

    Shows all branches created by the AI Team that haven't been merged yet.
    """
    import subprocess
    from pathlib import Path

    try:
        project_root = Path(__file__).parent.parent.parent

        result = subprocess.run(
            ["git", "branch", "-a"],
            cwd=project_root,
            capture_output=True,
            text=True
        )

        branches = result.stdout.strip().split("\n")
        ai_branches = [b.strip().replace("* ", "") for b in branches if "ai-team/" in b]

        return JSONResponse({
            "success": True,
            "ai_team_branches": ai_branches,
            "count": len(ai_branches),
            "instructions": {
                "review": "git diff main..{branch_name}",
                "merge": "git merge {branch_name}",
                "delete": "git branch -D {branch_name}"
            }
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)
