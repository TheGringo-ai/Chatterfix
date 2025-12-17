"""
ChatterFix Platform Knowledge Service
Provides AI Team with complete understanding of platform vision and purpose
This context is injected into every AI interaction to ensure alignment
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ============================================================================
# CHATTERFIX PLATFORM VISION & KNOWLEDGE
# This is the "DNA" that every AI Team member must understand
# ============================================================================

PLATFORM_KNOWLEDGE = {
    "name": "ChatterFix",
    "tagline": "The Technician-First CMMS",
    "version": "2.0",

    # CORE MISSION
    "mission": """
ChatterFix exists to ELIMINATE manual data entry for technicians on the factory floor.
We capture ALL the data companies need through NATURAL CONVERSATION and VISION -
not through tedious forms and keyboards. The technician's hands stay on their tools,
not on a tablet typing work order descriptions.
""",

    # CEO VISION (from Fred)
    "ceo_vision": """
ChatterFix was built FOR THE TECHNICIAN - the person on the floor with dirty hands,
safety glasses, and a job to do. Every feature must pass one test: Does this help
the technician do their job FASTER and with LESS friction?

We're not building another CMMS that managers love and technicians hate.
We're building the future of maintenance - where AI understands what the technician
needs before they even ask, where a photo captures more than 100 form fields,
and where "Hey ChatterFix, pump 7 is making that noise again" creates a complete
work order with history, parts, and recommended procedures.

This is the future: Smart Glasses + AR + Voice + AI = Zero Manual Data Entry
""",

    # CORE CAPABILITIES
    "capabilities": {
        "voice_commands": {
            "description": "Natural language work order creation, part checkout, status updates",
            "examples": [
                "Hey ChatterFix, create a work order for the conveyor belt - it's making grinding noises",
                "Check out 3 bearings for pump 7 repair",
                "What's the maintenance history on this compressor?",
                "Mark work order 1234 as complete, took 2 hours"
            ],
            "future": "Always-on listening mode with smart glasses"
        },
        "vision_ai": {
            "description": "OCR for documents, part recognition, equipment diagnosis from photos",
            "examples": [
                "Scan equipment nameplate to auto-populate asset data",
                "Take photo of part to identify and check inventory",
                "Photograph equipment issue - AI diagnoses and suggests repairs",
                "Scan barcode to instantly pull up asset history"
            ],
            "future": "AR overlays showing maintenance procedures on equipment"
        },
        "natural_conversation": {
            "description": "Talk to AI like a human assistant, get department insights",
            "examples": [
                "What equipment has had the most downtime this month?",
                "Show me all overdue preventive maintenance",
                "Which technician has the best completion rate?",
                "Predict what's likely to fail next week based on patterns"
            ],
            "future": "Proactive AI that alerts before failures happen"
        },
        "smart_data_capture": {
            "description": "All the data managers need, captured automatically",
            "features": [
                "Time tracking from work order start/complete voice commands",
                "Parts used tracked through checkout voice commands",
                "Equipment photos attached automatically",
                "Location captured from mobile device",
                "Technician notes via voice transcription"
            ]
        }
    },

    # PRODUCT MODULES
    "modules": {
        "quality_fix": {
            "description": "Quality management integrated with maintenance",
            "purpose": "Track quality issues, root cause analysis, corrective actions",
            "integration": "Quality issues can trigger work orders automatically"
        },
        "safety_fix": {
            "description": "Safety incident tracking and compliance",
            "purpose": "Log safety observations, near-misses, incidents with voice/photo",
            "integration": "Safety issues create high-priority work orders"
        },
        "dial_t": {
            "description": "Direct communication channel for technicians",
            "purpose": "Emergency support, expert consultation, remote assistance",
            "integration": "One-touch access to help when stuck on a repair"
        },
        "linesmart_training": {
            "description": "AI-generated training from equipment manuals",
            "purpose": "Convert PDFs to interactive training modules",
            "integration": "Training recommendations based on skill gaps"
        },
        "smart_glasses": {
            "description": "AR experience for hands-free maintenance",
            "purpose": "See procedures overlaid on equipment, voice everything",
            "status": "Future integration - platform designed for this",
            "requirements": "All data capture must work without touching device"
        }
    },

    # KEY DIFFERENTIATORS
    "differentiators": [
        "TECHNICIAN-FIRST: Built for the person doing the work, not just managers",
        "ZERO MANUAL ENTRY: Voice + Vision captures all required data",
        "AI-NATIVE: Not AI bolted on - AI is the core of the product",
        "HANDS-FREE READY: Designed for smart glasses from day one",
        "CONTEXTUAL: AI understands your equipment, history, and patterns",
        "CONVERSATIONAL: Ask questions in plain English, get real answers"
    ],

    # TARGET USERS
    "users": {
        "primary": {
            "role": "Maintenance Technician",
            "pain_points": [
                "Hate typing on tablets with dirty/gloved hands",
                "Waste time looking up procedures and part numbers",
                "Get blamed when paperwork isn't complete",
                "Can't easily share knowledge with team"
            ],
            "how_we_help": [
                "Voice commands for everything",
                "Photo capture for documentation",
                "AI suggests procedures and parts",
                "Automatic time and parts tracking"
            ]
        },
        "secondary": {
            "role": "Maintenance Manager",
            "pain_points": [
                "Technicians don't enter complete data",
                "Can't get real-time visibility",
                "Reporting requires manual data compilation",
                "Training new techs takes too long"
            ],
            "how_we_help": [
                "Complete data captured automatically",
                "Real-time dashboards and alerts",
                "AI-generated reports and insights",
                "AI training from your own manuals"
            ]
        }
    },

    # TECHNOLOGY STACK
    "technology": {
        "ai_models": ["Gemini 2.0", "GPT-4", "Grok", "Claude"],
        "speech": "Google Cloud Speech-to-Text with manufacturing vocabulary",
        "vision": "Gemini Vision for OCR, part recognition, equipment diagnosis",
        "backend": "FastAPI on Google Cloud Run",
        "database": "Firestore (multi-tenant, organization isolation)",
        "future": "Edge AI for offline smart glasses operation"
    },

    # AI TEAM GUIDELINES
    "ai_guidelines": """
