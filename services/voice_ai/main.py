#!/usr/bin/env python3
"""
ChatterFix Voice AI Service - Speech to Intent Processing
Phase 7 - Voice interface for CMMS operations
"""

import os
import io
import json
import uuid
import re
from datetime import datetime
from typing import List, Optional, Dict, Any, Union

import uvicorn
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ChatterFix Voice AI Service",
    description="Speech-to-intent processing for CMMS voice commands",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
AI_BRAIN_URL = os.getenv("AI_BRAIN_URL", "https://chatterfix-ai-brain-650169261019.us-central1.run.app")
WORK_ORDERS_URL = os.getenv("WORK_ORDERS_URL", "https://chatterfix-work-orders-650169261019.us-central1.run.app")
ASSETS_URL = os.getenv("ASSETS_URL", "https://chatterfix-assets-650169261019.us-central1.run.app")
PARTS_URL = os.getenv("PARTS_URL", "https://chatterfix-parts-650169261019.us-central1.run.app")
VOICE_AI_TOKEN = os.getenv("VOICE_AI_TOKEN", "voice-ai-secret-token")

# Pydantic models
class VoiceIntentRequest(BaseModel):
    transcription: Optional[str] = None
    context: Dict[str, Any]
    language: str = "en-US"
    confidence_threshold: float = 0.7

class IntentResponse(BaseModel):
    intent: str
    confidence: float
    parameters: Dict[str, Any]
    action_taken: Optional[Dict[str, Any]] = None
    message: str
    success: bool = True
    error_message: Optional[str] = None

