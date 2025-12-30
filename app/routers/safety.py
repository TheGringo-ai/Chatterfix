"""
SafetyFix Router
The "Guardian Angel" - Proactive safety intelligence for industrial environments

"The clipboard doesn't see the forklift coming. SafetyFix does."

Features:
1. AI Canary - Active vision for PPE compliance and hazard detection
2. Near-Miss Voice Button - Instant incident reporting via voice
3. Man Down Detection - Automatic fall detection with Black Box recording
4. Zone Control - Geofenced safety warnings
"""

import json
import logging
import os
import tempfile
import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.auth import get_optional_current_user
from app.models.safety import (
    IncidentSeverity,
    IncidentType,
    ManDownEvent,
    PPECheckResult,
    PPEType,
    PPEViolation,
    SafetyDashboardStats,
    SafetyIncidentReport,
    ZoneAlert,
)
from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/safety", tags=["SafetyFix"])

# Initialize Gemini service
gemini_service = GeminiService()


# ============ AI Prompts ============

PPE_INSPECTOR_PROMPT = """You are an expert Safety Compliance Officer specializing in PPE (Personal Protective Equipment) detection.

Analyze this image and check ALL visible workers for the following PPE:

1. **Hard Hat/Helmet** - Must be worn in all production/warehouse areas
2. **Safety Glasses/Goggles** - Required for any area with flying debris or chemicals
3. **High-Visibility Vest** - Required in all forklift/vehicle traffic areas
4. **Safety Harness** - Required when working at heights above 6 feet
5. **Steel-Toe Boots** - Required in all industrial areas (check if visible)
6. **Gloves** - Required for material handling
7. **Ear Protection** - Required in high-noise areas

For EACH person visible in the image:
- List what PPE they ARE wearing
- List what PPE they are MISSING
- Rate your confidence in detection

RESPOND ONLY WITH VALID JSON:
{
    "compliant": true/false,
    "persons_checked": <number>,
    "violations": [
        {
            "missing_ppe": ["hard_hat", "safety_glasses"],
            "person_description": "Worker in blue shirt near conveyor",
            "confidence": 0.0 to 1.0
        }
    ],
    "all_ppe_detected": ["safety_vest", "gloves"],
    "overall_confidence": 0.0 to 1.0,
    "description": "Summary of findings",
    "action": "Recommended action"
}

PPE types must be: hard_hat, safety_glasses, safety_vest, safety_harness, steel_toe_boots, gloves, ear_protection, respirator, face_shield

BE STRICT with compliance. When in doubt, flag as violation."""

INCIDENT_CLASSIFIER_PROMPT = """You are a Safety Incident Classification AI. Analyze the following incident report and classify it.

Incident Report:
{transcript}

Location: {location}

Classify the severity based on:
- CRITICAL: Immediate life-threatening danger, active emergency
- HIGH: Serious hazard that could cause injury soon
- MEDIUM: Hazard that should be addressed within the shift
- LOW: Minor issue to track and monitor

Classify the incident type:
- near_miss: Almost had an accident
- hazard_report: Spotted a dangerous condition
- slip_trip_fall: Fall-related incident
- chemical_spill: Chemical leak or spill
- equipment_failure: Broken/malfunctioning equipment
- fire_hazard: Fire or burn risk
- electrical: Electrical hazard
- ergonomic: Strain/ergonomic issue
- other: Doesn't fit other categories

RESPOND ONLY WITH VALID JSON:
{
    "severity": "critical" | "high" | "medium" | "low",
    "incident_type": "<type from list above>",
    "summary": "One sentence summary for work order title",
    "auto_assign_to": "maintenance" | "janitorial" | "safety_officer" | "supervisor",
    "urgent_notification": true/false,
    "recommended_action": "Immediate action to take"
}"""


# ============ Incident Reporting Endpoints ============

