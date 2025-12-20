/**
 * Audio Upload Service
 * Uploads audio files to Firebase Storage
 */

import { getStorage, ref, uploadBytes, getDownloadURL } from 'firebase/storage';
import * as FileSystem from 'expo-file-system';
import { app } from './firebase';

const storage = getStorage(app);

export interface UploadResult {
  downloadUrl: string;
  storagePath: string;
  fileSize: number;
}

class AudioUploaderService {
  private readonly AUDIO_FOLDER = 'voice_logs';

  /**
   * Upload an audio file to Firebase Storage
   */
  async uploadAudio(
    localUri: string,
    organizationId: string,
    fileName?: string
  ): Promise<UploadResult> {
    try {
      // Generate unique filename if not provided
      const timestamp = Date.now();
      const audioFileName = fileName || `audio_${timestamp}.m4a`;
      const storagePath = `${this.AUDIO_FOLDER}/${organizationId}/${audioFileName}`;

      // Read the file as base64
      const fileInfo = await FileSystem.getInfoAsync(localUri);
      if (!fileInfo.exists) {
        throw new Error('Audio file not found');
      }

      const base64Data = await FileSystem.readAsStringAsync(localUri, {
        encoding: FileSystem.EncodingType.Base64,
      });

      // Convert base64 to blob
      const response = await fetch(`data:audio/m4a;base64,${base64Data}`);
      const blob = await response.blob();

      // Upload to Firebase Storage
      const storageRef = ref(storage, storagePath);
      const snapshot = await uploadBytes(storageRef, blob, {
        contentType: 'audio/m4a',
        customMetadata: {
          organizationId,
          uploadedAt: new Date().toISOString(),
        },
      });

      // Get download URL
      const downloadUrl = await getDownloadURL(snapshot.ref);

      console.log('Audio uploaded successfully:', storagePath);

      return {
        downloadUrl,
        storagePath,
        fileSize: (fileInfo as any).size || 0,
      };
    } catch (error) {
      console.error('Failed to upload audio:', error);
      throw error;
    }
  }

  /**
   * Delete an audio file from Firebase Storage
   */
  async deleteAudio(storagePath: string): Promise<void> {
    try {
      const { deleteObject } = await import('firebase/storage');
      const storageRef = ref(storage, storagePath);
      await deleteObject(storageRef);
      console.log('Audio deleted:', storagePath);
    } catch (error) {
      console.error('Failed to delete audio:', error);
      throw error;
    }
  }
}

export const audioUploader = new AudioUploaderService();
export default audioUploader;
