/**
 * Firebase Configuration
 */

import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

// Firebase configuration for ChatterFix (fredfix project)
const firebaseConfig = {
  apiKey: "AIzaSyAaXlvuopHtTZglfghnlc_hBqGr1YzPrBk",
  authDomain: "fredfix.firebaseapp.com",
  projectId: "fredfix",
  storageBucket: "fredfix.firebasestorage.app",
  databaseURL: "https://fredfix-default-rtdb.firebaseio.com",
  messagingSenderId: "650169261019",
  appId: "1:650169261019:web:b77b48ae85b2cd49eca5fe",
  measurementId: "G-CPFPBM63QZ"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase services
export const auth = getAuth(app);
export const db = getFirestore(app);

export default app;