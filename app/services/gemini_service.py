import json
import logging
import os
from typing import Any, Dict, Optional

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
        return genai.GenerativeModel("gemini-1.5-flash")

    def _get_vision_model(
        self, user_id: Optional[int] = None
    ) -> Optional[genai.GenerativeModel]:
        """Get a configured vision model instance for the user"""
        api_key = self._get_api_key(user_id)
        if not api_key:
            return None
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-1.5-flash")

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
        # from app.core.database import get_db_connection

        conn = get_db_connection()
        try:
            # If asset_id is missing, try to find it by name in description or just set null
            # For now, we'll assume the AI extracted it or we proceed without it

            cursor = conn.execute(
                """
                INSERT INTO work_orders (title, description, priority, asset_id, status, created_date)
                VALUES (?, ?, ?, ?, 'Open', datetime('now'))
            """,
                (title, description, priority, asset_id),
            )
            conn.commit()
            wo_id = cursor.lastrowid

            return {
                "response": f"✅ Work Order #{wo_id} created successfully!\n\n**Title:** {title}\n**Priority:** {priority}",
                "action": {"type": "redirect", "url": f"/work-orders/{wo_id}"},
            }
        except Exception as e:
            return {"response": f"Failed to create work order: {e}"}
        finally:
            conn.close()

    async def _update_work_order(
        self, wo_id: int, status: str = None, priority: str = None, notes: str = None
    ):
        # from app.core.database import get_db_connection

        conn = get_db_connection()
        try:
            updates = []
            params = []
            if status:
                updates.append("status = ?")
                params.append(status)
            if priority:
                updates.append("priority = ?")
                params.append(priority)

            if updates:
                params.append(wo_id)
                conn.execute(
                    f"UPDATE work_orders SET {', '.join(updates)} WHERE id = ?", params
                )
                conn.commit()

            msg = f"✅ Work Order #{wo_id} updated."
            if notes:
                # In a real app, we'd add this to a notes table. For now, we'll just append to description or ignore.
                msg += f"\n(Note: '{notes}' was acknowledged but not saved to DB in this demo version)"

            return {
                "response": msg,
                "action": {"type": "redirect", "url": f"/work-orders/{wo_id}"},
            }
        except Exception as e:
            return {"response": f"Failed to update work order: {e}"}
        finally:
            conn.close()

    async def _update_part_stock(self, part_id: int, quantity_change: int):
        # from app.core.database import get_db_connection

        conn = get_db_connection()
        try:
            # Check current stock
            part = conn.execute(
                "SELECT name, current_stock FROM parts WHERE id = ?", (part_id,)
            ).fetchone()
            if not part:
                return {"response": f"Part #{part_id} not found."}

            new_stock = part["current_stock"] + quantity_change
            if new_stock < 0:
                return {
                    "response": f"Cannot reduce stock below 0. Current stock: {part['current_stock']}"
                }

            conn.execute(
                "UPDATE parts SET current_stock = ? WHERE id = ?", (new_stock, part_id)
            )
            conn.commit()

            return {
                "response": f"✅ Updated stock for **{part['name']}**. New Quantity: {new_stock}"
            }
        except Exception as e:
            return {"response": f"Failed to update stock: {e}"}
        finally:
            conn.close()

    async def _create_asset(
        self, name: str, type: str, location: str, status: str = "Operational"
    ):
        # from app.core.database import get_db_connection

        conn = get_db_connection()
        try:
            cursor = conn.execute(
                """
                INSERT INTO assets (name, type, location, status, created_date)
                VALUES (?, ?, ?, ?, datetime('now'))
            """,
                (name, type, location, status),
            )
            conn.commit()
            asset_id = cursor.lastrowid

            return {
                "response": f"✅ Asset **{name}** created successfully (ID: {asset_id})!",
                "action": {"type": "redirect", "url": f"/assets/{asset_id}"},
            }
        except Exception as e:
            return {"response": f"Failed to create asset: {e}"}
        finally:
            conn.close()

    async def _search_parts(self, query: str):
        # from app.core.database import get_db_connection

        conn = get_db_connection()
        results = conn.execute(
            """
            SELECT * FROM parts
            WHERE name LIKE ? OR part_number LIKE ? OR description LIKE ?
            LIMIT 5
        """,
            (f"%{query}%", f"%{query}%", f"%{query}%"),
        ).fetchall()
        conn.close()

        if not results:
            return {"response": f"I couldn't find any parts matching '{query}'."}

        response_text = f"Found {len(results)} parts matching '{query}':\n\n"
        for part in results:
            response_text += f"- **{part['name']}** (Stock: {part['current_stock']}) - Location: {part['location']}\n"

        return {"response": response_text}

    async def _get_asset_history(self, asset_name: str):
        # from app.core.database import get_db_connection

        conn = get_db_connection()

        # Find asset first
        asset = conn.execute(
            "SELECT id, name FROM assets WHERE name LIKE ?", (f"%{asset_name}%",)
        ).fetchone()
        if not asset:
            conn.close()
            return {"response": f"I couldn't find an asset named '{asset_name}'."}

        history = conn.execute(
            """
            SELECT * FROM maintenance_history
            WHERE asset_id = ?
            ORDER BY created_date DESC
            LIMIT 3
        """,
            (asset["id"],),
        ).fetchall()
        conn.close()

        if not history:
            return {
                "response": f"No maintenance history found for **{asset['name']}**."
            }

        response_text = f"**Recent History for {asset['name']}:**\n\n"
        for record in history:
            response_text += f"- {record['created_date']}: {record['description']} (Cost: ${record['total_cost']})\n"

        return {"response": response_text}


# Global instance
gemini_service = GeminiService()
