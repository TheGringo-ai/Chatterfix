/**
 * Settings Screen - App configuration and user preferences
 * Shows login/signup options when in demo mode
 */

import { useNavigation } from '@react-navigation/native';
import { signOut } from 'firebase/auth';
import { useState } from 'react';
import {
    Alert,
    ScrollView,
    StyleSheet,
    Switch,
    Text,
    TouchableOpacity,
    View,
} from 'react-native';
import { useAuth } from '../contexts/AuthContext';
import { auth } from '../services/firebase';
import { apiService } from '../services/api';

export default function SettingsScreen() {
  const { user, isAuthenticated } = useAuth();
  const navigation = useNavigation<any>();

  // Settings state
  const [pushNotifications, setPushNotifications] = useState(true);
  const [offlineMode, setOfflineMode] = useState(true);
  const [locationTracking, setLocationTracking] = useState(true);
  const [darkMode, setDarkMode] = useState(true);
  const [syncOnWifi, setSyncOnWifi] = useState(false);

  const handleLogin = () => {
    navigation.navigate('Auth', { screen: 'Login' });
  };

  const handleSignup = () => {
    navigation.navigate('Auth', { screen: 'Signup' });
  };

  const handleSignOut = () => {
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
              await signOut(auth);
              await apiService.logout();
              // App will show demo mode after sign out
            } catch (error) {
              Alert.alert('Error', 'Failed to sign out');
            }
          },
        },
      ]
    );
  };

  const handleSyncNow = async () => {
    Alert.alert('Sync Started', 'Syncing data with server...');
    try {
      const result = await apiService.syncOfflineData();
      Alert.alert('Sync Complete', `Synced ${result.success} items, ${result.failed} failed`);
    } catch (error) {
      Alert.alert('Sync Failed', 'Could not sync data. Please try again.');
    }
  };

  const handleClearCache = () => {
    Alert.alert(
      'Clear Cache',
      'This will remove all cached data. You will need to sync again.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: () => {
            Alert.alert('Cache Cleared', 'All cached data has been removed.');
          },
        },
      ]
    );
  };

  const SettingItem = ({
    icon,
    title,
    description,
    value,
    onValueChange,
  }: {
    icon: string;
    title: string;
    description: string;
    value: boolean;
    onValueChange: (value: boolean) => void;
  }) => (
    <View style={styles.settingItem}>
      <Text style={styles.settingIcon}>{icon}</Text>
      <View style={styles.settingInfo}>
        <Text style={styles.settingTitle}>{title}</Text>
        <Text style={styles.settingDescription}>{description}</Text>
      </View>
      <Switch
        value={value}
        onValueChange={onValueChange}
        trackColor={{ false: '#767577', true: '#3498db' }}
        thumbColor={value ? '#fff' : '#f4f3f4'}
      />
    </View>
  );

  return (
    <ScrollView style={styles.container}>
      {/* User Info / Auth Section */}
      {isAuthenticated ? (
        // Authenticated User Section
        <View style={styles.userSection}>
          <View style={styles.avatarContainer}>
            <Text style={styles.avatarText}>👤</Text>
          </View>
          <View style={styles.userInfo}>
            <Text style={styles.userName}>{user?.displayName || 'User'}</Text>
            <Text style={styles.userEmail}>{user?.email || 'user@chatterfix.com'}</Text>
          </View>
        </View>
      ) : (
        // Demo Mode - Show Login/Signup Options
        <View style={styles.authSection}>
          <View style={styles.authHeader}>
            <Text style={styles.authIcon}>🔐</Text>
            <View>
              <Text style={styles.authTitle}>Get Full Access</Text>
              <Text style={styles.authSubtitle}>Sign in to unlock all features</Text>
            </View>
          </View>

          <View style={styles.authFeatures}>
            <Text style={styles.featureItem}>✓ Sync data across devices</Text>
            <Text style={styles.featureItem}>✓ Create & manage work orders</Text>
            <Text style={styles.featureItem}>✓ Voice commands & OCR</Text>
            <Text style={styles.featureItem}>✓ Real-time notifications</Text>
          </View>

          <View style={styles.authButtons}>
            <TouchableOpacity style={styles.loginButton} onPress={handleLogin}>
              <Text style={styles.loginButtonText}>Sign In</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.signupButton} onPress={handleSignup}>
              <Text style={styles.signupButtonText}>Create Account</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Notifications Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Notifications</Text>
        <SettingItem
          icon="📱"
          title="Push Notifications"
          description="Receive alerts for urgent work orders"
          value={pushNotifications}
          onValueChange={setPushNotifications}
        />
      </View>

      {/* Offline & Sync Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Offline & Sync</Text>
        <SettingItem
          icon="💾"
          title="Offline Mode"
          description="Cache data for offline access"
          value={offlineMode}
          onValueChange={setOfflineMode}
        />
        <SettingItem
          icon="📶"
          title="Sync on WiFi Only"
          description="Only sync when connected to WiFi"
          value={syncOnWifi}
          onValueChange={setSyncOnWifi}
        />
        <TouchableOpacity style={styles.actionButton} onPress={handleSyncNow}>
          <Text style={styles.actionButtonIcon}>🔄</Text>
          <Text style={styles.actionButtonText}>Sync Now</Text>
        </TouchableOpacity>
      </View>

      {/* Location Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Location</Text>
        <SettingItem
          icon="🗺️"
          title="Location Tracking"
          description="Enable for work order routing"
          value={locationTracking}
          onValueChange={setLocationTracking}
        />
      </View>

      {/* Appearance Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Appearance</Text>
        <SettingItem
          icon="🌙"
          title="Dark Mode"
          description="Use dark theme"
          value={darkMode}
          onValueChange={setDarkMode}
        />
      </View>

      {/* Glasses Mode Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Glasses Mode</Text>
        <View style={styles.glassesModeInfo}>
          <Text style={styles.glassesModeIcon}>👓</Text>
          <View style={styles.glassesModeText}>
            <Text style={styles.glassesModeTitle}>Smart Glasses HUD</Text>
            <Text style={styles.glassesModeDesc}>
              Audio-only interface for Brilliant Labs glasses or testing hands-free operation
            </Text>
          </View>
        </View>
        <TouchableOpacity
          style={styles.glassesButton}
          onPress={() => navigation.navigate('GlassesHUD' as never)}
        >
          <Text style={styles.glassesButtonIcon}>🕶️</Text>
          <Text style={styles.glassesButtonText}>Enter Glasses Mode</Text>
        </TouchableOpacity>
        <Text style={styles.glassesModeHint}>
          Long-press anywhere to exit
        </Text>
      </View>

      {/* Data Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Data</Text>
        <TouchableOpacity style={styles.actionButton} onPress={handleClearCache}>
          <Text style={styles.actionButtonIcon}>🗑️</Text>
          <Text style={[styles.actionButtonText, { color: '#e74c3c' }]}>
            Clear Cache
          </Text>
        </TouchableOpacity>
      </View>

      {/* About Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>About</Text>
        <View style={styles.aboutItem}>
          <Text style={styles.aboutLabel}>Version</Text>
          <Text style={styles.aboutValue}>1.0.0</Text>
        </View>
        <View style={styles.aboutItem}>
          <Text style={styles.aboutLabel}>Server</Text>
          <Text style={styles.aboutValue}>chatterfix.com</Text>
        </View>
        <View style={styles.aboutItem}>
          <Text style={styles.aboutLabel}>Mode</Text>
          <Text style={styles.aboutValue}>{isAuthenticated ? 'Full Access' : 'Demo'}</Text>
        </View>
      </View>

      {/* Sign Out - Only show when authenticated */}
      {isAuthenticated && (
        <TouchableOpacity style={styles.signOutButton} onPress={handleSignOut}>
          <Text style={styles.signOutText}>Sign Out</Text>
        </TouchableOpacity>
      )}

      <View style={styles.footer}>
        <Text style={styles.footerText}>ChatterFix CMMS</Text>
        <Text style={styles.footerText}>AI-Powered Maintenance Management</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  // Authenticated User Section
  userSection: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    marginBottom: 20,
  },
  avatarContainer: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#3498db',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    fontSize: 30,
  },
  userInfo: {
    marginLeft: 15,
  },
  userName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
  },
  userEmail: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
    marginTop: 2,
  },
  // Demo Mode Auth Section
  authSection: {
    margin: 15,
    padding: 20,
    backgroundColor: 'rgba(52, 152, 219, 0.15)',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(52, 152, 219, 0.3)',
  },
  authHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 15,
  },
  authIcon: {
    fontSize: 40,
    marginRight: 15,
  },
  authTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#fff',
  },
  authSubtitle: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.7)',
    marginTop: 2,
  },
  authFeatures: {
    marginBottom: 20,
    paddingLeft: 5,
  },
  featureItem: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.8)',
    marginBottom: 8,
  },
  authButtons: {
    gap: 10,
  },
  loginButton: {
    backgroundColor: '#3498db',
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
  },
  loginButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  signupButton: {
    backgroundColor: 'transparent',
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#3498db',
  },
  signupButtonText: {
    color: '#3498db',
    fontSize: 16,
    fontWeight: '600',
  },
  // Sections
  section: {
    paddingHorizontal: 20,
    marginBottom: 25,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#3498db',
    marginBottom: 12,
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    padding: 15,
    marginBottom: 10,
  },
  settingIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  settingInfo: {
    flex: 1,
  },
  settingTitle: {
    fontSize: 15,
    fontWeight: '500',
    color: '#fff',
  },
  settingDescription: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.6)',
    marginTop: 2,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    padding: 15,
    marginTop: 5,
  },
  actionButtonIcon: {
    fontSize: 20,
    marginRight: 10,
  },
  actionButtonText: {
    fontSize: 15,
    fontWeight: '500',
    color: '#3498db',
  },
  aboutItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    padding: 15,
    marginBottom: 10,
  },
  aboutLabel: {
    fontSize: 15,
    color: 'rgba(255, 255, 255, 0.7)',
  },
  aboutValue: {
    fontSize: 15,
    color: '#fff',
    fontWeight: '500',
  },
  signOutButton: {
    margin: 20,
    padding: 15,
    backgroundColor: 'rgba(231, 76, 60, 0.2)',
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(231, 76, 60, 0.3)',
  },
  signOutText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#e74c3c',
  },
  footer: {
    padding: 30,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.4)',
    marginBottom: 4,
  },
  // Glasses Mode Section
  glassesModeInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    padding: 15,
    marginBottom: 10,
  },
  glassesModeIcon: {
    fontSize: 32,
    marginRight: 15,
  },
  glassesModeText: {
    flex: 1,
  },
  glassesModeTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#fff',
  },
  glassesModeDesc: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.6)',
    marginTop: 4,
    lineHeight: 18,
  },
  glassesButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#00FF41',
    borderRadius: 12,
    padding: 15,
    marginTop: 5,
  },
  glassesButtonIcon: {
    fontSize: 20,
    marginRight: 10,
  },
  glassesButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
  },
  glassesModeHint: {
    fontSize: 11,
    color: 'rgba(255, 255, 255, 0.4)',
    textAlign: 'center',
    marginTop: 8,
    fontStyle: 'italic',
  },
});