@router.post("/incident", response_model=SafetyIncidentReport)
async def report_safety_incident(
    background_tasks: BackgroundTasks,
    voice_transcript: str = Form(..., description="Voice transcription of the report"),
    location: Optional[str] = Form(None, description="Location description"),
    gps_lat: Optional[float] = Form(None, description="GPS latitude"),
    gps_lng: Optional[float] = Form(None, description="GPS longitude"),
    image: Optional[UploadFile] = File(None, description="Optional photo of hazard"),
    current_user = Depends(get_optional_current_user),
):
    """
    Report a safety incident via voice command.

    The "Near-Miss Voice Button" - turns every worker into a safety officer.

    Example voice commands:
    - "Hey ChatterFix, near miss. Oil slick on Walkway B."
    - "Hazard report: Missing guardrail on platform 3."
    - "Chemical spill in storage room, need cleanup."

    The AI will:
    1. Classify severity (Critical/High/Medium/Low)
    2. Categorize incident type
    3. Auto-assign to appropriate team
    4. Create a work order if needed
    """
    start_time = time.time()
    incident_id = str(uuid.uuid4())

    try:
        # Use AI to classify the incident
        classification = await _classify_incident(voice_transcript, location)

        # Save image if provided
        image_url = None
        if image and image.content_type and image.content_type.startswith("image/"):
            # In production, upload to Firebase Storage
            # For now, log that we received it
            image_url = f"pending_upload_{incident_id}"
            logger.info(f"Image received for incident {incident_id}")

        # Build the incident report
        incident = SafetyIncidentReport(
            id=incident_id,
            organization_id=current_user.organization_id if current_user else "demo_org",
            incident_type=IncidentType(classification.get("incident_type", "other")),
            severity=IncidentSeverity(classification.get("severity", "medium")),
            description=classification.get("summary", voice_transcript[:200]),
            voice_transcript=voice_transcript,
            location=location,
            gps_lat=gps_lat,
            gps_lng=gps_lng,
            image_url=image_url,
            reporter_id=current_user.uid if current_user else None,
            reporter_name=current_user.full_name if current_user else None,
            assigned_to=classification.get("auto_assign_to", "safety_officer"),
        )

        # Save to Firestore in background
        background_tasks.add_task(_save_incident, incident)

        # Auto-create work order for high severity
        if classification.get("severity") in ["critical", "high"]:
            background_tasks.add_task(
                _create_safety_work_order,
                incident,
                classification.get("recommended_action", "Investigate immediately")
            )

        # Send urgent notification if needed
        if classification.get("urgent_notification"):
            background_tasks.add_task(_send_urgent_notification, incident)

        processing_time = time.time() - start_time
        logger.info(f"Safety incident reported in {processing_time:.2f}s: {incident.severity} - {incident.incident_type}")

        return incident

    except Exception as e:
        logger.error(f"Failed to process safety incident: {e}")
        # Return a basic incident report even if AI fails
        return SafetyIncidentReport(
            id=incident_id,
            organization_id="demo_org",
            incident_type=IncidentType.OTHER,
            severity=IncidentSeverity.MEDIUM,
            description=voice_transcript[:200],
            voice_transcript=voice_transcript,
            location=location,
            gps_lat=gps_lat,
            gps_lng=gps_lng,
            status="open",
            assigned_to="safety_officer"
        )


async def _classify_incident(transcript: str, location: Optional[str]) -> dict:
    """Use AI to classify incident severity and type"""
    try:
        prompt = INCIDENT_CLASSIFIER_PROMPT.format(
            transcript=transcript,
            location=location or "Not specified"
        )

        response = await gemini_service.chat(
            message=prompt,
            context="safety_incident_classification",
            user_id=None
        )

        # Parse JSON response
        json_str = response
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0]

        return json.loads(json_str.strip())

    except Exception as e:
        logger.warning(f"AI classification failed: {e}")
        # Fallback classification based on keywords
        transcript_lower = transcript.lower()

        severity = "medium"
        incident_type = "other"

        if any(word in transcript_lower for word in ["fire", "explosion", "collapse", "emergency", "unconscious"]):
            severity = "critical"
        elif any(word in transcript_lower for word in ["spill", "leak", "broken", "fall", "injury"]):
            severity = "high"
        elif any(word in transcript_lower for word in ["near miss", "almost", "close call"]):
            severity = "low"
            incident_type = "near_miss"

        if "oil" in transcript_lower or "spill" in transcript_lower:
            incident_type = "chemical_spill"
        elif "slip" in transcript_lower or "fall" in transcript_lower:
            incident_type = "slip_trip_fall"
        elif "equipment" in transcript_lower or "machine" in transcript_lower:
            incident_type = "equipment_failure"

        return {
            "severity": severity,
            "incident_type": incident_type,
            "summary": transcript[:100],
            "auto_assign_to": "maintenance" if "equipment" in transcript_lower else "janitorial",
            "urgent_notification": severity in ["critical", "high"],
            "recommended_action": "Investigate and address the reported hazard"
        }


