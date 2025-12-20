"""
QualityFix Router
The "Digital Inspector" - AI-powered quality management and CAPA

Module C of the Gringo Industrial OS:
- Visual QA (AI comparison to golden sample)
- Non-Conformance tracking ("The Snitch")
- CAPA (Corrective/Preventive Actions)
- Voice-activated rejects ("Reject, scratch on surface")
"""

import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.auth import get_optional_current_user
from app.models.quality import (
    CAPA,
    CAPAStatus,
    ChecklistItem,
    DefectSeverity,
    Inspection,
    InspectionResult,
    InspectionTemplate,
    NonConformance,
    QualityDashboard,
    VisualQAResult,
)
from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/quality", tags=["QualityFix"])

gemini_service = GeminiService()


# ============ AI Prompts ============

VISUAL_QA_PROMPT = """You are an expert Quality Control Inspector with 20 years of experience in visual inspection.

You are comparing two images:
1. GOLDEN SAMPLE (Reference): The perfect, approved part
2. ACTUAL PART (Test): The part being inspected

Analyze the ACTUAL PART and compare it to the GOLDEN SAMPLE. Look for ANY deviations:

DEFECT TYPES TO CHECK:
1. **Surface Defects**: Scratches, dents, pitting, discoloration
2. **Dimensional Issues**: Size variations, warping, bending
3. **Missing Features**: Holes not drilled, threads missing
4. **Contamination**: Foreign material, stains, residue
5. **Assembly Errors**: Wrong orientation, missing components
6. **Finish Issues**: Paint defects, coating problems, rust

For each defect found, specify:
- TYPE: What kind of defect
- LOCATION: Where on the part (use quadrants: upper-left, center, lower-right, etc.)
- SEVERITY: critical (safety/function), major (rework needed), minor (cosmetic)

RESPOND ONLY WITH VALID JSON:
{
    "passed": true/false,
    "confidence": 0.0 to 1.0,
    "similarity_score": 0.0 to 1.0,
    "defects": [
        {
            "type": "scratch",
            "location": "upper-left quadrant",
            "severity": "major",
            "description": "3cm scratch visible on surface"
        }
    ],
    "summary": "One sentence summary",
    "action": "Recommended disposition: pass, rework, scrap, or hold for review"
}

BE STRICT. Quality is non-negotiable. When in doubt, fail the part."""

NC_CLASSIFIER_PROMPT = """You are a Quality Engineer analyzing a defect report.

Defect Description:
{description}

Voice Transcript (if available):
{voice_transcript}

Classify this non-conformance:

1. DEFECT TYPE: scratch, dent, dimension, missing_part, contamination, finish, assembly, other
2. SEVERITY: critical (safety/regulatory), major (functional), minor (cosmetic), observation
3. DISPOSITION RECOMMENDATION: scrap, rework, use_as_is, return_to_vendor, hold_for_review
4. CAPA REQUIRED: true if this is a recurring issue or critical defect

RESPOND WITH JSON:
{
    "defect_type": "...",
    "severity": "critical|major|minor|observation",
    "disposition": "scrap|rework|use_as_is|return_to_vendor|hold_for_review",
    "capa_required": true/false,
    "summary": "Technical summary for NC record"
}"""


# ============ In-Memory Store ============

_templates: Dict[str, InspectionTemplate] = {}
_inspections: Dict[str, Inspection] = {}
_ncs: Dict[str, NonConformance] = {}
_capas: Dict[str, CAPA] = {}


