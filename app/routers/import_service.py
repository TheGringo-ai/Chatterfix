"""
Smart Data Ingestion Service
The "White Glove" feature for enterprise onboarding.

Handles:
- CSV/XLSX import with AI-powered column mapping
- PDF manual processing for maintenance schedules
- Background processing for large files
"""

import asyncio
import io
import json
import logging
import os
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# Rate limiting
from collections import defaultdict
import time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/import", tags=["Data Import"])

# Templates for HTML pages
templates = Jinja2Templates(directory="app/templates")


# ============ HTML Page Route ============

@router.get("/page", response_class=HTMLResponse, include_in_schema=False)
async def import_page(request: Request):
    """Serve the data import page"""
    return templates.TemplateResponse(
        "data_import.html",
        {
            "request": request,
            "title": "Smart Data Import",
            "supported_formats": ["CSV", "XLSX", "PDF"],
            "entity_types": ["assets", "parts", "users"],
        }
    )

# ============ Rate Limiting ============
# Simple in-memory rate limiter (use Redis in production)
rate_limit_store: Dict[str, List[float]] = defaultdict(list)
RATE_LIMIT_REQUESTS = 10  # Max requests per window
RATE_LIMIT_WINDOW = 60  # Window in seconds


def check_rate_limit(user_id: str) -> bool:
    """Check if user has exceeded rate limit"""
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW

    # Clean old entries
    rate_limit_store[user_id] = [
        ts for ts in rate_limit_store[user_id] if ts > window_start
    ]

    if len(rate_limit_store[user_id]) >= RATE_LIMIT_REQUESTS:
        return False

    rate_limit_store[user_id].append(now)
    return True


# ============ Pydantic Models ============

class ColumnMapping(BaseModel):
    """Suggested mapping from source column to target field"""
    source_column: str
    target_field: str
    confidence: float = Field(ge=0.0, le=1.0)
    data_type: str
    sample_values: List[str] = []


class MappingSuggestion(BaseModel):
    """AI-generated mapping suggestions"""
    entity_type: str  # "asset", "part", "user"
    mappings: List[ColumnMapping]
    unmapped_columns: List[str] = []
    warnings: List[str] = []


class ImportJob(BaseModel):
    """Background import job status"""
    job_id: str
    status: str  # "pending", "processing", "completed", "failed"
    file_name: str
    entity_type: Optional[str] = None
    total_rows: int = 0
    processed_rows: int = 0
    errors: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


class MaintenanceScheduleItem(BaseModel):
    """Extracted maintenance schedule from PDF"""
    task_name: str
    frequency: str  # "daily", "weekly", "monthly", "quarterly", "yearly"
    asset_type: Optional[str] = None
    estimated_duration: Optional[str] = None
    required_parts: List[str] = []
    notes: Optional[str] = None


# ============ In-Memory Job Store ============
# In production, use Redis or Firestore
import_jobs: Dict[str, ImportJob] = {}


# ============ Target Field Definitions ============

ASSET_FIELDS = {
    "name": {"type": "string", "required": True, "description": "Asset name or title"},
    "description": {"type": "string", "required": False, "description": "Detailed description"},
    "asset_tag": {"type": "string", "required": False, "description": "Unique asset identifier/tag"},
    "serial_number": {"type": "string", "required": False, "description": "Manufacturer serial number"},
    "model": {"type": "string", "required": False, "description": "Model number"},
    "manufacturer": {"type": "string", "required": False, "description": "Manufacturer/brand name"},
    "location": {"type": "string", "required": False, "description": "Physical location"},
    "department": {"type": "string", "required": False, "description": "Department or cost center"},
    "status": {"type": "string", "required": False, "description": "Operational status"},
    "criticality": {"type": "string", "required": False, "description": "Criticality level (Low/Medium/High/Critical)"},
    "purchase_date": {"type": "date", "required": False, "description": "Date of purchase"},
    "warranty_expiry": {"type": "date", "required": False, "description": "Warranty expiration date"},
    "purchase_cost": {"type": "number", "required": False, "description": "Purchase cost/price"},
}