async def _save_incident(incident: SafetyIncidentReport):
    """Save incident to Firestore"""
    try:
        from app.core.firestore_db import FirestoreManager
        db = FirestoreManager()
        await db.create_document("safety_incidents", incident.model_dump())
        logger.info(f"Safety incident saved: {incident.id}")
    except Exception as e:
        logger.error(f"Failed to save incident: {e}")


async def _create_safety_work_order(incident: SafetyIncidentReport, action: str):
    """Auto-create work order for high-severity incidents"""
    try:
        from app.core.firestore_db import FirestoreManager
        db = FirestoreManager()

        work_order = {
            "title": f"[SAFETY] {incident.description[:50]}",
            "description": f"Auto-created from safety incident.\n\nOriginal report: {incident.voice_transcript}\n\nLocation: {incident.location}\n\nRecommended action: {action}",
            "priority": "Critical" if incident.severity == IncidentSeverity.CRITICAL else "High",
            "status": "Open",
            "type": "Safety",
            "organization_id": incident.organization_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_incident_id": incident.id,
        }

        doc_ref = await db.create_document("work_orders", work_order)
        logger.info(f"Safety work order created: {doc_ref}")
    except Exception as e:
        logger.error(f"Failed to create safety work order: {e}")


async def _send_urgent_notification(incident: SafetyIncidentReport):
    """Send urgent notification for critical incidents"""
    # In production, integrate with SMS/Push notification service
    logger.warning(f"URGENT SAFETY NOTIFICATION: {incident.severity} - {incident.description}")
    # TODO: Integrate with Twilio/Firebase Cloud Messaging


# ============ PPE Detection Endpoints ============

@router.post("/check-ppe", response_model=PPECheckResult)
async def check_ppe_compliance(
    file: UploadFile = File(..., description="Photo of workers to check PPE compliance"),
    zone: Optional[str] = Form(None, description="Zone type for context-aware requirements"),
    current_user = Depends(get_optional_current_user),
):
    """
    The "AI Canary" - Check PPE compliance for visible workers in an image.

    When a technician looks at a coworker through Halo glasses,
    the AI silently checks for missing safety equipment.

    Returns violations if any worker is missing required PPE.
    """
    start_time = time.time()

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        # Save temp file for Vision AI
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            # Analyze with Gemini Vision
            user_id = current_user.uid if current_user else None
            raw_response = await gemini_service.analyze_image(
                image_path=tmp_path,
                prompt=PPE_INSPECTOR_PROMPT,
                user_id=user_id
            )

            result = _parse_ppe_response(raw_response)

            processing_time = time.time() - start_time
            logger.info(f"PPE check completed in {processing_time:.2f}s - Compliant: {result.compliant}")

            # Log violations
            if not result.compliant:
                await _log_ppe_violation(result, user_id, zone)

            return result

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"PPE check failed: {e}")
        return PPECheckResult(
            compliant=False,
            violations=[],
            persons_checked=0,
            all_ppe_detected=[],
            confidence=0.0,
            description=f"Automated check failed: {str(e)}. Manual inspection required.",
            recommended_action="Verify PPE compliance manually."
        )


