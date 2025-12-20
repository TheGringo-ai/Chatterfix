/**
 * Backend Sync Service
 * Pushes voice logs to ChatterFix backend API
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { VoiceLog } from '@/db';

const BACKEND_URL = process.env.EXPO_PUBLIC_CHATTERFIX_API_URL || 'https://chatterfix.com';
const AUTH_TOKEN_KEY = 'chatterfix_auth_token';

export interface SyncResult {
  success: boolean;
  syncedCount: number;
  failedCount: number;
  errors: string[];
}

export interface WorkOrderFromVoice {
  title: string;
  description: string;
  priority: 'Low' | 'Medium' | 'High' | 'Critical';
  asset_id?: string;
  assigned_to?: string;
}

class BackendSyncService {
  private authToken: string | null = null;

  /**
   * Set authentication token
   */
  async setAuthToken(token: string): Promise<void> {
    this.authToken = token;
    await AsyncStorage.setItem(AUTH_TOKEN_KEY, token);
  }

  /**
   * Get authentication token
   */
  async getAuthToken(): Promise<string | null> {
    if (this.authToken) return this.authToken;
    this.authToken = await AsyncStorage.getItem(AUTH_TOKEN_KEY);
    return this.authToken;
  }

  /**
   * Clear authentication
   */
  async clearAuth(): Promise<void> {
    this.authToken = null;
    await AsyncStorage.removeItem(AUTH_TOKEN_KEY);
  }

  /**
   * Make authenticated request to backend
   */
  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = await this.getAuthToken();

    const response = await fetch(`${BACKEND_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...options.headers,
      },
      credentials: 'include',
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        `API error: ${response.status} - ${errorData.detail || 'Unknown error'}`
      );
    }

    return response.json();
  }

  /**
   * Sync a voice log to the backend
   */
  async syncVoiceLog(log: VoiceLog): Promise<boolean> {
    try {
      await this.makeRequest('/api/v1/voice-logs', {
        method: 'POST',
        body: JSON.stringify({
          asset_id: log.asset_id,
          audio_url: log.audio_file,
          transcript: log.transcript,
          command_type: log.command_type,
          organization_id: log.organization_id,
          created_at: log.created_at?.toDate?.()?.toISOString() || new Date().toISOString(),
        }),
      });

      console.log('Voice log synced:', log.id);
      return true;
    } catch (error) {
      console.error('Failed to sync voice log:', error);
      return false;
    }
  }

  /**
   * Sync multiple unsynced logs
   */
  async syncBatch(logs: VoiceLog[]): Promise<SyncResult> {
    const result: SyncResult = {
      success: true,
      syncedCount: 0,
      failedCount: 0,
      errors: [],
    };

    for (const log of logs) {
      try {
        const synced = await this.syncVoiceLog(log);
        if (synced) {
          result.syncedCount++;
        } else {
          result.failedCount++;
        }
      } catch (error) {
        result.failedCount++;
        result.errors.push(`Log ${log.id}: ${(error as Error).message}`);
      }
    }

    result.success = result.failedCount === 0;
    return result;
  }

  /**
   * Create work order from voice command
   */
  async createWorkOrderFromVoice(
    transcript: string,
    organizationId: string
  ): Promise<WorkOrderFromVoice | null> {
    try {
      // Send to AI endpoint to parse the voice command
      const result = await this.makeRequest<{ work_order: WorkOrderFromVoice }>(
        '/ai/voice',
        {
          method: 'POST',
          body: JSON.stringify({
            transcript,
            organization_id: organizationId,
            task: 'create_work_order',
          }),
        }
      );

      return result.work_order;
    } catch (error) {
      console.error('Failed to create work order from voice:', error);
      return null;
    }
  }

  /**
   * Process voice command through AI
   */
  async processVoiceCommand(
    transcript: string,
    organizationId: string
  ): Promise<{ action: string; response: string; data?: any }> {
    try {
      const result = await this.makeRequest<{
        action: string;
        response: string;
        data?: any;
      }>('/ai/voice', {
        method: 'POST',
        body: JSON.stringify({
          transcript,
          organization_id: organizationId,
        }),
      });

      return result;
    } catch (error) {
      console.error('Failed to process voice command:', error);
      return {
        action: 'error',
        response: 'Failed to process voice command. Please try again.',
      };
    }
  }

  /**
   * Get sync status
   */
  async getSyncStatus(): Promise<{
    pendingCount: number;
    lastSyncAt: string | null;
  }> {
    const lastSync = await AsyncStorage.getItem('last_sync_at');
    const pendingCount = parseInt(
      (await AsyncStorage.getItem('pending_sync_count')) || '0',
      10
    );

    return {
      pendingCount,
      lastSyncAt: lastSync,
    };
  }

  /**
   * Update sync status
   */
  async updateSyncStatus(syncedCount: number): Promise<void> {
    await AsyncStorage.setItem('last_sync_at', new Date().toISOString());
    const currentPending = parseInt(
      (await AsyncStorage.getItem('pending_sync_count')) || '0',
      10
    );
    await AsyncStorage.setItem(
      'pending_sync_count',
      Math.max(0, currentPending - syncedCount).toString()
    );
  }
}

export const backendSync = new BackendSyncService();
export default backendSync;
