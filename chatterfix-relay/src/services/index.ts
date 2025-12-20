/**
 * Services Index
 * Export all services for easy importing
 */

export { voiceRecorder, type RecordingResult } from './voiceRecorder';
export { audioUploader, type UploadResult } from './audioUploader';
export { whisperTranscription, type TranscriptionResult } from './whisperTranscription';
export { backendSync, type SyncResult, type WorkOrderFromVoice } from './backendSync';
export { authService, type UserData } from './authService';
export { voiceCommandService, type VoiceCommandResult, type CommandType } from './voiceCommandService';
export { app, db, auth } from './firebase';
