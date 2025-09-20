#!/usr/bin/env python3
"""
Enhanced Voice Command System for ChatterFix CMMS
Converts natural speech to actionable work orders using LLaMA AI
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import requests
from fastapi import HTTPException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceWorkOrderProcessor:
    """Enhanced voice command processor for CMMS work orders"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "llama3.1:8b"
        
        # Equipment and location mappings
        self.equipment_types = {
            "pump": ["pump", "pumps", "water pump", "circulation pump"],
            "motor": ["motor", "motors", "electric motor", "drive motor"],
            "conveyor": ["conveyor", "belt", "conveyor belt", "transport belt"],
            "hvac": ["hvac", "air conditioning", "ac", "heating", "ventilation"],
            "boiler": ["boiler", "boilers", "steam boiler", "water boiler"],
            "compressor": ["compressor", "air compressor", "gas compressor"],
            "generator": ["generator", "backup generator", "emergency generator"],
            "elevator": ["elevator", "lift", "passenger elevator", "freight elevator"]
        }
        
        self.locations = {
            "building_a": ["building a", "bldg a", "warehouse a", "section a"],
            "building_b": ["building b", "bldg b", "warehouse b", "section b"], 
            "production": ["production", "production floor", "manufacturing", "factory floor"],
            "warehouse": ["warehouse", "storage", "inventory area", "stock room"],
            "office": ["office", "admin", "administration", "headquarters"],
            "basement": ["basement", "lower level", "underground", "sub level"],
            "roof": ["roof", "rooftop", "top floor", "upper level"]
        }
        
        self.priorities = {
            "critical": ["critical", "emergency", "urgent", "immediate", "asap", "critical failure"],
            "high": ["high", "important", "priority", "soon", "quickly"],
            "medium": ["medium", "normal", "standard", "regular"],
            "low": ["low", "minor", "when possible", "non-urgent", "routine"]
        }

    async def process_voice_command(self, voice_text: str, user_id: str = "voice_user") -> Dict:
        """Process voice command and create work order"""
        try:
            logger.info(f"Processing voice command: {voice_text}")
            
            # Extract entities from voice command
            entities = await self._extract_entities(voice_text)
            
            # Generate work order using LLaMA
            work_order = await self._generate_work_order(voice_text, entities)
            
            # Validate and enhance work order
            enhanced_order = await self._enhance_work_order(work_order, voice_text)
            
            return {
                "success": True,
                "work_order": enhanced_order,
                "original_command": voice_text,
                "extracted_entities": entities,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Voice command processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "original_command": voice_text,
                "fallback_action": "Manual work order creation required"
            }

    async def _extract_entities(self, text: str) -> Dict:
        """Extract equipment, location, priority, and issue from voice text"""
        text_lower = text.lower()
        
        # Extract equipment type
        equipment = None
        for eq_type, keywords in self.equipment_types.items():
            if any(keyword in text_lower for keyword in keywords):
                equipment = eq_type
                break
        
        # Extract location
        location = None
        for loc_type, keywords in self.locations.items():
            if any(keyword in text_lower for keyword in keywords):
                location = loc_type
                break
        
        # Default location if none found
        if location is None:
            location = "unknown_location"
        
        # Extract priority
        priority = "medium"  # default
        for pri_level, keywords in self.priorities.items():
            if any(keyword in text_lower for keyword in keywords):
                priority = pri_level
                break
        
        # Extract issue type using common maintenance keywords
        issue_keywords = {
            "leak": ["leak", "leaking", "dripping", "water damage"],
            "noise": ["noise", "loud", "squeaking", "grinding", "rattling"],
            "failure": ["broken", "failed", "not working", "stopped", "dead"],
            "maintenance": ["maintenance", "service", "inspection", "check"],
            "performance": ["slow", "inefficient", "poor performance", "underperforming"]
        }
        
        issue_type = None
        for issue, keywords in issue_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                issue_type = issue
                break
        
        return {
            "equipment": equipment,
            "location": location,
            "priority": priority,
            "issue_type": issue_type,
            "raw_text": text
        }

    async def _generate_work_order(self, voice_text: str, entities: Dict) -> Dict:
        """Use LLaMA to generate structured work order"""
        
        prompt = f"""
You are a CMMS AI assistant. Convert this voice command into a structured work order:

Voice Command: "{voice_text}"

Extracted Info:
- Equipment: {entities.get('equipment', 'Unknown')}
- Location: {entities.get('location', 'Unknown')}
- Priority: {entities.get('priority', 'medium')}
- Issue Type: {entities.get('issue_type', 'General')}

Generate a JSON work order with these fields:
- title: Concise work order title
- description: Detailed description of the issue and required work
- priority: critical/high/medium/low
- estimated_hours: Estimated hours to complete
- required_skills: Array of required technician skills
- safety_notes: Important safety considerations
- parts_needed: Array of likely parts that may be needed

Return only valid JSON, no other text.
"""

        try:
            # Query LLaMA via Ollama
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "max_tokens": 500
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                llama_response = response.json()
                work_order_text = llama_response.get("response", "")
                
                # Try to parse JSON from LLaMA response
                try:
                    # Extract JSON from response (remove any extra text)
                    json_match = re.search(r'\{.*\}', work_order_text, re.DOTALL)
                    if json_match:
                        work_order = json.loads(json_match.group())
                        return work_order
                except json.JSONDecodeError:
                    pass
            
            # Fallback if LLaMA fails
            return self._generate_fallback_work_order(voice_text, entities)
            
        except Exception as e:
            logger.warning(f"LLaMA generation failed: {e}, using fallback")
            return self._generate_fallback_work_order(voice_text, entities)

    def _generate_fallback_work_order(self, voice_text: str, entities: Dict) -> Dict:
        """Generate work order when LLaMA is unavailable"""
        
        equipment = entities.get('equipment', 'Equipment')
        location = entities.get('location', 'Unknown Location')
        issue_type = entities.get('issue_type', 'maintenance')
        
        return {
            "title": f"{equipment.title()} {issue_type.title()} - {location.replace('_', ' ').title()}",
            "description": f"Voice-generated work order: {voice_text}. "
                          f"Issue reported with {equipment} in {location.replace('_', ' ')}.",
            "priority": entities.get('priority', 'medium'),
            "estimated_hours": 2.0,
            "required_skills": ["General Maintenance"],
            "safety_notes": "Follow standard safety procedures for equipment maintenance",
            "parts_needed": ["To be determined during inspection"],
            "ai_generated": True,
            "fallback_method": "rule_based"
        }

    async def _enhance_work_order(self, work_order: Dict, original_text: str) -> Dict:
        """Enhance work order with additional metadata and validation"""
        
        # Add metadata
        work_order.update({
            "created_via": "voice_command",
            "original_voice_text": original_text,
            "created_at": datetime.now().isoformat(),
            "status": "pending_assignment",
            "ai_confidence": 0.85 if work_order.get("ai_generated") else 0.95,
            "requires_review": work_order.get("ai_generated", False)
        })
        
        # Validate priority
        if work_order.get("priority") not in ["critical", "high", "medium", "low"]:
            work_order["priority"] = "medium"
        
        # Ensure estimated hours is reasonable
        if not isinstance(work_order.get("estimated_hours"), (int, float)):
            work_order["estimated_hours"] = 2.0
        elif work_order["estimated_hours"] > 40:
            work_order["estimated_hours"] = 8.0  # Cap at 8 hours
        
        # Add suggested technician assignment based on skills
        skills = work_order.get("required_skills", [])
        if "Electrical" in skills:
            work_order["suggested_technician_type"] = "Electrician"
        elif "HVAC" in skills:
            work_order["suggested_technician_type"] = "HVAC Technician"
        elif "Mechanical" in skills:
            work_order["suggested_technician_type"] = "Mechanical Technician"
        else:
            work_order["suggested_technician_type"] = "General Maintenance"
        
        return work_order

    async def get_voice_command_examples(self) -> List[str]:
        """Return example voice commands for user guidance"""
        return [
            "Create work order for leaking pump in Building A",
            "Emergency repair needed for broken elevator",
            "Schedule routine maintenance for HVAC system",
            "Motor in production area is making noise",
            "Urgent: Conveyor belt stopped working",
            "Inspect boiler in basement next week",
            "Replace filters in air conditioning unit",
            "Check compressor performance in warehouse"
        ]

    async def test_voice_processing(self) -> Dict:
        """Test the voice processing system"""
        test_commands = [
            "Emergency pump leak in Building A",
            "Motor maintenance needed in production",
            "Elevator inspection for next week"
        ]
        
        results = []
        for command in test_commands:
            result = await self.process_voice_command(command, "test_user")
            results.append({
                "command": command,
                "success": result["success"],
                "title": result.get("work_order", {}).get("title", "N/A")
            })
        
        return {
            "test_results": results,
            "ollama_available": await self._test_ollama_connection(),
            "system_status": "operational"
        }

    async def _test_ollama_connection(self) -> bool:
        """Test if Ollama is responding"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False


# FastAPI integration
async def process_voice_command_endpoint(voice_text: str) -> Dict:
    """FastAPI endpoint for voice command processing"""
    processor = VoiceWorkOrderProcessor()
    return await processor.process_voice_command(voice_text)


# Example usage and testing
if __name__ == "__main__":
    async def main():
        processor = VoiceWorkOrderProcessor()
        
        # Test commands
        test_commands = [
            "Emergency pump leak in Building A",
            "Schedule maintenance for motor in production area", 
            "Broken elevator needs immediate repair",
            "HVAC system making loud noise in office building"
        ]
        
        print("🎤 Voice Command Work Order System Test\n")
        
        for command in test_commands:
            print(f"Voice Command: '{command}'")
            result = await processor.process_voice_command(command)
            
            if result["success"]:
                wo = result["work_order"]
                print(f"✅ Work Order Created:")
                print(f"   Title: {wo['title']}")
                print(f"   Priority: {wo['priority']}")
                print(f"   Estimated Hours: {wo['estimated_hours']}")
                print(f"   Skills Required: {', '.join(wo['required_skills'])}")
            else:
                print(f"❌ Failed: {result['error']}")
            
            print("-" * 50)

    # Run test
    asyncio.run(main())