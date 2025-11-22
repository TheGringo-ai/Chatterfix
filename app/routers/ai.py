from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import JSONResponse
from app.services.ai_assistant import chatterfix_ai
from app.core.database import get_db_connection
import shutil
import os
import json

router = APIRouter(prefix="/ai", tags=["ai"])

@router.post("/chat")
async def chat(message: str = Form(...), context: str = Form("")):
    """General AI Chat"""
    response = await chatterfix_ai.process_message(message, context)
    return JSONResponse({"response": response})

@router.post("/analyze-image")
async def analyze_image(image: UploadFile = File(...), prompt: str = Form("Describe this image for maintenance purposes.")):
    """Analyze an uploaded image"""
    if not chatterfix_ai.gemini:
        return JSONResponse({"response": "AI features unavailable."})
    
    # Save temp file
    temp_path = f"temp_{image.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
        
    try:
        response = await chatterfix_ai.gemini.analyze_image(temp_path, prompt)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
    return JSONResponse({"response": response})

@router.post("/kpi-report")
async def kpi_report():
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
        "open_work_orders": len([wo for wo in work_orders if wo['status'] == 'Open']),
        "completed_work_orders": len([wo for wo in work_orders if wo['status'] == 'Completed']),
        "total_parts": len(parts),
        "low_stock_parts": len([p for p in parts if p['current_stock'] <= p['minimum_stock']])
    }
    
    report = await chatterfix_ai.gemini.generate_kpi_report(data)
    return JSONResponse({"response": report})

@router.post("/troubleshoot")
async def troubleshoot(asset: str = Form(...), issue: str = Form(...)):
    """Get troubleshooting advice"""
    if not chatterfix_ai.gemini:
        return JSONResponse({"response": "AI features unavailable."})
        
    advice = await chatterfix_ai.gemini.get_troubleshooting_advice(asset, issue)
    return JSONResponse({"response": advice})

@router.post("/assist")
async def assist(message: str = Form(...), context: str = Form("")):
    """Global AI Assistant Endpoint"""
    if not chatterfix_ai.gemini:
        return JSONResponse({"response": "AI features unavailable."})
        
    try:
        # Call the advanced assistant agent
        result = await chatterfix_ai.gemini.run_assistant_agent(message, context)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"response": f"I encountered an error: {str(e)}"})
