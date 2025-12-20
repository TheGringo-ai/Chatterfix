/**
 * Firestore Database Layer for ChatterFix Relay
 * Provides offline-first data access with automatic sync
 */

import {
  collection,
  doc,
  addDoc,
  getDoc,
  getDocs,
  updateDoc,
  query,
  where,
  orderBy,
  onSnapshot,
  serverTimestamp,
  Timestamp,
  type Unsubscribe,
  type DocumentData,
  type QueryDocumentSnapshot,
} from 'firebase/firestore';
import { db } from '@/services/firebase';

// Types
export interface Asset {
  id: string;
  name: string;
  status: 'operational' | 'warning' | 'critical' | 'offline';
  asset_tag?: string;
  location?: string;
  organization_id: string;
  created_at: Timestamp;
  updated_at: Timestamp;
}

export interface VoiceLog {
  id: string;
  asset_id: string;
  audio_file?: string;
  transcript?: string;
  command_type?: 'work_order' | 'checkout' | 'inspection' | 'query' | 'other';
  synced: boolean;
  organization_id: string;
  created_at: Timestamp;
}

// Collection references
const ASSETS_COLLECTION = 'relay_assets';
const LOGS_COLLECTION = 'relay_logs';

/**
 * Initialize database (Firestore is auto-initialized)
 */
export async function initDatabase(): Promise<void> {
  console.log('Firestore database ready with offline persistence');
  return Promise.resolve();
}

// ============ Asset Operations ============

/**
 * Create a new asset
 */
export async function createAsset(
  asset: Omit<Asset, 'id' | 'created_at' | 'updated_at'>,
): Promise<Asset> {
  const docRef = await addDoc(collection(db, ASSETS_COLLECTION), {
    ...asset,
    created_at: serverTimestamp(),
    updated_at: serverTimestamp(),
  });

  const newDoc = await getDoc(docRef);
  return { id: docRef.id, ...newDoc.data() } as Asset;
}

/**
 * Get all assets for an organization
 */
export async function getAssets(organizationId: string): Promise<Asset[]> {
  const q = query(
    collection(db, ASSETS_COLLECTION),
    where('organization_id', '==', organizationId),
    orderBy('updated_at', 'desc'),
  );

  const snapshot = await getDocs(q);
  return snapshot.docs.map((docSnap: QueryDocumentSnapshot<DocumentData>) => ({
    id: docSnap.id,
    ...docSnap.data(),
  })) as Asset[];
}

/**
 * Get a single asset by ID
 */
export async function getAssetById(id: string): Promise<Asset | null> {
  const docRef = doc(db, ASSETS_COLLECTION, id);
  const docSnap = await getDoc(docRef);

  if (!docSnap.exists()) return null;
  return { id: docSnap.id, ...docSnap.data() } as Asset;
}

/**
 * Update an asset
 */
export async function updateAsset(
  id: string,
  updates: Partial<Omit<Asset, 'id' | 'created_at'>>,
): Promise<void> {
  const docRef = doc(db, ASSETS_COLLECTION, id);
  await updateDoc(docRef, {
    ...updates,
    updated_at: serverTimestamp(),
  });
}

/**
 * Subscribe to real-time asset updates
 */
export function subscribeToAssets(
  organizationId: string,
  callback: (assets: Asset[]) => void,
): Unsubscribe {
  const q = query(
    collection(db, ASSETS_COLLECTION),
    where('organization_id', '==', organizationId),
    orderBy('updated_at', 'desc'),
  );

  return onSnapshot(q, (snapshot) => {
    const assets = snapshot.docs.map((docSnap: QueryDocumentSnapshot<DocumentData>) => ({
      id: docSnap.id,
      ...docSnap.data(),
    })) as Asset[];
    callback(assets);
  });
}

// ============ Voice Log Operations ============

/**
 * Create a new voice log
 */
export async function createLog(
  log: Omit<VoiceLog, 'id' | 'created_at' | 'synced'>,
): Promise<VoiceLog> {
  const docRef = await addDoc(collection(db, LOGS_COLLECTION), {
    ...log,
    synced: false,
    created_at: serverTimestamp(),
  });

  const newDoc = await getDoc(docRef);
  return { id: docRef.id, ...newDoc.data() } as VoiceLog;
}

/**
 * Get all logs, optionally filtered by asset
 */
export async function getLogs(
  organizationId: string,
  assetId?: string,
): Promise<VoiceLog[]> {
  let q = query(
    collection(db, LOGS_COLLECTION),
    where('organization_id', '==', organizationId),
    orderBy('created_at', 'desc'),
  );

  if (assetId) {
    q = query(
      collection(db, LOGS_COLLECTION),
      where('organization_id', '==', organizationId),
      where('asset_id', '==', assetId),
      orderBy('created_at', 'desc'),
    );
  }

  const snapshot = await getDocs(q);
  return snapshot.docs.map((docSnap: QueryDocumentSnapshot<DocumentData>) => ({
    id: docSnap.id,
    ...docSnap.data(),
  })) as VoiceLog[];
}

/**
 * Get unsynced logs (for offline queue processing)
 */
export async function getUnsyncedLogs(organizationId: string): Promise<VoiceLog[]> {
  const q = query(
    collection(db, LOGS_COLLECTION),
    where('organization_id', '==', organizationId),
    where('synced', '==', false),
  );

  const snapshot = await getDocs(q);
  return snapshot.docs.map((docSnap: QueryDocumentSnapshot<DocumentData>) => ({
    id: docSnap.id,
    ...docSnap.data(),
  })) as VoiceLog[];
}

/**
 * Mark a log as synced
 */
export async function markLogSynced(id: string): Promise<void> {
  const docRef = doc(db, LOGS_COLLECTION, id);
  await updateDoc(docRef, { synced: true });
}

/**
 * Subscribe to real-time log updates
 */
export function subscribeToLogs(
  organizationId: string,
  callback: (logs: VoiceLog[]) => void,
  assetId?: string,
): Unsubscribe {
  let q = query(
    collection(db, LOGS_COLLECTION),
    where('organization_id', '==', organizationId),
    orderBy('created_at', 'desc'),
  );

  if (assetId) {
    q = query(
      collection(db, LOGS_COLLECTION),
      where('organization_id', '==', organizationId),
      where('asset_id', '==', assetId),
      orderBy('created_at', 'desc'),
    );
  }

  return onSnapshot(q, (snapshot) => {
    const logs = snapshot.docs.map((docSnap: QueryDocumentSnapshot<DocumentData>) => ({
      id: docSnap.id,
      ...docSnap.data(),
    })) as VoiceLog[];
    callback(logs);
  });
}

export default { initDatabase };
