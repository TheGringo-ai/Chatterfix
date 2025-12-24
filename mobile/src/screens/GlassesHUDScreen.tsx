/**
 * GlassesHUDScreen - Mock Glasses Mode
 *
 * Simulates the Brilliant Labs smart glasses experience.
 * Entire screen is pitch black with minimal HUD text.
 * Tests the "blind" UX before hardware arrives.
 *
 * Features:
 * - Full-screen tap-to-talk
 * - TTS-only feedback
 * - Offline queue (Ghost Mode)
 * - Long-press to exit
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  StatusBar,
  Animated,
  Vibration,
} from 'react-native';
import { Audio } from 'expo-av';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { FeedbackService } from '../services/FeedbackService';
import { apiService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useAssetContext } from '../contexts/AssetContext';

// Status states for the HUD
type HUDStatus = 'IDLE' | 'LISTENING' | 'PROCESSING' | 'CONFIRMING' | 'OFFLINE';

// Offline queue storage key
const OFFLINE_QUEUE_KEY = '@chatterfix_glasses_queue';

interface QueuedCommand {
  id: string;
  transcript: string;
  assetId?: string;
  assetName?: string;
  timestamp: number;
}

export default function GlassesHUDScreen() {
  const navigation = useNavigation();
  const { user } = useAuth();
  const { currentAsset } = useAssetContext();

  const [status, setStatus] = useState<HUDStatus>('IDLE');
  const [hudMessage, setHudMessage] = useState('Ready');
  const [queueCount, setQueueCount] = useState(0);
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [pendingCommand, setPendingCommand] = useState<any>(null);

  // Animations
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const glowAnim = useRef(new Animated.Value(0.3)).current;

  // Ref to track recording for cleanup (avoids stale closure issues)
  const recordingRef = useRef<Audio.Recording | null>(null);

  // Keep ref in sync with state
  useEffect(() => {
    recordingRef.current = recording;
  }, [recording]);

  // Initialize on mount
  useEffect(() => {
    initializeHUD();
    return () => {
      // Cleanup recording if active (use ref to avoid stale closure)
      const activeRecording = recordingRef.current;
      if (activeRecording) {
        activeRecording.stopAndUnloadAsync().catch((err) => {
          console.warn('Cleanup: Error stopping recording:', err);
        });
      }
    };
  }, []);

  // Pulse animation when listening
  useEffect(() => {
    if (status === 'LISTENING') {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, { toValue: 1.2, duration: 500, useNativeDriver: true }),
          Animated.timing(pulseAnim, { toValue: 1, duration: 500, useNativeDriver: true }),
        ])
      ).start();

      Animated.loop(
        Animated.sequence([
          Animated.timing(glowAnim, { toValue: 1, duration: 800, useNativeDriver: true }),
          Animated.timing(glowAnim, { toValue: 0.3, duration: 800, useNativeDriver: true }),
        ])
      ).start();
    } else {
      pulseAnim.setValue(1);
      glowAnim.setValue(0.3);
    }
  }, [status]);

  const initializeHUD = async () => {
    // Request audio permissions
    const { status: audioStatus } = await Audio.requestPermissionsAsync();
    if (audioStatus !== 'granted') {
      await FeedbackService.announceError('Microphone access required');
      navigation.goBack();
      return;
    }

    // Configure audio
    await Audio.setAudioModeAsync({
      allowsRecordingIOS: true,
      playsInSilentModeIOS: true,
    });

    // Check offline queue
    await checkOfflineQueue();

    // Announce ready
    await FeedbackService.glassesMode.ready();
    setHudMessage('Ready');
  };

  const checkOfflineQueue = async () => {
    try {
      const queue = await AsyncStorage.getItem(OFFLINE_QUEUE_KEY);
      if (queue) {
        const items: QueuedCommand[] = JSON.parse(queue);
        setQueueCount(items.length);
        if (items.length > 0) {
          setHudMessage(`${items.length} queued`);
        }
      }
    } catch (error) {
      console.error('Error checking offline queue:', error);
    }
  };

  const addToOfflineQueue = async (command: QueuedCommand) => {
    try {
      const existing = await AsyncStorage.getItem(OFFLINE_QUEUE_KEY);
      const queue: QueuedCommand[] = existing ? JSON.parse(existing) : [];
      queue.push(command);
      await AsyncStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(queue));
      setQueueCount(queue.length);
    } catch (error) {
      console.error('Error adding to offline queue:', error);
    }
  };

  const syncOfflineQueue = async () => {
    try {
      const existing = await AsyncStorage.getItem(OFFLINE_QUEUE_KEY);
      if (!existing) return;

      const queue: QueuedCommand[] = JSON.parse(existing);
      if (queue.length === 0) return;

      setHudMessage('Syncing...');
      await FeedbackService.announceAction(`Syncing ${queue.length} commands`);

      let synced = 0;
      const remaining: QueuedCommand[] = [];

      for (const cmd of queue) {
        try {
          await apiService.processVoiceCommandWithContext({
            voice_text: cmd.transcript,
            technician_id: user?.uid,
            current_asset: cmd.assetId ? { asset_id: cmd.assetId, asset_name: cmd.assetName, source: 'session_history' } : undefined,
          });
          synced++;
        } catch {
          remaining.push(cmd);
        }
      }

      await AsyncStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(remaining));
      setQueueCount(remaining.length);

      if (synced > 0) {
        await FeedbackService.announceSuccess(`${synced} commands synced`);
      }
      if (remaining.length > 0) {
        setHudMessage(`${remaining.length} pending`);
      } else {
        setHudMessage('Ready');
      }
    } catch (error) {
      console.error('Error syncing offline queue:', error);
    }
  };

  // Main interaction handler - wrapped to prevent crashes
  const handleTap = useCallback(async () => {
    try {
      switch (status) {
        case 'IDLE':
          await startListening();
          break;
        case 'LISTENING':
          await stopListening();
          break;
        case 'CONFIRMING':
          await confirmCommand();
          break;
        case 'OFFLINE':
          await syncOfflineQueue();
          break;
        case 'PROCESSING':
          // Ignore taps while processing to prevent crashes
          console.log('Ignoring tap - currently processing');
          break;
      }
    } catch (error) {
      console.error('Error in handleTap:', error);
      setStatus('IDLE');
      setHudMessage('Error - tap to retry');
      await FeedbackService.announceError('Something went wrong');
    }
  }, [status]);

  const startListening = async () => {
    try {
      setStatus('LISTENING');
      setHudMessage('Listening...');
      Vibration.vibrate(50);

      await FeedbackService.announceListening();

      const { recording: newRecording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );
      setRecording(newRecording);
    } catch (error) {
      console.error('Error starting recording:', error);
      await FeedbackService.announceError('Mic error');
      setStatus('IDLE');
      setHudMessage('Ready');
    }
  };

  const stopListening = async () => {
    // Use ref for safety - state might be stale in async context
    const currentRecording = recordingRef.current;
    if (!currentRecording) {
      console.warn('stopListening called but no active recording');
      setStatus('IDLE');
      setHudMessage('Ready');
      await FeedbackService.announceError('No recording found');
      return;
    }

    try {
      setStatus('PROCESSING');
      setHudMessage('Processing...');
      Vibration.vibrate([0, 30, 50, 30]);

      await currentRecording.stopAndUnloadAsync();
      const uri = currentRecording.getURI();
      setRecording(null);

      if (!uri) {
        throw new Error('No audio recorded');
      }

      // Try to send to backend
      try {
        const response = await apiService.sendVoiceAudioWithContext(
          uri,
          user?.uid || 'anonymous',
          currentAsset || undefined,
          undefined // No GPS in glasses mode for simplicity
        );

        if (response.action === 'create_work_order') {
          // Need confirmation
          setPendingCommand(response);
          setStatus('CONFIRMING');
          const assetText = response.resolved_asset_name || 'equipment';
          setHudMessage(`${assetText}?`);

          await FeedbackService.askConfirmation(
            response.original_text,
            response.resolved_asset_name
          );
        } else {
          // Direct execution
          setStatus('IDLE');
          setHudMessage('Done');
          await FeedbackService.announceSuccess(response.response_text || 'Done');
          setTimeout(() => setHudMessage('Ready'), 2000);
        }
      } catch (error: any) {
        // OFFLINE MODE: Queue the command
        if (!error.response || error.message?.includes('Network')) {
          setStatus('OFFLINE');
          setHudMessage('Offline - Queued');

          // Create a placeholder command for the queue
          const queuedCommand: QueuedCommand = {
            id: Date.now().toString(),
            transcript: 'Voice command (pending transcription)',
            assetId: currentAsset?.asset_id,
            assetName: currentAsset?.asset_name,
            timestamp: Date.now(),
          };
          await addToOfflineQueue(queuedCommand);

          await FeedbackService.announceAction('Offline. Command queued.');
        } else {
          setStatus('IDLE');
          setHudMessage('Error');
          await FeedbackService.announceError();
          setTimeout(() => setHudMessage('Ready'), 2000);
        }
      }
    } catch (error) {
      console.error('Error stopping recording:', error);
      setStatus('IDLE');
      setHudMessage('Error');
      await FeedbackService.announceError();
    }
  };

  const confirmCommand = async () => {
    if (!pendingCommand) return;

    setStatus('IDLE');
    Vibration.vibrate(100);

    await FeedbackService.glassesMode.confirmYes();

    const ticketId = pendingCommand.action_result?.work_order_id;
    if (ticketId) {
      setHudMessage(`#${ticketId}`);
      await FeedbackService.announceSuccess('Work order created', ticketId);
    } else {
      setHudMessage('Created');
      await FeedbackService.announceSuccess('Created');
    }

    setPendingCommand(null);
    setTimeout(() => setHudMessage('Ready'), 3000);
  };

  const cancelCommand = async () => {
    setPendingCommand(null);
    setStatus('IDLE');
    setHudMessage('Cancelled');
    await FeedbackService.glassesMode.confirmNo();
    setTimeout(() => setHudMessage('Ready'), 2000);
  };

  const handleLongPress = () => {
    // Double vibrate as exit signal
    Vibration.vibrate([0, 100, 100, 100]);
    FeedbackService.stop();
    navigation.goBack();
  };

  // Double-tap detection for cancel in CONFIRMING state
  const lastTapRef = useRef<number>(0);
  const DOUBLE_TAP_DELAY = 300; // ms

  const handleTapWithDoubleTapDetection = useCallback(async () => {
    const now = Date.now();
    const timeSinceLastTap = now - lastTapRef.current;
    lastTapRef.current = now;

    // If double-tap detected and in CONFIRMING state, cancel
    if (timeSinceLastTap < DOUBLE_TAP_DELAY && status === 'CONFIRMING') {
      await cancelCommand();
      return;
    }

    // Otherwise, handle as regular tap
    await handleTap();
  }, [status, handleTap]);

  // Get icon based on status
  const getIcon = () => {
    switch (status) {
      case 'LISTENING':
        return 'mic';
      case 'PROCESSING':
        return 'sync';
      case 'CONFIRMING':
        return 'checkmark-circle';
      case 'OFFLINE':
        return 'cloud-offline';
      default:
        return 'glasses-outline';
    }
  };

  // Get color based on status
  const getColor = () => {
    switch (status) {
      case 'LISTENING':
        return '#FF3B30'; // Red while recording
      case 'PROCESSING':
        return '#FFD60A'; // Yellow while thinking
      case 'CONFIRMING':
        return '#30D158'; // Green for confirm
      case 'OFFLINE':
        return '#FF9500'; // Orange for offline
      default:
        return '#00FF41'; // Hacker green
    }
  };

  return (
    <TouchableOpacity
      style={styles.container}
      activeOpacity={1}
      onPress={handleTapWithDoubleTapDetection}
      onLongPress={handleLongPress}
      delayLongPress={1000}
    >
      <StatusBar hidden />

      {/* HUD Display */}
      <View style={styles.hudContainer}>
        <Animated.View
          style={[
            styles.iconContainer,
            {
              transform: [{ scale: pulseAnim }],
              opacity: status === 'LISTENING' ? glowAnim : 1,
            },
          ]}
        >
          <Ionicons name={getIcon() as any} size={64} color={getColor()} />
        </Animated.View>

        <Text style={[styles.hudText, { color: getColor() }]}>{hudMessage}</Text>

        {/* Asset Context Indicator */}
        {currentAsset && (
          <Text style={styles.contextText}>
            @ {currentAsset.asset_name || currentAsset.asset_id}
          </Text>
        )}

        {/* Offline Queue Badge */}
        {queueCount > 0 && (
          <View style={styles.queueBadge}>
            <Text style={styles.queueText}>{queueCount} queued</Text>
          </View>
        )}
      </View>

      {/* Status Ring */}
      <View style={[styles.statusRing, { borderColor: getColor() }]} />

      {/* Instructions (faint) */}
      <Text style={styles.hintText}>
        {status === 'CONFIRMING'
          ? 'Tap = Confirm  •  Double-tap = Cancel  •  Hold = Exit'
          : 'Tap = Speak  •  Hold = Exit'}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
    justifyContent: 'center',
    alignItems: 'center',
  },
  hudContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 40,
  },
  iconContainer: {
    marginBottom: 20,
  },
  hudText: {
    fontFamily: 'Courier',
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
    letterSpacing: 2,
  },
  contextText: {
    fontFamily: 'Courier',
    fontSize: 14,
    color: '#00FF41',
    opacity: 0.6,
    marginTop: 16,
  },
  queueBadge: {
    marginTop: 20,
    paddingHorizontal: 16,
    paddingVertical: 6,
    backgroundColor: '#FF9500',
    borderRadius: 12,
  },
  queueText: {
    fontFamily: 'Courier',
    fontSize: 12,
    color: '#000',
    fontWeight: 'bold',
  },
  statusRing: {
    position: 'absolute',
    width: 200,
    height: 200,
    borderRadius: 100,
    borderWidth: 2,
    opacity: 0.2,
  },
  hintText: {
    position: 'absolute',
    bottom: 50,
    color: '#333',
    fontSize: 12,
    fontFamily: 'Courier',
    textAlign: 'center',
  },
});
