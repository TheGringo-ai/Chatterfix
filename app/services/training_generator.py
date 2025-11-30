"""
AI Training Content Generator
Generates interactive training modules from equipment manuals and documentation
"""

import os
from app.core.database import get_db_connection
import logging
from datetime import datetime
import json

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

            # Save to database
            conn = get_db_connection()
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO training_modules 
                    (title, description, content_type, asset_type, skill_category, 
                     difficulty_level, estimated_duration_minutes, content_path, ai_generated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                    (
                        training_data["title"],
                        training_data["description"],
                        "ai_generated",
                        asset_type,
                        skill_category,
                        training_data["difficulty_level"],
                        training_data["estimated_duration_minutes"],
                        json.dumps(training_data),
                    ),
                )
                conn.commit()
                module_id = cursor.lastrowid

                logger.info(
                    f"Generated training module {module_id}: {training_data['title']}"
                )
                return module_id
            finally:
                conn.close()

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
    def assign_training(user_id: int, module_id: int):
        """Assign a training module to a user"""
        conn = get_db_connection()
        try:
            conn.execute(
                """
                INSERT INTO user_training (user_id, training_module_id, status)
                VALUES (?, ?, 'assigned')
            """,
                (user_id, module_id),
            )
            conn.commit()
            logger.info(f"Assigned training module {module_id} to user {user_id}")
        finally:
            conn.close()

    @staticmethod
    def complete_training(user_training_id: int, score: float = None):
        """Mark training as completed"""
        conn = get_db_connection()
        try:
            conn.execute(
                """
                UPDATE user_training 
                SET status = 'completed', completed_date = ?, score = ?
                WHERE id = ?
            """,
                (datetime.now(), score, user_training_id),
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def get_user_training(user_id: int):
        """Get all training for a user"""
        conn = get_db_connection()
        try:
            return conn.execute(
                """
                SELECT ut.*, tm.title, tm.description, tm.estimated_duration_minutes
                FROM user_training ut
                JOIN training_modules tm ON ut.training_module_id = tm.id
                WHERE ut.user_id = ?
                ORDER BY 
                    CASE ut.status 
                        WHEN 'assigned' THEN 1
                        WHEN 'in_progress' THEN 2
                        WHEN 'completed' THEN 3
                    END,
                    ut.started_date DESC
            """,
                (user_id,),
            ).fetchall()
        finally:
            conn.close()


# Global training generator instance
training_generator = TrainingGenerator()
