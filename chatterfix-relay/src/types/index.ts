/**
 * Type Definitions for ChatterFix Relay
 */

// Asset status types
export type AssetStatus = 'operational' | 'warning' | 'critical' | 'offline';

// Voice command types
export type CommandType = 'work_order' | 'checkout' | 'inspection' | 'query' | 'other';

// Sync status
export interface SyncStatus {
  lastSyncAt: number | null;
  isSyncing: boolean;
  pendingCount: number;
  errorMessage: string | null;
}

// API response types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

// Offline queue item
export interface QueuedAction {
  id: string;
  type: 'CREATE_ASSET' | 'UPDATE_ASSET' | 'CREATE_LOG' | 'SYNC_LOG';
  payload: Record<string, unknown>;
  timestamp: number;
  retryCount: number;
}
