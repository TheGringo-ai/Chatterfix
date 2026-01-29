"""
Voice Commands Service
AI-powered voice command processing with context awareness and Grok integration

Features:
- Context-aware command resolution (QR scan, GPS, camera)
- Input sanitization for security
- Deictic reference resolution ("this", "here", "it")
- Integration with AI Memory System
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional

import nh3

# Import work order service for creating work orders from voice commands
from app.services.work_order_service import work_order_service

# Import models
from app.models.voice_context import (
    AssetContext,
    GeoLocation,
    VoiceCommandRequest,
    VoiceCommandResponse,
)

# Import AI Memory Service for capturing interactions
try:
    from app.services.ai_memory_integration import get_ai_memory_service
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

# Import Voice/Vision Memory for learning from interactions
try:
    from app.services.voice_vision_memory import VoiceVisionMemory
    VOICE_MEMORY_AVAILABLE = True
except ImportError:
    VOICE_MEMORY_AVAILABLE = False

# Import asset service for context resolution
try:
    from app.core.firestore_db import get_firestore_manager
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False

# Import geolocation service
try:
    from app.services.geolocation_service import GeolocationService
    GEO_AVAILABLE = True
except ImportError:
    GEO_AVAILABLE = False

logger = logging.getLogger(__name__)

XAI_API_KEY = os.getenv("XAI_API_KEY")
DATABASE_PATH = os.getenv("CMMS_DB_PATH", "./data/cmms.db")

# Deictic reference triggers - words that need context to resolve
DEICTIC_TRIGGERS = ["this", "it", "here", "that", "these", "those"]
CONTEXT_ACTION_TRIGGERS = ["broken", "leak", "fix", "repair", "inspect", "check", "record"]


def sanitize_input(text: str) -> str:
    """
    Sanitize voice input to prevent injection attacks.

    Strips HTML/script tags and dangerous characters while
    preserving the natural language content.

    Uses nh3 (Rust-based) instead of deprecated bleach library.
    """
    if not text:
        return ""

    # Remove HTML tags and scripts using nh3
    cleaned = nh3.clean(text, tags=set(), strip_comments=True)

    # Remove null bytes and control characters (except newlines/tabs)
    cleaned = ''.join(char for char in cleaned if ord(char) >= 32 or char in '\n\r\t')

    # Limit length to prevent DoS
    cleaned = cleaned[:2000]

    return cleaned.strip()


async def resolve_asset_context(
    asset_id: Optional[str] = None,
    asset_context: Optional[AssetContext] = None,
) -> Optional[Dict[str, Any]]:
    """
    Resolve asset details from asset ID or context.

    Returns asset info dict or None if not found.
    """
    if not FIRESTORE_AVAILABLE:
        return None

    try:
        target_id = asset_id or (asset_context.asset_id if asset_context else None)
        if not target_id:
            return None

        firestore = get_firestore_manager()
        asset = await firestore.get_document("assets", target_id)

        if asset:
            return {
                "id": target_id,
                "name": asset.get("name", "Unknown Asset"),
                "type": asset.get("asset_type", "equipment"),
                "location": asset.get("location", ""),
                "status": asset.get("status", "operational"),
            }
    except Exception as e:
        logger.warning(f"Failed to resolve asset context: {e}")

    return None


async def resolve_location_context(
    location: Optional[GeoLocation] = None,
    radius_meters: float = 15.0,
) -> List[Dict[str, Any]]:
    """
    Find nearby assets based on GPS location.

    Returns list of nearby assets sorted by distance.
    """
    if not location or not GEO_AVAILABLE:
        return []

    try:
        geo_service = GeolocationService()
        # Check if technician is within property boundaries
        within_property = await geo_service.is_within_property(
            location.latitude, location.longitude
        )

        if not within_property:
            logger.info("Technician outside property boundaries, skipping location context")
            return []

        # Get nearby assets (implementation would query assets with geo data)
        # For now, return empty - this would integrate with asset geo-tagging
        return []

    except Exception as e:
        logger.warning(f"Failed to resolve location context: {e}")

    return []


def build_context_prompt(
    voice_text: str,
    resolved_asset: Optional[Dict[str, Any]] = None,
    nearby_assets: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Build context-enriched prompt for AI processing.

    Appends context information that helps AI models understand
    deictic references like "this", "here", "it".
    """
    voice_lower = voice_text.lower()
    context_clues = []

    # Check if the command contains context-dependent words
    has_deictic = any(trigger in voice_lower for trigger in DEICTIC_TRIGGERS)
    has_action = any(trigger in voice_lower for trigger in CONTEXT_ACTION_TRIGGERS)

    if not (has_deictic or has_action):
        # No context needed
        return voice_text

    # Add asset context if available (highest priority - from QR/NFC scan)
    if resolved_asset:
        context_clues.append(
            f"CURRENT_ASSET: Technician is inspecting '{resolved_asset['name']}' "
            f"(ID: {resolved_asset['id']}, Type: {resolved_asset['type']})"
        )
        if resolved_asset.get('location'):
            context_clues.append(f"ASSET_LOCATION: {resolved_asset['location']}")

    # Add nearby assets if available (fallback - from GPS)
    elif nearby_assets:
        asset_names = ", ".join([a['name'] for a in nearby_assets[:3]])
        context_clues.append(f"NEARBY_ASSETS: Technician is near: {asset_names}")

    # Build final prompt with context
    if context_clues:
        context_block = " | ".join(context_clues)
        return f"{voice_text}\n\n[CONTEXT: {context_block}]"

    return voice_text


