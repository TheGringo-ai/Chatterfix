import json
import logging
import os
from typing import Any, Dict, Optional

from openai import OpenAI

from app.services.work_order_service import work_order_service
from app.services.asset_service import asset_service
from app.services.part_service import part_service

logger = logging.getLogger(__name__)


class OpenAIService:
    def __init__(self):
        self.default_api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.default_api_key) if self.default_api_key else None
        self.available = bool(self.client)
        if self.available:
            logger.info("✨ OpenAI initialized with API key")
        else:
            logger.info("ℹ️ OpenAI API key not configured - service will use fallback mode")

    def is_available(self) -> bool:
        return self.available

    def _get_client(self, user_id: Optional[str] = None) -> Optional[OpenAI]:
        # In a real app, user-specific keys could be fetched here
        return self.client

    async def generate_response(
        self, prompt: str, context: str = "", user_id: Optional[str] = None
    ) -> str:
        """Generate a text response using OpenAI"""
        client = self._get_client(user_id)
        if not client:
            return "AI Assistant is currently unavailable. Please configure your OpenAI API Key in Settings."
        # ... (rest of the method is okay)

    # ... (other AI methods like analyze_image, etc. are okay)

    async def run_assistant_agent(
        self, message: str, context: str, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for the Global AI Assistant.
        Uses OpenAI to handle user requests with tool calling capabilities.
        """
        client = self._get_client(user_id)
        if not client:
            return {"response": "AI Service is unavailable. Please configure your OpenAI API Key."}

        # Simplified system prompt for brevity
        system_prompt = "You are ChatterFix, an intelligent CMMS assistant."
        
        try:
            # This is a simplified example. A real implementation would use OpenAI's tool calling features.
            # For now, we simulate the old logic of parsing JSON from the response.
            # ... (existing logic for calling OpenAI and parsing response)

            # Let's assume the response is a tool call for creating a work order
            # In a real scenario, this would come from the model
            if "create work order" in message.lower():
                # Dummy data extraction from message
                params = {"title": "New Work Order from AI", "description": message, "priority": "Medium"}
                return await self._create_work_order(**params)

            return {"response": "I am the OpenAI assistant."}

        except Exception as e:
            logger.error(f"AI Assistant Error: {e}")
            return {"response": "I'm sorry, I encountered an error."}


    # --- Tool Implementations (Refactored to use services) ---

    async def _create_work_order(self, title: str, description: str, priority: str = "Medium", asset_id: str = None) -> Dict[str, Any]:
        try:
            wo_data = {
                "title": title, "description": description, "priority": priority, 
                "asset_id": asset_id, "status": "Open", "work_order_type": "Corrective"
            }
            wo_id = await work_order_service.create_work_order(wo_data)
            return {"response": f"✅ Work Order #{wo_id} created successfully!", "action": {"type": "redirect", "url": f"/work-orders/{wo_id}"}}
        except Exception as e:
            return {"response": f"Failed to create work order: {e}"}

    async def _update_work_order(self, wo_id: str, status: Optional[str] = None, priority: Optional[str] = None, notes: Optional[str] = None) -> Dict[str, Any]:
        try:
            update_data = {}
            if status: update_data["status"] = status
            if priority: update_data["priority"] = priority
            if notes: update_data["notes"] = notes # Assuming 'notes' is a field in the model

            if update_data:
                await work_order_service.update_work_order(wo_id, update_data)
            
            return {"response": f"✅ Work Order #{wo_id} updated.", "action": {"type": "redirect", "url": f"/work-orders/{wo_id}"}}
        except Exception as e:
            return {"response": f"Failed to update work order: {e}"}

    async def _update_part_stock(self, part_id: str, quantity_change: int) -> Dict[str, Any]:
        try:
            success = await part_service.update_part_stock(part_id, quantity_change)
            if success:
                return {"response": "✅ Part stock updated successfully."}
            else:
                return {"response": "Failed to update part stock. Part not found or insufficient stock."}
        except Exception as e:
            return {"response": f"Failed to update part stock: {e}"}

    async def _create_asset(self, name: str, type: str, location: str, status: str = "Active") -> Dict[str, Any]:
        try:
            asset_data = {"name": name, "type": type, "location": location, "status": status}
            asset_id = await asset_service.create_asset(asset_data)
            return {"response": f"✅ Asset **{name}** created successfully (ID: {asset_id})!", "action": {"type": "redirect", "url": f"/assets/{asset_id}"}}
        except Exception as e:
            return {"response": f"Failed to create asset: {e}"}

    async def _search_parts(self, query: str) -> Dict[str, Any]:
        try:
            parts = await part_service.get_parts() # Simplified search
            results = [p for p in parts if query.lower() in p.name.lower()]
            
            if not results:
                return {"response": f"I couldn't find any parts matching '{query}'."}
            
            response_text = f"Found {len(results)} parts matching '{query}':\n\n"
            for part in results:
                response_text += f"- **{part.name}** (Stock: {part.current_stock}) - Location: {part.location}\n"
            return {"response": response_text}
        except Exception as e:
            return {"response": f"Error searching parts: {e}"}

    async def _get_asset_history(self, asset_name: str) -> Dict[str, Any]:
        # TODO: Implement get_asset_history in AssetService
        return {"response": f"Maintenance history for '{asset_name}' is not yet available via this tool."}

# Global instance
openai_service = OpenAIService()
