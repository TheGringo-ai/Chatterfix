"""
Logistics & Safety Router
AI-powered pallet inspection and warehouse safety analysis

The "Go/No-Go Gauge" for every pallet - before a driver touches a load,
the app confirms it's safe.
"""

import json
import logging
import os
import tempfile
import time
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.models.logistics import (
    HazardType,
    InspectionResult,
    SafetyIncident,
    SafetyStatus,
)
from app.auth import get_optional_current_user
from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/logistics", tags=["Logistics & Safety"])

# Initialize Gemini service
gemini_service = GeminiService()

# The "Expert" System Prompt for warehouse safety inspection
SAFETY_INSPECTOR_PROMPT = """You are an expert Warehouse Safety Officer with 20 years of experience in OSHA compliance and logistics safety.

Analyze this image of a pallet load, warehouse aisle, or storage area. Check STRICTLY for the following hazards:

1. **Leaning or unstable stacks** - Any visible tilt > 3 degrees is a DANGER
2. **Torn or loose shrink wrap** - Exposed product or loose wrap is a WARNING
3. **Broken or splintered pallet wood** - Cracked boards or missing slats is a DANGER
4. **Liquid leaks on floor** - Any puddles or wet spots is a DANGER (slip hazard)
5. **Obstructed aisles** - Items blocking forklift path is a WARNING
6. **Overloaded pallets** - Product stacked too high or beyond pallet edges is a DANGER
7. **Unsecured loads** - No strapping/wrap on heavy items is a DANGER
8. **Improper stacking** - Heavy items on top of light items is a WARNING

RESPOND ONLY WITH VALID JSON in this exact format:
{
    "status": "SAFE" | "WARNING" | "DANGER",
    "hazards": ["hazard_type_1", "hazard_type_2"],
    "confidence": 0.0 to 1.0,
    "description": "One sentence technical observation",
    "action": "Direct command to the driver (imperative voice)"
}

Hazard types must be one of: leaning_stack, torn_wrap, damaged_pallet, leaking_fluid, obstructed_aisle, overloaded, unsecured_load, improper_stacking, none

If the image is unclear or not a warehouse/logistics scene, set status to WARNING with description explaining why.

BE STRICT. When in doubt, err on the side of caution. A false positive is better than a missed hazard."""


@router.post("/inspect-load", response_model=InspectionResult)
async def inspect_pallet_load(
    file: UploadFile = File(..., description="Photo of the pallet/load to inspect"),
    location_aisle: Optional[str] = Form(None, description="Aisle or location identifier"),
    notes: Optional[str] = Form(None, description="Additional context from driver"),
    current_user = Depends(get_optional_current_user),
):
    """
    Analyzes a photo of a pallet/load for safety hazards before moving.

    This is the "Go/No-Go Gauge" for warehouse operations:
    - SAFE: Green light, proceed with transport
    - WARNING: Proceed with caution, consider re-wrapping
    - DANGER: STOP. Do not move until issue is resolved.

    Returns structured safety assessment with recommended action.
    """
    start_time = time.time()

    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image (JPEG, PNG, etc.)")

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            # Analyze image with Gemini Vision
            user_id = current_user.uid if current_user else None
            raw_response = await gemini_service.analyze_image(
                image_path=tmp_path,
                prompt=SAFETY_INSPECTOR_PROMPT,
                user_id=user_id
            )

            # Parse the AI response
            result = _parse_safety_response(raw_response, location_aisle)

            # Log processing time
            processing_time = time.time() - start_time
            logger.info(f"Safety inspection completed in {processing_time:.2f}s - Status: {result.status}")

            # Log near-misses and hazards for ROI tracking
            if result.status in [SafetyStatus.WARNING, SafetyStatus.DANGER]:
                await _log_safety_incident(result, user_id, location_aisle, notes)

            return result

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Vision analysis failed: {str(e)}")
        # Return a safe fallback that requires manual inspection
        return InspectionResult(
            status=SafetyStatus.WARNING,
            hazards_detected=[],
            confidence_score=0.0,
            description=f"Automated inspection failed: {str(e)}. Manual inspection required.",
            recommended_action="STOP. Perform manual safety check before moving this load.",
            location_aisle=location_aisle,
            inspector_id=current_user.uid if current_user else None
        )


