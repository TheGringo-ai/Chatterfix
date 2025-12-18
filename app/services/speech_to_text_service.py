"""
Server-Side Speech-to-Text Service
Google Cloud Speech-to-Text integration for reliable factory floor operation

Provides:
- Server-side transcription (not dependent on browser)
- Noise filtering for manufacturing environments
- Multiple language support
- Confidence scoring
- Streaming and batch transcription
- Custom vocabulary for equipment/parts terminology
"""

import asyncio
import base64
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Google Cloud Speech-to-Text
try:
    from google.cloud import speech_v1 as speech
    from google.cloud.speech_v1 import types

    GOOGLE_SPEECH_AVAILABLE = True
except ImportError:
    GOOGLE_SPEECH_AVAILABLE = False
    logger.warning(
        "Google Cloud Speech not available. Install with: pip install google-cloud-speech"
    )

# AI Memory integration for learning
try:
    from app.services.ai_memory_integration import get_ai_memory_service

    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False


class AudioEncoding(Enum):
    """Supported audio encodings"""

    LINEAR16 = "LINEAR16"  # Uncompressed 16-bit signed little-endian
    FLAC = "FLAC"
    MULAW = "MULAW"
    AMR = "AMR"
    AMR_WB = "AMR_WB"
    OGG_OPUS = "OGG_OPUS"
    WEBM_OPUS = "WEBM_OPUS"
    MP3 = "MP3"


@dataclass
class TranscriptionResult:
    """Result of speech transcription"""

    transcript: str
    confidence: float
    language_code: str
    is_final: bool
    alternatives: List[Dict[str, float]]
    words: List[Dict]
    processing_time_ms: float
    audio_duration_ms: float
    noise_level: str  # low, medium, high
    timestamp: str


@dataclass
class StreamingConfig:
    """Configuration for streaming transcription"""

    language_code: str = "en-US"
    sample_rate_hertz: int = 16000
    encoding: AudioEncoding = AudioEncoding.LINEAR16
    interim_results: bool = True
    single_utterance: bool = False
    enable_automatic_punctuation: bool = True
    enable_word_time_offsets: bool = True
    max_alternatives: int = 3
    profanity_filter: bool = False
    model: str = "latest_long"  # Best for manufacturing environments


