/**
 * useNetworkStatus.ts
 * Automatic network detection for Ghost Mode
 *
 * Features:
 * - Real-time connectivity monitoring
 * - Automatic Ghost Mode toggle
 * - Triggers sync when coming back online
 * - Works with WiFi, cellular, and ethernet
 */

import { useEffect, useRef, useCallback } from 'react';
import NetInfo, { NetInfoState, NetInfoSubscription } from '@react-native-community/netinfo';
import { useAppStore } from '@/stores';
import { backendSync } from '@/services/backendSync';

export interface NetworkStatus {
  isConnected: boolean;
  type: string | null;
  isInternetReachable: boolean | null;
}

/**
 * Hook for automatic network status monitoring
 * Automatically enables/disables Ghost Mode based on connectivity
 */
export function useNetworkStatus() {
  const {
    isOnline,
    setIsOnline,
    ghostModeEnabled,
    setGhostModeEnabled,
    syncStatus,
    startSync,
    endSync,
    setSyncStatus,
  } = useAppStore();

  const previouslyOnline = useRef<boolean | null>(null);
  const syncInProgress = useRef(false);

  /**
   * Attempt to sync queued data when coming back online
   */
  const attemptSync = useCallback(async () => {
    if (syncInProgress.current) {
      console.log('[NetworkStatus] Sync already in progress, skipping');
      return;
    }

    try {
      syncInProgress.current = true;
      startSync();
      console.log('[NetworkStatus] Starting sync after reconnection...');

      // Sync voice logs
      const result = await backendSync.syncPendingLogs();

      if (result.success) {
        console.log(`[NetworkStatus] Synced ${result.syncedCount} items`);
        endSync(true);
        setSyncStatus({ pendingCount: 0 });
      } else {
        console.warn('[NetworkStatus] Sync completed with errors:', result.errors);
        endSync(false, 'Some items failed to sync');
      }
    } catch (error: any) {
      console.error('[NetworkStatus] Sync failed:', error);
      endSync(false, error.message);
    } finally {
      syncInProgress.current = false;
    }
  }, [startSync, endSync, setSyncStatus]);

  /**
   * Handle network state changes
   */
  const handleNetworkChange = useCallback((state: NetInfoState) => {
    const wasOnline = previouslyOnline.current;
    const nowOnline = state.isConnected === true && state.isInternetReachable !== false;

    console.log('[NetworkStatus] Network changed:', {
      type: state.type,
      isConnected: state.isConnected,
      isInternetReachable: state.isInternetReachable,
      nowOnline,
      wasOnline,
    });

    // Update online status
    setIsOnline(nowOnline);

    // Toggle Ghost Mode automatically
    if (nowOnline) {
      // Coming back online
      if (ghostModeEnabled) {
        console.log('[NetworkStatus] Back online - disabling Ghost Mode');
        setGhostModeEnabled(false);
      }

      // If we were previously offline and now online, trigger sync
      if (wasOnline === false) {
        console.log('[NetworkStatus] Reconnected! Triggering sync...');
        attemptSync();
      }
    } else {
      // Going offline
      if (!ghostModeEnabled) {
        console.log('[NetworkStatus] Going offline - enabling Ghost Mode');
        setGhostModeEnabled(true);
      }
    }

    previouslyOnline.current = nowOnline;
  }, [setIsOnline, ghostModeEnabled, setGhostModeEnabled, attemptSync]);

  /**
   * Set up network listener on mount
   */
  useEffect(() => {
    let unsubscribe: NetInfoSubscription | null = null;

    const setupListener = async () => {
      // Get initial state
      const initialState = await NetInfo.fetch();
      handleNetworkChange(initialState);

      // Subscribe to network changes
      unsubscribe = NetInfo.addEventListener(handleNetworkChange);
      console.log('[NetworkStatus] Network monitoring active');
    };

    setupListener();

    return () => {
      if (unsubscribe) {
        unsubscribe();
        console.log('[NetworkStatus] Network monitoring stopped');
      }
    };
  }, [handleNetworkChange]);

  /**
   * Manual sync trigger (for UI button)
   */
  const manualSync = useCallback(async () => {
    if (!isOnline) {
      console.warn('[NetworkStatus] Cannot sync - offline');
      return { success: false, error: 'No internet connection' };
    }
    await attemptSync();
    return { success: true };
  }, [isOnline, attemptSync]);

  /**
   * Check current network status
   */
  const checkStatus = useCallback(async (): Promise<NetworkStatus> => {
    const state = await NetInfo.fetch();
    return {
      isConnected: state.isConnected === true,
      type: state.type,
      isInternetReachable: state.isInternetReachable,
    };
  }, []);

  return {
    isOnline,
    ghostModeEnabled,
    syncStatus,
    manualSync,
    checkStatus,
  };
}

export default useNetworkStatus;
