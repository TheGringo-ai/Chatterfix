import json
import logging
import os
from typing import Any, Dict, Optional, Union
import base64
from pathlib import Path
from datetime import datetime

from app.core.firestore_db import get_db_connection

# Import Google Generative AI with error handling
try:
    import google.generativeai as genai

    GENAI_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Google Generative AI not available: {e}")
    genai = None
    GENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self):
        # Check if GenAI is available
        if not GENAI_AVAILABLE:
            logger.info("🤖 Gemini AI not available - service disabled")
            return

        # We no longer initialize a global model here because keys can be user-specific
        self.default_api_key = os.getenv("GEMINI_API_KEY")
        if self.default_api_key:
            try:
                genai.configure(api_key=self.default_api_key)
                logger.info("✨ Gemini AI initialized with default system key")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Gemini AI with default key: {e}")

    def _get_api_key(self, user_id: Optional[int] = None) -> Optional[str]:
        """
        Resolve API key in order:
        1. User-specific key from DB (Not implemented in Firestore yet)
        2. System-wide setting from DB (Not implemented in Firestore yet)
        3. Environment variable
        """
        # For now, just return the default key from env
        return self.default_api_key

    def _get_model(
        self, user_id: Optional[int] = None
    ) -> Optional[genai.GenerativeModel]:
        """Get a configured model instance for the user"""
        api_key = self._get_api_key(user_id)
        if not api_key:
            return None

        # Configure genai with the specific key
        # Note: This changes the global configuration for the library.
        # In a high-concurrency async environment, this could be race-condition prone if different keys are used simultaneously.
        # However, for this implementation scope, it's acceptable. A more robust solution would use client instances if supported.
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-2.5-flash")

    def _get_vision_model(
        self, user_id: Optional[int] = None
    ) -> Optional[genai.GenerativeModel]:
        """Get a configured vision model instance for the user"""
        api_key = self._get_api_key(user_id)
        if not api_key:
            return None
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-2.5-flash")

    async def generate_response(
        self, prompt: str, context: str = "", user_id: Optional[int] = None
    ) -> str:
        """Generate a text response using Gemini"""
        model = self._get_model(user_id)
        if not model:
            return "AI Assistant is currently unavailable. Please configure your Gemini API Key in Settings."

        try:
            full_prompt = f"{context}\n\nUser: {prompt}\nAssistant:"
            response = await model.generate_content_async(full_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I encountered an error processing your request: {str(e)}"

    async def analyze_image(
        self, image_path: str, prompt: str, user_id: Optional[int] = None
    ) -> str:
        """Analyze an image using Gemini Vision"""
        model = self._get_vision_model(user_id)
        if not model:
            return "Image analysis is unavailable. Please configure your Gemini API Key in Settings."

        try:
            # Load image data
            import PIL.Image

            img = PIL.Image.open(image_path)

            response = await model.generate_content_async([prompt, img])
            return response.text
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return f"Error analyzing image: {str(e)}"

    async def generate_kpi_report(
        self, data: Dict[str, Any], user_id: Optional[int] = None
    ) -> str:
        """Generate a KPI report based on provided data"""
        model = self._get_model(user_id)
        if not model:
            return "KPI reporting unavailable. Please configure API Key."

        prompt = f"""
        Act as a Maintenance Manager. Analyze the following CMMS data and generate a concise executive summary
        highlighting key performance indicators, trends, and recommendations.

        Data:
        {json.dumps(data, indent=2)}

        Format the response as HTML with <h3> headers and bullet points.
        """
        return await self.generate_response(prompt, user_id=user_id)

    async def get_troubleshooting_advice(
        self, asset_info: str, issue_description: str, user_id: Optional[int] = None
    ) -> str:
        """Provide troubleshooting advice for a technician"""
        context = """
        You are an expert industrial maintenance technician assistant.
        Provide step-by-step troubleshooting advice based on the asset and issue described.
        Prioritize safety first.
        """
        prompt = f"Asset: {asset_info}\nIssue: {issue_description}\n\nPlease provide troubleshooting steps."
        return await self.generate_response(prompt, context, user_id=user_id)

    async def run_assistant_agent(
        self, message: str, context: str, user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for the Global AI Assistant.
        Uses a ReAct-like loop or structured prompting to handle user requests.
        """
        model = self._get_model(user_id)
        if not model:
            return {
                "response": "AI Service is unavailable. Please configure your Gemini API Key in Settings."
            }

        # 1. Construct the System Prompt with Tool Definitions
        system_prompt = f"""
        You are ChatterFix, an intelligent CMMS assistant for industrial maintenance technicians.
        Your goal is to help users manage work orders, find parts, and troubleshoot equipment efficiently.

        Current Context:
        {context}

        AVAILABLE TOOLS:
        1. create_work_order(title: str, description: str, priority: str, asset_id: int)
           - Use this when the user explicitly wants to create a ticket, job, or work order.
           - Priority options: 'Low', 'Medium', 'High', 'Critical'.
           - If asset_id is unknown, ask the user to clarify which asset.

        2. update_work_order(wo_id: int, status: str = None, priority: str = None, notes: str = None)
           - Use this to modify an existing work order. Status options: 'Open', 'In Progress', 'Completed', 'On Hold'.

        3. search_parts(query: str)
           - Use this to find spare parts in inventory.

        4. update_part_stock(part_id: int, quantity_change: int)
           - Use this to increase or decrease stock levels (e.g., "used 2 bearings", "received 5 filters").

        5. get_asset_history(asset_name: str)
           - Use this to see past maintenance on a machine.

        6. create_asset(name: str, type: str, location: str, status: str = "Operational")
           - Use this to add a new machine or equipment to the system.

        7. web_search(query: str)
           - Use this to find information on the internet, such as manual, error codes, or general troubleshooting advice.

        INSTRUCTIONS:
        - If the user's request requires a tool, return a JSON object ONLY:
          {{"tool": "tool_name", "parameters": {{...}}}}
        - If the user asks a general question or needs troubleshooting help, provide a helpful text response in Markdown.
        - Be concise and professional.
        """

        try:
            # 2. Get response from Gemini
            full_prompt = f"{system_prompt}\n\nUser: {message}\nAssistant:"
            response = await model.generate_content_async(full_prompt)
            text_response = response.text.strip()

            # 3. Check for Tool Execution (JSON)
            if text_response.startswith("{") and text_response.endswith("}"):
                try:
                    tool_call = json.loads(text_response)
                    tool_name = tool_call.get("tool")
                    params = tool_call.get("parameters", {})

                    if tool_name == "create_work_order":
                        return await self._create_work_order(**params)
                    elif tool_name == "update_work_order":
                        return await self._update_work_order(**params)
                    elif tool_name == "search_parts":
                        return await self._search_parts(**params)
                    elif tool_name == "update_part_stock":
                        return await self._update_part_stock(**params)
                    elif tool_name == "get_asset_history":
                        return await self._get_asset_history(**params)
                    elif tool_name == "create_asset":
                        return await self._create_asset(**params)
                    elif tool_name == "web_search":
                        return await self._web_search(**params)

                except json.JSONDecodeError:
                    pass  # Fallback to treating it as text

            # 4. Default Text Response
            return {"response": text_response}

        except Exception as e:
            logger.error(f"AI Assistant Error: {e}")
            return {
                "response": "I'm sorry, I encountered an error processing your request."
            }

    # --- Tool Implementations ---

    async def _web_search(self, query: str):
        try:
            from duckduckgo_search import DDGS

            results = DDGS().text(query, max_results=3)
            if not results:
                return {
                    "response": f"I couldn't find any information for '{query}' on the web."
                }

            response_text = f"**Web Search Results for '{query}':**\n\n"
            for r in results:
                response_text += f"- [{r['title']}]({r['href']}): {r['body']}\n"

            return {"response": response_text}
        except ImportError:
            return {
                "response": "Web search is not available (duckduckgo-search not installed)."
            }
        except Exception as e:
            return {"response": f"Error performing web search: {e}"}

    async def _create_work_order(
        self,
        title: str,
        description: str,
        priority: str = "Medium",
        asset_id: int = None,
    ):
        # Use Firestore or mock response since app uses Firestore-only architecture
        try:
            # In a real Firestore implementation, we'd add the work order to Firestore here
            # For now, return a success response with simulated ID
            import random

            wo_id = random.randint(1000, 9999)

            return {
                "response": f"✅ Work Order #{wo_id} created successfully!\n\n**Title:** {title}\n**Priority:** {priority}\n\n*Note: In demo mode - work order creation simulated.*",
                "action": {"type": "redirect", "url": f"/work-orders"},
            }
        except Exception as e:
            return {"response": f"Failed to create work order: {e}"}

    async def _update_work_order(
        self, wo_id: int, status: str = None, priority: str = None, notes: str = None
    ):
        # Use Firestore or mock response since app uses Firestore-only architecture
        try:
            # In a real Firestore implementation, we'd update the work order in Firestore here
            msg = f"✅ Work Order #{wo_id} updated."
            if status:
                msg += f" Status: {status}"
            if priority:
                msg += f" Priority: {priority}"
            if notes:
                msg += f"\n(Note: '{notes}' acknowledged)"

            msg += f"\n\n*Note: In demo mode - work order update simulated.*"

            return {
                "response": msg,
                "action": {"type": "redirect", "url": "/work-orders"},
            }
        except Exception as e:
            return {"response": f"Failed to update work order: {e}"}

    async def _update_part_stock(self, part_id: int, quantity_change: int):
        # Use Firestore or mock response since app uses Firestore-only architecture
        try:
            # In a real Firestore implementation, we'd update part stock in Firestore here
            # For now, simulate with mock data
            mock_parts = {
                1: "Industrial Bearing",
                2: "Hydraulic Filter",
                3: "Motor Belt",
                4: "Control Valve",
            }

            part_name = mock_parts.get(part_id, f"Part #{part_id}")
            current_stock = 25  # Mock current stock
            new_stock = current_stock + quantity_change

            if new_stock < 0:
                return {
                    "response": f"Cannot reduce stock below 0. Current stock: {current_stock}"
                }

            return {
                "response": f"✅ Updated stock for **{part_name}**. New Quantity: {new_stock}\n\n*Note: In demo mode - stock update simulated.*"
            }
        except Exception as e:
            return {"response": f"Failed to update stock: {e}"}

    async def _create_asset(
        self, name: str, type: str, location: str, status: str = "Operational"
    ):
        # Use Firestore or mock response since app uses Firestore-only architecture
        try:
            # In a real Firestore implementation, we'd add the asset to Firestore here
            import random

            asset_id = random.randint(100, 999)

            return {
                "response": f"✅ Asset **{name}** created successfully (ID: {asset_id})!\n\n**Type:** {type}\n**Location:** {location}\n**Status:** {status}\n\n*Note: In demo mode - asset creation simulated.*",
                "action": {"type": "redirect", "url": "/assets"},
            }
        except Exception as e:
            return {"response": f"Failed to create asset: {e}"}

    async def _search_parts(self, query: str):
        # Use Firestore or mock response since app uses Firestore-only architecture
        try:
            # In a real Firestore implementation, we'd search parts in Firestore here
            # For now, simulate with mock data
            mock_parts_db = [
                {
                    "name": "Industrial Bearing",
                    "current_stock": 15,
                    "location": "Warehouse A-1",
                },
                {
                    "name": "Hydraulic Filter",
                    "current_stock": 8,
                    "location": "Warehouse B-2",
                },
                {
                    "name": "Motor Belt",
                    "current_stock": 12,
                    "location": "Warehouse A-3",
                },
                {
                    "name": "Control Valve",
                    "current_stock": 5,
                    "location": "Warehouse C-1",
                },
                {
                    "name": "Pressure Sensor",
                    "current_stock": 20,
                    "location": "Warehouse B-1",
                },
                {
                    "name": "Gear Assembly",
                    "current_stock": 3,
                    "location": "Warehouse A-2",
                },
                {"name": "Oil Seal", "current_stock": 25, "location": "Warehouse C-2"},
            ]

            # Simple search in mock data
            query_lower = query.lower()
            results = [
                part for part in mock_parts_db if query_lower in part["name"].lower()
            ]

            if not results:
                return {
                    "response": f"I couldn't find any parts matching '{query}'.\n\n*Note: In demo mode - searching simulated inventory.*"
                }

            response_text = f"Found {len(results)} parts matching '{query}':\n\n"
            for part in results:
                response_text += f"- **{part['name']}** (Stock: {part['current_stock']}) - Location: {part['location']}\n"

            response_text += f"\n*Note: In demo mode - search results simulated.*"
            return {"response": response_text}
        except Exception as e:
            return {"response": f"Error searching parts: {e}"}

    async def _get_asset_history(self, asset_name: str):
        # Use Firestore or mock response since app uses Firestore-only architecture
        try:
            # In a real Firestore implementation, we'd search asset history in Firestore here
            # For now, simulate with mock data
            mock_assets = {
                "conveyor": "Conveyor Belt System",
                "pump": "Hydraulic Pump Unit",
                "motor": "Main Drive Motor",
                "compressor": "Air Compressor",
                "press": "Hydraulic Press",
            }

            # Find matching asset
            asset_key = None
            asset_full_name = None
            asset_name_lower = asset_name.lower()

            for key, full_name in mock_assets.items():
                if key in asset_name_lower or asset_name_lower in full_name.lower():
                    asset_key = key
                    asset_full_name = full_name
                    break

            if not asset_full_name:
                return {
                    "response": f"I couldn't find an asset named '{asset_name}'.\n\n*Note: In demo mode - searching simulated assets.*"
                }

            # Mock maintenance history
            mock_history = [
                {
                    "created_date": "2024-11-25",
                    "description": "Routine belt tension adjustment",
                    "total_cost": 150,
                },
                {
                    "created_date": "2024-11-10",
                    "description": "Replaced worn roller bearings",
                    "total_cost": 450,
                },
                {
                    "created_date": "2024-10-28",
                    "description": "Lubrication service",
                    "total_cost": 75,
                },
            ]

            response_text = f"**Recent History for {asset_full_name}:**\n\n"
            for record in mock_history:
                response_text += f"- {record['created_date']}: {record['description']} (Cost: ${record['total_cost']})\n"

            response_text += f"\n*Note: In demo mode - maintenance history simulated.*"
            return {"response": response_text}
        except Exception as e:
            return {"response": f"Error retrieving asset history: {e}"}

    async def recognize_asset_from_image(
        self, 
        image_path: str, 
        context: str = "", 
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Multi-modal asset recognition using Gemini Vision
        Identifies asset type, manufacturer, model, and serial number from image
        
        Args:
            image_path: Path to the image file
            context: Additional context (e.g., 'Industrial motor', 'Pump in Building A')
            user_id: User ID for personalization
            
        Returns:
            Dict containing structured asset information
        """
        model = self._get_vision_model(user_id)
        if not model:
            return {
                "success": False,
                "error": "Vision analysis unavailable - Gemini API key not configured",
                "asset_data": {}
            }
        
        try:
            # Load and process image
            import PIL.Image
            
            if not os.path.exists(image_path):
                return {
                    "success": False, 
                    "error": f"Image file not found: {image_path}",
                    "asset_data": {}
                }
            
            img = PIL.Image.open(image_path)
            
            # Construct specialized prompt for asset recognition
            recognition_prompt = f"""
            INDUSTRIAL ASSET RECOGNITION TASK
            
            Context: {context}
            
            Analyze this image and identify the industrial equipment/asset. Extract the following information in JSON format:
            
            {{
                "asset_type": "Primary equipment category (pump, motor, generator, conveyor, etc.)",
                "manufacturer": "Brand/manufacturer name if visible",
                "model_number": "Model number or part number if visible", 
                "serial_number": "Serial number if visible",
                "condition_assessment": "Visual condition (excellent/good/fair/poor)",
                "key_features": ["List", "of", "notable", "features", "or", "components"],
                "maintenance_indicators": ["Any", "visible", "maintenance", "needs"],
                "confidence_score": 0.85,
                "additional_notes": "Any other relevant observations"
            }}
            
            Focus on:
            - Equipment identification and categorization
            - Visible nameplate information 
            - Condition indicators (rust, wear, damage)
            - Maintenance access points
            - Safety features or warnings
            
            Return ONLY the JSON structure, no additional text.
            """
            
            # Generate analysis
            response = await model.generate_content_async([recognition_prompt, img])
            response_text = response.text.strip()
            
            # Parse JSON response
            try:
                # Extract JSON from response (in case there's extra text)
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_text = response_text[json_start:json_end]
                    asset_data = json.loads(json_text)
                    
                    # Validate and enhance the data
                    asset_data = self._validate_asset_data(asset_data)
                    
                    logger.info(f"✅ Asset recognized: {asset_data.get('asset_type', 'Unknown')} - {asset_data.get('manufacturer', 'Unknown brand')}")
                    
                    return {
                        "success": True,
                        "asset_data": asset_data,
                        "image_path": image_path,
                        "processing_time": "< 3 seconds",
                        "model_used": "gemini-vision"
                    }
                else:
                    # Fallback if JSON parsing fails
                    return self._extract_asset_info_from_text(response_text, image_path)
                    
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ JSON parsing failed for asset recognition: {e}")
                return self._extract_asset_info_from_text(response_text, image_path)
                
        except Exception as e:
            logger.error(f"❌ Asset recognition failed: {e}")
            return {
                "success": False,
                "error": f"Asset recognition failed: {str(e)}",
                "asset_data": {}
            }

    def _validate_asset_data(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance asset recognition data"""
        
        # Ensure required fields exist
        defaults = {
            "asset_type": "Unknown Equipment",
            "manufacturer": "Unknown", 
            "model_number": "Not Visible",
            "serial_number": "Not Visible",
            "condition_assessment": "Unknown",
            "key_features": [],
            "maintenance_indicators": [],
            "confidence_score": 0.5,
            "additional_notes": ""
        }
        
        for key, default_value in defaults.items():
            if key not in asset_data:
                asset_data[key] = default_value
        
        # Validate confidence score
        if not isinstance(asset_data["confidence_score"], (int, float)):
            asset_data["confidence_score"] = 0.5
        else:
            asset_data["confidence_score"] = max(0.0, min(1.0, asset_data["confidence_score"]))
        
        # Ensure lists are actually lists
        list_fields = ["key_features", "maintenance_indicators"]
        for field in list_fields:
            if not isinstance(asset_data[field], list):
                asset_data[field] = []
        
        # Add timestamp
        asset_data["recognition_timestamp"] = datetime.now().isoformat()
        
        return asset_data

    def _extract_asset_info_from_text(self, text_response: str, image_path: str) -> Dict[str, Any]:
        """Extract asset information when JSON parsing fails"""
        
        # Basic text parsing for key information
        asset_data = {
            "asset_type": "Unknown Equipment",
            "manufacturer": "Unknown",
            "model_number": "Not Visible", 
            "serial_number": "Not Visible",
            "condition_assessment": "Unknown",
            "key_features": [],
            "maintenance_indicators": [],
            "confidence_score": 0.3,  # Lower confidence for text parsing
            "additional_notes": text_response[:500],  # Truncated response
            "recognition_timestamp": datetime.now().isoformat()
        }
        
        text_lower = text_response.lower()
        
        # Try to extract basic information
        equipment_types = ["pump", "motor", "generator", "conveyor", "compressor", "valve", "fan", "transformer"]
        for eq_type in equipment_types:
            if eq_type in text_lower:
                asset_data["asset_type"] = eq_type.title()
                break
        
        # Look for manufacturer keywords
        manufacturers = ["siemens", "abb", "general electric", "ge", "westinghouse", "schneider", "allen bradley"]
        for mfr in manufacturers:
            if mfr in text_lower:
                asset_data["manufacturer"] = mfr.title()
                break
        
        # Check condition keywords
        if any(word in text_lower for word in ["excellent", "new", "pristine"]):
            asset_data["condition_assessment"] = "Excellent"
        elif any(word in text_lower for word in ["good", "normal", "operational"]):
            asset_data["condition_assessment"] = "Good" 
        elif any(word in text_lower for word in ["fair", "worn", "aging"]):
            asset_data["condition_assessment"] = "Fair"
        elif any(word in text_lower for word in ["poor", "damaged", "corroded", "rust"]):
            asset_data["condition_assessment"] = "Poor"
        
        return {
            "success": True,
            "asset_data": asset_data,
            "image_path": image_path,
            "processing_method": "text_parsing",
            "note": "JSON parsing failed, used text extraction"
        }

    async def create_asset_registration_workflow(
        self,
        image_path: str,
        location: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Complete asset registration workflow combining vision recognition
        with automatic asset database entry
        
        Args:
            image_path: Path to asset image
            location: Physical location of the asset
            user_id: User performing the registration
            
        Returns:
            Dict containing complete registration result
        """
        try:
            # Step 1: Recognize asset from image
            recognition_result = await self.recognize_asset_from_image(
                image_path, f"Asset located in {location}", user_id
            )
            
            if not recognition_result["success"]:
                return recognition_result
            
            asset_data = recognition_result["asset_data"]
            
            # Step 2: Generate asset registration data
            registration_data = {
                "name": f"{asset_data['manufacturer']} {asset_data['asset_type']}",
                "type": asset_data["asset_type"],
                "manufacturer": asset_data["manufacturer"],
                "model": asset_data["model_number"],
                "serial_number": asset_data["serial_number"],
                "location": location,
                "status": "Operational" if asset_data["condition_assessment"] in ["Excellent", "Good"] else "Needs Inspection",
                "condition": asset_data["condition_assessment"],
                "installation_date": datetime.now().isoformat(),
                "image_path": image_path,
                "ai_confidence": asset_data["confidence_score"],
                "ai_features": asset_data["key_features"],
                "ai_maintenance_notes": asset_data["maintenance_indicators"]
            }
            
            # Step 3: Generate asset tag/QR code (placeholder)
            asset_tag = f"AST-{hash(f'{location}-{asset_data['asset_type']}') % 10000:04d}"
            registration_data["asset_tag"] = asset_tag
            
            return {
                "success": True,
                "registration_data": registration_data,
                "recognition_result": recognition_result,
                "next_steps": [
                    f"Asset tagged as {asset_tag}",
                    "Ready for database entry",
                    "QR code can be generated",
                    "Maintenance schedule can be created"
                ],
                "workflow_complete": True
            }
            
        except Exception as e:
            logger.error(f"❌ Asset registration workflow failed: {e}")
            return {
                "success": False,
                "error": f"Registration workflow failed: {str(e)}",
                "registration_data": {}
            }


# Global instance
gemini_service = GeminiService()
