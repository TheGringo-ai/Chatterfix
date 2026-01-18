/**
 * Camera Screen
 * OCR, Part Recognition, and Equipment Condition Analysis for technicians
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  Image,
  Modal,
} from 'react-native';
import { Camera, CameraType } from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';
import { apiService } from '../services/api';

type AnalysisMode = 'ocr' | 'part' | 'condition';

interface AnalysisResult {
  mode: AnalysisMode;
  success: boolean;
  data: any;
  imageUri: string;
  timestamp: Date;
}

const ANALYSIS_MODES = [
  { mode: 'ocr' as AnalysisMode, label: 'Read Text (OCR)', icon: '📝', description: 'Extract text from documents, labels, or equipment plates' },
  { mode: 'part' as AnalysisMode, label: 'Identify Part', icon: '🔧', description: 'Recognize parts and look up in inventory' },
  { mode: 'condition' as AnalysisMode, label: 'Check Condition', icon: '🔍', description: 'Analyze equipment condition and wear' },
];

export default function CameraScreen() {
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [cameraReady, setCameraReady] = useState(false);
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>('ocr');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [showResultModal, setShowResultModal] = useState(false);
  const [facing, setFacing] = useState<CameraType>('back');

  const cameraRef = useRef<Camera>(null);

  useEffect(() => {
    checkPermissions();
  }, []);

  const checkPermissions = async () => {
    const { status } = await Camera.requestCameraPermissionsAsync();
    setHasPermission(status === 'granted');

    if (status !== 'granted') {
      Alert.alert(
        'Camera Permission Required',
        'Please enable camera access to use OCR and part recognition features.',
        [{ text: 'OK' }]
      );
    }
  };

  const takePicture = async () => {
    if (!cameraRef.current || !cameraReady) return;

    try {
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.8,
        base64: true,
      });

      if (photo) {
        setCapturedImage(photo.uri);
        await analyzeImage(photo.base64 || '', photo.uri);
      }
    } catch (error) {
      console.error('Error taking picture:', error);
      Alert.alert('Error', 'Failed to capture image. Please try again.');
    }
  };

  const pickImage = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        quality: 0.8,
        base64: true,
      });

      if (!result.canceled && result.assets[0]) {
        const asset = result.assets[0];
        setCapturedImage(asset.uri);
        await analyzeImage(asset.base64 || '', asset.uri);
      }
    } catch (error) {
      console.error('Error picking image:', error);
      Alert.alert('Error', 'Failed to pick image. Please try again.');
    }
  };

  const analyzeImage = async (base64: string, uri: string) => {
    setIsAnalyzing(true);

    try {
      let response;

      switch (analysisMode) {
        case 'ocr':
          response = await apiService.extractTextFromImage(base64);
          break;
        case 'part':
          response = await apiService.recognizePart(base64);
          break;
        case 'condition':
          response = await apiService.analyzeEquipmentCondition(base64);
          break;
      }

      const result: AnalysisResult = {
        mode: analysisMode,
        success: true,
        data: response,
        imageUri: uri,
        timestamp: new Date(),
      };

      setAnalysisResult(result);
      setShowResultModal(true);
    } catch (error) {
      console.error('Error analyzing image:', error);

      setAnalysisResult({
        mode: analysisMode,
        success: false,
        data: { error: 'Failed to analyze image. Please try again.' },
        imageUri: uri,
        timestamp: new Date(),
      });
      setShowResultModal(true);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const toggleCameraFacing = () => {
    setFacing(current => (current === 'back' ? 'front' : 'back'));
  };

  const retakePhoto = () => {
    setCapturedImage(null);
    setAnalysisResult(null);
    setShowResultModal(false);
  };

  const renderResultContent = () => {
    if (!analysisResult) return null;

    const { mode, success, data } = analysisResult;

    if (!success) {
      return (
        <View style={styles.resultError}>
          <Text style={styles.resultErrorIcon}>❌</Text>
          <Text style={styles.resultErrorText}>{data.error}</Text>
        </View>
      );
    }

    switch (mode) {
      case 'ocr':
        return (
          <View style={styles.resultContent}>
            <Text style={styles.resultTitle}>Extracted Text</Text>
            <ScrollView style={styles.textResultScroll}>
              <Text style={styles.extractedText}>
                {data.text || data.extracted_text || 'No text detected'}
              </Text>
            </ScrollView>
            {data.confidence && (
              <Text style={styles.confidence}>
                Confidence: {Math.round(data.confidence * 100)}%
              </Text>
            )}
          </View>
        );

      case 'part':
        return (
          <View style={styles.resultContent}>
            <Text style={styles.resultTitle}>Part Identified</Text>
            {data.part_name ? (
              <>
                <View style={styles.partInfo}>
                  <Text style={styles.partName}>{data.part_name}</Text>
                  <Text style={styles.partNumber}>
                    Part #: {data.part_number || 'N/A'}
                  </Text>
                </View>
                {data.in_stock !== undefined && (
                  <View style={[
                    styles.stockBadge,
                    data.in_stock ? styles.inStock : styles.outOfStock
                  ]}>
                    <Text style={styles.stockText}>
                      {data.in_stock ? `In Stock (${data.quantity})` : 'Out of Stock'}
                    </Text>
                  </View>
                )}
                {data.location && (
                  <Text style={styles.partLocation}>Location: {data.location}</Text>
                )}
              </>
            ) : (
              <Text style={styles.noResult}>Part not recognized</Text>
            )}
          </View>
        );

      case 'condition':
        return (
          <View style={styles.resultContent}>
            <Text style={styles.resultTitle}>Condition Analysis</Text>
            <View style={styles.conditionRating}>
              <Text style={styles.conditionScore}>
                {data.condition_score || data.score || 'N/A'}
              </Text>
              <Text style={styles.conditionLabel}>
                {data.condition || data.status || 'Unknown'}
              </Text>
            </View>
            {data.issues && data.issues.length > 0 && (
              <View style={styles.issuesList}>
                <Text style={styles.issuesTitle}>Issues Detected:</Text>
                {data.issues.map((issue: string, index: number) => (
                  <Text key={index} style={styles.issueItem}>• {issue}</Text>
                ))}
              </View>
            )}
            {data.recommendations && (
              <View style={styles.recommendations}>
                <Text style={styles.recommendationsTitle}>Recommendations:</Text>
                <Text style={styles.recommendationsText}>{data.recommendations}</Text>
              </View>
            )}
          </View>
        );
    }
  };

  if (hasPermission === null) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#4a90d9" />
        <Text style={styles.statusText}>Checking permissions...</Text>
      </View>
    );
  }

  if (hasPermission === false) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorIcon}>📷</Text>
        <Text style={styles.errorText}>Camera access denied</Text>
        <TouchableOpacity style={styles.retryButton} onPress={checkPermissions}>
          <Text style={styles.retryButtonText}>Grant Permission</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Camera View */}
      <View style={styles.cameraContainer}>
        {capturedImage ? (
          <Image source={{ uri: capturedImage }} style={styles.previewImage} />
        ) : (
          <Camera
            ref={cameraRef}
            style={styles.camera}
            type={facing}
            onCameraReady={() => setCameraReady(true)}
          >
            {/* Camera Overlay */}
            <View style={styles.cameraOverlay}>
              {/* Mode indicator at top */}
              <View style={styles.modeIndicator}>
                <Text style={styles.modeIndicatorText}>
                  {ANALYSIS_MODES.find(m => m.mode === analysisMode)?.icon}{' '}
                  {ANALYSIS_MODES.find(m => m.mode === analysisMode)?.label}
                </Text>
              </View>

              {/* Flip camera button */}
              <TouchableOpacity
                style={styles.flipButton}
                onPress={toggleCameraFacing}
              >
                <Text style={styles.flipButtonText}>🔄</Text>
              </TouchableOpacity>
            </View>
          </Camera>
        )}

        {isAnalyzing && (
          <View style={styles.analyzingOverlay}>
            <ActivityIndicator size="large" color="#fff" />
            <Text style={styles.analyzingText}>Analyzing...</Text>
          </View>
        )}
      </View>

      {/* Mode Selection */}
      <View style={styles.modeSection}>
        <Text style={styles.sectionTitle}>Analysis Mode</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {ANALYSIS_MODES.map((item) => (
            <TouchableOpacity
              key={item.mode}
              style={[
                styles.modeButton,
                analysisMode === item.mode && styles.modeButtonActive,
              ]}
              onPress={() => setAnalysisMode(item.mode)}
            >
              <Text style={styles.modeButtonIcon}>{item.icon}</Text>
              <Text style={[
                styles.modeButtonText,
                analysisMode === item.mode && styles.modeButtonTextActive,
              ]}>
                {item.label}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Controls */}
      <View style={styles.controls}>
        {capturedImage ? (
          <View style={styles.previewControls}>
            <TouchableOpacity style={styles.retakeButton} onPress={retakePhoto}>
              <Text style={styles.controlButtonText}>Retake</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <View style={styles.captureControls}>
            <TouchableOpacity style={styles.galleryButton} onPress={pickImage}>
              <Text style={styles.galleryButtonText}>📁</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.captureButton}
              onPress={takePicture}
              disabled={!cameraReady || isAnalyzing}
            >
              <View style={styles.captureButtonInner} />
            </TouchableOpacity>

            <View style={styles.placeholder} />
          </View>
        )}
      </View>

      {/* Result Modal */}
      <Modal
        visible={showResultModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowResultModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Analysis Result</Text>
              <TouchableOpacity
                onPress={() => setShowResultModal(false)}
                style={styles.closeButton}
              >
                <Text style={styles.closeButtonText}>✕</Text>
              </TouchableOpacity>
            </View>

            {analysisResult?.imageUri && (
              <Image
                source={{ uri: analysisResult.imageUri }}
                style={styles.resultImage}
                resizeMode="cover"
              />
            )}

            {renderResultContent()}

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.actionButton}
                onPress={() => {
                  setShowResultModal(false);
                  retakePhoto();
                }}
              >
                <Text style={styles.actionButtonText}>Scan Another</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.actionButton, styles.actionButtonPrimary]}
                onPress={() => {
                  Alert.alert('Feature', 'Create work order from this analysis');
                }}
              >
                <Text style={styles.actionButtonTextPrimary}>Create Work Order</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  statusText: {
    color: '#888',
    marginTop: 20,
    textAlign: 'center',
  },
  errorIcon: {
    fontSize: 64,
    textAlign: 'center',
    marginBottom: 20,
  },
  errorText: {
    color: '#fff',
    fontSize: 18,
    textAlign: 'center',
  },
  retryButton: {
    backgroundColor: '#4a90d9',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    marginTop: 20,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  cameraContainer: {
    flex: 1,
    position: 'relative',
  },
  camera: {
    flex: 1,
  },
  previewImage: {
    flex: 1,
  },
  cameraOverlay: {
    flex: 1,
    backgroundColor: 'transparent',
    justifyContent: 'space-between',
    padding: 20,
  },
  modeIndicator: {
    backgroundColor: 'rgba(0,0,0,0.6)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    alignSelf: 'center',
    marginTop: 50,
  },
  modeIndicatorText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  flipButton: {
    position: 'absolute',
    top: 60,
    right: 20,
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  flipButtonText: {
    fontSize: 24,
  },
  analyzingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  analyzingText: {
    color: '#fff',
    fontSize: 18,
    marginTop: 16,
  },
  modeSection: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    backgroundColor: '#1a1a1a',
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#888',
    marginBottom: 12,
  },
  modeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2a2a2a',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    marginRight: 10,
  },
  modeButtonActive: {
    backgroundColor: '#4a90d9',
  },
  modeButtonIcon: {
    fontSize: 18,
    marginRight: 8,
  },
  modeButtonText: {
    color: '#888',
    fontSize: 14,
  },
  modeButtonTextActive: {
    color: '#fff',
  },
  controls: {
    paddingHorizontal: 20,
    paddingVertical: 20,
    backgroundColor: '#0c0c0c',
  },
  captureControls: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  galleryButton: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#2a2a2a',
    justifyContent: 'center',
    alignItems: 'center',
  },
  galleryButtonText: {
    fontSize: 24,
  },
  captureButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 4,
    borderColor: '#4a90d9',
  },
  captureButtonInner: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#fff',
  },
  placeholder: {
    width: 50,
  },
  previewControls: {
    flexDirection: 'row',
    justifyContent: 'center',
  },
  retakeButton: {
    backgroundColor: '#2a2a2a',
    paddingHorizontal: 32,
    paddingVertical: 14,
    borderRadius: 8,
  },
  controlButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#1a1a1a',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#333',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  closeButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#333',
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeButtonText: {
    color: '#fff',
    fontSize: 18,
  },
  resultImage: {
    width: '100%',
    height: 150,
  },
  resultContent: {
    padding: 20,
  },
  resultTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 12,
  },
  textResultScroll: {
    maxHeight: 150,
    backgroundColor: '#0c0c0c',
    borderRadius: 8,
    padding: 12,
  },
  extractedText: {
    color: '#fff',
    fontSize: 14,
    lineHeight: 22,
  },
  confidence: {
    color: '#888',
    fontSize: 12,
    marginTop: 8,
  },
  resultError: {
    padding: 20,
    alignItems: 'center',
  },
  resultErrorIcon: {
    fontSize: 48,
    marginBottom: 12,
  },
  resultErrorText: {
    color: '#e74c3c',
    fontSize: 16,
    textAlign: 'center',
  },
  partInfo: {
    marginBottom: 12,
  },
  partName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  partNumber: {
    fontSize: 14,
    color: '#888',
    marginTop: 4,
  },
  stockBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 4,
    alignSelf: 'flex-start',
    marginBottom: 12,
  },
  inStock: {
    backgroundColor: '#27ae60',
  },
  outOfStock: {
    backgroundColor: '#e74c3c',
  },
  stockText: {
    color: '#fff',
    fontWeight: '600',
  },
  partLocation: {
    color: '#888',
    fontSize: 14,
  },
  noResult: {
    color: '#888',
    fontSize: 16,
    textAlign: 'center',
  },
  conditionRating: {
    alignItems: 'center',
    marginBottom: 16,
  },
  conditionScore: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#4a90d9',
  },
  conditionLabel: {
    fontSize: 18,
    color: '#fff',
    marginTop: 4,
  },
  issuesList: {
    backgroundColor: '#0c0c0c',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  issuesTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#e74c3c',
    marginBottom: 8,
  },
  issueItem: {
    color: '#fff',
    fontSize: 14,
    marginBottom: 4,
  },
  recommendations: {
    backgroundColor: '#1e3c72',
    borderRadius: 8,
    padding: 12,
  },
  recommendationsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 8,
  },
  recommendationsText: {
    color: '#ddd',
    fontSize: 14,
    lineHeight: 20,
  },
  modalActions: {
    flexDirection: 'row',
    padding: 20,
    gap: 12,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 8,
    backgroundColor: '#333',
    alignItems: 'center',
  },
  actionButtonPrimary: {
    backgroundColor: '#4a90d9',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  actionButtonTextPrimary: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
