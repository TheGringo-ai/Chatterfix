#!/usr/bin/env python3
"""
ChatterFix AI Memory and Training System
Creates intelligent RAG-powered memory for LLaMA to become a ChatterFix CMMS expert
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Import existing RAG system
from rag_system import RAGResponse, RAGSystem

logger = logging.getLogger(__name__)


class ChatterFixAIMemory:
    """
    Intelligent AI Memory System for ChatterFix CMMS
    Stores conversations, expertise, and creates comprehensive knowledge base
    """

    def __init__(self, memory_dir: str = "ai-memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)

        # Memory storage paths
        self.conversations_file = self.memory_dir / "conversations.jsonl"
        self.expertise_file = self.memory_dir / "chatterfix_expertise.json"
        self.training_sessions_file = self.memory_dir / "training_sessions.json"
        self.knowledge_base_file = self.memory_dir / "knowledge_base.json"

        # Initialize knowledge base
        self._init_chatterfix_knowledge()

        # Simple knowledge search (without complex RAG for now)
        self.knowledge_cache = {}

    def _init_chatterfix_knowledge(self):
        """Initialize comprehensive ChatterFix knowledge base"""

        chatterfix_knowledge = {
            "system_overview": {
                "name": "ChatterFix CMMS",
                "description": "AI-Powered Computerized Maintenance Management System",
                "key_features": [
                    "Work Order Management",
                    "Preventive Maintenance",
                    "Asset Management",
                    "Parts Inventory",
                    "AI-Powered Diagnostics",
                    "Voice Commands",
                    "Mobile Support",
                    "Real-time Analytics",
                ],
                "technology_stack": {
                    "backend": "Python FastAPI",
                    "frontend": "HTML/CSS/JavaScript",
                    "database": "SQLite",
                    "ai": "LLaMA, Grok, OpenAI GPT",
                    "voice": "Speech Recognition API",
                    "deployment": "Google Cloud Platform",
                },
            },
            "modules": {
                "workorders": {
                    "description": "Core work order management system",
                    "endpoints": [
                        "/cmms/workorders/dashboard",
                        "/cmms/workorders/create",
                        "/cmms/workorders/{id}/view",
                        "/cmms/workorders/{id}/edit",
                    ],
                    "features": [
                        "Create and assign work orders",
                        "Track progress and status",
                        "Add photos and notes",
                        "Priority management",
                        "SLA tracking",
                    ],
                },
                "assets": {
                    "description": "Equipment and asset management",
                    "endpoints": [
                        "/cmms/assets/dashboard",
                        "/cmms/assets/create",
                        "/cmms/assets/{id}/view",
                    ],
                    "features": [
                        "Asset registry",
                        "Maintenance history",
                        "Health scoring",
                        "Predictive analytics",
                    ],
                },
                "parts": {
                    "description": "Inventory and parts management",
                    "endpoints": ["/cmms/parts/dashboard", "/cmms/parts/inventory"],
                    "features": [
                        "Parts catalog",
                        "Stock tracking",
                        "Reorder alerts",
                        "Vendor management",
                    ],
                },
                "preventive": {
                    "description": "Preventive maintenance scheduling",
                    "features": [
                        "Automated scheduling",
                        "Recurring maintenance",
                        "Compliance tracking",
                    ],
                },
            },
            "ai_capabilities": {
                "global_assistant": {
                    "description": "Universal AI assistant available on all pages",
                    "features": [
                        "Natural language commands",
                        "Voice input support",
                        "Cross-page learning",
                        "Real-time responses",
                    ],
                },
                "voice_commands": [
                    "Create work order for [equipment]",
                    "Show me asset health for [asset]",
                    "Schedule maintenance for [equipment]",
                    "Check parts availability for [part]",
                    "What's the status of work order [id]",
                ],
                "diagnostic_ai": {
                    "description": "AI-powered equipment diagnostics",
                    "capabilities": [
                        "Symptom analysis",
                        "Root cause identification",
                        "Repair recommendations",
                        "Parts suggestions",
                    ],
                },
            },
            "common_workflows": {
                "create_work_order": {
                    "steps": [
                        "Navigate to work orders dashboard",
                        "Click 'Create Work Order'",
                        "Select asset and priority",
                        "Describe the issue",
                        "Assign technician",
                        "Set due date",
                    ]
                },
                "schedule_maintenance": {
                    "steps": [
                        "Go to preventive maintenance",
                        "Select asset",
                        "Choose maintenance type",
                        "Set schedule frequency",
                        "Assign technician",
                    ]
                },
                "manage_inventory": {
                    "steps": [
                        "Access parts dashboard",
                        "Check stock levels",
                        "Set reorder points",
                        "Update part information",
                    ]
                },
            },
            "troubleshooting": {
                "common_issues": {
                    "work_order_not_loading": [
                        "Check network connection",
                        "Verify work order ID",
                        "Refresh the page",
                        "Check server status",
                    ],
                    "ai_assistant_not_responding": [
                        "Check microphone permissions",
                        "Verify internet connection",
                        "Try typing instead of voice",
                        "Refresh the page",
                    ],
                    "asset_health_score_missing": [
                        "Ensure asset has recent data",
                        "Check sensor connections",
                        "Verify maintenance history",
                        "Run health analysis",
                    ],
                }
            },
            "best_practices": {
                "work_order_management": [
                    "Use clear, descriptive titles",
                    "Set appropriate priorities",
                    "Include photos when possible",
                    "Update status regularly",
                    "Document completion steps",
                ],
                "preventive_maintenance": [
                    "Schedule based on manufacturer recommendations",
                    "Track completion rates",
                    "Adjust schedules based on usage",
                    "Document findings",
                ],
                "inventory_management": [
                    "Set accurate reorder points",
                    "Track usage patterns",
                    "Maintain vendor relationships",
                    "Regular stock audits",
                ],
            },
        }

        # Save knowledge base
        with open(self.knowledge_base_file, "w") as f:
            json.dump(chatterfix_knowledge, f, indent=2)

        # Cache knowledge for quick search
        self.knowledge_cache = chatterfix_knowledge

    def _search_knowledge(self, query: str) -> List[Dict[str, str]]:
        """Simple keyword-based knowledge search"""

        query_lower = query.lower()
        relevant_knowledge = []

        def search_in_data(data, topic_prefix=""):
            """Recursively search knowledge data"""
            if isinstance(data, dict):
                for key, value in data.items():
                    current_topic = f"{topic_prefix}.{key}" if topic_prefix else key

                    if isinstance(value, str):
                        if any(word in value.lower() for word in query_lower.split()):
                            relevant_knowledge.append(
                                {
                                    "topic": current_topic.replace("_", " ").title(),
                                    "content": value,
                                }
                            )
                    elif isinstance(value, list):
                        content = " ".join(str(item) for item in value)
                        if any(word in content.lower() for word in query_lower.split()):
                            relevant_knowledge.append(
                                {
                                    "topic": current_topic.replace("_", " ").title(),
                                    "content": content,
                                }
                            )
                    else:
                        search_in_data(value, current_topic)

        # Search through cached knowledge
        search_in_data(self.knowledge_cache)

        # Sort by relevance (simple word count matching)
        def relevance_score(item):
            content = item["content"].lower()
            return sum(1 for word in query_lower.split() if word in content)

        relevant_knowledge.sort(key=relevance_score, reverse=True)

        return relevant_knowledge[:5]  # Return top 5 matches

    def _load_existing_knowledge(self):
        """Load existing knowledge from file if available"""
        if self.knowledge_base_file.exists():
            with open(self.knowledge_base_file, "r") as f:
                self.knowledge_cache = json.load(f)
        else:
            self.knowledge_cache = {}

    async def start_training_session(self, session_name: str) -> str:
        """Start a new training session with LLaMA"""

        session_id = hashlib.md5(f"{session_name}_{time.time()}".encode()).hexdigest()[
            :8
        ]

        session_data = {
            "session_id": session_id,
            "session_name": session_name,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "status": "active",
            "messages": [],
            "topics_covered": [],
            "knowledge_gained": [],
        }

        # Save session
        sessions = self._load_training_sessions()
        sessions[session_id] = session_data
        self._save_training_sessions(sessions)

        # Start with introduction
        intro_message = await self._generate_training_intro()

        await self.add_training_message(
            session_id, "system", intro_message, {"type": "introduction"}
        )

        return session_id

    async def _generate_training_intro(self) -> str:
        """Generate comprehensive training introduction"""

        return """