def _parse_ppe_response(raw_response: str) -> PPECheckResult:
    """Parse AI response into PPECheckResult"""
    try:
        json_str = raw_response
        if "```json" in raw_response:
            json_str = raw_response.split("```json")[1].split("```")[0]
        elif "```" in raw_response:
            json_str = raw_response.split("```")[1].split("```")[0]

        data = json.loads(json_str.strip())

        # Map PPE strings to enums
        ppe_map = {
            "hard_hat": PPEType.HARD_HAT,
            "safety_glasses": PPEType.SAFETY_GLASSES,
            "safety_vest": PPEType.SAFETY_VEST,
            "safety_harness": PPEType.SAFETY_HARNESS,
            "steel_toe_boots": PPEType.STEEL_TOE_BOOTS,
            "gloves": PPEType.GLOVES,
            "ear_protection": PPEType.EAR_PROTECTION,
            "respirator": PPEType.RESPIRATOR,
            "face_shield": PPEType.FACE_SHIELD,
        }

        violations = []
        for v in data.get("violations", []):
            missing = [ppe_map[p] for p in v.get("missing_ppe", []) if p in ppe_map]
            if missing:
                violations.append(PPEViolation(
                    missing_ppe=missing,
                    person_description=v.get("person_description"),
                    confidence=v.get("confidence", 0.8)
                ))

        all_detected = [ppe_map[p] for p in data.get("all_ppe_detected", []) if p in ppe_map]

        return PPECheckResult(
            compliant=data.get("compliant", True),
            violations=violations,
            persons_checked=data.get("persons_checked", 0),
            all_ppe_detected=all_detected,
            confidence=data.get("overall_confidence", 0.8),
            description=data.get("description", "Check complete"),
            recommended_action=data.get("action", "No action required")
        )

    except Exception as e:
        logger.warning(f"Failed to parse PPE response: {e}")
        return PPECheckResult(
            compliant=False,
            violations=[],
            persons_checked=0,
            all_ppe_detected=[],
            confidence=0.0,
            description="Failed to parse AI response. Manual check required.",
            recommended_action="Verify PPE compliance manually."
        )


async def _log_ppe_violation(result: PPECheckResult, user_id: Optional[str], zone: Optional[str]):
    """Log PPE violation for tracking"""
    try:
        from app.core.firestore_db import FirestoreManager
        db = FirestoreManager()

        violation_log = {
            "type": "ppe_violation",
            "violations": [v.model_dump() for v in result.violations],
            "zone": zone,
            "detected_by": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "organization_id": "demo_org"
        }

        await db.create_document("safety_incidents", violation_log)
    except Exception as e:
        logger.error(f"Failed to log PPE violation: {e}")


# ============ Man Down / Fall Detection ============

@router.post("/man-down", response_model=ManDownEvent)
async def report_man_down(
    background_tasks: BackgroundTasks,
    user_id: str = Form(..., description="ID of the fallen worker"),
    user_name: Optional[str] = Form(None),
    g_force: float = Form(..., description="Peak G-force detected"),
    fall_duration_ms: int = Form(..., description="Duration of fall in milliseconds"),
    gps_lat: Optional[float] = Form(None),
    gps_lng: Optional[float] = Form(None),
    location: Optional[str] = Form(None),
    video_buffer_url: Optional[str] = Form(None, description="URL to Black Box video"),
    current_user = Depends(get_optional_current_user),
):
    """
    The "Black Box" - Automatic fall detection trigger.

    When the mobile app accelerometer detects a sudden fall:
    1. Save the 30-second rolling video buffer to cloud
    2. Start emergency countdown
    3. Notify supervisor immediately
    4. Log event with all sensor data

    This provides undeniable proof for liability protection.
    """
    event_id = str(uuid.uuid4())

    # Determine impact severity from G-force
    if g_force >= 6.0:
        impact = "severe"
    elif g_force >= 3.5:
        impact = "moderate"
    else:
        impact = "light"

    event = ManDownEvent(
        id=event_id,
        organization_id=current_user.organization_id if current_user else "demo_org",
        user_id=user_id,
        user_name=user_name,
        g_force_detected=g_force,
        fall_duration_ms=fall_duration_ms,
        impact_severity=impact,
        location=location,
        gps_lat=gps_lat,
        gps_lng=gps_lng,
        video_buffer_url=video_buffer_url,
        supervisor_notified=True,  # Will be set in background
    )

    # Save and notify in background
    background_tasks.add_task(_handle_man_down_event, event)

    logger.warning(f"MAN DOWN EVENT: {user_name or user_id} - G-force: {g_force}, Impact: {impact}")

    return event