def _init_demo_templates():
    """Initialize demo inspection templates"""
    if _templates:
        return

    templates = [
        InspectionTemplate(
            id="template_final_assembly",
            organization_id="demo_org",
            name="Final Assembly Inspection",
            description="Standard checklist for finished assemblies",
            category="final",
            items=[
                ChecklistItem(id="1", question="All fasteners torqued to spec?", response_type="pass_fail"),
                ChecklistItem(id="2", question="Surface finish acceptable (no scratches)?", response_type="pass_fail"),
                ChecklistItem(id="3", question="Dimension A within tolerance?", response_type="numeric", numeric_min=99.5, numeric_max=100.5),
                ChecklistItem(id="4", question="Label applied correctly?", response_type="pass_fail"),
                ChecklistItem(id="5", question="Packaging complete?", response_type="pass_fail"),
            ]
        ),
        InspectionTemplate(
            id="template_incoming",
            organization_id="demo_org",
            name="Incoming Material Inspection",
            description="Check raw materials from vendors",
            category="incoming",
            items=[
                ChecklistItem(id="1", question="Material matches PO spec?", response_type="pass_fail"),
                ChecklistItem(id="2", question="Quantity matches packing slip?", response_type="pass_fail"),
                ChecklistItem(id="3", question="No visible damage?", response_type="pass_fail"),
                ChecklistItem(id="4", question="Certificate of Conformance received?", response_type="pass_fail"),
            ]
        ),
        InspectionTemplate(
            id="template_in_process",
            organization_id="demo_org",
            name="In-Process Check",
            description="Mid-production quality gate",
            category="in_process",
            items=[
                ChecklistItem(id="1", question="Dimension check (sample 5 parts)", response_type="pass_fail"),
                ChecklistItem(id="2", question="Visual inspection passed?", response_type="pass_fail"),
                ChecklistItem(id="3", question="Machine settings verified?", response_type="pass_fail"),
            ]
        ),
    ]

    for t in templates:
        _templates[t.id] = t


_init_demo_templates()


# ============ Visual QA (The AI Inspector) ============

@router.post("/inspect-part", response_model=VisualQAResult)
async def visual_qa_inspection(
    actual_image: UploadFile = File(..., description="Photo of the actual part being inspected"),
    golden_sample_url: Optional[str] = Form(None, description="URL to golden sample image"),
    product_sku: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    current_user=Depends(get_optional_current_user),
):
    """
    The "AI Inspector" - Compare actual part to golden sample.

    Uses Gemini Vision to detect defects and deviations from the approved reference.
    Circles defects and provides disposition recommendation.
    """
    if not actual_image.content_type or not actual_image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        # Save temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            content = await actual_image.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            # Analyze with Gemini Vision
            user_id = current_user.uid if current_user else None

            # Build prompt with context
            prompt = VISUAL_QA_PROMPT
            if product_sku:
                prompt += f"\n\nProduct SKU: {product_sku}"
            if notes:
                prompt += f"\n\nInspector notes: {notes}"

            raw_response = await gemini_service.analyze_image(
                image_path=tmp_path,
                prompt=prompt,
                user_id=user_id
            )

            result = _parse_visual_qa_response(raw_response)

            # Log result
            logger.info(f"Visual QA: {'PASS' if result.passed else 'FAIL'} - {result.defect_count} defects")

            return result

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Visual QA failed: {e}")
        return VisualQAResult(
            passed=False,
            confidence=0.0,
            defects_found=[],
            defect_count=0,
            similarity_score=0.0,
            analysis_summary=f"Inspection failed: {str(e)}",
            recommended_action="Manual inspection required."
        )


def _parse_visual_qa_response(raw_response: str) -> VisualQAResult:
    """Parse AI response into VisualQAResult"""
    try:
        json_str = raw_response
        if "```json" in raw_response:
            json_str = raw_response.split("```json")[1].split("```")[0]
        elif "```" in raw_response:
            json_str = raw_response.split("```")[1].split("```")[0]

        data = json.loads(json_str.strip())

        return VisualQAResult(
            passed=data.get("passed", False),
            confidence=min(1.0, max(0.0, data.get("confidence", 0.8))),
            defects_found=data.get("defects", []),
            defect_count=len(data.get("defects", [])),
            similarity_score=min(1.0, max(0.0, data.get("similarity_score", 0.5))),
            analysis_summary=data.get("summary", "Analysis complete"),
            recommended_action=data.get("action", "Review results"),
        )

    except Exception as e:
        logger.warning(f"Failed to parse Visual QA response: {e}")
        return VisualQAResult(
            passed=False,
            confidence=0.0,
            defects_found=[],
            defect_count=0,
            similarity_score=0.0,
            analysis_summary="Failed to parse AI response. Manual inspection required.",
            recommended_action="Perform manual quality inspection."
        )


# ============ Non-Conformance (The Snitch) ============

