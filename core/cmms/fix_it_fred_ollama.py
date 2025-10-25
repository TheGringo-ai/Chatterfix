"""
Fix It Fred - Ollama Integration Module
Enhanced HVAC troubleshooting powered by local Ollama models
"""

import os
import httpx
from typing import Dict, Any, List
import re
import json
import logging

logger = logging.getLogger(__name__)


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
            logger.error(f"Error checking Ollama models: {e}")
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
        """Generate response from Ollama model with extended timeout"""
        try:
            # Extended timeout for first inference (can take 60-180 seconds)
            timeout = httpx.Timeout(300.0, connect=10.0)

            async with httpx.AsyncClient(timeout=timeout) as client:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 512  # Limit response length for speed
                    }
                }

                logger.info(f"Sending request to Ollama with model: {model}")
                response = await client.post(
                    f'{self.base_url}/generate',
                    json=payload
                )

                if response.status_code == 200:
                    data = response.json()
                    result = data.get('response', '')
                    logger.info(f"Ollama response received: {len(result)} chars")
                    return result
                else:
                    logger.error(f"Ollama returned status {response.status_code}: {response.text}")

        except httpx.TimeoutException as e:
            logger.error(f"Ollama request timed out: {e}")
        except Exception as e:
            logger.error(f"Error generating Ollama response: {e}")
        return None

    def extract_steps(self, response_text: str) -> List[str]:
        """Extract numbered steps from AI response"""
        steps = []

        # Match patterns like "1.", "1)", "Step 1:", etc.
        step_pattern = r'(?:^|\n)\s*(?:Step\s+)?(\d+)[\.\):\-]\s*(.+?)(?=\n\s*(?:Step\s+)?\d+[\.\):\-]|\n\n|$)'
        matches = re.findall(step_pattern, response_text, re.MULTILINE | re.DOTALL)

        for num, step_text in matches:
            steps.append(step_text.strip())

        # If no numbered steps found, try to extract bullet points
        if not steps:
            bullet_pattern = r'(?:^|\n)\s*[•\-\*]\s*(.+?)(?=\n\s*[•\-\*]|\n\n|$)'
            matches = re.findall(bullet_pattern, response_text, re.MULTILINE | re.DOTALL)
            steps = [match.strip() for match in matches if match.strip()]

        return steps

    def extract_time_estimate(self, response_text: str) -> str:
        """Extract time estimate from AI response"""
        # Look for patterns like "15-30 minutes", "1-2 hours", etc.
        time_pattern = r'(?:estimated?\s+time|time\s+to\s+resolve|duration)[:\s]*(\d+[\-\s]*\d*\s*(?:minutes?|hours?|mins?))'
        match = re.search(time_pattern, response_text, re.IGNORECASE)

        if match:
            return match.group(1)

        return "15-30 minutes"  # Default estimate

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

        return 0.80  # Default good confidence

    async def troubleshoot(self, equipment: str, issue_description: str) -> Dict[str, Any]:
        """Enhanced troubleshooting with Ollama-powered AI

        Args:
            equipment: Type of equipment (e.g., "HVAC", "Boiler", "Chiller")
            issue_description: Description of the issue

        Returns:
            Dict with troubleshooting steps, confidence, and metadata
        """
        logger.info(f"Troubleshooting request: {equipment} - {issue_description}")

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

        # Construct concise prompt for faster response
        prompt = f"""Fix It Fred HVAC Expert: Diagnose and fix this issue.

Equipment: {equipment}
Problem: {issue_description}

Provide:
1. Most likely cause
2. Troubleshooting steps (numbered list, 3-5 steps)
3. Estimated time
4. Safety warnings if needed

Be concise and actionable."""

        # Generate response
        response_text = await self.generate_response(model, prompt)

        if not response_text:
            return {
                "success": False,
                "error": "Failed to generate response",
                "message": "Ollama model did not return a response. Check logs.",
                "steps": [],
                "confidence": 0.0
            }

        # Extract structured data
        steps = self.extract_steps(response_text)
        time_estimate = self.extract_time_estimate(response_text)
        confidence = self.extract_confidence(response_text)

        # Check for safety warnings
        has_safety_warnings = bool(re.search(r'(?:safety|warning|caution|danger|power off|turn off)', response_text, re.IGNORECASE))

        return {
            "success": True,
            "equipment": equipment,
            "issue": issue_description,
            "model_used": model,
            "response": response_text,
            "steps": steps if steps else ["Check the response field for detailed guidance"],
            "time_estimate": time_estimate,
            "confidence": confidence,
            "has_safety_warnings": has_safety_warnings,
            "message": f"Fix It Fred analysis powered by {model}"
        }


# Global instance
fred_ollama = FixItFredOllama()