class SpeechToTextService:
    """
    Enterprise-grade Speech-to-Text service for ChatterFix
    Optimized for factory floor environments with noise handling
    """

    # Custom vocabulary for manufacturing/maintenance domain
    MANUFACTURING_VOCABULARY = [
        # Equipment types
        "conveyor",
        "motor",
        "pump",
        "compressor",
        "valve",
        "actuator",
        "bearing",
        "gearbox",
        "hydraulic",
        "pneumatic",
        "plc",
        "scada",
        "hvac",
        "chiller",
        "boiler",
        "transformer",
        "switchgear",
        # Actions
        "preventive",
        "corrective",
        "calibration",
        "lubrication",
        "inspection",
        "overhaul",
        "replacement",
        "adjustment",
        # Parts terminology
        "gasket",
        "o-ring",
        "seal",
        "bushing",
        "coupling",
        "impeller",
        "rotor",
        "stator",
        "windings",
        "capacitor",
        "contactor",
        # Measurements
        "psi",
        "rpm",
        "amperage",
        "voltage",
        "temperature",
        "vibration",
        # ChatterFix specific
        "chatterfix",
        "work order",
        "checkout",
        "inventory",
        "asset",
    ]

    # Wake words for hands-free activation
    WAKE_WORDS = ["hey chatterfix", "chatterfix", "hey fred", "okay chatterfix"]

    def __init__(self):
        self.client = None
        self._initialize_client()
        self._speech_context = self._build_speech_context()

    def _initialize_client(self):
        """Initialize Google Cloud Speech client"""
        if not GOOGLE_SPEECH_AVAILABLE:
            logger.error("Google Cloud Speech SDK not installed")
            return

        try:
            # Check for credentials
            creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv(
                "GCP_PROJECT_ID"
            )

            if creds_path and os.path.exists(creds_path):
                self.client = speech.SpeechClient()
                logger.info(
                    "Google Cloud Speech client initialized with credentials file"
                )
            elif project_id:
                # Use default credentials (GCP environment)
                self.client = speech.SpeechClient()
                logger.info(
                    "Google Cloud Speech client initialized with default credentials"
                )
            else:
                logger.warning(
                    "No Google Cloud credentials configured. Using fallback."
                )
                self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize Speech client: {e}")
            self.client = None

    def _build_speech_context(self) -> Optional[Any]:
        """Build speech context with manufacturing vocabulary"""
        if not GOOGLE_SPEECH_AVAILABLE:
            return None

        return types.SpeechContext(
            phrases=self.MANUFACTURING_VOCABULARY + self.WAKE_WORDS,
            boost=15.0,  # Strong boost for domain-specific terms
        )

    def _estimate_noise_level(self, audio_data: bytes) -> str:
        """
        Estimate ambient noise level from audio data
        Returns: low, medium, high
        """
        try:
            # Simple RMS-based noise estimation
            import struct

            # Assuming 16-bit audio
            samples = struct.unpack(f"{len(audio_data)//2}h", audio_data)

            # Calculate RMS
            rms = (sum(s**2 for s in samples) / len(samples)) ** 0.5

            # Normalize to 0-1 range (max 16-bit value is 32767)
            normalized = rms / 32767

            if normalized < 0.05:
                return "low"
            elif normalized < 0.15:
                return "medium"
            else:
                return "high"
        except Exception:
            return "unknown"

    async def transcribe_audio(
        self,
        audio_data: bytes,
        encoding: AudioEncoding = AudioEncoding.LINEAR16,
        sample_rate_hertz: int = 16000,
        language_code: str = "en-US",
        enable_word_time_offsets: bool = True,
        model: str = "latest_long",
    ) -> TranscriptionResult:
        """
        Transcribe audio data to text (non-streaming)

        Args:
            audio_data: Raw audio bytes or base64 encoded string
            encoding: Audio encoding format
            sample_rate_hertz: Sample rate of the audio
            language_code: BCP-47 language code
            enable_word_time_offsets: Include word-level timestamps
            model: Speech recognition model to use

        Returns:
            TranscriptionResult with transcript and metadata
        """
        start_time = datetime.now()

        # Handle base64 encoded audio
        if isinstance(audio_data, str):
            audio_data = base64.b64decode(audio_data)

        noise_level = self._estimate_noise_level(audio_data)

        # Fallback if client not available
        if not self.client:
            return await self._fallback_transcription(
                audio_data, language_code, start_time, noise_level
            )

        try:
            # Build recognition config
            config = types.RecognitionConfig(
                encoding=getattr(
                    speech.RecognitionConfig.AudioEncoding, encoding.value
                ),
                sample_rate_hertz=sample_rate_hertz,
                language_code=language_code,
                enable_automatic_punctuation=True,
                enable_word_time_offsets=enable_word_time_offsets,
                max_alternatives=3,
                model=model,
                use_enhanced=True,  # Use enhanced model for better accuracy
                speech_contexts=[self._speech_context] if self._speech_context else [],
            )

            audio = types.RecognitionAudio(content=audio_data)

            # Perform transcription
            response = self.client.recognize(config=config, audio=audio)

            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            audio_duration = len(audio_data) / (
                sample_rate_hertz * 2
            )  # 16-bit = 2 bytes per sample

            # Process results
            if not response.results:
                return TranscriptionResult(
                    transcript="",
                    confidence=0.0,
                    language_code=language_code,
                    is_final=True,
                    alternatives=[],
                    words=[],
                    processing_time_ms=processing_time,
                    audio_duration_ms=audio_duration * 1000,
                    noise_level=noise_level,
                    timestamp=datetime.now().isoformat(),
                )

            # Get best result
            best_result = response.results[0]
            best_alternative = best_result.alternatives[0]

            # Extract word timings
            words = []
            if enable_word_time_offsets and hasattr(best_alternative, "words"):
                for word_info in best_alternative.words:
                    words.append(
                        {
                            "word": word_info.word,
                            "start_time": word_info.start_time.total_seconds(),
                            "end_time": word_info.end_time.total_seconds(),
                            "confidence": getattr(word_info, "confidence", 0.0),
                        }
                    )

            # Build alternatives list
            alternatives = []
            for alt in best_result.alternatives:
                alternatives.append(
                    {"transcript": alt.transcript, "confidence": alt.confidence}
                )

            result = TranscriptionResult(
                transcript=best_alternative.transcript,
                confidence=best_alternative.confidence,
                language_code=language_code,
                is_final=True,
                alternatives=alternatives,
                words=words,
                processing_time_ms=processing_time,
                audio_duration_ms=audio_duration * 1000,
                noise_level=noise_level,
                timestamp=datetime.now().isoformat(),
            )

            # Log to AI memory for learning
            await self._log_to_memory(result)

            return result

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return await self._fallback_transcription(
                audio_data, language_code, start_time, noise_level
            )

    async def transcribe_audio_streaming(
        self,
        audio_generator: AsyncGenerator[bytes, None],
        config: Optional[StreamingConfig] = None,
    ) -> AsyncGenerator[TranscriptionResult, None]:
        """
        Stream audio for real-time transcription

        Args:
            audio_generator: Async generator yielding audio chunks
            config: Streaming configuration

        Yields:
            TranscriptionResult for each recognition result
        """
        if config is None:
            config = StreamingConfig()

        if not self.client:
            logger.error("Streaming not available without Google Cloud Speech client")
            return

        try:
            # Build streaming config
            streaming_config = types.StreamingRecognitionConfig(
                config=types.RecognitionConfig(
                    encoding=getattr(
                        speech.RecognitionConfig.AudioEncoding, config.encoding.value
                    ),
                    sample_rate_hertz=config.sample_rate_hertz,
                    language_code=config.language_code,
                    enable_automatic_punctuation=config.enable_automatic_punctuation,
                    enable_word_time_offsets=config.enable_word_time_offsets,
                    max_alternatives=config.max_alternatives,
                    model=config.model,
                    use_enhanced=True,
                    speech_contexts=(
                        [self._speech_context] if self._speech_context else []
                    ),
                ),
                interim_results=config.interim_results,
                single_utterance=config.single_utterance,
            )

            # Create request generator
            async def request_generator():
                # First request has config
                yield types.StreamingRecognizeRequest(streaming_config=streaming_config)

                # Subsequent requests have audio
                async for chunk in audio_generator:
                    yield types.StreamingRecognizeRequest(audio_content=chunk)

            # Perform streaming recognition
            # Note: This is synchronous in the current SDK, wrap in executor
            loop = asyncio.get_event_loop()

            requests = [r async for r in request_generator()]
            responses = await loop.run_in_executor(
                None, lambda: list(self.client.streaming_recognize(requests))
            )

            for response in responses:
                for result in response.results:
                    if result.alternatives:
                        best = result.alternatives[0]

                        words = []
                        if config.enable_word_time_offsets and hasattr(best, "words"):
                            for word_info in best.words:
                                words.append(
                                    {
                                        "word": word_info.word,
                                        "start_time": word_info.start_time.total_seconds(),
                                        "end_time": word_info.end_time.total_seconds(),
                                    }
                                )

                        yield TranscriptionResult(
                            transcript=best.transcript,
                            confidence=best.confidence,
                            language_code=config.language_code,
                            is_final=result.is_final,
                            alternatives=[
                                {"transcript": a.transcript, "confidence": a.confidence}
                                for a in result.alternatives
                            ],
                            words=words,
                            processing_time_ms=0,
                            audio_duration_ms=0,
                            noise_level="unknown",
                            timestamp=datetime.now().isoformat(),
                        )

        except Exception as e:
            logger.error(f"Streaming transcription error: {e}")

    async def detect_wake_word(self, audio_data: bytes) -> Tuple[bool, str, float]:
        """
        Check if audio contains a wake word

        Args:
            audio_data: Audio bytes to check

        Returns:
            Tuple of (detected, wake_word, confidence)
        """
        result = await self.transcribe_audio(audio_data)

        if not result.transcript:
            return False, "", 0.0

        transcript_lower = result.transcript.lower()

        for wake_word in self.WAKE_WORDS:
            if wake_word in transcript_lower:
                return True, wake_word, result.confidence

        return False, "", 0.0

    async def transcribe_with_commands(self, audio_data: bytes, **kwargs) -> Dict:
        """
        Transcribe audio and detect ChatterFix commands

        Returns dict with:
        - transcription: The full transcription result
        - has_wake_word: Whether a wake word was detected
        - command: Extracted command (if any)
        - command_type: Type of command (work_order, inventory, status, etc.)
        """
        result = await self.transcribe_audio(audio_data, **kwargs)

        # Check for wake word
        has_wake_word = False
        command = result.transcript

        transcript_lower = result.transcript.lower()
        for wake_word in self.WAKE_WORDS:
            if wake_word in transcript_lower:
                has_wake_word = True
                # Extract command after wake word
                idx = transcript_lower.find(wake_word)
                command = result.transcript[idx + len(wake_word) :].strip()
                break

        # Detect command type
        command_type = self._detect_command_type(command)

        return {
            "transcription": {
                "transcript": result.transcript,
                "confidence": result.confidence,
                "language_code": result.language_code,
                "is_final": result.is_final,
                "words": result.words,
                "processing_time_ms": result.processing_time_ms,
                "audio_duration_ms": result.audio_duration_ms,
                "noise_level": result.noise_level,
                "timestamp": result.timestamp,
            },
            "has_wake_word": has_wake_word,
            "command": command,
            "command_type": command_type,
        }

    def _detect_command_type(self, command: str) -> str:
        """Detect the type of voice command"""
        command_lower = command.lower()

        # Work order commands
        if any(
            kw in command_lower
            for kw in ["work order", "create order", "new order", "maintenance request"]
        ):
            return "work_order"

        # Inventory commands
        if any(
            kw in command_lower
            for kw in ["inventory", "parts", "checkout", "check out", "stock"]
        ):
            return "inventory"

        # Asset/Equipment commands
        if any(
            kw in command_lower for kw in ["asset", "equipment", "machine", "status"]
        ):
            return "asset_status"

        # Inspection commands
        if any(
            kw in command_lower for kw in ["inspect", "inspection", "check", "examine"]
        ):
            return "inspection"

        # Reading commands
        if any(
            kw in command_lower for kw in ["reading", "gauge", "meter", "measurement"]
        ):
            return "reading"

        # Emergency commands
        if any(
            kw in command_lower
            for kw in ["emergency", "urgent", "critical", "stop", "shutdown"]
        ):
            return "emergency"

        # Query/Question commands
        if any(
            kw in command_lower for kw in ["what", "where", "when", "how", "who", "?"]
        ):
            return "query"

        return "general"

    async def _fallback_transcription(
        self,
        audio_data: bytes,
        language_code: str,
        start_time: datetime,
        noise_level: str,
    ) -> TranscriptionResult:
        """Fallback transcription when Google Cloud Speech not available"""
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        logger.warning(
            "Using fallback transcription - Google Cloud Speech not configured"
        )

        return TranscriptionResult(
            transcript="[Speech-to-text service not configured. Please set up Google Cloud Speech credentials.]",
            confidence=0.0,
            language_code=language_code,
            is_final=True,
            alternatives=[],
            words=[],
            processing_time_ms=processing_time,
            audio_duration_ms=len(audio_data) / 32000 * 1000,  # Rough estimate
            noise_level=noise_level,
            timestamp=datetime.now().isoformat(),
        )

    async def _log_to_memory(self, result: TranscriptionResult):
        """Log transcription to AI memory for learning"""
        if not MEMORY_AVAILABLE:
            return

        try:
            memory_service = get_ai_memory_service()
            await memory_service.capture_interaction(
                interaction_type="voice_transcription",
                content={
                    "transcript": result.transcript,
                    "confidence": result.confidence,
                    "language": result.language_code,
                    "noise_level": result.noise_level,
                },
                metadata={
                    "processing_time_ms": result.processing_time_ms,
                    "audio_duration_ms": result.audio_duration_ms,
                    "word_count": len(result.words),
                },
            )
        except Exception as e:
            logger.debug(f"Could not log to memory: {e}")

    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported languages for transcription"""
        return [
            {"code": "en-US", "name": "English (United States)"},
            {"code": "en-GB", "name": "English (United Kingdom)"},
            {"code": "es-ES", "name": "Spanish (Spain)"},
            {"code": "es-MX", "name": "Spanish (Mexico)"},
            {"code": "fr-FR", "name": "French"},
            {"code": "de-DE", "name": "German"},
            {"code": "pt-BR", "name": "Portuguese (Brazil)"},
            {"code": "zh-CN", "name": "Chinese (Simplified)"},
            {"code": "ja-JP", "name": "Japanese"},
            {"code": "ko-KR", "name": "Korean"},
        ]

    def get_service_status(self) -> Dict:
        """Get the status of the speech-to-text service"""
        return {
            "service": "Speech-to-Text",
            "provider": "Google Cloud Speech",
            "available": self.client is not None,
            "google_sdk_installed": GOOGLE_SPEECH_AVAILABLE,
            "memory_integration": MEMORY_AVAILABLE,
            "supported_encodings": [e.value for e in AudioEncoding],
            "wake_words": self.WAKE_WORDS,
            "custom_vocabulary_size": len(self.MANUFACTURING_VOCABULARY),
        }


# Singleton instance
_speech_service: Optional[SpeechToTextService] = None


def get_speech_service() -> SpeechToTextService:
    """Get the singleton SpeechToTextService instance"""
    global _speech_service
    if _speech_service is None:
        _speech_service = SpeechToTextService()
    return _speech_service