When working on ChatterFix, the AI Team must ALWAYS:

1. THINK TECHNICIAN-FIRST
   - Would a tech with dirty gloves be able to use this?
   - Does this require less typing, not more?
   - Is the voice command natural?

2. CAPTURE DATA AUTOMATICALLY
   - Never ask the user to manually enter what can be detected
   - Photos > Forms for equipment data
   - Voice > Typing for everything

3. PROVIDE CONTEXTUAL HELP
   - Know the equipment's history
   - Suggest based on patterns
   - Predict before they ask

4. STAY HANDS-FREE COMPATIBLE
   - Every feature must work with voice
   - Visual feedback must work on HUD/glasses
   - No small touch targets

5. BUILD FOR THE FLOOR, NOT THE OFFICE
   - Works in loud environments
   - Works with gloves
   - Works offline when needed
   - Simple, clear, fast
"""
}


def get_platform_context(include_full: bool = False) -> str:
    """
    Get platform context for AI Team prompts

    Args:
        include_full: If True, include complete knowledge. If False, summary only.

    Returns:
        String context to inject into AI prompts
    """
    if include_full:
        return f"""
=== CHATTERFIX PLATFORM KNOWLEDGE ===

{PLATFORM_KNOWLEDGE['mission']}

CEO VISION:
{PLATFORM_KNOWLEDGE['ceo_vision']}

KEY DIFFERENTIATORS:
{chr(10).join('- ' + d for d in PLATFORM_KNOWLEDGE['differentiators'])}

AI TEAM GUIDELINES:
{PLATFORM_KNOWLEDGE['ai_guidelines']}

CORE CAPABILITIES:
- Voice Commands: {PLATFORM_KNOWLEDGE['capabilities']['voice_commands']['description']}
- Vision AI: {PLATFORM_KNOWLEDGE['capabilities']['vision_ai']['description']}
- Natural Conversation: {PLATFORM_KNOWLEDGE['capabilities']['natural_conversation']['description']}
- Smart Data Capture: Automatic time, parts, photos, location tracking

