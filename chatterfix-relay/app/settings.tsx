/**
 * Settings Screen
 * User preferences and app configuration
 */

import { View, Text, Switch, Pressable, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { useAppStore } from '@/stores';
import { authService } from '@/services';

export default function SettingsScreen() {
  const router = useRouter();
  const { preferences, setPreference, setOrganizationId } = useAppStore();
  const userData = authService.getUserData();

  const SettingRow = ({
    label,
    description,
    value,
    onValueChange,
  }: {
    label: string;
    description: string;
    value: boolean;
    onValueChange: (value: boolean) => void;
  }) => (
    <View className="flex-row items-center justify-between py-4 border-b border-gray-700">
      <View className="flex-1 mr-4">
        <Text className="text-white font-medium">{label}</Text>
        <Text className="text-gray-400 text-sm">{description}</Text>
      </View>
      <Switch
        value={value}
        onValueChange={onValueChange}
        trackColor={{ false: '#3e3e3e', true: '#00d4ff' }}
        thumbColor={value ? '#ffffff' : '#f4f3f4'}
      />
    </View>
  );

  return (
    <View className="flex-1 bg-background p-4">
      {/* Theme Section */}
      <Text className="text-primary text-lg font-bold mb-2">Appearance</Text>
      <View className="bg-background-card rounded-xl p-4 mb-6">
        <SettingRow
          label="Field Mode"
          description="High-contrast UI for outdoor use"
          value={preferences.fieldMode}
          onValueChange={(v) => setPreference('fieldMode', v)}
        />
      </View>

      {/* Feedback Section */}
      <Text className="text-primary text-lg font-bold mb-2">Feedback</Text>
      <View className="bg-background-card rounded-xl p-4 mb-6">
        <SettingRow
          label="Haptic Feedback"
          description="Vibrate on actions"
          value={preferences.hapticFeedback}
          onValueChange={(v) => setPreference('hapticFeedback', v)}
        />
        <SettingRow
          label="Voice Confirmation"
          description="Speak confirmation after commands"
          value={preferences.voiceConfirmation}
          onValueChange={(v) => setPreference('voiceConfirmation', v)}
        />
      </View>

      {/* Database Section */}
      <Text className="text-primary text-lg font-bold mb-2">Database</Text>
      <View className="bg-background-card rounded-xl p-4 mb-6">
        <Pressable className="py-4 border-b border-gray-700">
          <Text className="text-white font-medium">Sync Now</Text>
          <Text className="text-gray-400 text-sm">Force sync with server</Text>
        </Pressable>
        <Pressable className="py-4">
          <Text className="text-danger font-medium">Clear Local Data</Text>
          <Text className="text-gray-400 text-sm">Remove all cached data</Text>
        </Pressable>
      </View>

      {/* Account Section */}
      <Text className="text-primary text-lg font-bold mb-2">Account</Text>
      <View className="bg-background-card rounded-xl p-4 mb-6">
        <View className="py-4 border-b border-gray-700">
          <Text className="text-white font-medium">{userData?.displayName || 'User'}</Text>
          <Text className="text-gray-400 text-sm">{userData?.email || 'Not signed in'}</Text>
          {userData?.organizationName && (
            <Text className="text-primary text-sm mt-1">{userData.organizationName}</Text>
          )}
        </View>
        <Pressable
          className="py-4"
          onPress={() => {
            Alert.alert(
              'Sign Out',
              'Are you sure you want to sign out?',
              [
                { text: 'Cancel', style: 'cancel' },
                {
                  text: 'Sign Out',
                  style: 'destructive',
                  onPress: async () => {
                    try {
                      await authService.signOut();
                      setOrganizationId(null);
                      router.replace('/(auth)/login');
                    } catch (error) {
                      Alert.alert('Error', 'Failed to sign out');
                    }
                  },
                },
              ]
            );
          }}
        >
          <Text className="text-danger font-medium">Sign Out</Text>
          <Text className="text-gray-400 text-sm">Log out of your account</Text>
        </Pressable>
      </View>

      {/* Close Button */}
      <Pressable
        onPress={() => router.back()}
        className="bg-primary rounded-xl py-4 items-center"
      >
        <Text className="text-background font-bold text-lg">Done</Text>
      </Pressable>
    </View>
  );
}
