import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

// Import authentication context
import { AuthProvider, useAuth } from './src/contexts/AuthContext';
import { AssetProvider } from './src/contexts/AssetContext';
import { FieldModeProvider } from './src/contexts/FieldModeContext';

// Import screens
import AssetsScreen from './src/screens/AssetsScreen';
import CameraScreen from './src/screens/CameraScreen';
import DashboardScreen from './src/screens/DashboardScreen';
import LoginScreen from './src/screens/LoginScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import SignupScreen from './src/screens/SignupScreen';
import VoiceCommandsScreen from './src/screens/VoiceCommandsScreen';
import WorkOrdersScreen from './src/screens/WorkOrdersScreen';
import GlassesHUDScreen from './src/screens/GlassesHUDScreen';

// Import components
import OfflineIndicator from './src/components/OfflineIndicator';
import DemoBanner from './src/components/DemoBanner';

// Create navigation stacks
const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

// Create query client for data fetching
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 2,
    },
  },
});

// Tab Navigator - Now always accessible (demo mode when not logged in)
function MainTabs() {
  const { isAuthenticated } = useAuth();

  return (
    <View style={{ flex: 1 }}>
      <OfflineIndicator />
      {/* Show demo banner when not authenticated */}
      {!isAuthenticated && <DemoBanner />}
      <Tab.Navigator
        screenOptions={{
          tabBarActiveTintColor: '#3498db',
          tabBarInactiveTintColor: '#7f8c8d',
          tabBarStyle: {
            backgroundColor: '#1a1a2e',
            borderTopColor: '#2d2d4a',
          },
          headerStyle: {
            backgroundColor: '#1e3c72',
          },
          headerTintColor: '#fff',
        }}
      >
      <Tab.Screen
        name="Dashboard"
        component={DashboardScreen}
        options={{
          tabBarIcon: ({ color }) => (
            <Text style={{ fontSize: 24 }}>📊</Text>
          ),
        }}
      />
      <Tab.Screen
        name="Work Orders"
        component={WorkOrdersScreen}
        options={{
          tabBarIcon: ({ color }) => (
            <Text style={{ fontSize: 24 }}>📋</Text>
          ),
        }}
      />
      <Tab.Screen
        name="Voice"
        component={VoiceCommandsScreen}
        options={{
          tabBarIcon: ({ color }) => (
            <Text style={{ fontSize: 24 }}>🎤</Text>
          ),
          tabBarLabel: 'Voice',
        }}
      />
      <Tab.Screen
        name="Camera"
        component={CameraScreen}
        options={{
          tabBarIcon: ({ color }) => (
            <Text style={{ fontSize: 24 }}>📷</Text>
          ),
          tabBarLabel: 'Scan',
        }}
      />
      <Tab.Screen
        name="Assets"
        component={AssetsScreen}
        options={{
          tabBarIcon: ({ color }) => (
            <Text style={{ fontSize: 24 }}>🔧</Text>
          ),
        }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          tabBarIcon: ({ color }) => (
            <Text style={{ fontSize: 24 }}>⚙️</Text>
          ),
        }}
      />
    </Tab.Navigator>
    </View>
  );
}

// Auth Navigator - For login/signup screens
function AuthStack() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
      }}
    >
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="Signup" component={SignupScreen} />
    </Stack.Navigator>
  );
}

// Root Navigator Component - DEMO FIRST approach
function RootNavigator() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
      }}
    >
      {/* Always show MainTabs first - demo mode when not logged in */}
      <Stack.Screen name="Main" component={MainTabs} />
      {/* Auth screens available when user wants to login */}
      <Stack.Screen
        name="Auth"
        component={AuthStack}
        options={{
          presentation: 'modal', // Slide up as modal
        }}
      />
      {/* Glasses HUD - Full screen immersive mode */}
      <Stack.Screen
        name="GlassesHUD"
        component={GlassesHUDScreen}
        options={{
          presentation: 'fullScreenModal',
          animation: 'fade',
          headerShown: false,
        }}
      />
    </Stack.Navigator>
  );
}

// Main App Component
export default function App() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <FieldModeProvider>
          <AssetProvider>
            <QueryClientProvider client={queryClient}>
              <NavigationContainer>
                <StatusBar style="light" />
                <RootNavigator />
              </NavigationContainer>
            </QueryClientProvider>
          </AssetProvider>
        </FieldModeProvider>
      </AuthProvider>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
});