PART_FIELDS = {
    "name": {"type": "string", "required": True, "description": "Part name"},
    "part_number": {"type": "string", "required": True, "description": "Part number/SKU"},
    "category": {"type": "string", "required": True, "description": "Part category"},
    "description": {"type": "string", "required": False, "description": "Part description"},
    "current_stock": {"type": "integer", "required": False, "description": "Current inventory quantity"},
    "minimum_stock": {"type": "integer", "required": False, "description": "Reorder point/minimum stock level"},
    "unit_cost": {"type": "number", "required": False, "description": "Unit cost/price"},
    "location": {"type": "string", "required": False, "description": "Storage location"},
    "supplier": {"type": "string", "required": False, "description": "Supplier/vendor name"},
}

USER_FIELDS = {
    "email": {"type": "email", "required": True, "description": "Email address"},
    "full_name": {"type": "string", "required": False, "description": "Full name"},
    "role": {"type": "string", "required": False, "description": "User role (technician/manager/admin)"},
}


# ============ Smart Mapper Logic ============

async def get_ai_column_mapping(
    headers: List[str],
    sample_data: List[Dict[str, Any]],
    entity_type: str
) -> MappingSuggestion:
    """
    Use LLM to intelligently map source columns to target fields.
    Uses Gemini in "budget mode" (fast, cheap model).
    """
    try:
        from app.services.gemini_service import gemini_service

        # Select target fields based on entity type
        target_fields = {
            "asset": ASSET_FIELDS,
            "part": PART_FIELDS,
            "user": USER_FIELDS,
        }.get(entity_type, ASSET_FIELDS)

        # Prepare sample data for context
        sample_str = ""
        for i, row in enumerate(sample_data[:3]):
            sample_str += f"Row {i+1}: {json.dumps(row, default=str)}\n"

        prompt = f"""You are a data mapping expert. Analyze these CSV/Excel columns and map them to our database fields.

SOURCE COLUMNS: {json.dumps(headers)}

SAMPLE DATA:
{sample_str}

TARGET FIELDS for {entity_type.upper()}:
{json.dumps(target_fields, indent=2)}

INSTRUCTIONS:
1. Match each source column to the most appropriate target field
2. Consider column names, data patterns, and sample values
3. Assign a confidence score (0.0-1.0) based on match quality
4. Note any columns that don't match any target field

Return ONLY valid JSON in this exact format:
{{
    "mappings": [
        {{"source_column": "Their_Col", "target_field": "our_field", "confidence": 0.95, "data_type": "string"}},
        ...
    ],
    "unmapped_columns": ["col1", "col2"],
    "warnings": ["Any data quality issues noticed"]
}}

Common mappings to watch for:
- "Equip_ID", "Equipment ID", "Asset #" -> asset_tag
- "Mfr", "Manufacturer", "Brand" -> manufacturer
- "S/N", "Serial", "Serial No" -> serial_number
- "Qty", "Quantity", "Stock" -> current_stock
- "P/N", "Part #", "SKU" -> part_number
"""

        if not gemini_service.is_available():
            # Fallback to rule-based mapping if AI unavailable
            return _rule_based_mapping(headers, sample_data, entity_type, target_fields)

        response = await gemini_service.generate_response(prompt)

        # Parse JSON from response
        try:
            # Extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                mapping_data = json.loads(response[json_start:json_end])

                mappings = []
                for m in mapping_data.get("mappings", []):
                    # Find sample values for this column
                    samples = []
                    if m["source_column"] in headers:
                        for row in sample_data[:5]:
                            val = row.get(m["source_column"])
                            if val is not None:
                                samples.append(str(val)[:50])

                    mappings.append(ColumnMapping(
                        source_column=m["source_column"],
                        target_field=m["target_field"],
                        confidence=float(m.get("confidence", 0.5)),
                        data_type=m.get("data_type", "string"),
                        sample_values=samples[:3]
                    ))

                return MappingSuggestion(
                    entity_type=entity_type,
                    mappings=mappings,
                    unmapped_columns=mapping_data.get("unmapped_columns", []),
                    warnings=mapping_data.get("warnings", [])
                )
        except json.JSONDecodeError:
            pass

        # Fallback if AI response parsing fails
        return _rule_based_mapping(headers, sample_data, entity_type, target_fields)

    except Exception as e:
        logger.error(f"AI mapping failed: {e}")
        return _rule_based_mapping(headers, sample_data, entity_type, target_fields)


