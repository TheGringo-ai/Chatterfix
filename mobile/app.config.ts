import 'dotenv/config';

export default {
  expo: {
    name: "ChatterFix",
    slug: "chatterfix-mobile",
    version: "1.0.0",
    orientation: "portrait",
    icon: "./assets/icon.png",
    userInterfaceStyle: "automatic",
    splash: {
      image: "./assets/splash.png",
      resizeMode: "contain",
      backgroundColor: "#1e3c72"
    },
    assetBundlePatterns: ["**/*"],
    ios: {
      supportsTablet: true,
      bundleIdentifier: "com.chatterfix.cmms",
      infoPlist: {
        NSCameraUsageDescription: "ChatterFix needs camera access to capture asset photos and scan QR codes",
        NSLocationWhenInUseUsageDescription: "ChatterFix needs location access to show nearby work orders",
        NSMicrophoneUsageDescription: "ChatterFix needs microphone access for voice commands",
        NSSpeechRecognitionUsageDescription: "ChatterFix needs speech recognition for voice commands"
      }
    },
    android: {
      adaptiveIcon: {
        foregroundImage: "./assets/adaptive-icon.png",
        backgroundColor: "#1e3c72"
      },
      package: "com.chatterfix.cmms",
      permissions: [
        "CAMERA",
        "ACCESS_FINE_LOCATION",
        "ACCESS_COARSE_LOCATION",
        "RECORD_AUDIO",
        "RECEIVE_BOOT_COMPLETED",
        "VIBRATE"
      ]
    },
    web: {
      favicon: "./assets/favicon.png"
    },
    plugins: [
      "expo-camera",
      "expo-location",
      [
        "expo-notifications",
        {
          icon: "./assets/notification-icon.png",
          color: "#1e3c72"
        }
      ]
    ],
    extra: {
      // API Configuration
      apiBaseUrl: process.env.API_BASE_URL || "https://chatterfix.com",

      // Firebase Configuration (loaded from environment)
      firebase: {
        apiKey: process.env.FIREBASE_API_KEY,
        authDomain: process.env.FIREBASE_AUTH_DOMAIN || "fredfix.firebaseapp.com",
        projectId: process.env.FIREBASE_PROJECT_ID || "fredfix",
        storageBucket: process.env.FIREBASE_STORAGE_BUCKET || "fredfix.firebasestorage.app",
        databaseURL: process.env.FIREBASE_DATABASE_URL || "https://fredfix-default-rtdb.firebaseio.com",
        messagingSenderId: process.env.FIREBASE_MESSAGING_SENDER_ID,
        appId: process.env.FIREBASE_APP_ID,
        measurementId: process.env.FIREBASE_MEASUREMENT_ID
      },

      // Feature Flags
      enableVoiceCommands: true,
      enableOCR: true,
      enablePartRecognition: true
    }
  }
};
