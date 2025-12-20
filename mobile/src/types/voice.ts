/**
 * Voice Command Types
 * Matches backend Pydantic models for type safety
 */

// Geographic location for context resolution
export interface GeoLocation {
  latitude: number;
  longitude: number;
  accuracy?: number;
  altitude?: number;
}

// Context source - how the asset was identified
export type ContextSource =
  | 'qr_scan'
  | 'nfc_tap'
  | 'gps_location'
  | 'camera_recognition'
  | 'manual_selection'
  | 'session_history';

// Asset context from QR scan, NFC, or camera
export interface AssetContext {
  asset_id: string;
  asset_name?: string;
  asset_type?: string;
  location?: string;
  source: ContextSource;
  confidence?: number;
  scanned_at?: string;
}

// Request payload for context-aware voice commands
export interface VoiceCommandPayload {
  voice_text: string;
  technician_id?: string;
  current_asset?: AssetContext;
  location?: GeoLocation;
  session_context?: Record<string, any>;
  audio_duration_ms?: number;
  noise_level?: 'low' | 'medium' | 'high';
  confidence_score?: number;
}

// Response from voice command processing
export interface VoiceCommandResponse {
  success: boolean;
  original_text: string;
  processed_text: string;
  context_used: boolean;
  resolved_asset_id?: string;
  resolved_asset_name?: string;
  resolved_location?: string;
  action?: string;
  action_result?: Record<string, any>;
  response_text?: string;
  processing_time_ms?: number;
  ai_model_used?: string;
}

// Upload error types from backend validation
export interface UploadError {
  code: 'FILE_TOO_LARGE' | 'INVALID_TYPE' | 'INVALID_EXTENSION' | 'UPLOAD_FAILED';
  message: string;
  filename?: string;
  max_size_mb?: number;
}