🤖 **ChatterFix CMMS AI Training Session Started**

Hello! I'm ready to learn everything about ChatterFix CMMS and become an expert assistant.

**What I need to learn:**
- Work order management workflows
- Asset and equipment handling
- Parts inventory systems
- Preventive maintenance scheduling
- AI-powered diagnostics
- Voice command processing
- User interaction patterns
- Troubleshooting procedures

**Training Goals:**
1. Master all ChatterFix modules and features
2. Understand user workflows and pain points
3. Learn to provide intelligent assistance
4. Develop expertise in CMMS best practices

**Please teach me about:**
- How users typically create and manage work orders
- Common maintenance scenarios and solutions
- Asset management strategies
- Parts inventory optimization
- Voice command patterns
- AI assistant integration

Let's start with any area you'd like to focus on first!
        """.strip()

    async def add_training_message(
        self, session_id: str, role: str, content: str, metadata: Dict = None
    ):
        """Add a message to training session"""

        sessions = self._load_training_sessions()

        if session_id not in sessions:
            raise ValueError(f"Training session {session_id} not found")

        message = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "role": role,  # 'user', 'assistant', 'system'
            "content": content,
            "metadata": metadata or {},
        }

        sessions[session_id]["messages"].append(message)

        # Extract knowledge if this is a learning message
        if role == "user" and "teach" in content.lower():
            await self._extract_knowledge(session_id, content)

        self._save_training_sessions(sessions)

        # Also log to conversation history
        await self.log_conversation(f"training_{session_id}", role, content, metadata)

    async def _extract_knowledge(self, session_id: str, content: str):
        """Extract and index new knowledge from training content"""

        # Simple keyword extraction for now
        keywords = []

        # Extract ChatterFix-specific terms
        chatterfix_terms = [
            "work order",
            "asset",
            "maintenance",
            "inventory",
            "parts",
            "technician",
            "schedule",
            "priority",
            "status",
            "dashboard",
            "preventive",
            "predictive",
            "diagnostic",
            "ai assistant",
        ]

        for term in chatterfix_terms:
            if term.lower() in content.lower():
                keywords.append(term)

        # Store extracted knowledge
        sessions = self._load_training_sessions()
        if "knowledge_gained" not in sessions[session_id]:
            sessions[session_id]["knowledge_gained"] = []

        sessions[session_id]["knowledge_gained"].extend(keywords)
        self._save_training_sessions(sessions)

        # Store training content in memory (simple approach)
        # This could be enhanced with more sophisticated indexing later

    async def get_intelligent_response(
        self, query: str, context: Dict = None
    ) -> Dict[str, Any]:
        """Generate intelligent response using knowledge base and memory"""

        # Search relevant knowledge using simple keyword matching
        relevant_knowledge = self._search_knowledge(query)

        # Build context from retrieved knowledge
        knowledge_context = []
        for knowledge in relevant_knowledge:
            knowledge_context.append(
                f"- {knowledge['topic']}: {knowledge['content'][:200]}..."
            )

        # Load conversation history for continuity
        recent_conversations = await self._get_recent_conversations(limit=10)

        response_data = {
            "query": query,
            "relevant_knowledge": knowledge_context,
            "recent_context": recent_conversations,
            "suggested_actions": await self._suggest_actions(query),
            "confidence_score": self._calculate_confidence(relevant_knowledge),
            "response_type": self._classify_query(query),
        }

        return response_data

    def _classify_query(self, query: str) -> str:
        """Classify the type of query"""

        query_lower = query.lower()

        if any(word in query_lower for word in ["create", "new", "add"]):
            return "creation"
        elif any(word in query_lower for word in ["status", "check", "show", "view"]):
            return "inquiry"
        elif any(word in query_lower for word in ["help", "how", "what", "why"]):
            return "help"
        elif any(
            word in query_lower for word in ["error", "problem", "issue", "broken"]
        ):
            return "troubleshooting"
        else:
            return "general"

    async def _suggest_actions(self, query: str) -> List[str]:
        """Suggest relevant actions based on query"""

        query_lower = query.lower()
        actions = []

        if "work order" in query_lower:
            actions.extend(
                [
                    "Navigate to Work Orders Dashboard",
                    "Create New Work Order",
                    "Check Work Order Status",
                ]
            )

        if "asset" in query_lower:
            actions.extend(
                [
                    "View Asset Dashboard",
                    "Check Asset Health",
                    "Schedule Asset Maintenance",
                ]
            )

        if "parts" in query_lower or "inventory" in query_lower:
            actions.extend(
                ["Check Parts Inventory", "Update Stock Levels", "Order New Parts"]
            )

        if "maintenance" in query_lower:
            actions.extend(
                [
                    "Schedule Preventive Maintenance",
                    "View Maintenance History",
                    "Update Maintenance Records",
                ]
            )

        return actions

    def _calculate_confidence(self, relevant_knowledge: List[Dict]) -> float:
        """Calculate confidence score based on retrieved knowledge"""

        if not relevant_knowledge:
            return 0.0

        # Simple confidence based on number of knowledge matches
        base_confidence = min(len(relevant_knowledge) / 5.0, 1.0)

        # Boost confidence based on knowledge relevance
        relevance_boost = min(len(relevant_knowledge) * 0.2, 0.5)

        return min(base_confidence + relevance_boost, 1.0)

    async def log_conversation(
        self, session_id: str, role: str, content: str, metadata: Dict = None
    ):
        """Log conversation for learning and context"""

        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "role": role,
            "content": content,
            "metadata": metadata or {},
        }

        # Append to conversations file
        with open(self.conversations_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    async def _get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        """Get recent conversation history"""

        if not self.conversations_file.exists():
            return []

        conversations = []

        with open(self.conversations_file, "r") as f:
            lines = f.readlines()

        # Get last N lines
        for line in lines[-limit:]:
            try:
                conversations.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue

        return conversations

    def _load_training_sessions(self) -> Dict[str, Any]:
        """Load training sessions data"""

        if not self.training_sessions_file.exists():
            return {}

        with open(self.training_sessions_file, "r") as f:
            return json.load(f)

    def _save_training_sessions(self, sessions: Dict[str, Any]):
        """Save training sessions data"""

        with open(self.training_sessions_file, "w") as f:
            json.dump(sessions, f, indent=2)

    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive summary of training session"""

        sessions = self._load_training_sessions()

        if session_id not in sessions:
            return {"error": "Session not found"}

        session = sessions[session_id]

        # Calculate session stats
        message_count = len(session.get("messages", []))
        topics_count = len(set(session.get("knowledge_gained", [])))
        duration = "Active" if session.get("status") == "active" else "Completed"

        return {
            "session_id": session_id,
            "session_name": session.get("session_name", "Unknown"),
            "status": session.get("status", "unknown"),
            "start_time": session.get("start_time"),
            "message_count": message_count,
            "topics_covered": topics_count,
            "knowledge_gained": session.get("knowledge_gained", []),
            "duration": duration,
            "summary": f"Training session with {message_count} messages covering {topics_count} ChatterFix topics",
        }

    async def complete_training_session(self, session_id: str):
        """Mark training session as complete and generate summary"""

        sessions = self._load_training_sessions()

        if session_id in sessions:
            sessions[session_id]["status"] = "completed"
            sessions[session_id]["end_time"] = datetime.now(timezone.utc).isoformat()

            # Generate completion summary
            summary = await self.get_session_summary(session_id)
            sessions[session_id]["completion_summary"] = summary

            self._save_training_sessions(sessions)

            return summary

        return {"error": "Session not found"}


