"""
Voice Commands Service
AI-powered voice command processing with Grok integration
"""

import logging
import httpx
import sqlite3
import random
from datetime import datetime, timedelta
from typing import Optional
import os

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
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Determine priority from AI analysis or voice text
        priority = "Medium"
        if any(
            word in voice_text.lower()
            for word in ["urgent", "emergency", "critical", "broken"]
        ):
            priority = "High"
        elif any(
            word in voice_text.lower() for word in ["routine", "scheduled", "minor"]
        ):
            priority = "Low"

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