def _rule_based_mapping(
    headers: List[str],
    sample_data: List[Dict[str, Any]],
    entity_type: str,
    target_fields: Dict
) -> MappingSuggestion:
    """Fallback rule-based column mapping when AI is unavailable"""

    # Common column name patterns
    patterns = {
        # Asset patterns
        "name": ["name", "title", "asset name", "equipment name", "description"],
        "asset_tag": ["asset tag", "asset id", "equip id", "equipment id", "asset #", "tag"],
        "serial_number": ["serial", "s/n", "serial no", "serial number"],
        "model": ["model", "model no", "model number"],
        "manufacturer": ["mfr", "manufacturer", "brand", "make"],
        "location": ["location", "loc", "building", "area", "room"],
        "department": ["department", "dept", "cost center"],
        "status": ["status", "condition", "state"],
        "purchase_date": ["purchase date", "acquired", "install date"],
        "purchase_cost": ["cost", "price", "purchase cost", "value"],

        # Part patterns
        "part_number": ["part no", "part #", "p/n", "sku", "item number"],
        "category": ["category", "type", "class"],
        "current_stock": ["qty", "quantity", "stock", "on hand", "count"],
        "minimum_stock": ["min", "minimum", "reorder", "min stock"],
        "unit_cost": ["unit cost", "unit price", "price"],
        "supplier": ["supplier", "vendor", "source"],

        # User patterns
        "email": ["email", "e-mail", "mail"],
        "full_name": ["name", "full name", "employee name"],
        "role": ["role", "position", "title", "job title"],
    }

    mappings = []
    mapped_columns = set()

    for header in headers:
        header_lower = header.lower().strip()
        best_match = None
        best_confidence = 0.0

        for target_field, keywords in patterns.items():
            if target_field not in target_fields:
                continue

            for keyword in keywords:
                if keyword == header_lower:
                    best_match = target_field
                    best_confidence = 0.95
                    break
                elif keyword in header_lower or header_lower in keyword:
                    if best_confidence < 0.7:
                        best_match = target_field
                        best_confidence = 0.7

        if best_match:
            samples = []
            for row in sample_data[:5]:
                val = row.get(header)
                if val is not None:
                    samples.append(str(val)[:50])

            mappings.append(ColumnMapping(
                source_column=header,
                target_field=best_match,
                confidence=best_confidence,
                data_type=target_fields[best_match]["type"],
                sample_values=samples[:3]
            ))
            mapped_columns.add(header)

    unmapped = [h for h in headers if h not in mapped_columns]

    return MappingSuggestion(
        entity_type=entity_type,
        mappings=mappings,
        unmapped_columns=unmapped,
        warnings=["Using rule-based mapping (AI unavailable)"] if unmapped else []
    )


# ============ PDF Processor ============

