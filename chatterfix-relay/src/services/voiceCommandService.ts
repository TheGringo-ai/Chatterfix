/**
 * Voice Command Service
 * Unified service for voice recording, transcription, and command processing
 */

import { voiceRecorder, RecordingResult } from './voiceRecorder';
import { audioUploader, UploadResult } from './audioUploader';
import { whisperTranscription, TranscriptionResult } from './whisperTranscription';
import { backendSync } from './backendSync';
import { createLog, markLogSynced, VoiceLog } from '@/db';
import { Timestamp } from 'firebase/firestore';

export interface VoiceCommandResult {
  success: boolean;
  transcript: string;
  action?: string;
  response?: string;
  workOrder?: any;
  logId?: string;
  error?: string;
}

export type CommandType = 'work_order' | 'checkout' | 'inspection' | 'query' | 'other';

class VoiceCommandService {
  private isProcessing = false;
  private organizationId: string | null = null;

  /**
   * Set the organization ID for voice commands
   */
  setOrganizationId(orgId: string): void {
    this.organizationId = orgId;
  }

  /**
   * Check if currently processing
   */
  getIsProcessing(): boolean {
    return this.isProcessing;
  }

  /**
   * Check if currently recording
   */
  getIsRecording(): boolean {
    return voiceRecorder.getIsRecording();
  }

  /**
   * Start recording a voice command
   */
  async startRecording(): Promise<void> {
    await voiceRecorder.startRecording();
  }

  /**
   * Stop recording and process the voice command
   * Handles edge cases: no recording, missing org ID, double-tap prevention
   */
  async stopAndProcess(): Promise<VoiceCommandResult> {
    // Guard: Check if there's actually a recording in progress
    if (!voiceRecorder.hasActiveRecording()) {
      console.warn('stopAndProcess called but no active recording');
      return {
        success: false,
        transcript: '',
        error: 'No recording in progress. Please tap the button to start recording first.',
      };
    }

    if (!this.organizationId) {
      // Cancel the recording to clean up
      await voiceRecorder.cancelRecording();
      return {
        success: false,
        transcript: '',
        error: 'Organization ID not set. Please log in again.',
      };
    }

    // Prevent double-processing
    if (this.isProcessing) {
      console.warn('Already processing a voice command');
      return {
        success: false,
        transcript: '',
        error: 'Already processing. Please wait.',
      };
    }

    this.isProcessing = true;

    try {
      // 1. Stop recording (now returns null if no recording)
      const recording = await voiceRecorder.stopRecording();

      // Double-check we got a valid recording
      if (!recording) {
        return {
          success: false,
          transcript: '',
          error: 'Recording failed. Please try again.',
        };
      }

      console.log('Recording stopped:', recording);

      // 2. Upload to Firebase Storage
      let uploadResult: UploadResult | null = null;
      try {
        uploadResult = await audioUploader.uploadAudio(
          recording.uri,
          this.organizationId
        );
        console.log('Audio uploaded:', uploadResult.storagePath);
      } catch (uploadError) {
        console.warn('Upload failed, continuing with local file:', uploadError);
      }

      // 3. Transcribe with Whisper
      let transcription: TranscriptionResult;
      try {
        if (uploadResult?.downloadUrl) {
          transcription = await whisperTranscription.transcribeFromUrl(
            uploadResult.downloadUrl
          );
        } else {
          transcription = await whisperTranscription.transcribe(recording.uri);
        }
        console.log('Transcription:', transcription.text);
      } catch (transcriptionError) {
        console.error('Transcription failed:', transcriptionError);
        return {
          success: false,
          transcript: '',
          error: 'Failed to transcribe audio. Please try again.',
        };
      }

      // 4. Determine command type from transcript
      const commandType = this.detectCommandType(transcription.text);

      // 5. Create voice log in Firestore
      const voiceLog = await createLog({
        asset_id: '',
        audio_file: uploadResult?.downloadUrl,
        transcript: transcription.text,
        command_type: commandType,
        organization_id: this.organizationId,
      });
      console.log('Voice log created:', voiceLog.id);

      // 6. Process command through backend AI
      let aiResponse;
      try {
        aiResponse = await backendSync.processVoiceCommand(
          transcription.text,
          this.organizationId
        );
        console.log('AI response:', aiResponse);

        // Mark log as synced
        await markLogSynced(voiceLog.id);
      } catch (syncError) {
        console.warn('Backend sync failed, command saved locally:', syncError);
        aiResponse = {
          action: 'queued',
          response: 'Your command has been saved and will be processed when online.',
        };
      }

      return {
        success: true,
        transcript: transcription.text,
        action: aiResponse.action,
        response: aiResponse.response,
        workOrder: aiResponse.data?.work_order,
        logId: voiceLog.id,
      };
    } catch (error) {
      console.error('Voice command processing failed:', error);
      return {
        success: false,
        transcript: '',
        error: (error as Error).message || 'Failed to process voice command',
      };
    } finally {
      this.isProcessing = false;
    }
  }

  /**
   * Cancel the current recording
   */
  async cancelRecording(): Promise<void> {
    await voiceRecorder.cancelRecording();
    this.isProcessing = false;
  }

  /**
   * Detect command type from transcript
   */
  private detectCommandType(transcript: string): CommandType {
    const lowerTranscript = transcript.toLowerCase();

    // Work order patterns
    if (
      lowerTranscript.includes('work order') ||
      lowerTranscript.includes('create') ||
      lowerTranscript.includes('new task') ||
      lowerTranscript.includes('maintenance') ||
      lowerTranscript.includes('repair')
    ) {
      return 'work_order';
    }

    // Checkout patterns
    if (
      lowerTranscript.includes('checkout') ||
      lowerTranscript.includes('check out') ||
      lowerTranscript.includes('need part') ||
      lowerTranscript.includes('grab') ||
      lowerTranscript.includes('inventory')
    ) {
      return 'checkout';
    }

    // Inspection patterns
    if (
      lowerTranscript.includes('inspect') ||
      lowerTranscript.includes('check') ||
      lowerTranscript.includes('condition') ||
      lowerTranscript.includes('status')
    ) {
      return 'inspection';
    }

    // Query patterns
    if (
      lowerTranscript.includes('how many') ||
      lowerTranscript.includes('what is') ||
      lowerTranscript.includes('show me') ||
      lowerTranscript.includes('list') ||
      lowerTranscript.includes('find')
    ) {
      return 'query';
    }

    return 'other';
  }

  /**
   * Play back the last recording
   */
  async playLastRecording(uri: string): Promise<void> {
    await voiceRecorder.playRecording(uri);
  }
}

export const voiceCommandService = new VoiceCommandService();
export default voiceCommandService;
