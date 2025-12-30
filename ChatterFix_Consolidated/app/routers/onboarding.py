from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.database import get_db_connection
import shutil
import os
import pandas as pd
import io
from datetime import datetime

router = APIRouter(prefix="/onboarding", tags=["onboarding"])
templates = Jinja2Templates(directory="app/templates")

# Ensure upload directory exists
UPLOAD_DIR = "app/static/uploads/imports"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/", response_class=HTMLResponse)
async def onboarding_dashboard(request: Request):
    """Render the onboarding dashboard"""
    return templates.TemplateResponse("onboarding/index.html", {"request": request})

@router.get("/template/{type}")
async def get_template(type: str):
    """Download a CSV template for the specified type"""
    if type == "assets":
        df = pd.DataFrame(columns=[
            "name", "description", "asset_tag", "serial_number", "model", 
            "manufacturer", "location", "department", "status", "criticality"
        ])
        filename = "assets_template.csv"
    elif type == "parts":
        df = pd.DataFrame(columns=[
            "name", "description", "part_number", "category", "current_stock", 
            "minimum_stock", "location", "unit_cost"
        ])
        filename = "parts_template.csv"
    elif type == "work_orders":
        df = pd.DataFrame(columns=[
            "title", "description", "priority", "assigned_to", "due_date"
        ])
        filename = "work_orders_template.csv"
    else:
        return HTMLResponse("Invalid template type", status_code=400)
    
    file_path = os.path.join(UPLOAD_DIR, filename)
    df.to_csv(file_path, index=False)
    return FileResponse(file_path, filename=filename)

@router.post("/import/{type}")
async def import_data(type: str, file: UploadFile = File(...)):
    """Import data from CSV or Excel"""
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        return HTMLResponse("Invalid file format. Please upload CSV or Excel.", status_code=400)
    
    # Save file temporarily
    file_path = os.path.join(UPLOAD_DIR, f"{type}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Read file
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
    except Exception as e:
        return HTMLResponse(f"Error reading file: {str(e)}", status_code=400)
    
    conn = get_db_connection()
    
    try:
        if type == "assets":
            # Map columns and insert
            for _, row in df.iterrows():
                conn.execute("""
                    INSERT INTO assets (name, description, asset_tag, serial_number, model, manufacturer, location, department, status, criticality)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get('name'), row.get('description', ''), row.get('asset_tag', ''), 
                    row.get('serial_number', ''), row.get('model', ''), row.get('manufacturer', ''), 
                    row.get('location', ''), row.get('department', ''), 
                    row.get('status', 'Active'), row.get('criticality', 'Medium')
                ))
                
        elif type == "parts":
            for _, row in df.iterrows():
                conn.execute("""
                    INSERT INTO parts (name, description, part_number, category, current_stock, minimum_stock, location, unit_cost)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get('name'), row.get('description', ''), row.get('part_number', ''), 
                    row.get('category', 'General'), row.get('current_stock', 0), 
                    row.get('minimum_stock', 5), row.get('location', ''), row.get('unit_cost', 0.0)
                ))
                
        elif type == "work_orders":
            for _, row in df.iterrows():
                conn.execute("""
                    INSERT INTO work_orders (title, description, priority, assigned_to, due_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    row.get('title'), row.get('description', ''), row.get('priority', 'Medium'), 
                    row.get('assigned_to', ''), row.get('due_date', '')
                ))
                
        conn.commit()
        message = f"Successfully imported {len(df)} records into {type}."
        
    except Exception as e:
        conn.rollback()
        message = f"Error importing data: {str(e)}"
    finally:
        conn.close()
        
    return RedirectResponse(url=f"/onboarding?message={message}", status_code=303)
