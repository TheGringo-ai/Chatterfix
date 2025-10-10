"""
Fix It Fred - Ollama Integration Module
Enhanced HVAC troubleshooting powered by local Ollama models
"""

import os
import httpx
from typing import Dict, Any, List
import re
import json


class FixItFredOllama:
    """Enhanced Fix It Fred with local Ollama AI integration"""

    def __init__(self):
        self.ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        self.base_url = f'{self.ollama_host}/api'

    async def get_available_models(self) -> List[str]:
        """Check which Ollama models are available"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f'{self.base_url}/tags')
                if response.status_code == 200:
                    data = response.json()
                    return [model['name'] for model in data.get('models', [])]
        except Exception as e:
            print(f"Error checking Ollama models: {e}")
        return []

    async def select_best_model(self) -> str:
        """Select the best available model for troubleshooting

        Preference order:
        1. mistral:7b - Faster, excellent for structured responses
        2. llama3:8b - More capable, better for complex reasoning
        """
        available = await self.get_available_models()

        # Preference: Mistral 7B (faster) > Llama3 8B (more capable)
        if 'mistral:7b' in available:
            return 'mistral:7b'
        elif 'llama3:8b' in available:
            return 'llama3:8b'
        elif 'mistral' in available:
            return 'mistral'
        elif 'llama3' in available:
            return 'llama3'

        # Fallback to first available model
        if available:
            return available[0]

        return None

    async def generate_response(self, model: str, prompt: str) -> str:
        """Generate response from Ollama model"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }

                response = await client.post(
                    f'{self.base_url}/generate',
                    json=payload
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get('response', '')
        except Exception as e:
            print(f"Error generating Ollama response: {e}")
        return None

    def extract_steps(self, response_text: str) -> List[str]:
        """Extract numbered steps from AI response"""
        steps = []

        # Match patterns like "1.", "1)", "Step 1:", etc.
        step_pattern = r'(?:^|\n)\s*(?:Step\s+)?(\d+)[\.\):\-]\s*(.+?)(?=\n\s*(?:Step\s+)?\d+[\.\):\-]|\n\n|$)'
        matches = re.findall(step_pattern, response_text, re.MULTILINE | re.DOTALL)

        for num, step_text in matches:
            steps.append(step_text.strip())

        return steps

    def extract_time_estimate(self, response_text: str) -> str:
        """Extract time estimate from AI response"""
        # Look for patterns like "15-30 minutes", "1-2 hours", etc.
        time_pattern = r'(?:estimated?\s+time|time\s+to\s+resolve|duration)[:\s]*(\d+[\-\s]*\d*\s*(?:minutes?|hours?|mins?))'
        match = re.search(time_pattern, response_text, re.IGNORECASE)

        if match:
            return match.group(1)

        return "Unknown"

    def extract_confidence(self, response_text: str) -> float:
        """Extract confidence score from AI response"""
        # Look for patterns like "Confidence: 0.85", "85% confident", etc.
        confidence_pattern = r'confidence[:\s]*(?:(\d+)%|(\d*\.\d+))'
        match = re.search(confidence_pattern, response_text, re.IGNORECASE)

        if match:
            if match.group(1):  # Percentage format
                return float(match.group(1)) / 100
            elif match.group(2):  # Decimal format
                return float(match.group(2))

        return 0.75  # Default medium-high confidence

    async def troubleshoot(self, equipment: str, issue_description: str) -> Dict[str, Any]:
        """Enhanced troubleshooting with Ollama-powered AI

        Args:
            equipment: Type of equipment (e.g., "HVAC", "Boiler", "Chiller")
            issue_description: Description of the issue

        Returns:
            Dict with troubleshooting steps, confidence, and metadata
        """
        # Select best available model
        model = await self.select_best_model()

        if not model:
            return {
                "success": False,
                "error": "No Ollama models available",
                "message": "Please ensure Ollama is running with at least one model installed",
                "steps": [],
                "confidence": 0.0
            }

        # Construct detailed prompt
        prompt = f"""You are Fix It Fred, an expert HVAC and maintenance AI assistant with decades of field experience.

Equipment Type: {equipment}
Issue Description: {issue_description}

Provide a detailed troubleshooting response with the following structure:

1. MOST LIKELY CAUSE: Brief explanation of the root cause

2. TROUBLESHOOTING STEPS: Numbered list of specific steps a technician should follow
   - Be precise and actionable
   - Include safety checks first
   - Order steps from most likely to least likely causes

3. ESTIMATED TIME: How long this will take to diagnose and fix

4. SAFETY WARNINGS: Any important safety considerations

5. CONFIDENCE: Your confidence level (0.0 to 1.0) in this diagnosis

Format your response clearly with numbered steps that a technician can follow immediately."""

        # Generate response
        response_text = await self.generate_response(model, prompt)

        if not response_text:
            return {
                "success": False,
                "error": "Failed to generate response",
                "message": "Ollama model did not return a response",
                "steps": [],
                "confidence": 0.0
            }

        # Extract structured data
        steps = self.extract_steps(response_text)
        time_estimate = self.extract_time_estimate(response_text)
        confidence = self.extract_confidence(response_text)

        # Check for safety warnings
        has_safety_warnings = bool(re.search(r'(?:safety|warning|caution|danger)', response_text, re.IGNORECASE))

        return {
            "success": True,
            "equipment": equipment,
            "issue": issue_description,
            "model_used": model,
            "response": response_text,
            "steps": steps,
            "time_estimate": time_estimate,
            "confidence": confidence,
            "has_safety_warnings": has_safety_warnings,
            "message": f"Fix It Fred analysis powered by {model}"
        }


# Global instance
fred_ollama = FixItFredOllama()
