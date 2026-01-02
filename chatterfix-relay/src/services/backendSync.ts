/**
 * Backend Sync Service
 * Pushes voice logs to ChatterFix backend API
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { VoiceLog, getUnsyncedLogs, markLogSynced } from '@/db';

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
   * Uses /api/v1/safety/voice-logs endpoint
   */
  async syncVoiceLog(log: VoiceLog): Promise<boolean> {
    try {
      await this.makeRequest('/api/v1/safety/voice-logs', {
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

  /**
   * Sync all pending logs (called when coming back online)
   * This is the main entry point for Ghost Mode sync
   */
  async syncPendingLogs(organizationId?: string): Promise<SyncResult> {
    console.log('[BackendSync] Starting pending logs sync...');

    const result: SyncResult = {
      success: true,
      syncedCount: 0,
      failedCount: 0,
      errors: [],
    };

    try {
      // Get organization ID from storage if not provided
      const orgId = organizationId || await AsyncStorage.getItem('organization_id');
      if (!orgId) {
        console.log('[BackendSync] No organization ID, skipping sync');
        return result;
      }

      // Get all unsynced logs from local database
      const unsyncedLogs = await getUnsyncedLogs(orgId);
      console.log(`[BackendSync] Found ${unsyncedLogs.length} unsynced logs`);

      if (unsyncedLogs.length === 0) {
        return result;
      }

      // Sync each log
      for (const log of unsyncedLogs) {
        try {
          const synced = await this.syncVoiceLog(log);
          if (synced) {
            // Mark as synced in local database
            await markLogSynced(log.id);
            result.syncedCount++;
            console.log(`[BackendSync] Synced log ${log.id}`);
          } else {
            result.failedCount++;
            result.errors.push(`Log ${log.id}: Sync returned false`);
          }
        } catch (error) {
          result.failedCount++;
          result.errors.push(`Log ${log.id}: ${(error as Error).message}`);
          console.error(`[BackendSync] Failed to sync log ${log.id}:`, error);
        }
      }

      // Also sync any offline fall events
      await this.syncOfflineFallEvents();

      // Also sync any offline black box recordings
      await this.syncOfflineBlackBoxRecordings();

      // Update sync status
      await this.updateSyncStatus(result.syncedCount);

      result.success = result.failedCount === 0;
      console.log(`[BackendSync] Sync complete: ${result.syncedCount} synced, ${result.failedCount} failed`);

    } catch (error) {
      result.success = false;
      result.errors.push(`Sync error: ${(error as Error).message}`);
      console.error('[BackendSync] Sync failed:', error);
    }

    return result;
  }

  /**
   * Sync offline fall detection events
   * Uses /api/v1/safety/man-down endpoint (SafetyFix Guardian Angel)
   */
  private async syncOfflineFallEvents(): Promise<void> {
    try {
      const eventsJson = await AsyncStorage.getItem('offline_fall_events');
      if (!eventsJson) return;

      const events = JSON.parse(eventsJson);
      console.log(`[BackendSync] Syncing ${events.length} offline fall events`);

      for (const event of events) {
        try {
          // Use the correct endpoint: /api/v1/safety/man-down
          await this.makeRequest('/api/v1/safety/man-down', {
            method: 'POST',
            body: JSON.stringify({
              user_id: event.user_id,
              location: event.location || 'Unknown',
              g_force: event.g_force || 2.0,
              fall_duration_ms: event.fall_duration_ms || 500,
              device_orientation: event.device_orientation || 'unknown',
              audio_recording_url: event.audio_recording_url,
            }),
          });
        } catch (error) {
          console.error('[BackendSync] Failed to sync fall event:', error);
        }
      }

      // Clear synced events
      await AsyncStorage.removeItem('offline_fall_events');
    } catch (error) {
      console.error('[BackendSync] Error syncing fall events:', error);
    }
  }

  /**
   * Sync offline black box recordings
   */
  private async syncOfflineBlackBoxRecordings(): Promise<void> {
    try {
      const queueJson = await AsyncStorage.getItem('blackbox_offline_queue');
      if (!queueJson) return;

      const queue = JSON.parse(queueJson);
      console.log(`[BackendSync] Syncing ${queue.length} offline black box recordings`);

      // Note: Actual upload would happen in BlackBox service
      // This just triggers the sync
      for (const recording of queue) {
        console.log(`[BackendSync] Would sync black box recording: ${recording.id}`);
      }
    } catch (error) {
      console.error('[BackendSync] Error syncing black box recordings:', error);
    }
  }
}

export const backendSync = new BackendSyncService();
export default backendSync;
