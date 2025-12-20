/**
 * FeedbackService - The Confidence Loop
 *
 * Provides audio and haptic feedback for hands-free operation.
 * Designed to work seamlessly with:
 * - Phone speakers (current)
 * - Bluetooth earbuds
 * - Brilliant Labs smart glasses (future)
 *
 * The "Jarvis" experience for technicians.
 */

import * as Speech from 'expo-speech';

// Haptics is optional - graceful fallback if not installed
let Haptics: any = null;
try {
  Haptics = require('expo-haptics');
} catch {
  console.log('[FeedbackService] expo-haptics not available, haptic feedback disabled');
}

// Voice configuration optimized for industrial environments
const VOICE_OPTIONS: Speech.SpeechOptions = {
  language: 'en-US',
  pitch: 1.0,
  rate: 0.85, // Slightly slower for noisy environments
};

// Confirmation phrases for natural conversation
const CONFIRMATION_PHRASES = [
  "Got it.",
  "Done.",
  "All set.",
  "Completed.",
];

const getRandomConfirmation = () =>
  CONFIRMATION_PHRASES[Math.floor(Math.random() * CONFIRMATION_PHRASES.length)];

// Safe haptic feedback (no-op if not available)
const hapticNotification = async (type: 'Success' | 'Warning' | 'Error') => {
  if (Haptics?.notificationAsync) {
    await Haptics.notificationAsync(Haptics.NotificationFeedbackType[type]);
  }
};

const hapticImpact = async (style: 'Light' | 'Medium' | 'Heavy') => {
  if (Haptics?.impactAsync) {
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle[style]);
  }
};

export const FeedbackService = {
  /**
   * Ask for confirmation before executing a command
   * "I'm creating a work order to replace the seal on Pump 3. Confirm?"
   */
  askConfirmation: async (action: string, assetName?: string): Promise<void> => {
    // Haptic cue to get attention
    await hapticNotification('Warning');

    let text: string;
    if (assetName) {
      text = `I'm creating a work order to ${action} on ${assetName}. Say yes to confirm.`;
    } else {
      text = `I'm going to ${action}. Say yes to confirm.`;
    }

    return new Promise((resolve) => {
      Speech.speak(text, {
        ...VOICE_OPTIONS,
        onDone: () => resolve(),
      });
    });
  },

  /**
   * Announce successful command execution
   * "Work order 2024-001 created for Hydraulic Pump 3."
   */
  announceSuccess: async (message: string, ticketId?: string): Promise<void> => {
    await hapticNotification('Success');

    const text = ticketId
      ? `${getRandomConfirmation()} Work order ${ticketId} created.`
      : message;

    return new Promise((resolve) => {
      Speech.speak(text, {
        ...VOICE_OPTIONS,
        onDone: () => resolve(),
      });
    });
  },

  /**
   * Announce context resolution
   * "I see you're at Hydraulic Pump 3."
   */
  announceContext: async (assetName: string, source: string): Promise<void> => {
    await hapticImpact('Light');

    const sourceText = source === 'qr_scan' ? 'scanned' :
                       source === 'nfc_tap' ? 'detected' : 'selected';

    Speech.speak(`${assetName} ${sourceText}.`, {
      ...VOICE_OPTIONS,
      rate: 1.0, // Slightly faster for quick acknowledgment
    });
  },

  /**
   * Announce error or ask for clarification
   * "I didn't catch that. Could you try again?"
   */
  announceError: async (message?: string): Promise<void> => {
    await hapticNotification('Error');

    const text = message || "Sorry, I didn't catch that. Could you try again?";

    return new Promise((resolve) => {
      Speech.speak(text, {
        ...VOICE_OPTIONS,
        onDone: () => resolve(),
      });
    });
  },

  /**
   * Announce listening state
   * "Listening..."
   */
  announceListening: async (): Promise<void> => {
    await hapticImpact('Medium');
    Speech.speak("Listening.", { ...VOICE_OPTIONS, rate: 1.1 });
  },

  /**
   * Announce processing state
   * "Processing..."
   */
  announceProcessing: async (): Promise<void> => {
    Speech.speak("Processing.", { ...VOICE_OPTIONS, rate: 1.1 });
  },

  /**
   * Read back what was heard for verification
   * "I heard: Replace the seal on pump 3"
   */
  readBack: async (transcription: string): Promise<void> => {
    await hapticImpact('Light');
    Speech.speak(`I heard: ${transcription}`, VOICE_OPTIONS);
  },

  /**
   * Announce navigation or action
   * "Opening work orders..."
   */
  announceAction: async (action: string): Promise<void> => {
    await hapticImpact('Light');
    Speech.speak(action, VOICE_OPTIONS);
  },

  /**
   * Stop all speech immediately (user interruption)
   */
  stop: (): void => {
    Speech.stop();
  },

  /**
   * Check if currently speaking
   */
  isSpeaking: async (): Promise<boolean> => {
    return Speech.isSpeakingAsync();
  },

  /**
   * Glasses Mode: Announce status without visual feedback
   * Used when screen is off / glasses-only mode
   */
  glassesMode: {
    ready: async (): Promise<void> => {
      await hapticNotification('Success');
      Speech.speak("ChatterFix ready. Say a command.", VOICE_OPTIONS);
    },

    confirmYes: async (): Promise<void> => {
      await hapticImpact('Heavy');
      Speech.speak("Confirmed.", { ...VOICE_OPTIONS, rate: 1.0 });
    },

    confirmNo: async (): Promise<void> => {
      await hapticImpact('Light');
      Speech.speak("Cancelled.", { ...VOICE_OPTIONS, rate: 1.0 });
    },
  },
};

export default FeedbackService;