# Intent processing classes
class IntentParser:
    """Parse voice transcriptions into structured intents"""
    
    def __init__(self):
        self.intent_patterns = {
            "create_work_order": [
                r"create.*work\s*order",
                r"new\s+work\s*order",
                r"add.*work\s*order",
                r"generate.*work\s*order",
                r"make.*work\s*order"
            ],
            "update_status": [
                r"(mark|set|change|update).*status",
                r"mark.*(complete|completed|done|finished)",
                r"set.*to.*(complete|in\s*progress|on\s*hold)",
                r"change.*status.*to"
            ],
            "add_comment": [
                r"add.*comment",
                r"add.*note",
                r"comment.*that",
                r"note.*that",
                r"log.*that"
            ],
            "checkout_part": [
                r"check.*out.*part",
                r"take.*part",
                r"use.*part",
                r"get.*part",
                r"checkout"
            ],
            "advise_troubleshoot": [
                r"how.*do.*i",
                r"what.*should.*i",
                r"help.*with",
                r"troubleshoot",
                r"diagnose",
                r"fix.*problem"
            ],
            "find_asset": [
                r"find.*asset",
                r"locate.*asset",
                r"where.*is.*asset",
                r"show.*asset"
            ],
            "check_inventory": [
                r"check.*inventory",
                r"check.*stock",
                r"how.*many.*parts",
                r"inventory.*level"
            ]
        }
        
        self.priority_keywords = {
            "high": ["urgent", "high priority", "critical", "emergency", "asap"],
            "medium": ["medium priority", "normal", "standard"],
            "low": ["low priority", "when possible", "not urgent"]
        }
        
        self.status_keywords = {
            "completed": ["complete", "completed", "done", "finished", "closed"],
            "in progress": ["in progress", "working", "started", "ongoing"],
            "on hold": ["on hold", "hold", "pause", "paused", "waiting"],
            "open": ["open", "new", "pending"]
        }
    
    def parse_intent(self, transcription: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse transcription and extract intent with parameters"""
        text = transcription.lower().strip()
        
        # Find matching intent
        best_intent = "unknown"
        best_confidence = 0.0
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    confidence = self._calculate_confidence(pattern, text)
                    if confidence > best_confidence:
                        best_intent = intent
                        best_confidence = confidence
        
        # Extract parameters based on intent
        parameters = self._extract_parameters(best_intent, text, context)
        
        return {
            "intent": best_intent,
            "confidence": best_confidence,
            "parameters": parameters,
            "original_text": transcription
        }
    
    def _calculate_confidence(self, pattern: str, text: str) -> float:
        """Calculate confidence score for pattern match"""
        # Simple confidence calculation based on pattern length and text match
        matches = re.findall(pattern, text, re.IGNORECASE)
        if not matches:
            return 0.0
        
        # Base confidence from pattern match
        base_confidence = 0.7
        
        # Boost confidence for exact matches or multiple keyword matches
        exact_keywords = len([word for word in pattern.split() if word in text])
        total_keywords = len(pattern.split())
        
        if total_keywords > 0:
            keyword_ratio = exact_keywords / total_keywords
            base_confidence += (keyword_ratio * 0.3)
        
        return min(base_confidence, 1.0)
    
    def _extract_parameters(self, intent: str, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters specific to the intent"""
        params = {}
        
        if intent == "create_work_order":
            params = self._extract_work_order_params(text, context)
        elif intent == "update_status":
            params = self._extract_status_params(text, context)
        elif intent == "add_comment":
            params = self._extract_comment_params(text, context)
        elif intent == "checkout_part":
            params = self._extract_checkout_params(text, context)
        elif intent == "advise_troubleshoot":
            params = self._extract_troubleshoot_params(text, context)
        elif intent == "find_asset":
            params = self._extract_asset_params(text, context)
        elif intent == "check_inventory":
            params = self._extract_inventory_params(text, context)
        
        return params
    
    def _extract_work_order_params(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract work order creation parameters"""
        params = {}
        
        # Extract title (look for "for" keyword)
        title_match = re.search(r"(?:work\s*order|wo)\s+(?:for|to)\s+(.+?)(?:\s+(?:on|at|in|by|due)|\s*$)", text, re.IGNORECASE)
        if title_match:
            params["title"] = title_match.group(1).strip().title()
        else:
            params["title"] = "Voice Created Work Order"
        
        # Extract priority
        params["priority"] = self._extract_priority(text)
        
        # Extract asset reference
        asset_id = self._extract_asset_reference(text)
        if asset_id:
            params["asset_id"] = asset_id
        
        # Extract due date keywords
        if any(word in text for word in ["today", "tomorrow", "friday", "monday", "week", "asap"]):
            params["due_date_text"] = self._extract_due_date_text(text)
        
        # Use transcription as description
        params["description"] = text.title()
        
        return params
    
    def _extract_status_params(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract status update parameters"""
        params = {}
        
        # Extract new status
        for status, keywords in self.status_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    params["status"] = status.title().replace(" ", " ")
                    break
            if "status" in params:
                break
        
        # Default to completed if not specified but has completion keywords
        if "status" not in params:
            if any(word in text for word in ["mark", "set", "done", "finished"]):
                params["status"] = "Completed"
        
        # Extract work order ID from context or text
        if context.get("work_order_id"):
            params["work_order_id"] = context["work_order_id"]
        
        return params
    
    def _extract_comment_params(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract comment parameters"""
        params = {}
        
        # Extract comment text (everything after comment/note keywords)
        comment_match = re.search(r"(?:comment|note|log)\s+(?:that\s+)?(.+)$", text, re.IGNORECASE)
        if comment_match:
            params["comment"] = comment_match.group(1).strip()
        else:
            params["comment"] = text
        
        # Extract work order ID from context
        if context.get("work_order_id"):
            params["work_order_id"] = context["work_order_id"]
        
        return params
    
    def _extract_checkout_params(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parts checkout parameters"""
        params = {}
        
        # Extract quantity
        qty_match = re.search(r"(\d+)\s*(?:x\s*)?(?:of\s*)?", text)
        if qty_match:
            params["quantity"] = int(qty_match.group(1))
        else:
            params["quantity"] = 1
        
        # Extract part reference
        part_match = re.search(r"(?:part|filter|bearing|belt)\s*(?:#?\s*)?(\w+)", text, re.IGNORECASE)
        if part_match:
            params["part_reference"] = part_match.group(1)
        
        # Extract work order reference
        wo_match = re.search(r"(?:work\s*order|wo)\s*#?\s*(\d+)", text, re.IGNORECASE)
        if wo_match:
            params["work_order_id"] = int(wo_match.group(1))
        elif context.get("work_order_id"):
            params["work_order_id"] = context["work_order_id"]
        
        return params
    
    def _extract_troubleshoot_params(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract troubleshooting parameters"""
        params = {}
        
        # Extract problem description
        problem_patterns = [
            r"(?:how\s+do\s+i|what\s+should\s+i)\s+(.+)",
            r"help\s+with\s+(.+)",
            r"troubleshoot\s+(.+)",
            r"diagnose\s+(.+)",
            r"fix\s+(.+)"
        ]
        
        for pattern in problem_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                params["problem"] = match.group(1).strip()
                break
        
        if "problem" not in params:
            params["problem"] = text
        
        # Extract equipment/asset references
        equipment_match = re.search(r"(hvac|generator|conveyor|pump|motor|compressor)", text, re.IGNORECASE)
        if equipment_match:
            params["equipment_type"] = equipment_match.group(1).lower()
        
        return params
    
    def _extract_asset_params(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract asset search parameters"""
        params = {}
        
        # Extract asset reference
        asset_id = self._extract_asset_reference(text)
        if asset_id:
            params["asset_id"] = asset_id
        
        # Extract asset name/type
        asset_match = re.search(r"(?:find|locate|show)\s+(?:asset\s+)?(.+)", text, re.IGNORECASE)
        if asset_match:
            params["search_term"] = asset_match.group(1).strip()
        
        return params
    
    def _extract_inventory_params(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract inventory check parameters"""
        params = {}
        
        # Extract part reference
        part_match = re.search(r"(?:how\s+many|check)\s+(.+?)(?:\s+(?:do\s+we\s+have|parts?|inventory)|\s*$)", text, re.IGNORECASE)
        if part_match:
            params["part_search"] = part_match.group(1).strip()
        
        return params
    
    def _extract_priority(self, text: str) -> str:
        """Extract priority from text"""
        for priority, keywords in self.priority_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return priority.title()
        return "Medium"
    
    def _extract_asset_reference(self, text: str) -> Optional[int]:
        """Extract asset ID from text"""
        # Look for patterns like "Asset A-103", "asset 103", etc.
        asset_patterns = [
            r"asset\s+a-?(\d+)",
            r"asset\s+(\d+)",
            r"equipment\s+(\d+)",
            r"a-(\d+)"
        ]
        
        for pattern in asset_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return None
    
    def _extract_due_date_text(self, text: str) -> str:
        """Extract due date text"""
        date_keywords = ["today", "tomorrow", "friday", "monday", "tuesday", "wednesday", "thursday", "saturday", "sunday", "week", "asap"]
        for keyword in date_keywords:
            if keyword in text:
                return keyword
        return "not specified"

# Action executor
class ActionExecutor:
    """Execute actions based on parsed intents"""
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def execute_intent(self, intent_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the action for the given intent"""
        intent = intent_data["intent"]
        params = intent_data["parameters"]
        
        try:
            if intent == "create_work_order":
                return await self._create_work_order(params)
            elif intent == "update_status":
                return await self._update_work_order_status(params)
            elif intent == "add_comment":
                return await self._add_comment(params)
            elif intent == "checkout_part":
                return await self._checkout_part(params)
            elif intent == "advise_troubleshoot":
                return await self._get_troubleshooting_advice(params)
            elif intent == "find_asset":
                return await self._find_asset(params)
            elif intent == "check_inventory":
                return await self._check_inventory(params)
            else:
                return {
                    "success": False,
                    "message": f"Unknown intent: {intent}",
                    "action": "none"
                }
        except Exception as e:
            logger.error(f"Error executing intent {intent}: {e}")
            return {
                "success": False,
                "message": f"Error executing action: {str(e)}",
                "action": "error"
            }
    
    async def _create_work_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new work order"""
        work_order_data = {
            "title": params.get("title", "Voice Created Work Order"),
            "description": params.get("description", "Created via voice command"),
            "priority": params.get("priority", "Medium"),
            "asset_id": params.get("asset_id")
        }
        
        response = await self.http_client.post(
            f"{WORK_ORDERS_URL}/work_orders",
            json=work_order_data
        )
        
        if response.status_code == 200:
            work_order = response.json()
            return {
                "success": True,
                "message": f"Created work order {work_order.get('code', work_order['id'])}",
                "action": "work_order_created",
                "data": work_order
            }
        else:
            return {
                "success": False,
                "message": "Failed to create work order",
                "action": "error"
            }
    
    async def _update_work_order_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update work order status"""
        work_order_id = params.get("work_order_id")
        new_status = params.get("status")
        
        if not work_order_id or not new_status:
            return {
                "success": False,
                "message": "Missing work order ID or status",
                "action": "error"
            }
        
        update_data = {"status": new_status}
        
        response = await self.http_client.put(
            f"{WORK_ORDERS_URL}/work_orders/{work_order_id}",
            json=update_data
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": f"Updated work order {work_order_id} status to {new_status}",
                "action": "status_updated",
                "data": {"work_order_id": work_order_id, "status": new_status}
            }
        else:
            return {
                "success": False,
                "message": "Failed to update work order status",
                "action": "error"
            }
    
    async def _add_comment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add comment to work order"""
        work_order_id = params.get("work_order_id")
        comment = params.get("comment")
        
        if not work_order_id or not comment:
            return {
                "success": False,
                "message": "Missing work order ID or comment",
                "action": "error"
            }
        
        comment_data = {"note": comment}
        
        response = await self.http_client.post(
            f"{WORK_ORDERS_URL}/work_orders/{work_order_id}/comment",
            json=comment_data
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": f"Added comment to work order {work_order_id}",
                "action": "comment_added",
                "data": {"work_order_id": work_order_id, "comment": comment}
            }
        else:
            return {
                "success": False,
                "message": "Failed to add comment",
                "action": "error"
            }
    
    async def _checkout_part(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Checkout parts from inventory"""
        quantity = params.get("quantity", 1)
        part_reference = params.get("part_reference")
        work_order_id = params.get("work_order_id")
        
        # For now, use a mock part ID (would need to search parts by reference)
        part_id = 1001  # Default to first sample part
        
        checkout_data = {
            "qty": quantity,
            "work_order_id": work_order_id
        }
        
        response = await self.http_client.post(
            f"{PARTS_URL}/parts/{part_id}/checkout",
            json=checkout_data
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "message": f"Checked out {quantity} parts",
                "action": "parts_checked_out",
                "data": result
            }
        else:
            return {
                "success": False,
                "message": "Failed to checkout parts",
                "action": "error"
            }
    
    async def _get_troubleshooting_advice(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get troubleshooting advice from AI Brain"""
        problem = params.get("problem", "general troubleshooting")
        equipment_type = params.get("equipment_type")
        
        # Call AI Brain service for advice
        advice_request = {
            "query": f"How to troubleshoot {problem}",
            "context": {"equipment_type": equipment_type} if equipment_type else {},
            "mode": "troubleshooting"
        }
        
        try:
            response = await self.http_client.post(
                f"{AI_BRAIN_URL}/api/advice",
                json=advice_request
            )
            
            if response.status_code == 200:
                advice = response.json()
                return {
                    "success": True,
                    "message": advice.get("response", "General troubleshooting advice available"),
                    "action": "advice_provided",
                    "data": advice
                }
            else:
                # Fallback advice
                return {
                    "success": True,
                    "message": f"For {problem}, start with basic checks: power, connections, and error codes. Consult the manual or contact a technician if needed.",
                    "action": "fallback_advice"
                }
        except:
            return {
                "success": True,
                "message": "Basic troubleshooting advice: Check power, connections, and look for error indicators. Document findings before proceeding.",
                "action": "fallback_advice"
            }
    
    async def _find_asset(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find asset information"""
        asset_id = params.get("asset_id")
        search_term = params.get("search_term")
        
        if asset_id:
            response = await self.http_client.get(f"{ASSETS_URL}/assets/{asset_id}")
            if response.status_code == 200:
                asset = response.json()
                return {
                    "success": True,
                    "message": f"Found asset: {asset['name']} at {asset.get('location', 'unknown location')}",
                    "action": "asset_found",
                    "data": asset
                }
        
        return {
            "success": False,
            "message": f"Could not find asset: {search_term or asset_id}",
            "action": "asset_not_found"
        }
    
    async def _check_inventory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check inventory levels"""
        part_search = params.get("part_search", "")
        
        # Get parts summary
        response = await self.http_client.get(f"{PARTS_URL}/parts/stats/summary")
        
        if response.status_code == 200:
            stats = response.json()
            return {
                "success": True,
                "message": f"Total parts: {stats['total_parts']}, Low stock items: {stats['low_stock_items']}",
                "action": "inventory_checked",
                "data": stats
            }
        else:
            return {
                "success": False,
                "message": "Could not check inventory",
                "action": "error"
            }

# Initialize components
intent_parser = IntentParser()
action_executor = ActionExecutor()

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "voice_ai",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "features": ["speech_processing", "intent_parsing", "action_execution"]
    }

@app.post("/voice/intent", response_model=IntentResponse)
async def process_voice_intent(
    audio_data: UploadFile = File(None),
    transcription: Optional[str] = Form(None),
    context: str = Form(...),  # JSON string
    language: str = Form("en-US"),
    confidence_threshold: float = Form(0.7)
):
    """Process voice input and execute corresponding actions"""
    
    # Validate input
    if not audio_data and not transcription:
        raise HTTPException(status_code=400, detail="Either audio_data or transcription required")
    
    try:
        context_data = json.loads(context)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid context JSON")
    
    # Transcribe audio if provided (placeholder - would use actual STT service)
    if audio_data and not transcription:
        # Mock transcription for development
        transcription = "Create work order for HVAC filter replacement high priority asset 101"
        logger.info(f"Mock transcription: {transcription}")
    
    if not transcription:
        raise HTTPException(status_code=400, detail="No transcription available")
    
    # Parse intent
    intent_data = intent_parser.parse_intent(transcription, context_data)
    
    # Check confidence threshold
    if intent_data["confidence"] < confidence_threshold:
        return IntentResponse(
            intent="unknown",
            confidence=intent_data["confidence"],
            parameters={},
            message=f"Could not understand: '{transcription}' (confidence: {intent_data['confidence']:.2f})",
            success=False
        )
    
    # Execute action
    action_result = await action_executor.execute_intent(intent_data, context_data)
    
    # Record intent in log (would save to database in production)
    intent_log = {
        "timestamp": datetime.now().isoformat(),
        "transcription": transcription,
        "intent": intent_data["intent"],
        "confidence": intent_data["confidence"],
        "parameters": intent_data["parameters"],
        "action_result": action_result,
        "context": context_data
    }
    logger.info(f"Voice intent processed: {intent_log}")
    
    return IntentResponse(
        intent=intent_data["intent"],
        confidence=intent_data["confidence"],
        parameters=intent_data["parameters"],
        action_taken=action_result,
        message=action_result.get("message", "Action completed"),
        success=action_result.get("success", False),
        error_message=None if action_result.get("success") else action_result.get("message")
    )

@app.post("/voice/test")
async def test_voice_processing(test_phrase: str, context: Dict[str, Any] = {}):
    """Test voice processing with a text phrase"""
    
    # Parse intent
    intent_data = intent_parser.parse_intent(test_phrase, context)
    
    # Execute action
    action_result = await action_executor.execute_intent(intent_data, context)
    
    return {
        "input": test_phrase,
        "intent_data": intent_data,
        "action_result": action_result
    }

@app.get("/voice/intents")
async def get_supported_intents():
    """Get list of supported voice intents"""
    return {
        "supported_intents": {
            "create_work_order": {
                "description": "Create a new work order",
                "examples": [
                    "Create work order for HVAC filter replacement",
                    "New work order for Asset A-103 high priority",
                    "Generate work order for conveyor belt lubrication"
                ]
            },
            "update_status": {
                "description": "Update work order status",
                "examples": [
                    "Mark work order complete",
                    "Set status to in progress",
                    "Change status to on hold"
                ]
            },
            "add_comment": {
                "description": "Add comment to work order",
                "examples": [
                    "Add comment unit still overheating",
                    "Note that filter was changed",
                    "Log that maintenance is complete"
                ]
            },
            "checkout_part": {
                "description": "Checkout parts from inventory",
                "examples": [
                    "Check out two filters",
                    "Take three bearings for work order 123",
                    "Checkout part filter for WO-2025-001"
                ]
            },
            "advise_troubleshoot": {
                "description": "Get troubleshooting advice",
                "examples": [
                    "How do I diagnose HVAC issues",
                    "What should I check for generator problems",
                    "Help with troubleshooting conveyor belt"
                ]
            },
            "find_asset": {
                "description": "Find asset information",
                "examples": [
                    "Find asset A-103",
                    "Locate HVAC unit",
                    "Show me asset 101"
                ]
            },
            "check_inventory": {
                "description": "Check inventory levels",
                "examples": [
                    "Check inventory levels",
                    "How many filters do we have",
                    "Check stock for bearings"
                ]
            }
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)