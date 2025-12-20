/**
 * Zustand App Store
 * Global state management for ChatterFix Relay
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Types
interface SyncStatus {
  lastSyncAt: number | null;
  isSyncing: boolean;
  pendingCount: number;
  errorMessage: string | null;
}

interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  fieldMode: boolean; // High-contrast mode for technicians
  hapticFeedback: boolean;
  voiceConfirmation: boolean;
}

interface AppState {
  // Organization (from auth or demo)
  organizationId: string | null;
  setOrganizationId: (id: string | null) => void;

  // Connection status
  isOnline: boolean;
  setIsOnline: (online: boolean) => void;

  // Sync status
  syncStatus: SyncStatus;
  setSyncStatus: (status: Partial<SyncStatus>) => void;
  startSync: () => void;
  endSync: (success: boolean, errorMessage?: string) => void;

  // User preferences
  preferences: UserPreferences;
  setPreference: <K extends keyof UserPreferences>(
    key: K,
    value: UserPreferences[K]
  ) => void;

  // Selected asset (for detail views)
  selectedAssetId: string | null;
  setSelectedAssetId: (id: string | null) => void;

  // Ghost Mode (offline queue indicator)
  ghostModeEnabled: boolean;
  setGhostModeEnabled: (enabled: boolean) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Organization
      organizationId: null,
      setOrganizationId: (id) => set({ organizationId: id }),

      // Connection status
      isOnline: true,
      setIsOnline: (online) => set({ isOnline: online }),

      // Sync status
      syncStatus: {
        lastSyncAt: null,
        isSyncing: false,
        pendingCount: 0,
        errorMessage: null,
      },
      setSyncStatus: (status) =>
        set((state) => ({
          syncStatus: { ...state.syncStatus, ...status },
        })),
      startSync: () =>
        set((state) => ({
          syncStatus: { ...state.syncStatus, isSyncing: true, errorMessage: null },
        })),
      endSync: (success, errorMessage) =>
        set((state) => ({
          syncStatus: {
            ...state.syncStatus,
            isSyncing: false,
            lastSyncAt: success ? Date.now() : state.syncStatus.lastSyncAt,
            errorMessage: errorMessage || null,
          },
        })),

      // User preferences
      preferences: {
        theme: 'dark',
        fieldMode: false,
        hapticFeedback: true,
        voiceConfirmation: true,
      },
      setPreference: (key, value) =>
        set((state) => ({
          preferences: { ...state.preferences, [key]: value },
        })),

      // Selected asset
      selectedAssetId: null,
      setSelectedAssetId: (id) => set({ selectedAssetId: id }),

      // Ghost Mode
      ghostModeEnabled: false,
      setGhostModeEnabled: (enabled) => set({ ghostModeEnabled: enabled }),
    }),
    {
      name: 'chatterfix-relay-storage',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        organizationId: state.organizationId,
        preferences: state.preferences,
        syncStatus: { lastSyncAt: state.syncStatus.lastSyncAt },
      }),
    }
  )
);

export default useAppStore;
