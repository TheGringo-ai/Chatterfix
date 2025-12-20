/**
 * Authentication Service
 * Firebase Auth integration with ChatterFix backend sync
 */

import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  User,
  updateProfile,
} from 'firebase/auth';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { auth } from './firebase';
import { backendSync } from './backendSync';

const USER_DATA_KEY = 'chatterfix_user_data';

// Check if we're running on the client side
const isClient = typeof window !== 'undefined';

export interface UserData {
  uid: string;
  email: string | null;
  displayName: string | null;
  organizationId: string | null;
  organizationName: string | null;
  role: string;
}

class AuthService {
  private currentUser: User | null = null;
  private userData: UserData | null = null;
  private authStateListeners: ((user: User | null) => void)[] = [];
  private initialized = false;

  constructor() {
    // Only initialize auth listener on client side
    if (isClient) {
      this.initializeAuthListener();
    }
  }

  private initializeAuthListener() {
    if (this.initialized) return;
    this.initialized = true;

    // Listen for auth state changes
    onAuthStateChanged(auth, async (user) => {
      this.currentUser = user;
      if (user) {
        await this.loadUserData(user);
      } else {
        this.userData = null;
        try {
          await AsyncStorage.removeItem(USER_DATA_KEY);
        } catch (e) {
          // Ignore storage errors during SSR
        }
      }

      // Notify listeners
      this.authStateListeners.forEach((listener) => listener(user));
    });
  }

  /**
   * Subscribe to auth state changes
   */
  onAuthStateChange(callback: (user: User | null) => void): () => void {
    // Initialize listener if on client and not yet initialized
    if (isClient && !this.initialized) {
      this.initializeAuthListener();
    }

    this.authStateListeners.push(callback);
    // Return unsubscribe function
    return () => {
      this.authStateListeners = this.authStateListeners.filter(
        (cb) => cb !== callback
      );
    };
  }

  /**
   * Get current user
   */
  getCurrentUser(): User | null {
    return this.currentUser;
  }

  /**
   * Get current user data with organization info
   */
  getUserData(): UserData | null {
    return this.userData;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return this.currentUser !== null;
  }

  /**
   * Sign in with email and password
   */
  async signIn(email: string, password: string): Promise<UserData> {
    try {
      const credential = await signInWithEmailAndPassword(auth, email, password);
      const user = credential.user;

      // Get ID token for backend
      const idToken = await user.getIdToken();

      // Sync with ChatterFix backend
      await this.syncWithBackend(idToken);

      await this.loadUserData(user);

      console.log('User signed in:', user.email);
      return this.userData!;
    } catch (error: any) {
      console.error('Sign in failed:', error);
      throw this.formatAuthError(error);
    }
  }

  /**
   * Create new account
   */
  async signUp(
    email: string,
    password: string,
    displayName: string
  ): Promise<UserData> {
    try {
      const credential = await createUserWithEmailAndPassword(
        auth,
        email,
        password
      );
      const user = credential.user;

      // Update display name
      await updateProfile(user, { displayName });

      // Get ID token for backend
      const idToken = await user.getIdToken();

      // Create user in ChatterFix backend
      await this.createBackendUser(idToken, displayName);

      await this.loadUserData(user);

      console.log('User created:', user.email);
      return this.userData!;
    } catch (error: any) {
      console.error('Sign up failed:', error);
      throw this.formatAuthError(error);
    }
  }

  /**
   * Sign out
   */
  async signOut(): Promise<void> {
    try {
      await firebaseSignOut(auth);
      await backendSync.clearAuth();
      await AsyncStorage.removeItem(USER_DATA_KEY);
      this.userData = null;
      console.log('User signed out');
    } catch (error) {
      console.error('Sign out failed:', error);
      throw error;
    }
  }

  /**
   * Load user data from backend or cache
   */
  private async loadUserData(user: User): Promise<void> {
    try {
      // Try to load from cache first
      const cachedData = await AsyncStorage.getItem(USER_DATA_KEY);
      if (cachedData) {
        this.userData = JSON.parse(cachedData);
      }

      // Fetch fresh data from backend
      const idToken = await user.getIdToken();
      await this.syncWithBackend(idToken);
    } catch (error) {
      console.error('Failed to load user data:', error);
      // Use basic data if backend fails
      this.userData = {
        uid: user.uid,
        email: user.email,
        displayName: user.displayName,
        organizationId: null,
        organizationName: null,
        role: 'technician',
      };
    }
  }

  /**
   * Sync with ChatterFix backend
   */
  private async syncWithBackend(idToken: string): Promise<void> {
    const BACKEND_URL =
      process.env.EXPO_PUBLIC_CHATTERFIX_API_URL || 'https://chatterfix.com';

    try {
      const response = await fetch(`${BACKEND_URL}/auth/firebase-signin`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ idToken }),
      });

      if (response.ok) {
        const data = await response.json();
        this.userData = {
          uid: data.user_id || this.currentUser?.uid || '',
          email: data.email || this.currentUser?.email,
          displayName: data.full_name || this.currentUser?.displayName,
          organizationId: data.organization_id,
          organizationName: data.organization_name,
          role: data.role || 'technician',
        };

        // Cache user data
        await AsyncStorage.setItem(USER_DATA_KEY, JSON.stringify(this.userData));

        // Store session token for backend sync
        if (data.session_token) {
          await backendSync.setAuthToken(data.session_token);
        }
      }
    } catch (error) {
      console.error('Backend sync failed:', error);
    }
  }

  /**
   * Create user in ChatterFix backend
   */
  private async createBackendUser(
    idToken: string,
    displayName: string
  ): Promise<void> {
    const BACKEND_URL =
      process.env.EXPO_PUBLIC_CHATTERFIX_API_URL || 'https://chatterfix.com';

    try {
      await fetch(`${BACKEND_URL}/auth/firebase-signin`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          idToken,
          full_name: displayName,
          create_user: true,
        }),
      });
    } catch (error) {
      console.error('Failed to create backend user:', error);
    }
  }

  /**
   * Format Firebase auth errors
   */
  private formatAuthError(error: any): Error {
    const code = error.code || '';
    const messages: Record<string, string> = {
      'auth/email-already-in-use': 'This email is already registered.',
      'auth/invalid-email': 'Please enter a valid email address.',
      'auth/weak-password': 'Password should be at least 6 characters.',
      'auth/user-not-found': 'No account found with this email.',
      'auth/wrong-password': 'Incorrect password.',
      'auth/too-many-requests': 'Too many attempts. Please try again later.',
      'auth/network-request-failed': 'Network error. Please check your connection.',
    };

    return new Error(messages[code] || error.message || 'Authentication failed.');
  }
}

export const authService = new AuthService();
export default authService;
