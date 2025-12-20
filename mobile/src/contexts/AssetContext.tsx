/**
 * Asset Context for tracking current scanned/selected asset
 *
 * This context is CRITICAL for context-aware voice commands.
 * When a technician scans a QR code or selects an asset,
 * voice commands like "Fix this" will automatically resolve
 * to the correct asset.
 */

import React, { createContext, useContext, useState, useCallback } from 'react';
import { AssetContext as AssetContextType, ContextSource } from '../types/voice';

interface AssetContextState {
  // The currently scanned/selected asset
  currentAsset: AssetContextType | null;

  // Set asset from QR scan
  setAssetFromQRScan: (assetId: string, assetName?: string, assetType?: string) => void;

  // Set asset from NFC tap
  setAssetFromNFC: (assetId: string, assetName?: string) => void;

  // Set asset from manual selection
  setAssetManually: (asset: Partial<AssetContextType>) => void;

  // Set asset from camera/AI recognition
  setAssetFromCamera: (assetId: string, confidence: number, assetName?: string) => void;

  // Clear current asset (technician moved away)
  clearCurrentAsset: () => void;

  // Check if we have a valid asset context
  hasAssetContext: boolean;
}

const AssetContextDefault: AssetContextState = {
  currentAsset: null,
  setAssetFromQRScan: () => {},
  setAssetFromNFC: () => {},
  setAssetManually: () => {},
  setAssetFromCamera: () => {},
  clearCurrentAsset: () => {},
  hasAssetContext: false,
};

const AssetContext = createContext<AssetContextState>(AssetContextDefault);

export const useAssetContext = () => useContext(AssetContext);

export const AssetProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentAsset, setCurrentAsset] = useState<AssetContextType | null>(null);

  // Set asset from QR code scan (highest confidence)
  const setAssetFromQRScan = useCallback(
    (assetId: string, assetName?: string, assetType?: string) => {
      setCurrentAsset({
        asset_id: assetId,
        asset_name: assetName,
        asset_type: assetType,
        source: 'qr_scan',
        confidence: 1.0, // QR scans are 100% accurate
        scanned_at: new Date().toISOString(),
      });
      console.log(`[AssetContext] Asset set from QR scan: ${assetId}`);
    },
    []
  );

  // Set asset from NFC tap
  const setAssetFromNFC = useCallback((assetId: string, assetName?: string) => {
    setCurrentAsset({
      asset_id: assetId,
      asset_name: assetName,
      source: 'nfc_tap',
      confidence: 1.0, // NFC taps are 100% accurate
      scanned_at: new Date().toISOString(),
    });
    console.log(`[AssetContext] Asset set from NFC: ${assetId}`);
  }, []);

  // Set asset manually (from asset picker)
  const setAssetManually = useCallback((asset: Partial<AssetContextType>) => {
    setCurrentAsset({
      asset_id: asset.asset_id || '',
      asset_name: asset.asset_name,
      asset_type: asset.asset_type,
      location: asset.location,
      source: 'manual_selection',
      confidence: 1.0,
      scanned_at: new Date().toISOString(),
    });
    console.log(`[AssetContext] Asset set manually: ${asset.asset_id}`);
  }, []);

  // Set asset from camera recognition (may have lower confidence)
  const setAssetFromCamera = useCallback(
    (assetId: string, confidence: number, assetName?: string) => {
      // Only update if confidence is high enough
      if (confidence >= 0.7) {
        setCurrentAsset({
          asset_id: assetId,
          asset_name: assetName,
          source: 'camera_recognition',
          confidence,
          scanned_at: new Date().toISOString(),
        });
        console.log(`[AssetContext] Asset set from camera: ${assetId} (${(confidence * 100).toFixed(0)}%)`);
      } else {
        console.log(`[AssetContext] Camera recognition confidence too low: ${(confidence * 100).toFixed(0)}%`);
      }
    },
    []
  );

  // Clear asset context
  const clearCurrentAsset = useCallback(() => {
    setCurrentAsset(null);
    console.log('[AssetContext] Asset context cleared');
  }, []);

  const value: AssetContextState = {
    currentAsset,
    setAssetFromQRScan,
    setAssetFromNFC,
    setAssetManually,
    setAssetFromCamera,
    clearCurrentAsset,
    hasAssetContext: currentAsset !== null,
  };

  return <AssetContext.Provider value={value}>{children}</AssetContext.Provider>;
};

export default AssetContext;
