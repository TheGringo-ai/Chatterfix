/**
 * Whisper Transcription Service
 * Uses OpenAI's Whisper API for speech-to-text
 */

import * as FileSystem from 'expo-file-system';

export interface TranscriptionResult {
  text: string;
  language?: string;
  duration?: number;
}

class WhisperTranscriptionService {
  private apiKey: string | null = null;
  private readonly WHISPER_API_URL = 'https://api.openai.com/v1/audio/transcriptions';

  /**
   * Set the OpenAI API key
   */
  setApiKey(key: string): void {
    this.apiKey = key;
  }

  /**
   * Transcribe audio file using Whisper API
   */
  async transcribe(audioUri: string): Promise<TranscriptionResult> {
    if (!this.apiKey) {
      // Try to get from environment
      this.apiKey = process.env.EXPO_PUBLIC_OPENAI_API_KEY || null;
    }

    if (!this.apiKey) {
      throw new Error('OpenAI API key not configured');
    }

    try {
      // Read file as base64
      const base64Audio = await FileSystem.readAsStringAsync(audioUri, {
        encoding: FileSystem.EncodingType.Base64,
      });

      // Create form data for the API request
      const formData = new FormData();

      // Convert base64 to blob
      const response = await fetch(`data:audio/m4a;base64,${base64Audio}`);
      const blob = await response.blob();

      // Append the audio file
      formData.append('file', blob, 'audio.m4a');
      formData.append('model', 'whisper-1');
      formData.append('response_format', 'json');

      // Send to Whisper API
      const apiResponse = await fetch(this.WHISPER_API_URL, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
        },
        body: formData,
      });

      if (!apiResponse.ok) {
        const errorData = await apiResponse.json().catch(() => ({}));
        throw new Error(
          `Whisper API error: ${apiResponse.status} - ${errorData.error?.message || 'Unknown error'}`
        );
      }

      const result = await apiResponse.json();

      console.log('Transcription complete:', result.text?.substring(0, 50) + '...');

      return {
        text: result.text || '',
        language: result.language,
        duration: result.duration,
      };
    } catch (error) {
      console.error('Transcription failed:', error);
      throw error;
    }
  }

  /**
   * Transcribe from a download URL (Firebase Storage)
   */
  async transcribeFromUrl(downloadUrl: string): Promise<TranscriptionResult> {
    if (!this.apiKey) {
      this.apiKey = process.env.EXPO_PUBLIC_OPENAI_API_KEY || null;
    }

    if (!this.apiKey) {
      throw new Error('OpenAI API key not configured');
    }

    try {
      // Download the audio file
      const audioResponse = await fetch(downloadUrl);
      const blob = await audioResponse.blob();

      // Create form data
      const formData = new FormData();
      formData.append('file', blob, 'audio.m4a');
      formData.append('model', 'whisper-1');
      formData.append('response_format', 'json');

      // Send to Whisper API
      const apiResponse = await fetch(this.WHISPER_API_URL, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
        },
        body: formData,
      });

      if (!apiResponse.ok) {
        const errorData = await apiResponse.json().catch(() => ({}));
        throw new Error(
          `Whisper API error: ${apiResponse.status} - ${errorData.error?.message || 'Unknown error'}`
        );
      }

      const result = await apiResponse.json();

      return {
        text: result.text || '',
        language: result.language,
        duration: result.duration,
      };
    } catch (error) {
      console.error('Transcription from URL failed:', error);
      throw error;
    }
  }
}

export const whisperTranscription = new WhisperTranscriptionService();
export default whisperTranscription;
