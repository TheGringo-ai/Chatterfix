"""
Voice Context Models
Pydantic models for context-aware voice command processing
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ContextSource(str, Enum):
    """Source of the context information"""
    QR_SCAN = "qr_scan"
    NFC_TAP = "nfc_tap"
    GPS_LOCATION = "gps_location"
    CAMERA_RECOGNITION = "camera_recognition"
    MANUAL_SELECTION = "manual_selection"
    SESSION_HISTORY = "session_history"


class GeoLocation(BaseModel):
    """Geographic coordinates"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    accuracy: Optional[float] = Field(None, ge=0, description="Accuracy in meters")
    altitude: Optional[float] = Field(None, description="Altitude in meters")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @field_validator('latitude')
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @field_validator('longitude')
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v


class AssetContext(BaseModel):
    """Context about the current asset being inspected"""
    asset_id: str = Field(..., min_length=1, description="Asset unique identifier")
    asset_name: Optional[str] = Field(None, description="Human-readable asset name")
    asset_type: Optional[str] = Field(None, description="Type of asset (pump, motor, etc.)")
    location: Optional[str] = Field(None, description="Asset location description")
    source: ContextSource = Field(
        ContextSource.MANUAL_SELECTION,
        description="How the asset was identified"
    )
    confidence: Optional[float] = Field(
        None, ge=0, le=1,
        description="Confidence score for AI-detected assets"
    )
    scanned_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class VoiceCommandRequest(BaseModel):
    """
    Request model for voice command processing with context.

    This model ensures all context data is properly validated
    before processing voice commands.
    """
    # Required: The voice command text
    voice_text: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Transcribed voice command text"
    )

    # Optional: Technician context
    technician_id: Optional[str] = Field(
        None,
        description="ID of the technician issuing the command"
    )

    # Optional: Asset context (from QR scan, NFC, or AI recognition)
    current_asset: Optional[AssetContext] = Field(
        None,
        description="Current asset context if technician scanned/selected one"
    )

    # Optional: Location context
    location: Optional[GeoLocation] = Field(
        None,
        description="GPS coordinates of the technician"
    )

    # Optional: Additional context from session
    session_context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional session context (last viewed screen, etc.)"
    )

    # Metadata
    audio_duration_ms: Optional[int] = Field(
        None, ge=0,
        description="Duration of the audio recording in milliseconds"
    )
    noise_level: Optional[str] = Field(
        None,
        description="Ambient noise level (low, medium, high)"
    )
    confidence_score: Optional[float] = Field(
        None, ge=0, le=1,
        description="Speech-to-text confidence score"
    )

    @field_validator('voice_text')
    @classmethod
    def sanitize_voice_text(cls, v: str) -> str:
        """Basic sanitization of voice text"""
        if v:
            # Remove null bytes and control characters
            v = ''.join(char for char in v if ord(char) >= 32 or char in '\n\r\t')
            v = v.strip()
        return v

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        json_schema_extra={
            "example": {
                "voice_text": "This pump is leaking oil",
                "technician_id": "tech_123",
                "current_asset": {
                    "asset_id": "asset_456",
                    "asset_name": "Hydraulic Pump 3",
                    "asset_type": "pump",
                    "source": "qr_scan"
                },
                "location": {
                    "latitude": 37.7749,
                    "longitude": -122.4194,
                    "accuracy": 5.0
                }
            }
        }
    )


class VoiceCommandResponse(BaseModel):
    """Response model for processed voice commands"""
    success: bool = Field(..., description="Whether the command was processed successfully")
    original_text: str = Field(..., description="Original voice command text")
    processed_text: str = Field(..., description="Processed text with context injected")

    # Context resolution results
    context_used: bool = Field(False, description="Whether context was used to resolve references")
    resolved_asset_id: Optional[str] = Field(None, description="Asset ID if resolved from context")
    resolved_asset_name: Optional[str] = Field(None, description="Asset name if resolved")
    resolved_location: Optional[str] = Field(None, description="Location if resolved from GPS")

    # Action taken
    action: Optional[str] = Field(None, description="Action type (create_work_order, navigate, etc.)")
    action_result: Optional[Dict[str, Any]] = Field(None, description="Result of the action")

    # For voice response
    response_text: Optional[str] = Field(None, description="Text to speak back to technician")

    # Metadata
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    ai_model_used: Optional[str] = Field(None, description="AI model that processed the command")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "original_text": "This pump is leaking oil",
                "processed_text": "This pump is leaking oil\n\n[CONTEXT: Technician inspecting 'Hydraulic Pump 3' (ID: asset_456)]",
                "context_used": True,
                "resolved_asset_id": "asset_456",
                "resolved_asset_name": "Hydraulic Pump 3",
                "action": "create_work_order",
                "action_result": {"work_order_id": "WO-2024-001"},
                "response_text": "Work order created for Hydraulic Pump 3"
            }
        }
    )


class NearbyAsset(BaseModel):
    """Asset found near the technician's location"""
    asset_id: str
    asset_name: str
    asset_type: Optional[str] = None
    distance_meters: float = Field(..., ge=0)
    location_description: Optional[str] = None