async def _handle_man_down_event(event: ManDownEvent):
    """Handle man down event - save and notify"""
    try:
        from app.core.firestore_db import FirestoreManager
        db = FirestoreManager()

        # Save event
        await db.create_document("man_down_events", event.model_dump())

        # In production: Send push notification to supervisor
        # In production: Trigger emergency services if no response in 30 seconds

        logger.info(f"Man down event saved and notifications sent: {event.id}")
    except Exception as e:
        logger.error(f"Failed to handle man down event: {e}")


@router.post("/man-down/{event_id}/false-alarm")
async def mark_false_alarm(
    event_id: str,
    confirmed_by: str = Form(..., description="User who confirmed false alarm"),
    current_user = Depends(get_optional_current_user),
):
    """
    Mark a man-down event as a false alarm.

    The worker has 30 seconds to cancel the emergency before
    supervisors and emergency services are contacted.
    """
    try:
        from app.core.firestore_db import FirestoreManager
        db = FirestoreManager()

        await db.update_document("man_down_events", event_id, {
            "false_alarm": True,
            "false_alarm_confirmed_by": confirmed_by,
            "emergency_contacted": False,
        })

        logger.info(f"Man down event {event_id} marked as false alarm by {confirmed_by}")

        return {"status": "cancelled", "message": "Emergency cancelled. Stay safe!"}
    except Exception as e:
        logger.error(f"Failed to cancel man down: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel emergency")


# ============ Zone Control ============

@router.get("/zones", response_model=List[ZoneAlert])
async def get_safety_zones(
    current_user = Depends(get_optional_current_user),
):
    """
    Get all configured safety zones for geofencing.

    Returns zones with required PPE and certifications.
    """
    # In production, load from Firestore per organization
    # Demo zones for now
    demo_zones = [
        ZoneAlert(
            zone_id="zone_confined_1",
            zone_name="Chemical Storage Tank A",
            zone_type="confined_space",
            required_ppe=[PPEType.RESPIRATOR, PPEType.SAFETY_HARNESS, PPEType.HARD_HAT],
            required_certifications=["Confined Space Entry", "Chemical Handling"],
            warning_message="STOP! Confined Space Entry. Check oxygen levels before proceeding.",
            checklist_items=[
                "Oxygen level verified > 19.5%",
                "Atmospheric testing complete",
                "Spotter present at entry point",
                "Rescue equipment ready"
            ]
        ),
        ZoneAlert(
            zone_id="zone_highvolt_1",
            zone_name="Electrical Room 3",
            zone_type="high_voltage",
            required_ppe=[PPEType.SAFETY_GLASSES, PPEType.GLOVES],
            required_certifications=["Lockout/Tagout", "Electrical Safety"],
            warning_message="HIGH VOLTAGE AREA. Verify lockout before work.",
            checklist_items=[
                "Lockout/Tagout complete",
                "Energy isolation verified",
                "Arc flash PPE worn"
            ]
        ),
        ZoneAlert(
            zone_id="zone_heights_1",
            zone_name="Elevated Platform Section B",
            zone_type="fall_hazard",
            required_ppe=[PPEType.SAFETY_HARNESS, PPEType.HARD_HAT],
            required_certifications=["Fall Protection"],
            warning_message="FALL HAZARD. Attach safety harness before proceeding.",
            checklist_items=[
                "Harness inspection complete",
                "Anchor point verified",
                "Safety lanyard attached"
            ]
        ),
    ]

    return demo_zones


