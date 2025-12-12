"""
Fix-it-Fred AI Service
Provides AI-powered maintenance consulting using OpenAI
"""

import logging
import os
from typing import Dict, Any, Optional

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class FixItFredService:
    """AI-powered maintenance consultant service"""
    
    def __init__(self):
        """Initialize the Fix-it-Fred AI service"""
        self.client = None
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize OpenAI client with API key"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found - Fix-it-Fred will be in demo mode")
            return
            
        try:
            self.client = AsyncOpenAI(api_key=api_key)
            logger.info("✅ Fix-it-Fred AI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.client = None

    async def get_maintenance_solution(self, problem_description: str, 
                                     equipment_type: Optional[str] = None,
                                     priority: Optional[str] = None) -> Dict[str, Any]:
        """
        Get AI-powered maintenance solution from Fix-it-Fred
        
        Args:
            problem_description: Description of the maintenance issue
            equipment_type: Type of equipment (optional)
            priority: Issue priority level (optional)
            
        Returns:
            Dict containing Fred's analysis and recommendations
        """
        
        # Fallback response if OpenAI is not available
        if not self.client:
            return self._get_demo_response(problem_description)
        
        try:
            # Build context for the AI
            context_parts = [problem_description]
            if equipment_type:
                context_parts.append(f"Equipment: {equipment_type}")
            if priority:
                context_parts.append(f"Priority: {priority}")
            
            user_message = " | ".join(context_parts)
            
            # Call OpenAI API with Fix-it-Fred persona
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are Fix-it-Fred, a veteran industrial maintenance technician with 30+ years of experience. You provide:

SAFETY FIRST: Always start with safety considerations
PRACTICAL SOLUTIONS: Focus on actionable, real-world fixes
PREVENTIVE INSIGHTS: Include tips to prevent future issues
TOOL RECOMMENDATIONS: Suggest specific tools when relevant
ESCALATION GUIDANCE: Know when to call specialists

Your responses should be:
- Concise but thorough (2-3 paragraphs max)
- Written in plain language that both technicians and managers understand
- Focused on immediate solutions first, then long-term prevention
- Always include safety warnings when relevant

Format your response with:
1. IMMEDIATE ACTION (what to do right now)
2. ROOT CAUSE (likely causes)
3. PREVENTION (how to avoid this in future)"""
                    },
                    {
                        "role": "user", 
                        "content": user_message
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent technical advice
                max_tokens=500
            )
            
            fred_response = response.choices[0].message.content
            
            return {
                "success": True,
                "fred_says": fred_response,
                "problem": problem_description,
                "equipment_type": equipment_type,
                "priority": priority,
                "model_used": "gpt-4",
                "response_type": "ai_generated"
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return {
                "success": False,
                "error": f"Fred is temporarily unavailable: {str(e)}",
                "problem": problem_description,
                "response_type": "error"
            }
    
    def _get_demo_response(self, problem_description: str) -> Dict[str, Any]:
        """
        Provide demo response when OpenAI API is not available
        """
        demo_responses = {
            "conveyor": "🔧 IMMEDIATE ACTION: Stop the conveyor and check for loose bolts. ROOT CAUSE: Likely worn bearings or misaligned rollers. PREVENTION: Weekly vibration checks and monthly lubrication.",
            "pump": "🔧 IMMEDIATE ACTION: Check coolant levels and clean air filters. ROOT CAUSE: Blocked cooling passages or excessive load. PREVENTION: Regular filter changes and flow monitoring.",
            "motor": "🔧 IMMEDIATE ACTION: Check electrical connections and measure current draw. ROOT CAUSE: Possible overload or bearing wear. PREVENTION: Monthly thermal imaging and load monitoring.",
            "hydraulic": "🔧 IMMEDIATE ACTION: Check hydraulic fluid levels and inspect hoses for leaks. ROOT CAUSE: Low fluid or contaminated oil. PREVENTION: Regular fluid analysis and filter replacement."
        }
        
        # Simple keyword matching for demo
        problem_lower = problem_description.lower()
        response = "🔧 IMMEDIATE ACTION: Contact your maintenance supervisor for proper diagnosis. This appears to be a safety-critical issue that requires hands-on inspection."
        
        for keyword, demo_response in demo_responses.items():
            if keyword in problem_lower:
                response = demo_response
                break
        
        return {
            "success": True,
            "fred_says": f"[DEMO MODE] {response}",
            "problem": problem_description,
            "response_type": "demo",
            "note": "This is a demo response. Configure OPENAI_API_KEY for full AI functionality."
        }

# Global service instance
fix_it_fred_service = FixItFredService()

async def get_maintenance_solution(problem_description: str, 
                                 equipment_type: Optional[str] = None,
                                 priority: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to get maintenance solution from Fix-it-Fred
    """
    return await fix_it_fred_service.get_maintenance_solution(
        problem_description, equipment_type, priority
    )