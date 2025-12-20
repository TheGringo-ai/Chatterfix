/**
 * Firebase Configuration for ChatterFix Relay
 * Uses the same Firebase project as the main ChatterFix app
 */

import { initializeApp, getApps, getApp } from 'firebase/app';
import {
  getFirestore,
  initializeFirestore,
  persistentLocalCache,
  persistentMultipleTabManager,
} from 'firebase/firestore';
import { getAuth } from 'firebase/auth';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Firebase configuration - matches main ChatterFix project
const firebaseConfig = {
  apiKey: process.env.EXPO_PUBLIC_FIREBASE_API_KEY || 'AIzaSyDJILCnREm8P9QAUZdkGTWMaQu32rW-eqA',
  authDomain: 'fredfix.firebaseapp.com',
  projectId: 'fredfix',
  storageBucket: 'fredfix.firebasestorage.app',
  messagingSenderId: '650169261019',
  appId: '1:650169261019:web:b77b48ae85b2cd49eca5fe',
  measurementId: 'G-CPFPBM63QZ',
};

// Initialize Firebase (singleton pattern)
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();

// Initialize Firestore with offline persistence
const db = initializeFirestore(app, {
  localCache: persistentLocalCache({
    tabManager: persistentMultipleTabManager(),
  }),
});

// Initialize Auth
const auth = getAuth(app);

export { app, db, auth };
export default db;