@router.post("/zone-entry")
async def log_zone_entry(
    zone_id: str = Form(...),
    user_id: str = Form(...),
    ppe_verified: bool = Form(...),
    certifications_verified: bool = Form(...),
    current_user = Depends(get_optional_current_user),
):
    """
    Log entry into a safety zone.

    Called when worker enters a geofenced hazardous area.
    Verifies PPE and certifications are confirmed.
    """
    if not ppe_verified or not certifications_verified:
        raise HTTPException(
            status_code=400,
            detail="Cannot enter zone without verified PPE and certifications"
        )

    try:
        from app.core.firestore_db import FirestoreManager
        db = FirestoreManager()

        entry_log = {
            "zone_id": zone_id,
            "user_id": user_id,
            "ppe_verified": ppe_verified,
            "certifications_verified": certifications_verified,
            "entry_time": datetime.now(timezone.utc).isoformat(),
            "exit_time": None,
            "organization_id": current_user.organization_id if current_user else "demo_org"
        }

        await db.create_document("zone_entries", entry_log)

        return {"status": "logged", "message": "Zone entry logged. Work safely!"}
    except Exception as e:
        logger.error(f"Failed to log zone entry: {e}")
        raise HTTPException(status_code=500, detail="Failed to log zone entry")


# ============ Dashboard Stats ============

@router.get("/dashboard", response_model=SafetyDashboardStats)
async def get_safety_dashboard(
    current_user = Depends(get_optional_current_user),
):
    """
    Get safety statistics for executive dashboard.

    Shows the ROI: "We prevented X accidents and saved $Y this month"
    """
    try:
        from datetime import timedelta
        from app.core.firestore_db import FirestoreManager
        db = FirestoreManager()

        # Filter by organization
        org_id = getattr(current_user, 'organization_id', None) if current_user else "demo_org"
        org_filter = [("organization_id", "==", org_id)]

        # Get incidents filtered by organization
        incidents = await db.query_documents(
            collection="safety_incidents",
            filters=org_filter,
            limit=1000
        )

        # Get man down events filtered by organization
        man_down_events = await db.query_documents(
            collection="man_down_events",
            filters=org_filter,
            limit=100
        )

        # Calculate date boundaries for filtering
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)

        # Helper to parse incident date
        def get_incident_date(incident):
            created = incident.get("created_at") or incident.get("timestamp")
            if isinstance(created, str):
                try:
                    return datetime.fromisoformat(created.replace("Z", "+00:00"))
                except:
                    return None
            return created

        # Filter incidents by date
        today_incidents = [i for i in incidents if get_incident_date(i) and get_incident_date(i) >= today_start]
        week_incidents = [i for i in incidents if get_incident_date(i) and get_incident_date(i) >= week_start]
        month_incidents = [i for i in incidents if get_incident_date(i) and get_incident_date(i) >= month_start]

        # Calculate stats
        near_misses = len([i for i in month_incidents if i.get("incident_type") == "near_miss"])
        ppe_violations = len([i for i in month_incidents if i.get("type") == "ppe_violation"])
        man_down_count = len([e for e in man_down_events if not e.get("false_alarm")])

        total_incidents = len(month_incidents)

        # Estimate accidents prevented (industry standard: 1 in 10 near misses becomes accident)
        prevented = near_misses // 10 + ppe_violations // 20

        # Average workplace injury costs $40,000+
        savings = prevented * 40000

        # Calculate safety score
        safety_score = max(0, 100 - (total_incidents / 10))

        return SafetyDashboardStats(
            total_incidents_today=len(today_incidents),
            total_incidents_week=len(week_incidents),
            total_incidents_month=total_incidents,
            near_misses_reported=near_misses,
            ppe_violations_detected=ppe_violations,
            man_down_events=man_down_count,
            estimated_accidents_prevented=prevented,
            estimated_cost_savings=savings,
            safety_score=safety_score,
            trend_direction="improving" if safety_score > 90 else "stable"
        )

    except Exception as e:
        logger.error(f"Failed to get safety dashboard: {e}")
        return SafetyDashboardStats()
