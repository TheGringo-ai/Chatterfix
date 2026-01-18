/**
 * Firebase Configuration
 * Uses environment variables from app.config.ts via Expo Constants
 */

import { initializeApp, getApps, getApp } from 'firebase/app';
import { initializeAuth, getReactNativePersistence, getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';
import ReactNativeAsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';

// Get Firebase config from Expo Constants (loaded from environment via app.config.ts)
const expoConfig = Constants.expoConfig?.extra?.firebase;

// Firebase configuration for ChatterFix (fredfix project)
// All values loaded from environment variables via app.config.ts
// Set these in mobile/.env file (see .env.example)
const firebaseConfig = {
  apiKey: expoConfig?.apiKey,
  authDomain: expoConfig?.authDomain || "fredfix.firebaseapp.com",
  projectId: expoConfig?.projectId || "fredfix",
  storageBucket: expoConfig?.storageBucket || "fredfix.firebasestorage.app",
  databaseURL: expoConfig?.databaseURL || "https://fredfix-default-rtdb.firebaseio.com",
  messagingSenderId: expoConfig?.messagingSenderId,
  appId: expoConfig?.appId,
  measurementId: expoConfig?.measurementId
};

// Validate required config in development
if (__DEV__ && !firebaseConfig.apiKey) {
  console.warn(
    'Firebase API key not configured.\n' +
    'Create mobile/.env file with FIREBASE_API_KEY=your-key\n' +
    'See mobile/.env.example for all required variables.'
  );
}

// Initialize Firebase (check if already initialized for hot reload)
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();

// Initialize Firebase Auth with AsyncStorage persistence
// Use try-catch to handle hot reload scenarios where auth is already initialized
let auth;
try {
  auth = initializeAuth(app, {
    persistence: getReactNativePersistence(ReactNativeAsyncStorage)
  });
} catch (error: any) {
  // Auth already initialized, get the existing instance
  if (error.code === 'auth/already-initialized') {
    auth = getAuth(app);
  } else {
    throw error;
  }
}

export { auth };
export const db = getFirestore(app);

// Export config for debugging
export const getFirebaseConfig = () => ({
  projectId: firebaseConfig.projectId,
  authDomain: firebaseConfig.authDomain,
  hasApiKey: !!firebaseConfig.apiKey,
  hasAppId: !!firebaseConfig.appId
});

export default app;