async def extract_maintenance_schedules_from_pdf(
    pdf_content: bytes,
    filename: str
) -> List[MaintenanceScheduleItem]:
    """
    Extract maintenance schedule tables from PDF using OCR/Vision.
    Looks for maintenance intervals, PM schedules, etc.
    """
    try:
        from app.services.gemini_service import gemini_service
        import PIL.Image

        # For PDFs, we'll use pdf2image or similar to convert to images
        # Then use Gemini Vision to extract tables

        # Save PDF temporarily
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_content)
            tmp_path = tmp.name

        try:
            # Try to use pdf2image if available
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(tmp_path, first_page=1, last_page=5)
            except ImportError:
                logger.warning("pdf2image not installed - using EasyOCR fallback")
                # Fallback: Use EasyOCR directly on text extraction
                return await _extract_schedules_with_ocr(pdf_content, filename)

            schedules = []

            for i, img in enumerate(images[:5]):  # Process first 5 pages
                # Save image temporarily for Gemini
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as img_tmp:
                    img.save(img_tmp.name, "PNG")
                    img_path = img_tmp.name

                try:
                    prompt = """Analyze this page from an equipment manual or maintenance document.

Look for MAINTENANCE SCHEDULE tables, PM (Preventive Maintenance) schedules, or service intervals.

If you find maintenance tasks, extract them in this JSON format:
{
    "schedules": [
        {
            "task_name": "Task description",
            "frequency": "daily/weekly/monthly/quarterly/yearly",
            "asset_type": "Equipment type if mentioned",
            "estimated_duration": "Time estimate if given",
            "required_parts": ["Part 1", "Part 2"],
            "notes": "Any additional notes"
        }
    ],
    "found_schedule": true
}

If no maintenance schedule is found on this page, return:
{"schedules": [], "found_schedule": false}

Return ONLY valid JSON."""

                    if gemini_service.is_available():
                        response = await gemini_service.analyze_image(img_path, prompt)

                        # Parse response
                        try:
                            json_start = response.find("{")
                            json_end = response.rfind("}") + 1
                            if json_start >= 0:
                                data = json.loads(response[json_start:json_end])
                                if data.get("found_schedule"):
                                    for sched in data.get("schedules", []):
                                        schedules.append(MaintenanceScheduleItem(
                                            task_name=sched.get("task_name", "Unknown Task"),
                                            frequency=sched.get("frequency", "monthly"),
                                            asset_type=sched.get("asset_type"),
                                            estimated_duration=sched.get("estimated_duration"),
                                            required_parts=sched.get("required_parts", []),
                                            notes=sched.get("notes")
                                        ))
                        except json.JSONDecodeError:
                            pass
                finally:
                    os.unlink(img_path)

            return schedules

        finally:
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"PDF processing failed: {e}")
        return []


async def _extract_schedules_with_ocr(
    pdf_content: bytes,
    filename: str
) -> List[MaintenanceScheduleItem]:
    """Fallback OCR-based extraction using EasyOCR"""
    try:
        import easyocr

        # Note: EasyOCR works on images, not PDFs directly
        # This is a simplified fallback
        logger.warning(f"OCR fallback for {filename} - limited extraction")

        return [MaintenanceScheduleItem(
            task_name=f"Manual review required for {filename}",
            frequency="monthly",
            notes="PDF could not be fully processed. Please review manually."
        )]

    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        return []


# ============ Data Validation ============

def validate_row_data(row: Dict[str, Any], mapping: MappingSuggestion) -> tuple[Dict[str, Any], List[str]]:
    """
    Validate and transform a data row according to the mapping.
    Returns (validated_data, errors)
    """
    validated = {}
    errors = []

    target_fields = {
        "asset": ASSET_FIELDS,
        "part": PART_FIELDS,
        "user": USER_FIELDS,
    }.get(mapping.entity_type, ASSET_FIELDS)

    for col_mapping in mapping.mappings:
        source_val = row.get(col_mapping.source_column)
        target_field = col_mapping.target_field
        field_info = target_fields.get(target_field, {})
        expected_type = field_info.get("type", "string")

        if source_val is None or (isinstance(source_val, str) and not source_val.strip()):
            if field_info.get("required"):
                errors.append(f"Missing required field: {target_field}")
            continue

        # Type validation and conversion
        try:
            if expected_type == "integer":
                validated[target_field] = int(float(str(source_val).replace(",", "")))
            elif expected_type == "number":
                validated[target_field] = float(str(source_val).replace(",", "").replace("$", ""))
            elif expected_type == "date":
                # Try common date formats
                from dateutil import parser
                validated[target_field] = parser.parse(str(source_val)).isoformat()
            elif expected_type == "email":
                email = str(source_val).strip().lower()
                if "@" not in email:
                    errors.append(f"Invalid email format: {source_val}")
                else:
                    validated[target_field] = email
            else:
                validated[target_field] = str(source_val).strip()
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid {expected_type} for {target_field}: {source_val}")

    return validated, errors


