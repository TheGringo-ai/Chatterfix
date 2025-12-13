import os
import shutil

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.firestore_db import get_db_connection

# # from app.core.database import get_db_connection
from app.routers.auth import get_current_user
from app.services.ai_assistant import chatterfix_ai
from app.services.computer_vision import analyze_asset_condition, recognize_part, extract_text_from_image, detect_equipment_issues
from app.services.voice_commands import (
    get_voice_command_suggestions,
    process_voice_command,
)

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


@router.post("/chat")
async def chat(request: ChatRequest):
    """General AI Chat"""
    try:
        response = await chatterfix_ai.process_message(
            request.message, request.context, user_id=request.user_id
        )
        return JSONResponse({"response": response})
    except Exception as e:
        return JSONResponse(
            {"response": f"I encountered an error: {str(e)}"}, status_code=500
        )


@router.post("/analyze-image")
async def analyze_image(
    image: UploadFile = File(...),
    prompt: str = Form("Describe this image for maintenance purposes."),
    current_user: dict = Depends(get_current_user),
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
            temp_path, prompt, user_id=current_user["id"]
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return JSONResponse({"response": response})


@router.post("/kpi-report")
async def kpi_report(current_user: dict = Depends(get_current_user)):
    """Generate KPI Report"""
    if not chatterfix_ai.gemini:
        return JSONResponse({"response": "AI features unavailable."})

    # Gather data
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
        data, user_id=current_user["id"]
    )
    return JSONResponse({"response": report})


@router.post("/troubleshoot")
async def troubleshoot(
    asset: str = Form(...),
    issue: str = Form(...),
    current_user: dict = Depends(get_current_user),
):
    """Get troubleshooting advice"""
    if not chatterfix_ai.gemini:
        return JSONResponse({"response": "AI features unavailable."})

    advice = await chatterfix_ai.gemini.get_troubleshooting_advice(
        asset, issue, user_id=current_user["id"]
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
