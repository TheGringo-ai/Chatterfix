/**
 * Home Screen - Dashboard
 * Main entry point with voice recording and quick actions
 */

import { useState, useEffect } from 'react';
import { View, Text, Pressable, Alert, ActivityIndicator } from 'react-native';
import { Link } from 'expo-router';
import { useAppStore } from '@/stores';
import { voiceCommandService, authService } from '@/services';

export default function HomeScreen() {
  const { isOnline, syncStatus, ghostModeEnabled, organizationId, setOrganizationId } = useAppStore();
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [lastResult, setLastResult] = useState<string | null>(null);

  // Set organization ID in voice service
  useEffect(() => {
    if (organizationId) {
      voiceCommandService.setOrganizationId(organizationId);
    } else {
      // Try to get from auth service
      const userData = authService.getUserData();
      if (userData?.organizationId) {
        setOrganizationId(userData.organizationId);
        voiceCommandService.setOrganizationId(userData.organizationId);
      }
    }
  }, [organizationId, setOrganizationId]);

  const handleRecordPress = async () => {
    if (isProcessing) return;

    if (!isRecording) {
      // Start recording
      try {
        await voiceCommandService.startRecording();
        setIsRecording(true);
        setLastResult(null);
      } catch (error: any) {
        Alert.alert('Recording Error', error.message);
      }
    } else {
      // Stop recording and process
      setIsRecording(false);
      setIsProcessing(true);
      try {
        const result = await voiceCommandService.stopAndProcess();
        if (result.success) {
          setLastResult(result.response || result.transcript);
          if (result.action === 'work_order' && result.workOrder) {
            Alert.alert(
              'Work Order Created',
              `${result.workOrder.title}\n\n${result.response || 'Work order has been created.'}`
            );
          }
        } else {
          Alert.alert('Processing Error', result.error || 'Failed to process command');
        }
      } catch (error: any) {
        Alert.alert('Error', error.message);
      } finally {
        setIsProcessing(false);
      }
    }
  };

  const userData = authService.getUserData();

  return (
    <View className="flex-1 bg-background p-4">
      {/* User Greeting */}
      <View className="mb-4">
        <Text className="text-gray-400 text-sm">Welcome back,</Text>
        <Text className="text-white text-xl font-bold">
          {userData?.displayName || 'Technician'}
        </Text>
      </View>

      {/* Ghost Mode Banner */}
      {ghostModeEnabled && (
        <View className="bg-warning/20 border border-warning rounded-lg p-3 mb-4 flex-row items-center">
          <Text className="text-warning text-lg mr-2">👻</Text>
          <Text className="text-warning font-medium">
            GHOST MODE - Actions queued for sync
          </Text>
        </View>
      )}

      {/* Big Voice Record Button */}
      <View className="items-center my-6">
        <Pressable
          onPress={handleRecordPress}
          disabled={isProcessing}
          className={`w-32 h-32 rounded-full items-center justify-center shadow-lg ${
            isRecording
              ? 'bg-danger'
              : isProcessing
              ? 'bg-gray-600'
              : 'bg-primary'
          }`}
          style={{
            shadowColor: isRecording ? '#ef4444' : '#00d4ff',
            shadowOffset: { width: 0, height: 4 },
            shadowOpacity: 0.5,
            shadowRadius: 10,
            elevation: 10,
          }}
        >
          {isProcessing ? (
            <ActivityIndicator size="large" color="#fff" />
          ) : (
            <>
              <Text className="text-white text-4xl">🎤</Text>
              <Text className="text-white font-semibold mt-1">
                {isRecording ? 'STOP' : 'RECORD'}
              </Text>
            </>
          )}
        </Pressable>
        <Text className="text-gray-400 text-sm mt-3">
          {isRecording
            ? 'Tap to stop recording'
            : isProcessing
            ? 'Processing command...'
            : 'Tap to start voice command'}
        </Text>
      </View>

      {/* Last Result */}
      {lastResult && (
        <View className="bg-background-card rounded-xl p-4 mb-4">
          <Text className="text-gray-400 text-sm mb-1">AI Response:</Text>
          <Text className="text-white">{lastResult}</Text>
        </View>
      )}

      {/* Sync Status Card */}
      <View className="bg-background-card rounded-xl p-4 mb-4">
        <View className="flex-row justify-between items-center mb-2">
          <Text className="text-white text-lg font-bold">Sync Status</Text>
          <View
            className={`w-3 h-3 rounded-full ${
              isOnline ? 'bg-success' : 'bg-danger'
            }`}
          />
        </View>
        <Text className="text-gray-400">
          {syncStatus.isSyncing
            ? 'Syncing...'
            : syncStatus.lastSyncAt
            ? `Last sync: ${new Date(syncStatus.lastSyncAt).toLocaleTimeString()}`
            : 'Never synced'}
        </Text>
        {syncStatus.pendingCount > 0 && (
          <Text className="text-warning mt-1">
            {syncStatus.pendingCount} items pending sync
          </Text>
        )}
      </View>

      {/* Quick Actions */}
      <Text className="text-white text-xl font-bold mb-3">Quick Actions</Text>
      <View className="flex-row flex-wrap gap-3">
        <Link href="/assets" asChild>
          <Pressable className="bg-primary/20 border border-primary rounded-xl p-4 flex-1 min-w-[140px]">
            <Text className="text-primary text-2xl mb-2">🔧</Text>
            <Text className="text-white font-semibold">Assets</Text>
            <Text className="text-gray-400 text-sm">View equipment</Text>
          </Pressable>
        </Link>

        <Link href="/logs" asChild>
          <Pressable className="bg-accent/20 border border-accent rounded-xl p-4 flex-1 min-w-[140px]">
            <Text className="text-accent text-2xl mb-2">📋</Text>
            <Text className="text-white font-semibold">Voice Logs</Text>
            <Text className="text-gray-400 text-sm">Recent commands</Text>
          </Pressable>
        </Link>
      </View>

      <View className="flex-row flex-wrap gap-3 mt-3">
        <Link href="/settings" asChild>
          <Pressable className="bg-gray-500/20 border border-gray-500 rounded-xl p-4 flex-1 min-w-[140px]">
            <Text className="text-gray-400 text-2xl mb-2">⚙️</Text>
            <Text className="text-white font-semibold">Settings</Text>
            <Text className="text-gray-400 text-sm">Preferences</Text>
          </Pressable>
        </Link>
      </View>

      {/* Footer */}
      <View className="mt-auto pt-4">
        <Text className="text-gray-500 text-center text-sm">
          ChatterFix Relay v1.0.0
        </Text>
        <Text className="text-gray-600 text-center text-xs">
          {userData?.organizationName || 'Offline-first voice command relay'}
        </Text>
      </View>
    </View>
  );
}
