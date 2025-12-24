/**
 * Voice Recording Service
 * Uses expo-av for audio recording with high-quality settings
 */

import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';

export interface RecordingResult {
  uri: string;
  duration: number;
  fileSize: number;
}

class VoiceRecorderService {
  private recording: Audio.Recording | null = null;
  private isRecording = false;

  /**
   * Request microphone permissions
   */
  async requestPermissions(): Promise<boolean> {
    const { status } = await Audio.requestPermissionsAsync();
    return status === 'granted';
  }

  /**
   * Check if currently recording
   */
  getIsRecording(): boolean {
    return this.isRecording;
  }

  /**
   * Start recording audio
   */
  async startRecording(): Promise<void> {
    try {
      // Check permissions
      const hasPermission = await this.requestPermissions();
      if (!hasPermission) {
        throw new Error('Microphone permission not granted');
      }

      // Configure audio mode for recording
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      // Create recording with high quality settings for speech
      const { recording } = await Audio.Recording.createAsync({
        android: {
          extension: '.m4a',
          outputFormat: Audio.AndroidOutputFormat.MPEG_4,
          audioEncoder: Audio.AndroidAudioEncoder.AAC,
          sampleRate: 16000,
          numberOfChannels: 1,
          bitRate: 64000,
        },
        ios: {
          extension: '.m4a',
          outputFormat: Audio.IOSOutputFormat.MPEG4AAC,
          audioQuality: Audio.IOSAudioQuality.HIGH,
          sampleRate: 16000,
          numberOfChannels: 1,
          bitRate: 64000,
        },
        web: {
          mimeType: 'audio/webm',
          bitsPerSecond: 64000,
        },
      });

      this.recording = recording;
      this.isRecording = true;
      console.log('Recording started');
    } catch (error) {
      console.error('Failed to start recording:', error);
      throw error;
    }
  }

  /**
   * Check if a recording is currently in progress
   */
  hasActiveRecording(): boolean {
    return this.recording !== null && this.isRecording;
  }

  /**
   * Stop recording and return the audio file
   * Returns null if no recording is in progress (prevents crash on double-tap)
   */
  async stopRecording(): Promise<RecordingResult | null> {
    if (!this.recording) {
      console.warn('stopRecording called but no recording in progress');
      return null;
    }

    try {
      await this.recording.stopAndUnloadAsync();

      // Reset audio mode
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
      });

      const uri = this.recording.getURI();
      if (!uri) {
        throw new Error('Recording URI not available');
      }

      // Get file info
      const fileInfo = await FileSystem.getInfoAsync(uri);
      const status = await this.recording.getStatusAsync();

      this.isRecording = false;
      const result: RecordingResult = {
        uri,
        duration: status.durationMillis || 0,
        fileSize: fileInfo.exists ? (fileInfo as any).size || 0 : 0,
      };

      this.recording = null;
      console.log('Recording stopped:', result);
      return result;
    } catch (error) {
      console.error('Failed to stop recording:', error);
      this.isRecording = false;
      this.recording = null;
      throw error;
    }
  }

  /**
   * Cancel recording without saving
   */
  async cancelRecording(): Promise<void> {
    if (this.recording) {
      try {
        await this.recording.stopAndUnloadAsync();
        const uri = this.recording.getURI();
        if (uri) {
          await FileSystem.deleteAsync(uri, { idempotent: true });
        }
      } catch (error) {
        console.error('Error canceling recording:', error);
      }
      this.recording = null;
      this.isRecording = false;
    }
  }

  /**
   * Play back a recording
   */
  async playRecording(uri: string): Promise<void> {
    try {
      const { sound } = await Audio.Sound.createAsync({ uri });
      await sound.playAsync();

      // Unload when done
      sound.setOnPlaybackStatusUpdate((status) => {
        if (status.isLoaded && status.didJustFinish) {
          sound.unloadAsync();
        }
      });
    } catch (error) {
      console.error('Failed to play recording:', error);
      throw error;
    }
  }
}

export const voiceRecorder = new VoiceRecorderService();
export default voiceRecorder;
