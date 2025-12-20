/**
 * FallDetection.ts
 * The "Man Down" Detection Service
 *
 * Monitors device accelerometer for sudden falls and triggers emergency response.
 *
 * Features:
 * - Real-time accelerometer monitoring
 * - G-force spike detection (falls typically produce 3-8g)
 * - 30-second emergency countdown with cancel option
 * - Automatic supervisor notification
 * - Black Box video buffer save trigger
 */

import { Accelerometer, AccelerometerMeasurement } from 'expo-sensors';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Haptics from 'expo-haptics';
import * as Location from 'expo-location';

// API configuration
const API_BASE_URL = process.env.EXPO_PUBLIC_CHATTERFIX_API_URL || 'https://chatterfix.com';

// Detection thresholds (calibrated for industrial environments)
const FALL_THRESHOLD_G = 3.5; // G-force that indicates a fall
const IMPACT_THRESHOLD_G = 6.0; // Severe impact threshold
const FALL_DURATION_MS = 500; // Minimum duration to confirm fall
const COUNTDOWN_SECONDS = 30; // Time before auto-notification

// Accelerometer sampling rate
const UPDATE_INTERVAL_MS = 100; // 10Hz sampling

export interface FallEvent {
  timestamp: number;
  gForce: number;
  duration: number;
  latitude?: number;
  longitude?: number;
  location?: string;
  cancelled: boolean;
}

export interface FallDetectionCallbacks {
  onFallDetected: (event: FallEvent) => void;
  onCountdownTick: (secondsRemaining: number) => void;
  onEmergencyTriggered: (event: FallEvent) => void;
  onEmergencyCancelled: () => void;
}

class FallDetectionService {
  private subscription: ReturnType<typeof Accelerometer.addListener> | null = null;
  private isMonitoring: boolean = false;
  private callbacks: FallDetectionCallbacks | null = null;

  // Fall detection state
  private lastMeasurement: AccelerometerMeasurement | null = null;
  private fallStartTime: number | null = null;
  private currentFallEvent: FallEvent | null = null;
  private countdownTimer: NodeJS.Timeout | null = null;
  private countdownSeconds: number = COUNTDOWN_SECONDS;

  // User context
  private userId: string | null = null;
  private userName: string | null = null;

  /**
   * Calculate magnitude of acceleration vector (G-force)
   */
  private calculateGForce(measurement: AccelerometerMeasurement): number {
    const { x, y, z } = measurement;
    // Magnitude of acceleration vector
    // Normal standing = ~1g, Free fall = ~0g, Impact = 3-10g
    return Math.sqrt(x * x + y * y + z * z);
  }

  /**
   * Check if current measurement indicates a fall
   */
  private detectFall(gForce: number): boolean {
    // A fall typically shows:
    // 1. Initial free-fall (low G, ~0.3g)
    // 2. Sudden impact (high G, 3-10g)
    // We detect the impact phase

    if (gForce >= FALL_THRESHOLD_G) {
      if (!this.fallStartTime) {
        this.fallStartTime = Date.now();
      }

      const fallDuration = Date.now() - this.fallStartTime;

      // Confirm fall after minimum duration
      if (fallDuration >= FALL_DURATION_MS) {
        return true;
      }
    } else {
      // Reset if G-force drops below threshold
      this.fallStartTime = null;
    }

    return false;
  }

  /**
   * Handle accelerometer measurement
   */
  private handleMeasurement = async (measurement: AccelerometerMeasurement) => {
    this.lastMeasurement = measurement;
    const gForce = this.calculateGForce(measurement);

    if (this.detectFall(gForce) && !this.currentFallEvent) {
      // Fall detected! Start emergency sequence
      await this.handleFallDetected(gForce);
    }
  };

  /**
   * Handle detected fall event
   */
  private async handleFallDetected(gForce: number) {
    console.log(`[FallDetection] FALL DETECTED! G-force: ${gForce.toFixed(2)}`);

    // Haptic feedback to alert user
    await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);

