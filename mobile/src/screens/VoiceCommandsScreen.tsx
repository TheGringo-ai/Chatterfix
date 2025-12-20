/**
 * Voice Commands Screen
 * Hands-free work order creation and AI interaction for technicians
 *
 * Context-Aware Features:
 * - Automatically includes scanned asset from QR/NFC
 * - Includes GPS location for "here" context
 * - Resolves "this", "it", "here" to actual assets
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Animated,
  Alert,
  Platform,
} from 'react-native';
import { Audio } from 'expo-av';
import * as Speech from 'expo-speech';
import * as Location from 'expo-location';
import { apiService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useAssetContext } from '../contexts/AssetContext';
import { GeoLocation, VoiceCommandPayload } from '../types/voice';

interface CommandResult {
  id: string;
  command: string;
  response: string;
  action?: string;
  success: boolean;
  timestamp: Date;
}

const QUICK_COMMANDS = [
  { label: 'Create Work Order', command: 'Create a new work order' },
  { label: 'Check My Tasks', command: 'What are my open work orders?' },
  { label: 'Find Part', command: 'Find a replacement part for' },
  { label: 'Equipment Status', command: 'What is the status of' },
  { label: 'Log Maintenance', command: 'Log maintenance completed on' },
  { label: 'Report Issue', command: 'Report an issue with' },
];

export default function VoiceCommandsScreen() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [commandHistory, setCommandHistory] = useState<CommandResult[]>([]);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [currentLocation, setCurrentLocation] = useState<GeoLocation | null>(null);

  // Get context from providers
  const { user } = useAuth();
  const { currentAsset, hasAssetContext } = useAssetContext();

  const pulseAnim = useRef(new Animated.Value(1)).current;
  const scrollViewRef = useRef<ScrollView>(null);

  useEffect(() => {
    checkPermissions();
    requestLocationPermission();
  }, []);

  // Request location permission for "here" context
  const requestLocationPermission = async () => {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status === 'granted') {
        const location = await Location.getCurrentPositionAsync({});
        setCurrentLocation({
          latitude: location.coords.latitude,
          longitude: location.coords.longitude,
          accuracy: location.coords.accuracy || undefined,
          altitude: location.coords.altitude || undefined,
        });
      }
    } catch (error) {
      console.log('Location permission denied or error:', error);
    }
  };

  useEffect(() => {
    if (isRecording) {
      // Pulse animation while recording
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.3,
            duration: 500,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 500,
            useNativeDriver: true,
          }),
        ])
      ).start();
    } else {
      pulseAnim.setValue(1);
    }
  }, [isRecording]);

  const checkPermissions = async () => {
    try {
      const { status } = await Audio.requestPermissionsAsync();
      setHasPermission(status === 'granted');

      if (status !== 'granted') {
        Alert.alert(
          'Microphone Permission Required',
          'Please enable microphone access to use voice commands.',
          [{ text: 'OK' }]
        );
      }
    } catch (error) {
      console.error('Error checking permissions:', error);
      setHasPermission(false);
    }
  };

  const startRecording = async () => {
    if (!hasPermission) {
      await checkPermissions();
      return;
    }

    try {
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      const { recording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );

      setRecording(recording);
      setIsRecording(true);
      setTranscript('Listening...');
    } catch (error) {
      console.error('Failed to start recording:', error);
      Alert.alert('Error', 'Failed to start recording. Please try again.');
    }
  };

  const stopRecording = async () => {
    if (!recording) return;

    try {
      setIsRecording(false);
      setIsProcessing(true);
      setTranscript('Processing...');

      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      setRecording(null);

      if (uri) {
        // Send audio with context to backend for transcription + processing
        try {
          const response = await apiService.sendVoiceAudioWithContext(
            uri,
            user?.uid || 'anonymous',
            currentAsset || undefined,
            currentLocation || undefined
          );

          // Process the response
          const result: CommandResult = {
            id: Date.now().toString(),
            command: response.original_text || 'Voice command',
            response: response.response_text || 'Command processed',
            action: response.action,
            success: response.success,
            timestamp: new Date(),
          };

          setTranscript(response.original_text || '');
          setCommandHistory(prev => [result, ...prev]);

          // Speak the response
          if (response.response_text) {
            Speech.speak(response.response_text, {
              language: 'en-US',
              pitch: 1,
              rate: 0.9,
            });
          }

          // Show context info if used
          if (response.context_used && response.resolved_asset_name) {
            Alert.alert(
              'Context Applied',
              `Resolved to: ${response.resolved_asset_name}`,
              [{ text: 'OK' }]
            );
          }

          // Handle work order creation
          if (response.action === 'create_work_order' && response.action_result?.work_order_id) {
            Alert.alert(
              'Work Order Created',
              `Work order #${response.action_result.work_order_id} has been created.`,
              [{ text: 'View', onPress: () => {} }, { text: 'OK' }]
            );
          }
        } catch (error: any) {
          // Handle upload errors gracefully
          if (apiService.isUploadError(error)) {
            const message = apiService.getUploadErrorMessage(error);
            Alert.alert('Upload Error', message);
            Speech.speak(message, { language: 'en-US' });
          } else {
            throw error;
          }
        }
      }
    } catch (error) {
      console.error('Failed to stop recording:', error);
      const result: CommandResult = {
        id: Date.now().toString(),
        command: 'Voice command',
        response: 'Failed to process recording. Please try again.',
        success: false,
        timestamp: new Date(),
      };
      setCommandHistory(prev => [result, ...prev]);
      Speech.speak('Failed to process recording.', { language: 'en-US' });
    } finally {
      setIsProcessing(false);
      setTranscript('');
    }
  };

  const processVoiceCommand = async (command: string) => {
    try {
      setTranscript(command);

      // Build context-aware payload
      const payload: VoiceCommandPayload = {
        voice_text: command,
        technician_id: user?.uid,
        current_asset: currentAsset || undefined,
        location: currentLocation || undefined,
      };

      // Use context-aware API
      const response = await apiService.processVoiceCommandWithContext(payload);

      const result: CommandResult = {
        id: Date.now().toString(),
        command,
        response: response.response_text || 'Command processed',
        action: response.action,
        success: response.success,
        timestamp: new Date(),
      };

      setCommandHistory(prev => [result, ...prev]);

      // Speak the response
      if (response.response_text) {
        Speech.speak(response.response_text, {
          language: 'en-US',
          pitch: 1,
          rate: 0.9,
        });
      }

      // Show context resolution info
      if (response.context_used && response.resolved_asset_name) {
        console.log(`Context resolved to: ${response.resolved_asset_name}`);
      }

      // Handle specific actions
      if (response.action === 'create_work_order' && response.action_result?.work_order_id) {
        Alert.alert(
          'Work Order Created',
          `Work order #${response.action_result.work_order_id} has been created for ${response.resolved_asset_name || 'equipment'}.`,
          [{ text: 'View', onPress: () => {} }, { text: 'OK' }]
        );
      }
    } catch (error: any) {
      console.error('Error processing command:', error);

      // Handle upload/API errors
      let errorMessage = 'Sorry, I could not process that command. Please try again.';
      if (apiService.isUploadError(error)) {
        errorMessage = apiService.getUploadErrorMessage(error);
      }

      const result: CommandResult = {
        id: Date.now().toString(),
        command,
        response: errorMessage,
        success: false,
        timestamp: new Date(),
      };

      setCommandHistory(prev => [result, ...prev]);
      Speech.speak(errorMessage, { language: 'en-US' });
    } finally {
      setIsProcessing(false);
      setTranscript('');
    }
  };

  const handleQuickCommand = (command: string) => {
    setIsProcessing(true);
    setTranscript(command);
    processVoiceCommand(command);
  };

  const clearHistory = () => {
    setCommandHistory([]);
  };

  if (hasPermission === null) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#4a90d9" />
        <Text style={styles.statusText}>Checking permissions...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Voice Commands</Text>
        <Text style={styles.subtitle}>Hands-free work order management</Text>

        {/* Context Indicator - Shows when asset is scanned */}
        {hasAssetContext && currentAsset && (
          <View style={styles.contextBanner}>
            <Text style={styles.contextIcon}>📍</Text>
            <View style={styles.contextInfo}>
              <Text style={styles.contextLabel}>Current Asset</Text>
              <Text style={styles.contextValue}>
                {currentAsset.asset_name || currentAsset.asset_id}
              </Text>
            </View>
            <Text style={styles.contextSource}>
              {currentAsset.source === 'qr_scan' ? 'QR' :
               currentAsset.source === 'nfc_tap' ? 'NFC' : 'Selected'}
            </Text>
          </View>
        )}
      </View>

      {/* Main Microphone Button */}
      <View style={styles.microphoneSection}>
        <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
          <TouchableOpacity
            style={[
              styles.micButton,
              isRecording && styles.micButtonRecording,
              isProcessing && styles.micButtonProcessing,
            ]}
            onPressIn={startRecording}
            onPressOut={stopRecording}
            disabled={isProcessing}
          >
            {isProcessing ? (
              <ActivityIndicator size="large" color="#fff" />
            ) : (
              <Text style={styles.micIcon}>{isRecording ? '🔴' : '🎤'}</Text>
            )}
          </TouchableOpacity>
        </Animated.View>

        <Text style={styles.instruction}>
          {isRecording
            ? 'Release to send command'
            : isProcessing
            ? 'Processing...'
            : 'Hold to speak'}
        </Text>

        {transcript ? (
          <View style={styles.transcriptBox}>
            <Text style={styles.transcriptText}>{transcript}</Text>
          </View>
        ) : null}
      </View>

      {/* Quick Commands */}
      <View style={styles.quickCommandsSection}>
        <Text style={styles.sectionTitle}>Quick Commands</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {QUICK_COMMANDS.map((item, index) => (
            <TouchableOpacity
              key={index}
              style={styles.quickCommandButton}
              onPress={() => handleQuickCommand(item.command)}
              disabled={isProcessing}
            >
              <Text style={styles.quickCommandText}>{item.label}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Command History */}
      <View style={styles.historySection}>
        <View style={styles.historyHeader}>
          <Text style={styles.sectionTitle}>Recent Commands</Text>
          {commandHistory.length > 0 && (
            <TouchableOpacity onPress={clearHistory}>
              <Text style={styles.clearButton}>Clear</Text>
            </TouchableOpacity>
          )}
        </View>

        <ScrollView
          ref={scrollViewRef}
          style={styles.historyList}
          showsVerticalScrollIndicator={false}
        >
          {commandHistory.length === 0 ? (
            <Text style={styles.emptyText}>
              No commands yet. Hold the microphone button to speak.
            </Text>
          ) : (
            commandHistory.map((item) => (
              <View
                key={item.id}
                style={[
                  styles.historyItem,
                  !item.success && styles.historyItemError,
                ]}
              >
                <View style={styles.historyCommand}>
                  <Text style={styles.historyCommandText}>{item.command}</Text>
                  <Text style={styles.historyTime}>
                    {item.timestamp.toLocaleTimeString()}
                  </Text>
                </View>
                <Text style={styles.historyResponse}>{item.response}</Text>
                {item.action && (
                  <View style={styles.actionBadge}>
                    <Text style={styles.actionBadgeText}>{item.action}</Text>
                  </View>
                )}
              </View>
            ))
          )}
        </ScrollView>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  header: {
    padding: 20,
    paddingTop: 60,
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
  },
  subtitle: {
    fontSize: 14,
    color: '#888',
    marginTop: 4,
  },
  statusText: {
    color: '#888',
    marginTop: 20,
  },
  microphoneSection: {
    alignItems: 'center',
    paddingVertical: 30,
  },
  micButton: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: '#4a90d9',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#4a90d9',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.5,
    shadowRadius: 20,
    elevation: 10,
  },
  micButtonRecording: {
    backgroundColor: '#e74c3c',
    shadowColor: '#e74c3c',
  },
  micButtonProcessing: {
    backgroundColor: '#666',
    shadowColor: '#666',
  },
  micIcon: {
    fontSize: 48,
  },
  instruction: {
    color: '#888',
    marginTop: 20,
    fontSize: 16,
  },
  transcriptBox: {
    marginTop: 20,
    paddingHorizontal: 20,
    paddingVertical: 12,
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    marginHorizontal: 20,
    maxWidth: '90%',
  },
  transcriptText: {
    color: '#fff',
    fontSize: 16,
    textAlign: 'center',
  },
  quickCommandsSection: {
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 12,
  },
  quickCommandButton: {
    backgroundColor: '#1e3c72',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    marginRight: 10,
  },
  quickCommandText: {
    color: '#fff',
    fontSize: 14,
  },
  historySection: {
    flex: 1,
    paddingHorizontal: 20,
  },
  historyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  clearButton: {
    color: '#4a90d9',
    fontSize: 14,
  },
  historyList: {
    flex: 1,
  },
  emptyText: {
    color: '#666',
    textAlign: 'center',
    marginTop: 40,
  },
  historyItem: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 3,
    borderLeftColor: '#4a90d9',
  },
  historyItemError: {
    borderLeftColor: '#e74c3c',
  },
  historyCommand: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  historyCommandText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    flex: 1,
  },
  historyTime: {
    color: '#666',
    fontSize: 12,
  },
  historyResponse: {
    color: '#aaa',
    fontSize: 14,
    lineHeight: 20,
  },
  actionBadge: {
    backgroundColor: '#27ae60',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    alignSelf: 'flex-start',
    marginTop: 8,
  },
  actionBadgeText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  // Context Banner Styles
  contextBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1e3c72',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 10,
    marginTop: 16,
    borderWidth: 1,
    borderColor: '#4a90d9',
  },
  contextIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  contextInfo: {
    flex: 1,
  },
  contextLabel: {
    color: '#88a8d9',
    fontSize: 11,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  contextValue: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginTop: 2,
  },
  contextSource: {
    color: '#4a90d9',
    fontSize: 12,
    fontWeight: '600',
    backgroundColor: 'rgba(74, 144, 217, 0.2)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    overflow: 'hidden',
  },
});