def _parse_safety_response(raw_response: str, location_aisle: Optional[str] = None) -> InspectionResult:
    """Parse AI response into structured InspectionResult"""
    try:
        # Try to extract JSON from response
        # Handle cases where AI wraps JSON in markdown code blocks
        json_str = raw_response
        if "```json" in raw_response:
            json_str = raw_response.split("```json")[1].split("```")[0]
        elif "```" in raw_response:
            json_str = raw_response.split("```")[1].split("```")[0]

        data = json.loads(json_str.strip())

        # Map status string to enum
        status_map = {
            "SAFE": SafetyStatus.SAFE,
            "WARNING": SafetyStatus.WARNING,
            "DANGER": SafetyStatus.DANGER,
        }
        status = status_map.get(data.get("status", "WARNING").upper(), SafetyStatus.WARNING)

        # Map hazard strings to enum
        hazard_map = {
            "leaning_stack": HazardType.LEANING_STACK,
            "torn_wrap": HazardType.TORN_WRAP,
            "damaged_pallet": HazardType.DAMAGED_PALLET,
            "leaking_fluid": HazardType.LEAKING_FLUID,
            "obstructed_aisle": HazardType.OBSTRUCTED_AISLE,
            "overloaded": HazardType.OVERLOADED,
            "unsecured_load": HazardType.UNSECURED_LOAD,
            "improper_stacking": HazardType.IMPROPER_STACKING,
            "none": HazardType.NONE,
        }
        hazards = [
            hazard_map.get(h.lower(), HazardType.NONE)
            for h in data.get("hazards", [])
            if h.lower() in hazard_map
        ]

        return InspectionResult(
            status=status,
            hazards_detected=hazards if hazards else [],
            confidence_score=min(1.0, max(0.0, float(data.get("confidence", 0.8)))),
            description=data.get("description", "Analysis complete"),
            recommended_action=data.get("action", "Proceed with caution"),
            location_aisle=location_aisle
        )

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning(f"Failed to parse AI response: {e}. Raw: {raw_response[:200]}")
        # Fallback: treat unparseable response as requiring manual check
        return InspectionResult(
            status=SafetyStatus.WARNING,
            hazards_detected=[],
            confidence_score=0.5,
            description="AI response unclear. Manual verification recommended.",
            recommended_action="Perform visual inspection before moving.",
            location_aisle=location_aisle
        )


async def _log_safety_incident(
    result: InspectionResult,
    user_id: Optional[str],
    location: Optional[str],
    notes: Optional[str]
):
    """Log safety incident to Firestore for tracking and ROI reporting"""
    try:
        from app.core.firestore_db import FirestoreManager

        db = FirestoreManager()

        incident = SafetyIncident(
            organization_id="demo_org",  # TODO: Get from user context
            inspection_result=result,
            notes=notes
        )

        await db.create_document(
            collection="safety_incidents",
            data=incident.model_dump()
        )

        logger.info(f"Safety incident logged: {result.status} - {result.hazards_detected}")

    except Exception as e:
        # Don't fail the main request if logging fails
        logger.error(f"Failed to log safety incident: {e}")


@router.get("/incidents")
async def get_safety_incidents(
    status: Optional[str] = None,
    limit: int = 50,
    current_user = Depends(get_optional_current_user),
):
    """
    Get recent safety incidents for reporting and ROI tracking.

    This shows the value of the system - every WARNING and DANGER
    is a potential accident that was prevented.
    """
    try:
        from app.core.firestore_db import FirestoreManager

        db = FirestoreManager()

        # Query incidents
        incidents = await db.query_documents(
            collection="safety_incidents",
            filters=[],  # TODO: Add org filter
            order_by="created_at",
            order_direction="DESCENDING",
            limit=limit
        )

        # Filter by status if specified
        if status:
            incidents = [i for i in incidents if i.get("inspection_result", {}).get("status") == status]

        return {
            "total": len(incidents),
            "incidents": incidents,
            "summary": {
                "danger_count": len([i for i in incidents if i.get("inspection_result", {}).get("status") == "DANGER"]),
                "warning_count": len([i for i in incidents if i.get("inspection_result", {}).get("status") == "WARNING"]),
            }
        }

    except Exception as e:
        logger.error(f"Failed to get safety incidents: {e}")
        return {"total": 0, "incidents": [], "summary": {"danger_count": 0, "warning_count": 0}}


@router.get("/stats")
async def get_safety_stats(
    current_user = Depends(get_optional_current_user),
):
    """
    Get safety statistics for the ROI dashboard.

    Shows: "We prevented X potential accidents this month"
    """
    try:
        from app.core.firestore_db import FirestoreManager

        db = FirestoreManager()

        # Get all incidents (in production, filter by date range and org)
        incidents = await db.query_documents(
            collection="safety_incidents",
            filters=[],
            limit=1000
        )

        danger_count = len([i for i in incidents if i.get("inspection_result", {}).get("status") == "DANGER"])
        warning_count = len([i for i in incidents if i.get("inspection_result", {}).get("status") == "WARNING"])
        total_inspections = len(incidents)

        # Calculate "prevented accidents" metric
        # Industry average: 1 in 20 DANGER situations results in injury if not caught
        prevented_injuries_estimate = danger_count // 20

        return {
            "total_inspections": total_inspections,
            "danger_interventions": danger_count,
            "warning_interventions": warning_count,
            "estimated_injuries_prevented": prevented_injuries_estimate,
            "safety_score": round(100 - (danger_count / max(1, total_inspections) * 100), 1),
            "message": f"Your team has prevented an estimated {prevented_injuries_estimate} potential injuries through proactive safety inspections."
        }

    except Exception as e:
        logger.error(f"Failed to get safety stats: {e}")
        return {
            "total_inspections": 0,
            "danger_interventions": 0,
            "warning_interventions": 0,
            "estimated_injuries_prevented": 0,
            "safety_score": 100,
            "message": "No inspection data available yet."
        }
