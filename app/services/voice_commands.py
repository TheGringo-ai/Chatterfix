"""
Voice Commands Service
AI-powered voice command processing with Grok integration
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import httpx

from app.core.firestore_db import get_db_connection

logger = logging.getLogger(__name__)

XAI_API_KEY = os.getenv("XAI_API_KEY")
DATABASE_PATH = os.getenv("CMMS_DB_PATH", "./data/cmms.db")


async def process_voice_command(voice_text: str, technician_id: Optional[int] = None):
    """
    Process voice commands with AI intelligence

    Args:
        voice_text: The transcribed voice command
        technician_id: ID of the technician issuing the command

    Returns:
        dict: Work order details and AI analysis
    """
    try:
        # Process with Grok AI if available
        ai_analysis = "AI Analysis: Processing voice command"

        if XAI_API_KEY:
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    headers = {
                        "Authorization": f"Bearer {XAI_API_KEY}",
                        "Content-Type": "application/json",
                    }

                    payload = {
                        "model": "grok-beta",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a maintenance AI assistant. Analyze voice commands and create structured work orders with priority assessment and recommended actions.",
                            },
                            {
                                "role": "user",
                                "content": f"Voice command: '{voice_text}'. Create a work order with priority, urgency score, and recommended actions.",
                            },
                        ],
                        "temperature": 0.3,
                        "max_tokens": 400,
                    }

                    response = await client.post(
                        "https://api.x.ai/v1/chat/completions",
                        headers=headers,
                        json=payload,
                    )

                    if response.status_code == 200:
                        result = response.json()
                        ai_analysis = result["choices"][0]["message"]["content"]
                    else:
                        logger.warning(
                            f"Grok AI returned status {response.status_code}"
                        )

                except Exception as e:
                    logger.warning(f"Grok AI request failed: {e}")
        else:
            logger.info("XAI_API_KEY not set, using basic voice processing")

        # Create AI-enhanced work order
        # from app.core.database import get_db_connection

        conn = get_db_connection()
        cursor = conn.cursor()

        # Enhanced priority and command detection
        priority = "Medium"
        voice_lower = voice_text.lower()
        
        # Check for voice command shortcuts
        command_result = process_voice_shortcuts(voice_text)
        if command_result:
            return command_result
        
        # Priority detection with more keywords
        if any(
            word in voice_lower
            for word in ["urgent", "emergency", "critical", "broken", "down", "failed", "leak", "fire", "smoke"]
        ):
            priority = "High"
        elif any(
            word in voice_lower for word in ["routine", "scheduled", "minor", "inspection", "check"]
        ):
            priority = "Low"
        
        # Smart work order type detection
        work_order_type = detect_work_order_type(voice_text)
        
        # Location extraction
        location = extract_location(voice_text)

        cursor.execute(
            """
            INSERT INTO work_orders (title, description, priority, status, assigned_to)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                f"Voice Command: {voice_text[:50]}",
                f"{voice_text}\n\nAI Analysis:\n{ai_analysis}",
                priority,
                "Open",
                technician_id,
            ),
        )

        work_order_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return {
            "success": True,
            "work_order_id": work_order_id,
            "voice_text": voice_text,
            "ai_analysis": ai_analysis,
            "priority": priority,
            "estimated_completion": (datetime.now() + timedelta(hours=4)).isoformat(),
            "message": "Voice command processed and work order created",
        }

    except Exception as e:
        logger.error(f"Voice command processing failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to process voice command",
        }


def process_voice_shortcuts(voice_text: str):
    """
    Process common voice command shortcuts for quick actions
    """
    voice_lower = voice_text.lower().strip()
    
    # Quick status commands
    if "status" in voice_lower and ("dashboard" in voice_lower or "overview" in voice_lower):
        return {
            "success": True,
            "action": "navigate",
            "destination": "/dashboard",
            "message": "Opening dashboard overview"
        }
    
    if "create" in voice_lower and "work order" in voice_lower:
        return None  # Let normal work order creation handle this
    
    # Parts inventory shortcuts
    if "check inventory" in voice_lower or "parts status" in voice_lower:
        return {
            "success": True,
            "action": "navigate",
            "destination": "/inventory",
            "message": "Opening parts inventory"
        }
    
    # Quick asset lookup
    if "find asset" in voice_lower or "locate equipment" in voice_lower:
        return {
            "success": True,
            "action": "navigate", 
            "destination": "/assets",
            "message": "Opening asset management"
        }
    
    # Emergency shortcuts
    if any(word in voice_lower for word in ["emergency shutdown", "stop all", "emergency stop"]):
        return {
            "success": True,
            "action": "emergency_alert",
            "priority": "Critical",
            "message": "Emergency stop command processed - alerting management"
        }
    
    return None


def detect_work_order_type(voice_text: str):
    """
    Detect work order type from voice command
    """
    voice_lower = voice_text.lower()
    
    if any(word in voice_lower for word in ["repair", "fix", "broken", "replace"]):
        return "Corrective Maintenance"
    elif any(word in voice_lower for word in ["inspect", "check", "maintenance", "service"]):
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
        "utility": ["boiler room", "electrical room", "hvac", "basement"]
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
        r"by (\w+\s*\w*)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, voice_lower)
        if match:
            return match.group(1).title()
    
    return "Unspecified"


async def get_voice_command_suggestions():
    """
    Get intelligent voice command suggestions based on current context
    """
    suggestions = [
        "Create urgent work order for broken pump in warehouse A",
        "Schedule maintenance check for production line 2",
        "Report leak in boiler room",
        "Check inventory for hydraulic parts",
        "Emergency shutdown all equipment",
        "Create inspection task for HVAC system",
        "Replace filter in unit 5",
        "Order new parts for conveyor belt"
    ]
    
    return {
        "suggestions": suggestions,
        "tips": [
            "Speak clearly and include location details",
            "Mention priority level (urgent, routine, etc.)",
            "Be specific about equipment names",
            "Include what action needs to be taken"
        ]
    }