async def process_voice_command_with_context(
    request: VoiceCommandRequest,
) -> VoiceCommandResponse:
    """
    Process voice commands with full context awareness.

    This is the primary entry point for context-aware voice processing.
    Resolves "this", "here", "it" using scanned assets or geolocation.
    """
    start_time = time.time()

    # 1. Sanitize input
    sanitized_text = sanitize_input(request.voice_text)
    if not sanitized_text:
        return VoiceCommandResponse(
            success=False,
            original_text=request.voice_text,
            processed_text="",
            response_text="I couldn't understand your command. Please try again."
        )

    # 2. Resolve asset context (from QR scan, NFC, or manual selection)
    resolved_asset = None
    if request.current_asset:
        resolved_asset = await resolve_asset_context(
            asset_context=request.current_asset
        )

    # 3. Resolve location context (fallback if no asset scanned)
    nearby_assets = []
    if not resolved_asset and request.location:
        nearby_assets = await resolve_location_context(request.location)

    # 4. Build context-enriched prompt
    processed_text = build_context_prompt(
        sanitized_text,
        resolved_asset,
        nearby_assets,
    )

    # 5. Log contextual interaction
    logger.info(
        f"Voice Command: '{sanitized_text[:50]}...' | "
        f"Asset: {resolved_asset['name'] if resolved_asset else 'None'} | "
        f"Nearby: {len(nearby_assets)} assets"
    )

    # 6. Process the command (create work order, navigate, etc.)
    action_result = await _execute_voice_action(
        processed_text,
        sanitized_text,
        request.technician_id,
        resolved_asset,
    )

    # 7. Calculate processing time
    processing_time = int((time.time() - start_time) * 1000)

    return VoiceCommandResponse(
        success=action_result.get("success", False),
        original_text=request.voice_text,
        processed_text=processed_text,
        context_used=bool(resolved_asset or nearby_assets),
        resolved_asset_id=resolved_asset["id"] if resolved_asset else None,
        resolved_asset_name=resolved_asset["name"] if resolved_asset else None,
        action=action_result.get("action"),
        action_result=action_result.get("result"),
        response_text=action_result.get("message"),
        processing_time_ms=processing_time,
    )