# Global instance
chatterfix_memory = ChatterFixAIMemory()


async def train_llama_on_chatterfix():
    """Comprehensive LLaMA training function"""

    print("🚀 Starting ChatterFix AI Training for LLaMA...")

    # Start training session
    session_id = await chatterfix_memory.start_training_session(
        "ChatterFix Expert Training"
    )

    print(f"📚 Training Session {session_id} started")

    # Core training topics
    training_topics = [
        {
            "topic": "Work Order Management",
            "content": """
            Work orders are the core of ChatterFix CMMS. Users create work orders to track maintenance tasks:

            - Create: /cmms/workorders/create - Users select asset, describe issue, set priority
            - Dashboard: /cmms/workorders/dashboard - Shows all work orders with filters
            - View: /cmms/workorders/{id}/view - Detailed work order information
            - Common statuses: Open, Assigned, In Progress, Completed, Cancelled
            - Priorities: Low, Medium, High, Urgent
            - Users can add photos, notes, and track time spent
            - SLA tracking shows if work orders are overdue
            """,
        },
        {
            "topic": "Asset Management",
            "content": """
            Assets represent equipment, machinery, and systems that need maintenance:

            - Asset Dashboard: /cmms/assets/dashboard - Overview of all assets
            - Health Scoring: Assets have health scores from 0-100%
            - Maintenance History: Track all work performed on assets
            - Predictive Analytics: AI predicts when maintenance is needed
            - Asset Types: Pumps, motors, conveyors, HVAC, electrical systems
            - Critical assets get priority maintenance scheduling
            """,
        },
        {
            "topic": "Parts Inventory",
            "content": """
            Parts management ensures maintenance teams have needed supplies:

            - Parts Dashboard: /cmms/parts/dashboard - Inventory overview
            - Stock Tracking: Monitor quantities and usage
            - Reorder Alerts: Automatic notifications when stock is low
            - Vendor Management: Track suppliers and pricing
            - Parts are linked to work orders for usage tracking
            - Common parts: Bearings, seals, filters, belts, oils
            """,
        },
        {
            "topic": "AI Assistant Integration",
            "content": """
            ChatterFix has a global AI assistant available on every page:

            - Voice Commands: Users can speak naturally to create work orders
            - Natural Language: "Create maintenance for pump 3" creates work order
            - Cross-page Learning: Assistant learns from all user interactions
            - Quick Actions: Pre-built buttons for common tasks
            - Real-time Responses: Instant feedback and suggestions
            - Context Aware: Understands what page user is on
            """,
        },
    ]

    # Train on each topic
    for topic_data in training_topics:
        await chatterfix_memory.add_training_message(
            session_id,
            "user",
            f"Please learn about {topic_data['topic']}:\n\n{topic_data['content']}",
            {"topic": topic_data["topic"], "type": "knowledge_transfer"},
        )

        # Simulate AI learning response
        await chatterfix_memory.add_training_message(
            session_id,
            "assistant",
            f"✅ I've learned about {topic_data['topic']}. I now understand the key concepts and can help users with related tasks.",
            {"topic": topic_data["topic"], "type": "acknowledgment"},
        )

    # Complete training session
    summary = await chatterfix_memory.complete_training_session(session_id)

    print("🎓 Training completed successfully!")
    print(f"📊 Session Summary: {summary}")

    return session_id, summary


if __name__ == "__main__":
    # Run training
    asyncio.run(train_llama_on_chatterfix())