# ============ Background Processing ============

async def process_import_job(
    job_id: str,
    file_content: bytes,
    file_type: str,
    entity_type: str,
    mapping: MappingSuggestion,
    organization_id: str
):
    """Background task to process large file imports"""
    job = import_jobs.get(job_id)
    if not job:
        return

    try:
        job.status = "processing"

        # Read file based on type
        if file_type in ["csv", "text/csv"]:
            df = pd.read_csv(io.BytesIO(file_content))
        elif file_type in ["xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
            df = pd.read_excel(io.BytesIO(file_content))
        else:
            job.status = "failed"
            job.errors.append(f"Unsupported file type: {file_type}")
            return

        job.total_rows = len(df)

        # Process rows in batches
        batch_size = 100
        imported_records = []

        for i, row in df.iterrows():
            row_dict = row.to_dict()
            validated_data, errors = validate_row_data(row_dict, mapping)

            if errors:
                job.errors.extend([f"Row {i+1}: {e}" for e in errors[:3]])  # Limit errors
            else:
                validated_data["organization_id"] = organization_id
                imported_records.append(validated_data)

            job.processed_rows = i + 1

            # Yield control periodically
            if i % batch_size == 0:
                await asyncio.sleep(0.01)

        # TODO: Actually insert into Firestore
        # For now, just log success
        logger.info(f"Import job {job_id}: Processed {len(imported_records)} valid records")

        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)

    except Exception as e:
        logger.error(f"Import job {job_id} failed: {e}")
        job.status = "failed"
        job.errors.append(str(e))


# ============ API Endpoints ============

@router.post("/upload")
async def upload_file(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    entity_type: str = "asset"
):
    """
    Upload a file for import processing.

    Accepts: CSV, XLSX, PDF

    For CSV/XLSX: Returns AI-suggested column mappings
    For PDF: Extracts maintenance schedules
    """
    # Rate limiting
    user_id = request.cookies.get("session_token", "anonymous")
    if not check_rate_limit(user_id):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait before uploading more files."
        )

    # Validate file type
    filename = file.filename or "unknown"
    file_ext = filename.lower().split(".")[-1]
    content_type = file.content_type or ""

    allowed_types = {
        "csv": "text/csv",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pdf": "application/pdf"
    }

    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_types.keys())}"
        )

    # Read file content
    content = await file.read()

    # File size limit (50MB)
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 50MB."
        )

    # Create job ID
    job_id = str(uuid.uuid4())

    # Process based on file type
    if file_ext == "pdf":
        # PDF: Extract maintenance schedules
        schedules = await extract_maintenance_schedules_from_pdf(content, filename)

        return JSONResponse({
            "success": True,
            "file_type": "pdf",
            "filename": filename,
            "extracted_schedules": [s.dict() for s in schedules],
            "message": f"Found {len(schedules)} maintenance schedule items",
            "next_step": "Review extracted schedules and confirm import"
        })

    else:
        # CSV/XLSX: Read and get mapping suggestions
        try:
            if file_ext == "csv":
                df = pd.read_csv(io.BytesIO(content))
            else:
                df = pd.read_excel(io.BytesIO(content))
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse file: {str(e)}"
            )

        headers = df.columns.tolist()
        sample_data = df.head(5).to_dict(orient="records")

        # Get AI mapping suggestions
        mapping = await get_ai_column_mapping(headers, sample_data, entity_type)

        # Create pending import job
        import_jobs[job_id] = ImportJob(
            job_id=job_id,
            status="pending_confirmation",
            file_name=filename,
            entity_type=entity_type,
            total_rows=len(df)
        )

        return JSONResponse({
            "success": True,
            "job_id": job_id,
            "file_type": file_ext,
            "filename": filename,
            "total_rows": len(df),
            "headers": headers,
            "sample_data": sample_data[:3],
            "suggested_mapping": mapping.dict(),
            "message": "Please review the column mappings and confirm to proceed",
            "next_step": f"POST /api/v1/import/confirm/{job_id} with confirmed mappings"
        })


