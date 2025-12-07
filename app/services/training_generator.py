"""
AI Training Content Generator
Generates interactive training modules from equipment manuals and documentation
"""

import json
import logging
import os
from datetime import datetime

from app.core.firestore_db import get_firestore_manager

# Import Google Generative AI with error handling
try:
    import google.generativeai as genai

    GENAI_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Google Generative AI not available: {e}")
    genai = None
    GENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY and GENAI_AVAILABLE:
    genai.configure(api_key=GEMINI_API_KEY)


class TrainingGenerator:

    @staticmethod
    async def generate_from_manual(
        manual_path: str, asset_type: str, skill_category: str
    ):
        """
        Generate training module from equipment manual
        Supports PDF, images, and text files
        """
        if not GEMINI_API_KEY or not GENAI_AVAILABLE:
            logger.warning(
                "GEMINI_API_KEY not set or Google Generative AI not available, cannot generate training"
            )
            return None

        try:
            # Read manual content
            with open(manual_path, "rb") as f:
                manual_content = f.read()

            # Use Gemini to analyze and extract training content
            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = f"""
            You are an expert technical trainer creating a comprehensive training module for maintenance technicians.

            Analyze this equipment manual and create a structured training module that includes:

            1. **Overview** - Brief introduction to the equipment
            2. **Safety Procedures** - Critical safety information (MUST be first)
            3. **Operating Procedures** - Step-by-step operation instructions
            4. **Maintenance Procedures** - Routine maintenance tasks
            5. **Troubleshooting Guide** - Common issues and solutions
            6. **Key Specifications** - Important technical specs to remember
            7. **Quiz Questions** - 5 multiple-choice questions to test understanding

            Asset Type: {asset_type}
            Skill Category: {skill_category}

            Format the response as JSON with the following structure:
            {{
                "title": "Training module title",
                "description": "Brief description",
                "difficulty_level": 1-5,
                "estimated_duration_minutes": estimated time,
                "sections": [
                    {{"title": "Section name", "content": "Section content"}},
                    ...
                ],
                "quiz": [
                    {{
                        "question": "Question text",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": 0-3,
                        "explanation": "Why this is correct"
                    }},
                    ...
                ]
            }}

            Make it practical, technician-friendly, and focused on hands-on skills.
            """

            # Generate content
            response = model.generate_content([prompt, manual_content])
            training_data = json.loads(response.text)

            # Save to Firestore database
            firestore_manager = get_firestore_manager()
            module_data = {
                "title": training_data["title"],
                "description": training_data["description"],
                "content_type": "ai_generated",
                "asset_type": asset_type,
                "skill_category": skill_category,
                "difficulty_level": training_data["difficulty_level"],
                "estimated_duration_minutes": training_data[
                    "estimated_duration_minutes"
                ],
                "content_path": json.dumps(training_data),
                "ai_generated": True,
            }

            module_id = await firestore_manager.create_training_module(module_data)

            logger.info(
                f"Generated training module {module_id}: {training_data['title']}"
            )
            return module_id

        except Exception as e:
            logger.error(f"Error generating training from manual: {e}")
            return None

    @staticmethod
    async def generate_quick_guide(equipment_name: str, task_description: str):
        """
        Generate a quick reference guide for a specific task
        """
        if not GEMINI_API_KEY or not GENAI_AVAILABLE:
            return "GEMINI_API_KEY not configured or Google Generative AI not available"

        try:
            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = f"""
            Create a concise, step-by-step quick reference guide for a maintenance technician.

            Equipment: {equipment_name}
            Task: {task_description}

            Provide:
            1. Safety warnings (if applicable)
            2. Required tools/parts
            3. Step-by-step procedure (numbered)
            4. Common mistakes to avoid
            5. Verification steps

            Keep it brief and practical - this is a field reference guide.
            Format in markdown.
            """

            response = model.generate_content(prompt)
            return response.text

        except Exception as e:
            logger.error(f"Error generating quick guide: {e}")
            return f"Error: {str(e)}"

    @staticmethod
    async def answer_technical_question(question: str, context: str = None):
        """
        Real-time knowledge assistant for technicians
        """
        if not GEMINI_API_KEY or not GENAI_AVAILABLE:
            return "GEMINI_API_KEY not configured or Google Generative AI not available"

        try:
            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = f"""
            You are an expert maintenance technician assistant. Answer this question clearly and practically.

            Question: {question}
            """

            if context:
                prompt += f"\n\nContext: {context}"

            prompt += """

            Provide:
            - Direct answer
            - Safety considerations (if relevant)
            - Best practices
            - Common pitfalls to avoid

            Keep it concise and actionable.
            """

            response = model.generate_content(prompt)
            return response.text

        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return f"Error: {str(e)}"

    @staticmethod
    async def assign_training(user_id: str, module_id: str):
        """Assign a training module to a user"""
        firestore_manager = get_firestore_manager()
        try:
            training_data = {
                "user_id": user_id,
                "training_module_id": module_id,
                "status": "assigned",
                "assigned_date": datetime.now(),
                "started_date": None,
                "completed_date": None,
                "score": None,
            }
            await firestore_manager.create_user_training(training_data)
            logger.info(f"Assigned training module {module_id} to user {user_id}")
        except Exception as e:
            logger.error(f"Error assigning training: {e}")
            raise

    @staticmethod
    async def complete_training(user_training_id: str, score: float = None):
        """Mark training as completed"""
        firestore_manager = get_firestore_manager()
        try:
            await firestore_manager.update_document(
                "user_training",
                user_training_id,
                {
                    "status": "completed",
                    "completed_date": datetime.now(),
                    "score": score,
                },
            )
            logger.info(f"Completed training {user_training_id} with score {score}")
        except Exception as e:
            logger.error(f"Error completing training: {e}")
            raise

    @staticmethod
    async def get_user_training(user_id: str):
        """Get all training for a user"""
        firestore_manager = get_firestore_manager()
        try:
            # Get user training records
            user_training = await firestore_manager.get_user_training(user_id)

            # Enrich with module details
            enriched_training = []
            for training in user_training:
                module_id = training.get("training_module_id")
                if module_id:
                    module = await firestore_manager.get_document(
                        "training_modules", module_id
                    )
                    if module:
                        training.update(
                            {
                                "title": module.get("title"),
                                "description": module.get("description"),
                                "estimated_duration_minutes": module.get(
                                    "estimated_duration_minutes"
                                ),
                            }
                        )
                enriched_training.append(training)

            # Sort by status priority and date
            status_order = {"assigned": 1, "in_progress": 2, "completed": 3}
            enriched_training.sort(
                key=lambda x: (
                    status_order.get(x.get("status", "assigned"), 4),
                    x.get("started_date") or datetime.min,
                ),
                reverse=True,
            )

            return enriched_training
        except Exception as e:
            logger.error(f"Error getting user training: {e}")
            return []


# Global training generator instance
training_generator = TrainingGenerator()