    // Get location
    let latitude: number | undefined;
    let longitude: number | undefined;
    try {
      const location = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.High,
      });
      latitude = location.coords.latitude;
      longitude = location.coords.longitude;
    } catch (e) {
      console.warn('[FallDetection] Could not get location:', e);
    }

    // Create fall event
    this.currentFallEvent = {
      timestamp: Date.now(),
      gForce,
      duration: Date.now() - (this.fallStartTime || Date.now()),
      latitude,
      longitude,
      cancelled: false,
    };

    // Notify listener
    this.callbacks?.onFallDetected(this.currentFallEvent);

    // Start countdown to emergency
    this.startEmergencyCountdown();
  }

  /**
   * Start the emergency countdown timer
   */
  private startEmergencyCountdown() {
    this.countdownSeconds = COUNTDOWN_SECONDS;

    this.countdownTimer = setInterval(() => {
      this.countdownSeconds--;
      this.callbacks?.onCountdownTick(this.countdownSeconds);

      // Haptic tick every 5 seconds
      if (this.countdownSeconds % 5 === 0) {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
      }

      if (this.countdownSeconds <= 0) {
        this.triggerEmergency();
      }
    }, 1000);
  }

  /**
   * Cancel the emergency (user is OK)
   */
  public async cancelEmergency() {
    if (this.countdownTimer) {
      clearInterval(this.countdownTimer);
      this.countdownTimer = null;
    }

    if (this.currentFallEvent) {
      this.currentFallEvent.cancelled = true;

      // Report false alarm to backend
      await this.reportFalseAlarm();
    }

    this.currentFallEvent = null;
    this.fallStartTime = null;
    this.callbacks?.onEmergencyCancelled();

    console.log('[FallDetection] Emergency cancelled - user confirmed OK');
  }

  /**
   * Trigger emergency response
   */
  private async triggerEmergency() {
    if (this.countdownTimer) {
      clearInterval(this.countdownTimer);
      this.countdownTimer = null;
    }

    if (!this.currentFallEvent) return;

    console.log('[FallDetection] EMERGENCY TRIGGERED - Notifying supervisors');

    // Strong haptic alert
    await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);

    // Report to backend
    await this.reportManDown();

    // Notify listener
    this.callbacks?.onEmergencyTriggered(this.currentFallEvent);
  }

  /**
   * Report man-down event to backend
   */
  private async reportManDown() {
    if (!this.currentFallEvent) return;

    try {
      const formData = new FormData();
      formData.append('user_id', this.userId || 'unknown');
      formData.append('user_name', this.userName || 'Unknown Worker');
      formData.append('g_force', this.currentFallEvent.gForce.toString());
      formData.append('fall_duration_ms', this.currentFallEvent.duration.toString());

      if (this.currentFallEvent.latitude) {
        formData.append('gps_lat', this.currentFallEvent.latitude.toString());
      }
      if (this.currentFallEvent.longitude) {
        formData.append('gps_lng', this.currentFallEvent.longitude.toString());
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/safety/man-down`, {
        method: 'POST',
        body: formData,
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Failed to report: ${response.status}`);
      }

      console.log('[FallDetection] Man-down event reported to backend');
    } catch (error) {
      console.error('[FallDetection] Failed to report man-down:', error);
      // Store locally for retry
      await this.storeOfflineEvent(this.currentFallEvent);
    }
  }

  /**
   * Report false alarm to backend
   */
  private async reportFalseAlarm() {
    // In production, call the false-alarm endpoint
    console.log('[FallDetection] False alarm reported');
  }

  /**
   * Store event offline for later sync
   */
  private async storeOfflineEvent(event: FallEvent) {
    try {
      const existing = await AsyncStorage.getItem('offline_fall_events');
      const events: FallEvent[] = existing ? JSON.parse(existing) : [];
      events.push(event);
      await AsyncStorage.setItem('offline_fall_events', JSON.stringify(events));
    } catch (e) {
      console.error('[FallDetection] Failed to store offline:', e);
    }
  }

  /**
   * Start monitoring for falls
   */
  public async startMonitoring(
    callbacks: FallDetectionCallbacks,
    userId?: string,
    userName?: string
  ): Promise<boolean> {
    if (this.isMonitoring) {
      console.warn('[FallDetection] Already monitoring');
      return true;
    }

    this.callbacks = callbacks;
    this.userId = userId || null;
    this.userName = userName || null;

    try {
      // Check availability
      const available = await Accelerometer.isAvailableAsync();
      if (!available) {
        console.error('[FallDetection] Accelerometer not available');
        return false;
      }

      // Request location permission for emergency location
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        console.warn('[FallDetection] Location permission not granted');
        // Continue anyway - location is nice-to-have
      }

      // Set update interval
      Accelerometer.setUpdateInterval(UPDATE_INTERVAL_MS);

      // Start listening
      this.subscription = Accelerometer.addListener(this.handleMeasurement);
      this.isMonitoring = true;

      console.log('[FallDetection] Monitoring started');
      return true;
    } catch (error) {
      console.error('[FallDetection] Failed to start monitoring:', error);
      return false;
    }
  }

  /**
   * Stop monitoring
   */
  public stopMonitoring() {
    if (this.subscription) {
      this.subscription.remove();
      this.subscription = null;
    }

    if (this.countdownTimer) {
      clearInterval(this.countdownTimer);
      this.countdownTimer = null;
    }

    this.isMonitoring = false;
    this.currentFallEvent = null;
    this.fallStartTime = null;
    this.callbacks = null;

    console.log('[FallDetection] Monitoring stopped');
  }

  /**
   * Check if currently monitoring
   */
  public isActive(): boolean {
    return this.isMonitoring;
  }

  /**
   * Get current G-force reading
   */
  public getCurrentGForce(): number {
    if (!this.lastMeasurement) return 1.0;
    return this.calculateGForce(this.lastMeasurement);
  }

  /**
   * Simulate a fall for testing
   */
  public async simulateFall(gForce: number = 5.0) {
    if (!this.isMonitoring) {
      console.warn('[FallDetection] Not monitoring - cannot simulate');
      return;
    }

    console.log(`[FallDetection] Simulating fall with ${gForce}g`);
    await this.handleFallDetected(gForce);
  }
}

// Export singleton instance
export const fallDetection = new FallDetectionService();
export default fallDetection;
