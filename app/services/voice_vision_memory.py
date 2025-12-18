"""
Voice & Vision Memory Integration Service
Connects voice commands and computer vision to the AI Memory System
for continuous learning and improvement

This service:
- Captures all voice command interactions and outcomes
- Tracks technician behavior patterns
- Learns from successful vs failed commands
- Stores vision analysis results for equipment recognition improvement
- Enables cross-application pattern sharing
- Provides personalized command suggestions based on history
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Import the core memory service
try:
    from app.services.ai_memory_integration import (
        get_ai_memory_service,
        AIMemoryService,
    )

    MEMORY_SERVICE_AVAILABLE = True
except ImportError:
    MEMORY_SERVICE_AVAILABLE = False
    logger.warning("AI Memory Service not available")


class CommandOutcome(Enum):
    """Outcome of a voice command"""

    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    NOT_UNDERSTOOD = "not_understood"


class VisionTaskType(Enum):
    """Types of vision tasks"""

    PART_RECOGNITION = "part_recognition"
    EQUIPMENT_INSPECTION = "equipment_inspection"
    DOCUMENT_SCAN = "document_scan"
    BARCODE_SCAN = "barcode_scan"
    CONDITION_ANALYSIS = "condition_analysis"
    SAFETY_CHECK = "safety_check"


@dataclass
class VoiceCommandRecord:
    """Record of a voice command interaction"""

    command_id: str
    technician_id: str
    raw_transcript: str
    processed_command: str
    command_type: str
    confidence: float
    noise_level: str
    outcome: CommandOutcome
    execution_time_ms: float
    result_data: Dict[str, Any]
    feedback_given: str
    timestamp: datetime


@dataclass
class VisionAnalysisRecord:
    """Record of a vision analysis"""

    analysis_id: str
    technician_id: str
    task_type: VisionTaskType
    image_hash: str
    detected_items: List[str]
    confidence_scores: Dict[str, float]
    equipment_condition: Optional[float]
    issues_found: List[Dict]
    processing_time_ms: float
    outcome: str
    timestamp: datetime


@dataclass
class TechnicianProfile:
    """Profile of technician behavior patterns"""

    technician_id: str
    total_commands: int
    successful_commands: int
    most_used_commands: List[str]
    preferred_language: str
    average_confidence: float
    common_equipment: List[str]
    work_patterns: Dict[str, Any]
    last_active: datetime


class VoiceVisionMemoryService:
    """
    Service for capturing and learning from voice/vision interactions
    """

    # Collections in Firestore
    VOICE_COMMANDS_COLLECTION = "voice_command_history"
    VISION_ANALYSIS_COLLECTION = "vision_analysis_history"
    TECHNICIAN_PROFILES_COLLECTION = "technician_profiles"
    COMMAND_PATTERNS_COLLECTION = "command_patterns"
    EQUIPMENT_LEARNING_COLLECTION = "equipment_learning"

    def __init__(self):
        self.memory_service: Optional[AIMemoryService] = None
        if MEMORY_SERVICE_AVAILABLE:
            try:
                self.memory_service = get_ai_memory_service()
                logger.info("Voice/Vision Memory Service initialized with AI Memory")
            except Exception as e:
                logger.warning(f"Could not connect to AI Memory Service: {e}")

    async def capture_voice_command(
        self,
        technician_id: str,
        raw_transcript: str,
        processed_command: str,
        command_type: str,
        confidence: float,
        noise_level: str = "unknown",
        outcome: CommandOutcome = CommandOutcome.SUCCESS,
        execution_time_ms: float = 0,
        result_data: Optional[Dict] = None,
        feedback_given: str = "",
    ) -> str:
        """
        Capture a voice command interaction for learning

        Returns: command_id
        """
        if not self.memory_service:
            logger.debug("Memory service not available, skipping capture")
            return ""

        try:
            command_id = self.memory_service._generate_id(f"voice_{raw_transcript}")

            # Create command record
            command_data = {
                "command_id": command_id,
                "technician_id": technician_id or "anonymous",
                "raw_transcript": raw_transcript,
                "processed_command": processed_command,
                "command_type": command_type,
                "confidence": confidence,
                "noise_level": noise_level,
                "outcome": outcome.value,
                "execution_time_ms": execution_time_ms,
                "result_data": result_data or {},
                "feedback_given": feedback_given,
                "timestamp": datetime.now(timezone.utc),
                "application": "ChatterFix",
            }

            # Store in Firestore
            await self.memory_service.firestore.create_document(
                self.VOICE_COMMANDS_COLLECTION, command_data, command_id
            )

            # Also capture as general AI interaction
            await self.memory_service.capture_interaction(
                user_message=raw_transcript,
                ai_response=feedback_given or str(result_data),
                model="voice_command_processor",
                context=f"command_type:{command_type}",
                success=(outcome == CommandOutcome.SUCCESS),
                metadata={
                    "confidence": confidence,
                    "noise_level": noise_level,
                    "technician_id": technician_id,
                },
            )

            # Update technician profile
            await self._update_technician_profile(
                technician_id,
                command_type,
                outcome == CommandOutcome.SUCCESS,
                confidence,
            )

            # Learn from outcome
            if (
                outcome == CommandOutcome.FAILED
                or outcome == CommandOutcome.NOT_UNDERSTOOD
            ):
                await self._capture_command_failure(
                    raw_transcript, processed_command, command_type, confidence
                )
            elif outcome == CommandOutcome.SUCCESS:
                await self._capture_successful_pattern(
                    raw_transcript, processed_command, command_type
                )

            logger.info(f"Captured voice command: {command_id} ({outcome.value})")
            return command_id

        except Exception as e:
            logger.error(f"Failed to capture voice command: {e}")
            return ""

    async def capture_vision_analysis(
        self,
        technician_id: str,
        task_type: VisionTaskType,
        image_hash: str,
        detected_items: List[str],
        confidence_scores: Dict[str, float],
        equipment_condition: Optional[float] = None,
        issues_found: Optional[List[Dict]] = None,
        processing_time_ms: float = 0,
        outcome: str = "success",
    ) -> str:
        """
        Capture a vision analysis result for learning

        Returns: analysis_id
        """
        if not self.memory_service:
            return ""

        try:
            analysis_id = self.memory_service._generate_id(f"vision_{image_hash}")

            analysis_data = {
                "analysis_id": analysis_id,
                "technician_id": technician_id or "anonymous",
                "task_type": task_type.value,
                "image_hash": image_hash,
                "detected_items": detected_items,
                "confidence_scores": confidence_scores,
                "equipment_condition": equipment_condition,
                "issues_found": issues_found or [],
                "processing_time_ms": processing_time_ms,
                "outcome": outcome,
                "timestamp": datetime.now(timezone.utc),
                "application": "ChatterFix",
            }

            await self.memory_service.firestore.create_document(
                self.VISION_ANALYSIS_COLLECTION, analysis_data, analysis_id
            )

            # If issues found, capture for learning
            if issues_found:
                await self._capture_equipment_issues(
                    detected_items, issues_found, equipment_condition
                )

            logger.info(f"Captured vision analysis: {analysis_id}")
            return analysis_id

        except Exception as e:
            logger.error(f"Failed to capture vision analysis: {e}")
            return ""

    async def get_technician_profile(self, technician_id: str) -> Optional[Dict]:
        """Get or create a technician profile"""
        if not self.memory_service:
            return None

        try:
            profile = await self.memory_service.firestore.get_document(
                self.TECHNICIAN_PROFILES_COLLECTION, technician_id
            )

            if not profile:
                # Create default profile
                profile = {
                    "technician_id": technician_id,
                    "total_commands": 0,
                    "successful_commands": 0,
                    "most_used_commands": [],
                    "preferred_language": "en-US",
                    "average_confidence": 0.0,
                    "common_equipment": [],
                    "work_patterns": {},
                    "created_at": datetime.now(timezone.utc),
                    "last_active": datetime.now(timezone.utc),
                }
                await self.memory_service.firestore.create_document(
                    self.TECHNICIAN_PROFILES_COLLECTION, profile, technician_id
                )

            return profile

        except Exception as e:
            logger.error(f"Failed to get technician profile: {e}")
            return None

    async def get_command_suggestions(
        self, technician_id: str, context: str = "", limit: int = 5
    ) -> List[Dict]:
        """
        Get personalized command suggestions based on history

        Returns list of suggested commands with confidence
        """
        if not self.memory_service:
            return self._get_default_suggestions()

        try:
            # Get technician's command history
            commands = await self.memory_service.firestore.get_collection(
                self.VOICE_COMMANDS_COLLECTION,
                filters={"technician_id": technician_id},
                limit=100,
                order_by="-timestamp",
            )

            # Analyze patterns
            command_counts = {}
            successful_patterns = []

            for cmd in commands:
                cmd_type = cmd.get("command_type", "general")
                command_counts[cmd_type] = command_counts.get(cmd_type, 0) + 1

                if cmd.get("outcome") == "success":
                    successful_patterns.append(
                        {
                            "command": cmd.get("processed_command"),
                            "type": cmd_type,
                            "confidence": cmd.get("confidence", 0),
                        }
                    )

            # Get most used commands
            sorted_commands = sorted(
                command_counts.items(), key=lambda x: x[1], reverse=True
            )[:limit]

            suggestions = []
            for cmd_type, count in sorted_commands:
                # Find best example of this command type
                examples = [p for p in successful_patterns if p["type"] == cmd_type]
                if examples:
                    best = max(examples, key=lambda x: x["confidence"])
                    suggestions.append(
                        {
                            "command_type": cmd_type,
                            "example": best["command"],
                            "usage_count": count,
                            "confidence": best["confidence"],
                            "suggestion": self._generate_suggestion_text(cmd_type),
                        }
                    )

            # Add context-based suggestions
            if context:
                context_suggestions = await self._get_context_suggestions(context)
                suggestions.extend(context_suggestions)

            return suggestions[:limit]

        except Exception as e:
            logger.error(f"Failed to get suggestions: {e}")
            return self._get_default_suggestions()

    async def get_equipment_recognition_data(
        self, equipment_type: str
    ) -> Dict[str, Any]:
        """
        Get learned data about equipment for better recognition

        Returns recognition hints and common issues
        """
        if not self.memory_service:
            return {}

        try:
            # Get vision analyses for this equipment type
            analyses = await self.memory_service.firestore.get_collection(
                self.VISION_ANALYSIS_COLLECTION, limit=50, order_by="-timestamp"
            )

            # Filter for this equipment type
            relevant = [
                a
                for a in analyses
                if equipment_type.lower() in str(a.get("detected_items", [])).lower()
            ]

            if not relevant:
                return {}

            # Aggregate learning
            all_issues = []
            confidence_sum = 0
            condition_sum = 0
            condition_count = 0

            for analysis in relevant:
                all_issues.extend(analysis.get("issues_found", []))

                for item, conf in analysis.get("confidence_scores", {}).items():
                    confidence_sum += conf

                if analysis.get("equipment_condition"):
                    condition_sum += analysis["equipment_condition"]
                    condition_count += 1

            # Find common issues
            issue_types = {}
            for issue in all_issues:
                issue_type = issue.get("type", "unknown")
                issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

            common_issues = sorted(
                issue_types.items(), key=lambda x: x[1], reverse=True
            )[:5]

            return {
                "equipment_type": equipment_type,
                "sample_count": len(relevant),
                "average_condition": (
                    condition_sum / condition_count if condition_count else None
                ),
                "common_issues": [{"type": t, "count": c} for t, c in common_issues],
                "recognition_hints": self._generate_recognition_hints(
                    equipment_type, relevant
                ),
            }

        except Exception as e:
            logger.error(f"Failed to get equipment data: {e}")
            return {}

    async def get_voice_analytics(
        self, technician_id: Optional[str] = None, days: int = 30
    ) -> Dict[str, Any]:
        """Get analytics about voice command usage"""
        if not self.memory_service:
            return {}

        try:
            filters = {}
            if technician_id:
                filters["technician_id"] = technician_id

            commands = await self.memory_service.firestore.get_collection(
                self.VOICE_COMMANDS_COLLECTION,
                filters=filters,
                limit=1000,
                order_by="-timestamp",
            )

            # Calculate analytics
            total = len(commands)
            successful = sum(1 for c in commands if c.get("outcome") == "success")
            failed = sum(1 for c in commands if c.get("outcome") == "failed")

            # Command type distribution
            type_counts = {}
            for cmd in commands:
                cmd_type = cmd.get("command_type", "general")
                type_counts[cmd_type] = type_counts.get(cmd_type, 0) + 1

            # Average confidence
            confidences = [
                c.get("confidence", 0) for c in commands if c.get("confidence")
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            # Noise level distribution
            noise_counts = {"low": 0, "medium": 0, "high": 0, "unknown": 0}
            for cmd in commands:
                noise = cmd.get("noise_level", "unknown")
                if noise in noise_counts:
                    noise_counts[noise] += 1

            return {
                "total_commands": total,
                "successful_commands": successful,
                "failed_commands": failed,
                "success_rate": (successful / total * 100) if total else 0,
                "average_confidence": round(avg_confidence, 2),
                "command_distribution": type_counts,
                "noise_distribution": noise_counts,
                "unique_technicians": len(
                    set(c.get("technician_id") for c in commands)
                ),
            }

        except Exception as e:
            logger.error(f"Failed to get voice analytics: {e}")
            return {}

    async def _update_technician_profile(
        self, technician_id: str, command_type: str, success: bool, confidence: float
    ):
        """Update technician profile with new command data"""
        if not technician_id or not self.memory_service:
            return

        try:
            profile = await self.get_technician_profile(technician_id)
            if not profile:
                return

            # Update counts
            profile["total_commands"] = profile.get("total_commands", 0) + 1
            if success:
                profile["successful_commands"] = (
                    profile.get("successful_commands", 0) + 1
                )

            # Update most used commands
            most_used = profile.get("most_used_commands", [])
            if command_type not in most_used:
                most_used.append(command_type)
            profile["most_used_commands"] = most_used[-10:]  # Keep last 10

            # Update average confidence
            old_avg = profile.get("average_confidence", 0)
            total = profile["total_commands"]
            profile["average_confidence"] = (old_avg * (total - 1) + confidence) / total

            profile["last_active"] = datetime.now(timezone.utc)

            # Save updated profile
            await self.memory_service.firestore.update_document(
                self.TECHNICIAN_PROFILES_COLLECTION, technician_id, profile
            )

        except Exception as e:
            logger.debug(f"Failed to update technician profile: {e}")

    async def _capture_command_failure(
        self,
        raw_transcript: str,
        processed_command: str,
        command_type: str,
        confidence: float,
    ):
        """Capture failed command for learning"""
        if not self.memory_service:
            return

        try:
            await self.memory_service.capture_mistake(
                mistake_type="voice_command_failure",
                description=f"Voice command failed: '{raw_transcript[:100]}'",
                context={
                    "raw_transcript": raw_transcript,
                    "processed_command": processed_command,
                    "command_type": command_type,
                    "confidence": confidence,
                },
                error_message=f"Command not understood or failed to execute",
                severity="low" if confidence < 0.5 else "medium",
                resolution=f"Improve recognition for command type: {command_type}",
            )
        except Exception as e:
            logger.debug(f"Failed to capture command failure: {e}")

    async def _capture_successful_pattern(
        self, raw_transcript: str, processed_command: str, command_type: str
    ):
        """Capture successful command pattern"""
        if not self.memory_service:
            return

        try:
            # Only capture unique patterns
            pattern_id = self.memory_service._generate_id(
                f"pattern_{command_type}_{processed_command[:50]}"
            )

            pattern_data = {
                "pattern_id": pattern_id,
                "raw_transcript": raw_transcript,
                "processed_command": processed_command,
                "command_type": command_type,
                "success_count": 1,
                "timestamp": datetime.now(timezone.utc),
            }

            await self.memory_service.firestore.create_document(
                self.COMMAND_PATTERNS_COLLECTION, pattern_data, pattern_id
            )

        except Exception as e:
            logger.debug(f"Failed to capture successful pattern: {e}")

    async def _capture_equipment_issues(
        self,
        detected_items: List[str],
        issues_found: List[Dict],
        condition_score: Optional[float],
    ):
        """Capture equipment issues for learning"""
        if not self.memory_service or not issues_found:
            return

        try:
            # Store in equipment learning collection
            for item in detected_items:
                learning_id = self.memory_service._generate_id(f"equip_{item}")

                learning_data = {
                    "learning_id": learning_id,
                    "equipment_type": item,
                    "issues": issues_found,
                    "condition_score": condition_score,
                    "timestamp": datetime.now(timezone.utc),
                }

                await self.memory_service.firestore.create_document(
                    self.EQUIPMENT_LEARNING_COLLECTION, learning_data, learning_id
                )

        except Exception as e:
            logger.debug(f"Failed to capture equipment issues: {e}")

    async def _get_context_suggestions(self, context: str) -> List[Dict]:
        """Get suggestions based on current context"""
        context_lower = context.lower()

        suggestions = []

        if "work order" in context_lower or "maintenance" in context_lower:
            suggestions.append(
                {
                    "command_type": "work_order",
                    "example": "Create work order for [equipment]",
                    "suggestion": "Try: 'Create work order for pump 5, high priority'",
                }
            )

        if "inventory" in context_lower or "parts" in context_lower:
            suggestions.append(
                {
                    "command_type": "inventory",
                    "example": "Check inventory for [part]",
                    "suggestion": "Try: 'Check inventory for bearing 6205'",
                }
            )

        if "inspect" in context_lower or "check" in context_lower:
            suggestions.append(
                {
                    "command_type": "inspection",
                    "example": "Inspect [equipment]",
                    "suggestion": "Try: 'Run inspection on conveyor belt'",
                }
            )

        return suggestions

    def _get_default_suggestions(self) -> List[Dict]:
        """Get default suggestions when no history available"""
        return [
            {
                "command_type": "work_order",
                "example": "Create work order",
                "suggestion": "Say: 'Create work order for [equipment], [priority] priority'",
            },
            {
                "command_type": "inventory",
                "example": "Check inventory",
                "suggestion": "Say: 'Check inventory for [part name or number]'",
            },
            {
                "command_type": "asset_status",
                "example": "Show status",
                "suggestion": "Say: 'Show status of [equipment name]'",
            },
            {
                "command_type": "inspection",
                "example": "Run inspection",
                "suggestion": "Say: 'Run inspection on [equipment]'",
            },
            {
                "command_type": "emergency",
                "example": "Emergency stop",
                "suggestion": "Say: 'Emergency stop [equipment]' for urgent issues",
            },
        ]

    def _generate_suggestion_text(self, command_type: str) -> str:
        """Generate helpful suggestion text for a command type"""
        suggestions = {
            "work_order": "Create or update work orders by voice",
            "inventory": "Check parts inventory and availability",
            "asset_status": "Get equipment status and information",
            "inspection": "Run equipment inspections",
            "reading": "Record gauge and meter readings",
            "emergency": "Report emergency situations",
            "query": "Ask questions about maintenance",
            "general": "General voice commands",
        }
        return suggestions.get(command_type, "Voice command")

    def _generate_recognition_hints(
        self, equipment_type: str, analyses: List[Dict]
    ) -> List[str]:
        """Generate hints for better equipment recognition"""
        hints = []

        # Analyze successful recognitions
        high_conf_items = []
        for analysis in analyses:
            for item, conf in analysis.get("confidence_scores", {}).items():
                if conf > 0.8:
                    high_conf_items.append(item)

        if high_conf_items:
            hints.append(
                f"Best recognized when labeled: {', '.join(set(high_conf_items)[:3])}"
            )

        # Check lighting conditions from issues
        lighting_issues = sum(
            1
            for a in analyses
            for i in a.get("issues_found", [])
            if "lighting" in str(i).lower()
        )
        if lighting_issues > len(analyses) * 0.3:
            hints.append("Ensure good lighting for better recognition")

        return hints


# Singleton instance
_voice_vision_memory: Optional[VoiceVisionMemoryService] = None


def get_voice_vision_memory() -> VoiceVisionMemoryService:
    """Get the singleton VoiceVisionMemoryService instance"""
    global _voice_vision_memory
    if _voice_vision_memory is None:
        _voice_vision_memory = VoiceVisionMemoryService()
    return _voice_vision_memory
