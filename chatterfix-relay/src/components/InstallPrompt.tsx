/**
 * InstallPrompt Component
 * Shows a banner prompting users to install the app on their device
 * Works on web (PWA) and shows instructions for mobile
 */

import { useState, useEffect, useCallback } from 'react';
import { View, Text, Pressable, Platform, Linking } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

const INSTALL_DISMISSED_KEY = 'install_prompt_dismissed';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

export function InstallPrompt() {
  const [showPrompt, setShowPrompt] = useState(false);
  const [installEvent, setInstallEvent] = useState<BeforeInstallPromptEvent | null>(null);
  const [isStandalone, setIsStandalone] = useState(false);
  const [platform, setPlatform] = useState<'ios' | 'android' | 'desktop' | 'native'>('native');

  useEffect(() => {
    checkInstallStatus();
  }, []);

  const checkInstallStatus = async () => {
    // Check if already dismissed
    const dismissed = await AsyncStorage.getItem(INSTALL_DISMISSED_KEY);
    if (dismissed === 'true') {
      return;
    }

    // Native app - already installed
    if (Platform.OS !== 'web') {
      setPlatform('native');
      return;
    }

    // Check if already running as PWA/standalone
    if (typeof window !== 'undefined') {
      const isStandaloneMode =
        window.matchMedia('(display-mode: standalone)').matches ||
        (window.navigator as any).standalone === true;

      if (isStandaloneMode) {
        setIsStandalone(true);
        return;
      }

      // Detect platform for instructions
      const userAgent = navigator.userAgent.toLowerCase();
      if (/iphone|ipad|ipod/.test(userAgent)) {
        setPlatform('ios');
        setShowPrompt(true);
      } else if (/android/.test(userAgent)) {
        setPlatform('android');
        setShowPrompt(true);
      } else {
        setPlatform('desktop');
        setShowPrompt(true);
      }

      // Listen for beforeinstallprompt (Chrome/Edge)
      const handleBeforeInstall = (e: Event) => {
        e.preventDefault();
        setInstallEvent(e as BeforeInstallPromptEvent);
        setShowPrompt(true);
      };

      window.addEventListener('beforeinstallprompt', handleBeforeInstall);

      return () => {
        window.removeEventListener('beforeinstallprompt', handleBeforeInstall);
      };
    }
  };

  const handleInstall = async () => {
    if (installEvent) {
      // Chrome/Edge PWA install
      await installEvent.prompt();
      const choice = await installEvent.userChoice;
      if (choice.outcome === 'accepted') {
        setShowPrompt(false);
        await AsyncStorage.setItem(INSTALL_DISMISSED_KEY, 'true');
      }
    }
  };

  const handleDismiss = async () => {
    setShowPrompt(false);
    await AsyncStorage.setItem(INSTALL_DISMISSED_KEY, 'true');
  };

  // Don't show if native app, already standalone, or dismissed
  if (!showPrompt || isStandalone || platform === 'native') {
    return null;
  }

  return (
    <View className="bg-primary/20 border border-primary rounded-xl p-4 mb-4">
      <View className="flex-row items-start justify-between">
        <View className="flex-1 mr-3">
          <View className="flex-row items-center mb-2">
            <Text className="text-2xl mr-2">📲</Text>
            <Text className="text-white font-bold text-lg">Install App</Text>
          </View>

          {platform === 'ios' && (
            <Text className="text-gray-300 text-sm mb-3">
              Tap the <Text className="text-primary font-bold">Share</Text> button below, then{' '}
              <Text className="text-primary font-bold">"Add to Home Screen"</Text>
            </Text>
          )}

          {platform === 'android' && !installEvent && (
            <Text className="text-gray-300 text-sm mb-3">
              Tap the <Text className="text-primary font-bold">menu (⋮)</Text> and select{' '}
              <Text className="text-primary font-bold">"Add to Home screen"</Text>
            </Text>
          )}

          {platform === 'android' && installEvent && (
            <Text className="text-gray-300 text-sm mb-3">
              Install ChatterFix Relay for quick access and offline support
            </Text>
          )}

          {platform === 'desktop' && !installEvent && (
            <Text className="text-gray-300 text-sm mb-3">
              Click the <Text className="text-primary font-bold">install icon (⊕)</Text> in your address bar
            </Text>
          )}

          {platform === 'desktop' && installEvent && (
            <Text className="text-gray-300 text-sm mb-3">
              Install ChatterFix Relay on your desktop for quick access
            </Text>
          )}

          <View className="flex-row gap-3">
            {installEvent && (
              <Pressable
                onPress={handleInstall}
                className="bg-primary px-4 py-2 rounded-lg"
              >
                <Text className="text-white font-semibold">Install Now</Text>
              </Pressable>
            )}

            <Pressable
              onPress={handleDismiss}
              className="bg-gray-600 px-4 py-2 rounded-lg"
            >
              <Text className="text-gray-300">Maybe Later</Text>
            </Pressable>
          </View>
        </View>

        {/* Close button */}
        <Pressable onPress={handleDismiss} className="p-1">
          <Text className="text-gray-400 text-xl">✕</Text>
        </Pressable>
      </View>
    </View>
  );
}

export default InstallPrompt;
