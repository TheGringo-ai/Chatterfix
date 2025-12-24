/**
 * Root Layout - Expo Router
 * Wraps all screens with providers and global configuration
 */

import { useEffect, useState } from 'react';
import { Stack, router, useSegments } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { View, Text, ActivityIndicator } from 'react-native';
import { User } from 'firebase/auth';
import { useAppStore } from '@/stores';
import { initDatabase } from '@/db';
import { authService } from '@/services/authService';
import { useNetworkStatus } from '@/hooks';

// Import global styles
import '../global.css';

export default function RootLayout() {
  const { preferences, setOrganizationId } = useAppStore();
  const [dbReady, setDbReady] = useState(false);
  const [dbError, setDbError] = useState<string | null>(null);
  const [user, setUser] = useState<User | null | undefined>(undefined);
  const segments = useSegments();

  // Automatic network monitoring - enables/disables Ghost Mode
  // This runs continuously in the background while the app is open
  const { isOnline, ghostModeEnabled, syncStatus } = useNetworkStatus();

  // Log network status changes for debugging
  useEffect(() => {
    console.log('[RootLayout] Network status:', { isOnline, ghostModeEnabled, syncStatus });
  }, [isOnline, ghostModeEnabled, syncStatus]);

  // Initialize database
  useEffect(() => {
    initDatabase()
      .then(() => setDbReady(true))
      .catch((err) => {
        console.error('Database init failed:', err);
        setDbError(err.message);
      });
  }, []);

  // Listen to auth state
  useEffect(() => {
    const unsubscribe = authService.onAuthStateChange((authUser) => {
      setUser(authUser);
      const userData = authService.getUserData();
      if (userData?.organizationId) {
        setOrganizationId(userData.organizationId);
      }
    });

    return unsubscribe;
  }, [setOrganizationId]);

  // Handle auth redirects
  useEffect(() => {
    if (user === undefined) return; // Still loading

    const inAuthGroup = segments[0] === '(auth)';

    if (!user && !inAuthGroup) {
      // Not logged in and not on auth screen -> redirect to login
      router.replace('/(auth)/login');
    } else if (user && inAuthGroup) {
      // Logged in but on auth screen -> redirect to home
      router.replace('/');
    }
  }, [user, segments]);

  // Show loading while initializing
  if (!dbReady || user === undefined) {
    return (
      <View className="flex-1 bg-background items-center justify-center">
        <ActivityIndicator size="large" color="#00d4ff" />
        <Text className="text-white mt-4">
          {!dbReady ? 'Initializing...' : 'Checking authentication...'}
        </Text>
      </View>
    );
  }

  // Show error if database failed
  if (dbError) {
    return (
      <View className="flex-1 bg-background items-center justify-center p-4">
        <Text className="text-danger text-xl font-bold">Database Error</Text>
        <Text className="text-gray-400 mt-2 text-center">{dbError}</Text>
      </View>
    );
  }

  const isDark = preferences.theme === 'dark';

  return (
    <>
      <StatusBar style={isDark ? 'light' : 'dark'} />
      <Stack
        screenOptions={{
          headerStyle: {
            backgroundColor: isDark ? '#1a1a2e' : '#ffffff',
          },
          headerTintColor: isDark ? '#00d4ff' : '#1a1a2e',
          headerTitleStyle: {
            fontWeight: 'bold',
          },
          contentStyle: {
            backgroundColor: isDark ? '#1a1a2e' : '#f5f5f5',
          },
        }}
      >
        <Stack.Screen
          name="(auth)"
          options={{
            headerShown: false,
          }}
        />
        <Stack.Screen
          name="index"
          options={{
            title: 'ChatterFix Relay',
          }}
        />
        <Stack.Screen
          name="assets/index"
          options={{
            title: 'Assets',
          }}
        />
        <Stack.Screen
          name="assets/[id]"
          options={{
            title: 'Asset Details',
          }}
        />
        <Stack.Screen
          name="logs/index"
          options={{
            title: 'Voice Logs',
          }}
        />
        <Stack.Screen
          name="settings"
          options={{
            title: 'Settings',
            presentation: 'modal',
          }}
        />
      </Stack>
    </>
  );
}