PRODUCT MODULES:
- Quality Fix: {PLATFORM_KNOWLEDGE['modules']['quality_fix']['description']}
- Safety Fix: {PLATFORM_KNOWLEDGE['modules']['safety_fix']['description']}
- Dial T: {PLATFORM_KNOWLEDGE['modules']['dial_t']['description']}
- LineSmart Training: {PLATFORM_KNOWLEDGE['modules']['linesmart_training']['description']}
- Smart Glasses: {PLATFORM_KNOWLEDGE['modules']['smart_glasses']['description']}

=== END PLATFORM KNOWLEDGE ===
"""
    else:
        # Condensed version for cost-effective prompts
        return """
=== CHATTERFIX CONTEXT ===
ChatterFix is a TECHNICIAN-FIRST CMMS that eliminates manual data entry through:
- VOICE COMMANDS: Natural language for work orders, parts, status updates
- VISION AI: Photos for documentation, part recognition, equipment diagnosis
- HANDS-FREE: Designed for smart glasses and AR integration

ALWAYS: Think technician-first, capture data automatically, stay hands-free compatible.
=== END CONTEXT ===
"""


def get_platform_knowledge() -> Dict[str, Any]:
    """Get full platform knowledge as dictionary"""
    return PLATFORM_KNOWLEDGE


async def store_platform_knowledge_to_firestore():
    """Store platform knowledge in Firestore for persistence and querying"""
    try:
        from app.core.firestore_db import get_firestore_manager

        firestore = get_firestore_manager()

        # Store as a system document
        doc_data = {
            "type": "platform_knowledge",
            "name": PLATFORM_KNOWLEDGE["name"],
            "version": PLATFORM_KNOWLEDGE["version"],
            "mission": PLATFORM_KNOWLEDGE["mission"],
            "ceo_vision": PLATFORM_KNOWLEDGE["ceo_vision"],
            "differentiators": PLATFORM_KNOWLEDGE["differentiators"],
            "ai_guidelines": PLATFORM_KNOWLEDGE["ai_guidelines"],
            "modules": list(PLATFORM_KNOWLEDGE["modules"].keys()),
            "capabilities": list(PLATFORM_KNOWLEDGE["capabilities"].keys()),
            "updated_at": datetime.now(timezone.utc),
        }

        await firestore.create_document(
            "system_knowledge",
            doc_data,
            "chatterfix_platform"
        )

        logger.info("Stored platform knowledge to Firestore")
        return True

    except Exception as e:
        logger.error(f"Failed to store platform knowledge: {e}")
        return False


async def get_ai_team_context(task_type: str = "general") -> str:
    """
    Get contextual knowledge for AI Team based on task type

    Args:
        task_type: Type of task (code_review, feature, troubleshooting, etc.)

    Returns:
        Appropriate context for the task
    """
    base_context = get_platform_context(include_full=False)

    task_contexts = {
        "code_review": """
FOCUS FOR CODE REVIEW:
- Is this code technician-friendly?
- Does it support voice/vision input?
- Is it hands-free compatible?
- Does it minimize manual data entry?
""",
        "feature": """
FOCUS FOR FEATURES:
- How would a technician with dirty gloves use this?
- Can this be triggered by voice command?
- Does this capture data automatically?
- Will this work on smart glasses?
""",
        "troubleshooting": """
FOCUS FOR TROUBLESHOOTING:
- This is a maintenance technician asking for help
- Provide clear, step-by-step guidance
- Suggest relevant parts and procedures
- Reference equipment history if available
""",
        "training": """
FOCUS FOR TRAINING:
- Create content for frontline technicians
- Use simple, clear language
- Include hands-on procedures
- Make it work for AR/glasses display
""",
        "quality": """
FOCUS FOR QUALITY:
- Track root causes and corrective actions
- Link quality issues to equipment
- Capture with photos when possible
- Enable voice-based quality reports
""",
        "safety": """
FOCUS FOR SAFETY:
- Safety is the TOP priority
- Enable easy incident reporting via voice
- Capture photos for documentation
- Auto-escalate critical issues
"""
    }

    additional_context = task_contexts.get(task_type, "")

    return f"{base_context}\n{additional_context}"


# Singleton for quick access
_platform_context_cache: Optional[str] = None


def get_cached_platform_context() -> str:
    """Get cached platform context for performance"""
    global _platform_context_cache
    if _platform_context_cache is None:
        _platform_context_cache = get_platform_context(include_full=False)
    return _platform_context_cache