@router.post("/nc", response_model=NonConformance)
async def create_non_conformance(
    background_tasks: BackgroundTasks,
    description: str = Form(...),
    voice_transcript: Optional[str] = Form(None, description="Voice command like 'Reject, scratch on surface'"),
    severity: Optional[str] = Form(None),
    defect_type: Optional[str] = Form(None),
    product_sku: Optional[str] = Form(None),
    lot_number: Optional[str] = Form(None),
    quantity: int = Form(default=1),
    image: Optional[UploadFile] = File(None),
    current_user=Depends(get_optional_current_user),
):
    """
    The "Snitch" - Report a non-conformance.

    Supports voice commands: "Reject, scratch on surface" creates NC automatically.
    AI classifies severity and recommends disposition.
    """
    nc_id = f"nc_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    # Use AI to classify if not provided
    if not severity or not defect_type:
        classification = await _classify_nc(description, voice_transcript)
        severity = severity or classification.get("severity", "major")
        defect_type = defect_type or classification.get("defect_type", "other")
        capa_required = classification.get("capa_required", False)
    else:
        capa_required = severity == "critical"

    # Handle image upload
    image_url = None
    if image and image.content_type and image.content_type.startswith("image/"):
        image_url = f"pending_upload_{nc_id}"

    nc = NonConformance(
        id=nc_id,
        organization_id=current_user.organization_id if current_user else "demo_org",
        defect_type=defect_type,
        description=description,
        severity=DefectSeverity(severity),
        voice_transcript=voice_transcript,
        product_sku=product_sku,
        lot_number=lot_number,
        quantity_affected=quantity,
        image_url=image_url,
        capa_required=capa_required,
        reported_by=current_user.uid if current_user else None,
    )

    _ncs[nc_id] = nc

    # Save to Firestore in background
    background_tasks.add_task(_save_nc, nc)

    # Auto-create CAPA if required
    if capa_required:
        background_tasks.add_task(_auto_create_capa, nc)

    logger.info(f"NC created: {nc_id} - {defect_type} - {severity}")

    return nc


async def _classify_nc(description: str, voice_transcript: Optional[str]) -> dict:
    """Use AI to classify non-conformance"""
    try:
        prompt = NC_CLASSIFIER_PROMPT.format(
            description=description,
            voice_transcript=voice_transcript or "Not provided"
        )

        response = await gemini_service.chat(
            message=prompt,
            context="quality_nc_classification",
            user_id=None
        )

        json_str = response
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0]

        return json.loads(json_str.strip())

    except Exception as e:
        logger.warning(f"NC classification failed: {e}")
        return {
            "defect_type": "other",
            "severity": "major",
            "disposition": "hold_for_review",
            "capa_required": False,
            "summary": description[:100]
        }


async def _save_nc(nc: NonConformance):
    """Save NC to Firestore"""
    try:
        from app.core.firestore_db import FirestoreManager
        db = FirestoreManager()
        await db.create_document("non_conformances", nc.model_dump())
    except Exception as e:
        logger.error(f"Failed to save NC: {e}")


async def _auto_create_capa(nc: NonConformance):
    """Auto-create CAPA for critical defects"""
    capa = CAPA(
        id=f"capa_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        organization_id=nc.organization_id,
        nc_ids=[nc.id],
        problem_statement=f"Critical defect detected: {nc.description}",
        status=CAPAStatus.OPEN,
        priority="high" if nc.severity == DefectSeverity.CRITICAL else "medium",
    )

    _capas[capa.id] = capa
    nc.capa_id = capa.id

    logger.info(f"Auto-created CAPA {capa.id} for NC {nc.id}")


@router.get("/nc", response_model=List[NonConformance])
async def list_non_conformances(
    severity: Optional[str] = None,
    disposition: Optional[str] = None,
    current_user=Depends(get_optional_current_user),
):
    """List non-conformances"""
    ncs = list(_ncs.values())

    if severity:
        ncs = [n for n in ncs if n.severity.value == severity]
    if disposition:
        ncs = [n for n in ncs if n.disposition == disposition]

    return sorted(ncs, key=lambda n: n.reported_at, reverse=True)