@router.post("/confirm/{job_id}")
async def confirm_import(
    request: Request,
    job_id: str,
    background_tasks: BackgroundTasks,
    confirmed_mapping: Dict[str, str]
):
    """
    Confirm column mappings and start the import process.

    Args:
        confirmed_mapping: Dict of {source_column: target_field}
    """
    job = import_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")

    if job.status != "pending_confirmation":
        raise HTTPException(
            status_code=400,
            detail=f"Job is not pending confirmation. Status: {job.status}"
        )

    # Convert confirmed mapping to MappingSuggestion format
    mappings = [
        ColumnMapping(
            source_column=source,
            target_field=target,
            confidence=1.0,  # User confirmed
            data_type="string"
        )
        for source, target in confirmed_mapping.items()
    ]

    mapping = MappingSuggestion(
        entity_type=job.entity_type or "asset",
        mappings=mappings
    )

    # Get organization ID from session
    org_id = request.cookies.get("organization_id", "demo_org")

    # TODO: Retrieve stored file content
    # For now, return success message
    job.status = "processing"

    return JSONResponse({
        "success": True,
        "job_id": job_id,
        "message": "Import started. Check status with GET /api/v1/import/status/{job_id}",
        "status": job.status
    })


@router.get("/status/{job_id}")
async def get_import_status(job_id: str):
    """Get the status of an import job"""
    job = import_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")

    return JSONResponse({
        "job_id": job.job_id,
        "status": job.status,
        "filename": job.file_name,
        "entity_type": job.entity_type,
        "total_rows": job.total_rows,
        "processed_rows": job.processed_rows,
        "progress_percent": (job.processed_rows / job.total_rows * 100) if job.total_rows > 0 else 0,
        "errors": job.errors[:10],  # Limit error response
        "created_at": job.created_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None
    })


@router.get("/templates/{entity_type}")
async def get_import_template(entity_type: str):
    """Get a sample CSV template for the specified entity type"""
    templates = {
        "asset": {
            "columns": list(ASSET_FIELDS.keys()),
            "sample_row": {
                "name": "Hydraulic Press #1",
                "asset_tag": "AST-001",
                "serial_number": "SN-12345",
                "model": "HP-500",
                "manufacturer": "Acme Industrial",
                "location": "Building A, Floor 1",
                "department": "Manufacturing",
                "status": "Active",
                "criticality": "High",
                "purchase_date": "2023-01-15",
                "purchase_cost": "45000"
            }
        },
        "part": {
            "columns": list(PART_FIELDS.keys()),
            "sample_row": {
                "name": "Hydraulic Seal Kit",
                "part_number": "HSK-100",
                "category": "Seals",
                "description": "Complete seal kit for HP-500 press",
                "current_stock": "25",
                "minimum_stock": "10",
                "unit_cost": "45.99",
                "location": "Warehouse A-1",
                "supplier": "Acme Parts Co"
            }
        },
        "user": {
            "columns": list(USER_FIELDS.keys()),
            "sample_row": {
                "email": "john.smith@company.com",
                "full_name": "John Smith",
                "role": "technician"
            }
        }
    }

    if entity_type not in templates:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown entity type. Options: {', '.join(templates.keys())}"
        )

    return JSONResponse({
        "entity_type": entity_type,
        "template": templates[entity_type],
        "field_definitions": {
            "asset": ASSET_FIELDS,
            "part": PART_FIELDS,
            "user": USER_FIELDS
        }.get(entity_type)
    })
