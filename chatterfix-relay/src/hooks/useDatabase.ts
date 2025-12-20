/**
 * React hooks for Firestore database operations
 * Supports real-time updates and offline persistence
 */

import { useState, useEffect, useCallback } from 'react';
import {
  getAssets,
  getAssetById,
  createAsset,
  subscribeToAssets,
  getLogs,
  createLog,
  subscribeToLogs,
  getUnsyncedLogs,
  markLogSynced,
  type Asset,
  type VoiceLog,
} from '@/db';
import { useAppStore } from '@/stores';

// Default organization for demo (will be replaced with auth)
const DEMO_ORG_ID = 'demo_org';

/**
 * Hook to fetch and manage assets with real-time updates
 */
export function useAssets() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Get org from store or use demo
  const organizationId = useAppStore((state) => state.organizationId) || DEMO_ORG_ID;

  useEffect(() => {
    setLoading(true);

    // Subscribe to real-time updates
    const unsubscribe = subscribeToAssets(organizationId, (updatedAssets) => {
      setAssets(updatedAssets);
      setLoading(false);
      setError(null);
    });

    // Handle errors with initial fetch
    getAssets(organizationId)
      .then((data) => {
        setAssets(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });

    return () => unsubscribe();
  }, [organizationId]);

  const addAsset = useCallback(
    async (asset: Omit<Asset, 'id' | 'created_at' | 'updated_at' | 'organization_id'>) => {
      const newAsset = await createAsset({
        ...asset,
        organization_id: organizationId,
      });
      return newAsset;
    },
    [organizationId],
  );

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getAssets(organizationId);
      setAssets(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh');
    } finally {
      setLoading(false);
    }
  }, [organizationId]);

  return { assets, loading, error, refresh, addAsset };
}

/**
 * Hook to fetch a single asset by ID
 */
export function useAsset(id: string) {
  const [asset, setAsset] = useState<Asset | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) {
      setLoading(false);
      return;
    }

    setLoading(true);
    getAssetById(id)
      .then((data) => {
        setAsset(data);
        setError(null);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to load asset');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [id]);

  return { asset, loading, error };
}

/**
 * Hook to fetch and manage voice logs with real-time updates
 */
export function useLogs(assetId?: string) {
  const [logs, setLogs] = useState<VoiceLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const organizationId = useAppStore((state) => state.organizationId) || DEMO_ORG_ID;

  useEffect(() => {
    setLoading(true);

    // Subscribe to real-time updates
    const unsubscribe = subscribeToLogs(
      organizationId,
      (updatedLogs) => {
        setLogs(updatedLogs);
        setLoading(false);
        setError(null);
      },
      assetId,
    );

    // Initial fetch
    getLogs(organizationId, assetId)
      .then((data) => {
        setLogs(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });

    return () => unsubscribe();
  }, [organizationId, assetId]);

  const addLog = useCallback(
    async (log: Omit<VoiceLog, 'id' | 'created_at' | 'synced' | 'organization_id'>) => {
      const newLog = await createLog({
        ...log,
        organization_id: organizationId,
      });
      return newLog;
    },
    [organizationId],
  );

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getLogs(organizationId, assetId);
      setLogs(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh');
    } finally {
      setLoading(false);
    }
  }, [organizationId, assetId]);

  return { logs, loading, error, refresh, addLog };
}

/**
 * Hook for sync status tracking
 */
export function useSyncStatus() {
  const [unsyncedCount, setUnsyncedCount] = useState(0);
  const [syncing, setSyncing] = useState(false);

  const organizationId = useAppStore((state) => state.organizationId) || DEMO_ORG_ID;

  const checkUnsynced = useCallback(async () => {
    try {
      const unsynced = await getUnsyncedLogs(organizationId);
      setUnsyncedCount(unsynced.length);
    } catch (err) {
      console.error('Failed to check unsynced logs:', err);
    }
  }, [organizationId]);

  useEffect(() => {
    checkUnsynced();
    // Check every 30 seconds
    const interval = setInterval(checkUnsynced, 30000);
    return () => clearInterval(interval);
  }, [checkUnsynced]);

  const syncLog = useCallback(
    async (id: string) => {
      setSyncing(true);
      try {
        await markLogSynced(id);
        await checkUnsynced();
      } finally {
        setSyncing(false);
      }
    },
    [checkUnsynced],
  );

  return { unsyncedCount, syncing, checkUnsynced, syncLog };
}
