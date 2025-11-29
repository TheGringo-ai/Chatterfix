from fastapi import APIRouter, Request, Form, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from app.services.ai_assistant import chatterfix_ai
from app.services.voice_commands import process_voice_command
from app.services.computer_vision import recognize_part, analyze_asset_condition
from app.core.database import get_db_connection
from app.core.db_adapter import get_db_adapter
from app.routers.auth import get_current_user
import shutil
import os
import json

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat")
async def chat(
    message: str = Form(...),
    context: str = Form(""),
    current_user: dict = Depends(get_current_user),
):
    """General AI Chat"""
    response = await chatterfix_ai.process_message(
        message, context, user_id=current_user["id"]
    )
    return JSONResponse({"response": response})


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
async def assist(
    message: str = Form(...),
    context: str = Form(""),
    current_user: dict = Depends(get_current_user),
):
    """Global AI Assistant Endpoint"""
    if not chatterfix_ai.gemini:
        return JSONResponse({"response": "AI features unavailable."})

    try:
        # Call the advanced assistant agent
        result = await chatterfix_ai.gemini.run_assistant_agent(
            message, context, user_id=current_user["id"]
        )
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"response": f"I encountered an error: {str(e)}"})


@router.post("/voice-command")
async def voice_command(voice_text: str = Form(...), technician_id: int = Form(None)):
    """Process voice commands with AI"""
    result = await process_voice_command(voice_text, technician_id)
    return JSONResponse(result)


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
