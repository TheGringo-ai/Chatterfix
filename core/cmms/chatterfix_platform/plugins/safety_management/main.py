#!/usr/bin/env python3
"""
ChatterFix Safety Management Module
OSHA-compliant safety department management with incident tracking,
training records, hazard analysis, and regulatory compliance.
"""

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import os
import sys

# Import ChatterFix platform services
import os, sys
platform_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, platform_root)
from chatterfix_platform.core import shared_services, event_system, SystemEvents

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="safety_management Web App",
    description="Web application",
    version="1.0.0"
)

# Setup static files and templates
app.mount("/safety_management/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Safety Management Models
class SafetyIncident(BaseModel):
    incident_id: Optional[str] = None
    date: str
    location: str
    description: str
    severity: str  # "Minor", "Major", "Critical", "Fatal"
    injured_person: str
    witness: Optional[str] = None
    root_cause: Optional[str] = None
    corrective_actions: Optional[str] = None
    osha_recordable: bool = False
    reported_by: str
    investigation_status: str = "Open"  # "Open", "Under Investigation", "Closed"

class SafetyTraining(BaseModel):
    training_id: Optional[str] = None
    employee_id: str
    training_type: str
    completion_date: str
    expiration_date: Optional[str] = None
    certification: Optional[str] = None
    instructor: str
    score: Optional[float] = None

class HazardAssessment(BaseModel):
    hazard_id: Optional[str] = None
    asset_id: Optional[str] = None
    location: str
    hazard_type: str  # "Chemical", "Physical", "Biological", "Ergonomic", "Environmental"
    risk_level: str  # "Low", "Medium", "High", "Critical"
    description: str
    mitigation_measures: str
    assessment_date: str
    next_review_date: str
    assessed_by: str
    status: str = "Active"  # "Active", "Mitigated", "Closed"

class SafetyInspection(BaseModel):
    inspection_id: Optional[str] = None
    area: str
    inspection_date: str
    inspector: str
    inspection_type: str  # "Routine", "OSHA", "Internal Audit", "Incident Follow-up"
    findings: str
    violations: Optional[str] = None
    corrective_actions: str
    completion_date: Optional[str] = None
    compliance_status: str = "In Progress"  # "Compliant", "Non-Compliant", "In Progress"

@app.on_event("startup")
async def startup():
    """Application startup"""
    logger.info("Starting safety_management Web App")
    
    # Emit startup event
    await event_system.emit(
        SystemEvents.PLUGIN_STARTED,
        {"plugin_name": "safety_management"},
        source="safety_management"
    )

@app.on_event("shutdown")
async def shutdown():
    """Application shutdown"""
    logger.info("Shutting down safety_management Web App")
    
    # Emit shutdown event
    await event_system.emit(
        SystemEvents.PLUGIN_STOPPED,
        {"plugin_name": "safety_management"},
        source="safety_management"
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": "safety_management",
        "version": "1.0.0"
    }

# ===== SAFETY INCIDENTS MANAGEMENT =====

@app.get("/api/safety_management/incidents")
async def get_incidents():
    """Get all safety incidents"""
    try:
        result = await shared_services.database.execute_query(
            "SELECT * FROM safety_incidents ORDER BY date DESC",
            fetch="all"
        )
        return {"success": True, "incidents": result.get("data", [])}
    except Exception as e:
        logger.error(f"Error fetching incidents: {e}")
        return {"success": False, "error": str(e), "incidents": []}

@app.post("/api/safety_management/incidents")
async def create_incident(incident: SafetyIncident):
    """Create a new safety incident report"""
    try:
        # Generate incident ID
        import uuid
        incident_id = f"INC-{str(uuid.uuid4())[:8].upper()}"
        
        result = await shared_services.database.execute_query(
            """INSERT INTO safety_incidents 
               (incident_id, date, location, description, severity, injured_person, 
                witness, root_cause, corrective_actions, osha_recordable, reported_by, investigation_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [incident_id, incident.date, incident.location, incident.description, 
             incident.severity, incident.injured_person, incident.witness, 
             incident.root_cause, incident.corrective_actions, incident.osha_recordable, 
             incident.reported_by, incident.investigation_status]
        )
        
        # Emit safety incident event
        await event_system.emit(
            "safety.incident.created",
            {
                "incident_id": incident_id,
                "severity": incident.severity,
                "osha_recordable": incident.osha_recordable,
                "location": incident.location
            },
            source="safety_management"
        )
        
        return {"success": True, "incident_id": incident_id, "message": "Safety incident reported successfully"}
    except Exception as e:
        logger.error(f"Error creating incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== SAFETY TRAINING MANAGEMENT =====

@app.get("/api/safety_management/training")
async def get_training_records():
    """Get all training records"""
    try:
        result = await shared_services.database.execute_query(
            "SELECT * FROM safety_training ORDER BY completion_date DESC",
            fetch="all"
        )
        return {"success": True, "training_records": result.get("data", [])}
    except Exception as e:
        logger.error(f"Error fetching training records: {e}")
        return {"success": False, "error": str(e), "training_records": []}

@app.post("/api/safety_management/training")
async def record_training(training: SafetyTraining):
    """Record safety training completion"""
    try:
        import uuid
        training_id = f"TRN-{str(uuid.uuid4())[:8].upper()}"
        
        result = await shared_services.database.execute_query(
            """INSERT INTO safety_training 
               (training_id, employee_id, training_type, completion_date, 
                expiration_date, certification, instructor, score)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [training_id, training.employee_id, training.training_type, 
             training.completion_date, training.expiration_date, 
             training.certification, training.instructor, training.score]
        )
        
        await event_system.emit(
            "safety.training.completed",
            {
                "training_id": training_id,
                "employee_id": training.employee_id,
                "training_type": training.training_type
            },
            source="safety_management"
        )
        
        return {"success": True, "training_id": training_id, "message": "Training record created successfully"}
    except Exception as e:
        logger.error(f"Error recording training: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== HAZARD ASSESSMENTS =====

@app.get("/api/safety_management/hazards")
async def get_hazard_assessments():
    """Get all hazard assessments"""
    try:
        result = await shared_services.database.execute_query(
            "SELECT * FROM hazard_assessments WHERE status != 'Closed' ORDER BY risk_level DESC, assessment_date DESC",
            fetch="all"
        )
        return {"success": True, "hazards": result.get("data", [])}
    except Exception as e:
        logger.error(f"Error fetching hazards: {e}")
        return {"success": False, "error": str(e), "hazards": []}

@app.post("/api/safety_management/hazards")
async def create_hazard_assessment(hazard: HazardAssessment):
    """Create a new hazard assessment"""
    try:
        import uuid
        hazard_id = f"HAZ-{str(uuid.uuid4())[:8].upper()}"
        
        result = await shared_services.database.execute_query(
            """INSERT INTO hazard_assessments 
               (hazard_id, asset_id, location, hazard_type, risk_level, description, 
                mitigation_measures, assessment_date, next_review_date, assessed_by, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [hazard_id, hazard.asset_id, hazard.location, hazard.hazard_type,
             hazard.risk_level, hazard.description, hazard.mitigation_measures,
             hazard.assessment_date, hazard.next_review_date, hazard.assessed_by, hazard.status]
        )
        
        await event_system.emit(
            "safety.hazard.identified",
            {
                "hazard_id": hazard_id,
                "risk_level": hazard.risk_level,
                "location": hazard.location,
                "hazard_type": hazard.hazard_type
            },
            source="safety_management"
        )
        
        return {"success": True, "hazard_id": hazard_id, "message": "Hazard assessment created successfully"}
    except Exception as e:
        logger.error(f"Error creating hazard assessment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== SAFETY INSPECTIONS =====

@app.get("/api/safety_management/inspections")
async def get_inspections():
    """Get all safety inspections"""
    try:
        result = await shared_services.database.execute_query(
            "SELECT * FROM safety_inspections ORDER BY inspection_date DESC",
            fetch="all"
        )
        return {"success": True, "inspections": result.get("data", [])}
    except Exception as e:
        logger.error(f"Error fetching inspections: {e}")
        return {"success": False, "error": str(e), "inspections": []}

@app.post("/api/safety_management/inspections")
async def create_inspection(inspection: SafetyInspection):
    """Create a new safety inspection record"""
    try:
        import uuid
        inspection_id = f"INS-{str(uuid.uuid4())[:8].upper()}"
        
        result = await shared_services.database.execute_query(
            """INSERT INTO safety_inspections 
               (inspection_id, area, inspection_date, inspector, inspection_type, 
                findings, violations, corrective_actions, completion_date, compliance_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [inspection_id, inspection.area, inspection.inspection_date, 
             inspection.inspector, inspection.inspection_type, inspection.findings,
             inspection.violations, inspection.corrective_actions, 
             inspection.completion_date, inspection.compliance_status]
        )
        
        await event_system.emit(
            "safety.inspection.completed",
            {
                "inspection_id": inspection_id,
                "area": inspection.area,
                "compliance_status": inspection.compliance_status,
                "inspector": inspection.inspector
            },
            source="safety_management"
        )
        
        return {"success": True, "inspection_id": inspection_id, "message": "Safety inspection recorded successfully"}
    except Exception as e:
        logger.error(f"Error creating inspection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== OSHA COMPLIANCE & REPORTING =====

@app.get("/api/safety_management/osha/dashboard")
async def get_osha_dashboard():
    """Get OSHA compliance dashboard data"""
    try:
        # Get OSHA recordable incidents
        osha_incidents = await shared_services.database.execute_query(
            "SELECT COUNT(*) as count FROM safety_incidents WHERE osha_recordable = true",
            fetch="one"
        )
        
        # Get total training completions this year
        training_completions = await shared_services.database.execute_query(
            "SELECT COUNT(*) as count FROM safety_training WHERE completion_date >= date('now', 'start of year')",
            fetch="one"
        )
        
        # Get high-risk hazards
        high_risk_hazards = await shared_services.database.execute_query(
            "SELECT COUNT(*) as count FROM hazard_assessments WHERE risk_level IN ('High', 'Critical') AND status = 'Active'",
            fetch="one"
        )
        
        # Get pending inspections
        pending_inspections = await shared_services.database.execute_query(
            "SELECT COUNT(*) as count FROM safety_inspections WHERE compliance_status = 'In Progress'",
            fetch="one"
        )
        
        return {
            "success": True,
            "osha_recordable_incidents": osha_incidents.get("data", {}).get("count", 0),
            "training_completions_ytd": training_completions.get("data", {}).get("count", 0),
            "high_risk_hazards": high_risk_hazards.get("data", {}).get("count", 0),
            "pending_inspections": pending_inspections.get("data", {}).get("count", 0)
        }
    except Exception as e:
        logger.error(f"Error fetching OSHA dashboard: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/safety_management/analytics/incident-trends")
async def get_incident_trends():
    """Get incident trend analysis using AI"""
    try:
        # Get recent incidents
        result = await shared_services.database.execute_query(
            "SELECT * FROM safety_incidents WHERE date >= date('now', '-90 days') ORDER BY date DESC",
            fetch="all"
        )
        
        incidents = result.get("data", [])
        
        if not incidents:
            return {"success": True, "analysis": "No incidents in the last 90 days to analyze.", "trends": []}
        
        # Use AI to analyze trends
        incident_summary = f"Safety incidents in last 90 days: {len(incidents)} total. "
        incident_summary += f"Severity breakdown: "
        
        severity_counts = {}
        for incident in incidents:
            severity = incident.get("severity", "Unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        incident_summary += ", ".join([f"{k}: {v}" for k, v in severity_counts.items()])
        
        prompt = f"""
        Analyze this safety incident data for trends and provide actionable insights:
        
        {incident_summary}
        
        Provide:
        1. Key trends identified
        2. Risk areas of concern
        3. Recommended preventive actions
        4. OSHA compliance considerations
        """
        
        analysis = await shared_services.ai.generate_text(prompt, provider="openai")
        
        return {
            "success": True,
            "analysis": analysis,
            "incident_count": len(incidents),
            "severity_breakdown": severity_counts
        }
    except Exception as e:
        logger.error(f"Error analyzing incident trends: {e}")
        return {"success": False, "error": str(e)}

# ===== SAFETY BULK OPERATIONS =====

@app.post("/api/safety_management/incidents/bulk-upload")
async def bulk_upload_safety_incidents(request: Request):
    """Bulk upload safety incidents from CSV/Excel file"""
    try:
        import pandas as pd
        import io
        
        form = await request.form()
        file = form.get("file")
        
        if not file:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Read the file content
        content = await file.read()
        
        # Determine file type and parse accordingly
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV or Excel.")
        
        # Validate required columns
        required_columns = ['date', 'location', 'description', 'severity', 'injured_person', 'reported_by']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        # Process each row
        success_count = 0
        error_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                import uuid
                incident_id = f"INC-{str(uuid.uuid4())[:8].upper()}"
                
                # Prepare incident data
                incident_data = {
                    'date': str(row['date']).strip(),
                    'location': str(row['location']).strip(),
                    'description': str(row['description']).strip(),
                    'severity': str(row['severity']).strip(),
                    'injured_person': str(row['injured_person']).strip(),
                    'witness': str(row.get('witness', '')).strip(),
                    'root_cause': str(row.get('root_cause', '')).strip(),
                    'corrective_actions': str(row.get('corrective_actions', '')).strip(),
                    'osha_recordable': bool(row.get('osha_recordable', False)),
                    'reported_by': str(row['reported_by']).strip(),
                    'investigation_status': str(row.get('investigation_status', 'Open')).strip()
                }
                
                # Validate severity
                valid_severities = ['Minor', 'Major', 'Critical', 'Fatal']
                if incident_data['severity'] not in valid_severities:
                    raise ValueError(f"Invalid severity '{incident_data['severity']}'. Must be one of: {', '.join(valid_severities)}")
                
                # Insert into database
                result = await shared_services.database.execute_query(
                    """INSERT INTO safety_incidents 
                       (incident_id, date, location, description, severity, injured_person, 
                        witness, root_cause, corrective_actions, osha_recordable, reported_by, investigation_status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    [incident_id, incident_data['date'], incident_data['location'], incident_data['description'], 
                     incident_data['severity'], incident_data['injured_person'], incident_data['witness'], 
                     incident_data['root_cause'], incident_data['corrective_actions'], incident_data['osha_recordable'], 
                     incident_data['reported_by'], incident_data['investigation_status']]
                )
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(f"Row {index + 2}: {str(e)}")
        
        return {
            "success": True,
            "message": f"Processed {len(df)} safety incidents",
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors[:10]  # Limit to first 10 errors
        }
        
    except Exception as e:
        logger.error(f"Error in bulk upload safety incidents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/safety_management/incidents/bulk-download")
async def bulk_download_safety_incidents(format: str = "csv"):
    """Bulk download safety incidents as CSV or Excel file"""
    try:
        import pandas as pd
        import io
        from fastapi.responses import StreamingResponse
        
        # Get all safety incidents
        result = await shared_services.database.execute_query(
            "SELECT * FROM safety_incidents ORDER BY date DESC",
            fetch="all"
        )
        
        incidents = result.get("data", [])
        if not incidents:
            raise HTTPException(status_code=404, detail="No safety incidents found")
        
        # Convert to DataFrame
        df = pd.DataFrame(incidents)
        
        # Generate file
        if format.lower() == "excel":
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Safety Incidents', index=False)
            output.seek(0)
            
            return StreamingResponse(
                io.BytesIO(output.read()),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=safety_incidents.xlsx"}
            )
        else:
            # Default to CSV
            output = io.StringIO()
            df.to_csv(output, index=False)
            output.seek(0)
            
            return StreamingResponse(
                io.StringIO(output.getvalue()),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=safety_incidents.csv"}
            )
            
    except Exception as e:
        logger.error(f"Error in bulk download safety incidents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/safety_management/incidents/template")
async def download_safety_incidents_template(format: str = "csv"):
    """Download safety incidents upload template"""
    try:
        import pandas as pd
        import io
        from fastapi.responses import StreamingResponse
        
        # Create template with sample data
        template_data = {
            'date': ['2024-01-15', '2024-01-20'],
            'location': ['Factory Floor A', 'Warehouse Section B'],
            'description': ['Employee slipped on wet floor', 'Minor cut from equipment'],
            'severity': ['Minor', 'Minor'],
            'injured_person': ['John Smith', 'Jane Doe'],
            'witness': ['Mike Johnson', ''],
            'root_cause': ['Wet floor not marked', 'Equipment maintenance needed'],
            'corrective_actions': ['Install slip-resistant mats', 'Schedule equipment maintenance'],
            'osha_recordable': [False, False],
            'reported_by': ['Safety Manager', 'Supervisor'],
            'investigation_status': ['Closed', 'Open']
        }
        
        df = pd.DataFrame(template_data)
        
        if format.lower() == "excel":
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Safety Incidents Template', index=False)
            output.seek(0)
            
            return StreamingResponse(
                io.BytesIO(output.read()),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=safety_incidents_template.xlsx"}
            )
        else:
            # Default to CSV
            output = io.StringIO()
            df.to_csv(output, index=False)
            output.seek(0)
            
            return StreamingResponse(
                io.StringIO(output.getvalue()),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=safety_incidents_template.csv"}
            )
            
    except Exception as e:
        logger.error(f"Error generating safety incidents template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/safety_management", response_class=HTMLResponse)
async def home(request: Request):
    """Home page"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "app_name": "safety_management",
        "description": "Web application"
    })

@app.get("/api/safety_management/data")
async def get_app_data():
    """Get application data"""
    # Example: fetch from database using shared services
    try:
        # Use shared database service
        result = await shared_services.database.execute_query(
            "SELECT 'Example data' as title, 'This is example content' as content",
            fetch="one"
        )
        
        if result.get("success"):
            data = result.get("data", {})
            return AppData(
                title=data.get("title", "No title"),
                content=data.get("content", "No content"),
                metadata={"source": "safety_management"}
            )
        else:
            raise HTTPException(status_code=500, detail="Database query failed")
            
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/safety_management/data")
async def create_app_data(data: AppData):
    """Create new application data"""
    try:
        # Example: save to database using shared services
        result = await shared_services.database.execute_query(
            "INSERT INTO safety_management_data (title, content) VALUES (?, ?)",
            [data.title, data.content],
            fetch="none"
        )
        
        if result.get("success"):
            return {"message": "Data created successfully", "id": result.get("data")}
        else:
            raise HTTPException(status_code=500, detail="Failed to create data")
            
    except Exception as e:
        logger.error(f"Error creating data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Plugin lifecycle functions
async def start():
    """Start the plugin"""
    logger.info("safety_management plugin started")

async def stop():
    """Stop the plugin"""
    logger.info("safety_management plugin stopped")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8200))
    uvicorn.run(app, host="0.0.0.0", port=port)