@router.post("/nc/{nc_id}/disposition")
async def update_nc_disposition(
    nc_id: str,
    disposition: str,
    notes: Optional[str] = None,
    current_user=Depends(get_optional_current_user),
):
    """Update NC disposition (scrap, rework, use_as_is, etc.)"""
    if nc_id not in _ncs:
        raise HTTPException(status_code=404, detail="NC not found")

    nc = _ncs[nc_id]
    nc.disposition = disposition
    nc.disposition_notes = notes
    nc.disposition_by = current_user.uid if current_user else "system"
    nc.disposition_at = datetime.now(timezone.utc).isoformat()

    return {"status": "updated", "disposition": disposition}


# ============ CAPA (Corrective/Preventive Action) ============

@router.get("/capa", response_model=List[CAPA])
async def list_capas(
    status: Optional[str] = None,
    current_user=Depends(get_optional_current_user),
):
    """List CAPAs"""
    capas = list(_capas.values())

    if status:
        capas = [c for c in capas if c.status.value == status]

    return sorted(capas, key=lambda c: c.created_at, reverse=True)


@router.get("/capa/{capa_id}", response_model=CAPA)
async def get_capa(
    capa_id: str,
    current_user=Depends(get_optional_current_user),
):
    """Get CAPA details"""
    if capa_id not in _capas:
        raise HTTPException(status_code=404, detail="CAPA not found")

    return _capas[capa_id]


@router.post("/capa/{capa_id}/update")
async def update_capa(
    capa_id: str,
    root_cause: Optional[str] = Form(None),
    corrective_action: Optional[str] = Form(None),
    preventive_action: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    current_user=Depends(get_optional_current_user),
):
    """Update CAPA progress"""
    if capa_id not in _capas:
        raise HTTPException(status_code=404, detail="CAPA not found")

    capa = _capas[capa_id]

    if root_cause:
        capa.root_cause = root_cause
    if corrective_action:
        capa.corrective_action_plan = corrective_action
    if preventive_action:
        capa.preventive_action_plan = preventive_action
    if status:
        capa.status = CAPAStatus(status)
        if status == "closed":
            capa.closed_at = datetime.now(timezone.utc).isoformat()
            capa.closed_by = current_user.uid if current_user else "system"

    return {"status": "updated", "capa_status": capa.status.value}


# ============ Inspection Templates ============

@router.get("/templates", response_model=List[InspectionTemplate])
async def list_templates(
    category: Optional[str] = None,
    current_user=Depends(get_optional_current_user),
):
    """List inspection templates (the Template Library)"""
    _init_demo_templates()
    templates = list(_templates.values())

    if category:
        templates = [t for t in templates if t.category == category]

    return templates


# ============ Dashboard ============

@router.get("/dashboard", response_model=QualityDashboard)
async def get_quality_dashboard(
    current_user=Depends(get_optional_current_user),
):
    """Quality metrics dashboard"""
    inspections = list(_inspections.values())
    ncs = list(_ncs.values())
    capas = list(_capas.values())

    passed = len([i for i in inspections if i.result == InspectionResult.PASS])
    failed = len([i for i in inspections if i.result == InspectionResult.FAIL])
    total = len(inspections) or 1

    open_ncs = len([n for n in ncs if n.disposition == "pending"])
    open_capas = len([c for c in capas if c.status in [CAPAStatus.OPEN, CAPAStatus.IN_PROGRESS]])

    # Count by severity
    severity_counts = {}
    for nc in ncs:
        sev = nc.severity.value
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    # Top defect types
    defect_counts = {}
    for nc in ncs:
        dt = nc.defect_type
        defect_counts[dt] = defect_counts.get(dt, 0) + 1

    top_defects = sorted(
        [{"type": k, "count": v} for k, v in defect_counts.items()],
        key=lambda x: x["count"],
        reverse=True
    )[:5]

    return QualityDashboard(
        inspections_today=len(inspections),
        inspections_passed=passed,
        inspections_failed=failed,
        first_pass_yield=round((passed / total) * 100, 1),
        open_ncs=open_ncs,
        ncs_today=len(ncs),
        ncs_by_severity=severity_counts,
        open_capas=open_capas,
        overdue_capas=0,
        yield_trend="stable",
        top_defect_types=top_defects,
    )