async def _execute_voice_action(
    processed_text: str,
    original_text: str,
    technician_id: Optional[str],
    resolved_asset: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Execute the action based on the voice command.
    """
    try:
        # Detect priority
        priority = "Medium"
        text_lower = original_text.lower()
        if any(word in text_lower for word in ["urgent", "emergency", "critical"]):
            priority = "High"
        elif any(word in text_lower for word in ["low", "minor", "when possible"]):
            priority = "Low"

        # Build work order title
        if resolved_asset:
            title = f"{resolved_asset['name']}: {original_text[:40]}"
        else:
            title = f"Voice Command: {original_text[:50]}"

        # Create work order data
        work_order_data = {
            "title": title,
            "description": f"{original_text}\n\n---\nProcessed Context:\n{processed_text}",
            "priority": priority,
            "status": "Open",
            "assigned_to_uid": str(technician_id) if technician_id else None,
            "work_order_type": detect_work_order_type(original_text),
            "asset_id": resolved_asset["id"] if resolved_asset else None,
            "asset_name": resolved_asset["name"] if resolved_asset else None,
        }

        # Create the work order
        work_order_id = await work_order_service.create_work_order(work_order_data)

        # Build response message
        if resolved_asset:
            message = f"Work order created for {resolved_asset['name']}"
        else:
            message = "Work order created successfully"

        return {
            "success": True,
            "action": "create_work_order",
            "result": {"work_order_id": work_order_id},
            "message": message,
        }

    except Exception as e:
        logger.error(f"Voice action execution failed: {e}")
        return {
            "success": False,
            "action": "error",
            "message": f"Failed to process command: {str(e)}",
        }


# Legacy function for backwards compatibility
async def process_voice_command(
    voice_text: str,
    technician_id: Optional[str] = None,
    current_asset_id: Optional[str] = None,
    location: Optional[Dict[str, float]] = None,
):
    """
    Process voice commands with AI intelligence and create a work order.

    This is the legacy function maintained for backwards compatibility.
    New code should use process_voice_command_with_context() with VoiceCommandRequest.
    """
    # Sanitize input
    sanitized_text = sanitize_input(voice_text)

    # Build request object
    request = VoiceCommandRequest(
        voice_text=sanitized_text,
        technician_id=technician_id,
        current_asset=AssetContext(asset_id=current_asset_id) if current_asset_id else None,
        location=GeoLocation(**location) if location else None,
    )

    # Process with new context-aware function
    response = await process_voice_command_with_context(request)

    # Return legacy format
    return {
        "success": response.success,
        "work_order_id": response.action_result.get("work_order_id") if response.action_result else None,
        "message": response.response_text,
        "context_used": response.context_used,
        "resolved_asset": response.resolved_asset_name,
    }


def process_voice_shortcuts(voice_text: str):
    """
    Process common voice command shortcuts for quick actions
    """
    voice_lower = voice_text.lower().strip()

    # Quick status commands
    if "status" in voice_lower and (
        "dashboard" in voice_lower or "overview" in voice_lower
    ):
        return {
            "success": True,
            "action": "navigate",
            "destination": "/dashboard",
            "message": "Opening dashboard overview",
        }

    if "create" in voice_lower and "work order" in voice_lower:
        return None  # Let normal work order creation handle this

    # Parts inventory shortcuts
    if "check inventory" in voice_lower or "parts status" in voice_lower:
        return {
            "success": True,
            "action": "navigate",
            "destination": "/inventory",
            "message": "Opening parts inventory",
        }

    # Quick asset lookup
    if "find asset" in voice_lower or "locate equipment" in voice_lower:
        return {
            "success": True,
            "action": "navigate",
            "destination": "/assets",
            "message": "Opening asset management",
        }

    # Emergency shortcuts
    if any(
        word in voice_lower
        for word in ["emergency shutdown", "stop all", "emergency stop"]
    ):
        return {
            "success": True,
            "action": "emergency_alert",
            "priority": "Critical",
            "message": "Emergency stop command processed - alerting management",
        }

    return None


def detect_work_order_type(voice_text: str):
    """
    Detect work order type from voice command
    """
    voice_lower = voice_text.lower()

    if any(word in voice_lower for word in ["repair", "fix", "broken", "replace"]):
        return "Corrective Maintenance"
    elif any(
        word in voice_lower for word in ["inspect", "check", "maintenance", "service"]
    ):
        return "Preventive Maintenance"
    elif any(word in voice_lower for word in ["install", "setup", "new"]):
        return "Installation"
    elif any(word in voice_lower for word in ["clean", "cleaning"]):
        return "Housekeeping"
    elif any(word in voice_lower for word in ["calibrate", "adjust", "tune"]):
        return "Calibration"
    else:
        return "General"


def extract_location(voice_text: str):
    """
    Extract location information from voice command
    """
    voice_lower = voice_text.lower()

    # Common location patterns
    location_keywords = {
        "warehouse": ["warehouse a", "warehouse b", "warehouse c", "storage"],
        "production": ["production floor", "assembly line", "manufacturing"],
        "office": ["office", "admin", "break room"],
        "outside": ["parking lot", "yard", "exterior", "roof"],
        "utility": ["boiler room", "electrical room", "hvac", "basement"],
    }

    for category, keywords in location_keywords.items():
        for keyword in keywords:
            if keyword in voice_lower:
                return keyword.title()

    # Look for specific patterns like "in warehouse A" or "at line 3"
    import re

    patterns = [
        r"in (\w+\s*\w*)",
        r"at (\w+\s*\w*)",
        r"near (\w+\s*\w*)",
        r"by (\w+\s*\w*)",
    ]

    for pattern in patterns:
        match = re.search(pattern, voice_lower)
        if match:
            return match.group(1).title()

    return "Unspecified"


async def process_golden_workflow_commands(voice_text: str):
    """
    Process Golden Workflow voice commands that trigger integrated AI workflows
    """
    voice_lower = voice_text.lower().strip()

    # Golden Workflow 1: Complete Equipment Inspection
    if any(
        phrase in voice_lower
        for phrase in [
            "inspect equipment",
            "inspect this",
            "analyze equipment",
            "check condition",
            "visual inspection",
            "equipment analysis",
        ]
    ):
        return {
            "success": True,
            "action": "golden_workflow",
            "workflow_type": "complete_inspection",
            "message": "🎯 GOLDEN WORKFLOW: Starting complete equipment inspection",
            "next_steps": [
                "Camera interface will activate",
                "Point camera at equipment for visual analysis",
                "AI will analyze condition and extract details",
                "Work order will be created automatically",
                "Predictive maintenance will be scheduled",
            ],
            "voice_guidance": "Camera ready. Point at equipment to begin inspection.",
            "ui_action": "activate_camera_inspection_mode",
        }

    # Golden Workflow 2: Smart Gauge Reading
    if any(
        phrase in voice_lower
        for phrase in [
            "read gauge",
            "check gauge",
            "measure pressure",
            "read meter",
            "check reading",
            "gauge reading",
            "meter reading",
        ]
    ):
        return {
            "success": True,
            "action": "golden_workflow",
            "workflow_type": "smart_gauge_reading",
            "message": "📊 GOLDEN WORKFLOW: Starting smart gauge reading",
            "next_steps": [
                "Camera will focus on gauge/meter",
                "AI will extract numerical reading",
                "System will announce reading aloud",
                "Automatic trend analysis performed",
                "Alert generated if reading abnormal",
            ],
            "voice_guidance": "Point camera at gauge or meter. AI will read it for you.",
            "ui_action": "activate_gauge_reading_mode",
        }

    # Golden Workflow 3: Instant Part Lookup
    if any(
        phrase in voice_lower
        for phrase in [
            "identify part",
            "what part is this",
            "scan part",
            "check part",
            "part lookup",
            "recognize part",
            "part number",
        ]
    ):
        return {
            "success": True,
            "action": "golden_workflow",
            "workflow_type": "instant_part_lookup",
            "message": "🔧 GOLDEN WORKFLOW: Starting instant part identification",
            "next_steps": [
                "Camera captures part image",
                "AI recognizes part number",
                "System checks inventory availability",
                "Announces part status aloud",
                "Creates reorder request if needed",
            ],
            "voice_guidance": "Point camera at part nameplate or label for identification.",
            "ui_action": "activate_part_recognition_mode",
        }

    # Golden Workflow 4: Take Photo and Analyze
    if any(
        phrase in voice_lower
        for phrase in [
            "take photo and analyze",
            "photo analysis",
            "capture and analyze",
            "take picture and check",
            "photograph and inspect",
        ]
    ):
        return {
            "success": True,
            "action": "golden_workflow",
            "workflow_type": "photo_and_analyze",
            "message": "📸 GOLDEN WORKFLOW: Photo capture with instant AI analysis",
            "next_steps": [
                "Camera activates for photo capture",
                "AI performs comprehensive visual analysis",
                "Text extraction from any visible labels",
                "Equipment condition assessment",
                "Automatic documentation in work order",
            ],
            "voice_guidance": "Camera ready. Take photo when positioned correctly.",
            "ui_action": "activate_photo_analysis_mode",
        }

    # Voice + Vision Integration Commands
    if any(
        phrase in voice_lower
        for phrase in [
            "what do you see",
            "analyze this view",
            "what am i looking at",
            "describe this equipment",
            "tell me about this",
        ]
    ):
        return {
            "success": True,
            "action": "voice_vision_integration",
            "workflow_type": "live_analysis",
            "message": "👁️ AI VISION: Live equipment analysis activated",
            "voice_guidance": "I'm analyzing what you're looking at. Point camera at equipment.",
            "ui_action": "activate_live_vision_analysis",
        }

    return None


async def get_voice_command_suggestions():
    """
    Get intelligent voice command suggestions based on current context
    """
    # Enhanced suggestions with technician-first workflows
    suggestions = [
        "Create urgent work order for broken pump in warehouse A",
        "Take photo and analyze condition of main conveyor belt",
        "Read pressure gauge and create maintenance alert",
        "Scan equipment nameplate and check inventory",
        "Schedule maintenance check for production line 2",
        "Report leak in boiler room with visual inspection",
        "Check inventory for hydraulic parts and order if needed",
        "Emergency shutdown all equipment",
        "Create inspection task for HVAC system",
        "Replace filter in unit 5 and document completion",
        "Analyze vibration in motor and predict maintenance",
        "Extract text from work order and process digitally",
        "Inspect equipment condition and update asset database",
        "Voice command: What maintenance is due today?",
        "Golden workflow: Inspect, photograph, analyze, document",
    ]

    # Context-aware tips for technicians
    technician_tips = [
        "🎯 GOLDEN WORKFLOW: Say 'inspect equipment' → camera opens → AI analyzes → work order created automatically",
        "📸 PHOTO INTEGRATION: Say 'take photo and analyze' for instant visual inspection",
        "🎤 VOICE + VISION: Combine voice commands with camera for hands-free operation",
        "📊 REAL-TIME ANALYSIS: Say 'read gauge' while pointing camera at meters",
        "🔧 SMART WORKFLOWS: Voice commands automatically trigger appropriate AI analysis",
        "⚡ QUICK COMMANDS: 'Emergency stop', 'Check inventory', 'Create work order'",
        "🎯 CONTEXT AWARE: System understands your location and nearby equipment",
        "📝 AUTO-DOCUMENTATION: All voice commands automatically logged and processed",
    ]

    return {
        "suggestions": suggestions,
        "tips": technician_tips,
        "golden_workflows": [
            {
                "name": "Complete Equipment Inspection",
                "voice_trigger": "inspect equipment",
                "steps": [
                    "Voice command activates camera",
                    "AI analyzes visual condition",
                    "OCR extracts equipment details",
                    "System creates detailed work order",
                    "Predictive maintenance scheduled",
                ],
            },
            {
                "name": "Smart Gauge Reading",
                "voice_trigger": "read gauge",
                "steps": [
                    "Camera focuses on gauge/meter",
                    "AI extracts numerical reading",
                    "System announces reading aloud",
                    "Automatic trend analysis",
                    "Alert if reading abnormal",
                ],
            },
            {
                "name": "Instant Part Lookup",
                "voice_trigger": "identify part",
                "steps": [
                    "Camera captures part image",
                    "AI recognizes part number",
                    "System checks inventory",
                    "Announces availability status",
                    "Creates reorder if needed",
                ],
            },
        ],
    }
