# ChatterFix Mobile App

A React Native mobile application for the ChatterFix CMMS system.

## Features

- 📱 Cross-platform (iOS & Android)
- 🔄 Offline-first architecture
- 📍 GPS-based work order routing
- 📸 Camera integration for asset photos
- 🔔 Push notifications for urgent work orders
- 🎤 Voice commands for hands-free operation

## Prerequisites

- Node.js 18+ 
- React Native CLI or Expo CLI
- For iOS: macOS with Xcode
- For Android: Android Studio with SDK

## Getting Started

### Using Expo (Recommended for development)

```bash
cd mobile
npm install
npx expo start
```

### Using React Native CLI

```bash
cd mobile
npm install
npx react-native run-ios     # For iOS
npx react-native run-android # For Android
```

## Project Structure

```
mobile/
├── App.tsx                 # Main app entry point
├── src/
│   ├── components/         # Reusable UI components
│   ├── screens/           # Screen components
│   ├── services/          # API and offline services
│   ├── hooks/             # Custom React hooks
│   ├── navigation/        # Navigation configuration
│   └── utils/             # Utility functions
├── package.json
└── app.json               # Expo configuration
```

## Configuration

Update the API base URL in `src/services/api.ts`:

```typescript
const API_BASE_URL = 'https://your-chatterfix-instance.com';
```

## Building for Production

### Expo

```bash
npx eas build --platform all
```

### React Native CLI

```bash
cd android && ./gradlew assembleRelease  # Android
# iOS builds via Xcode
```

## API Integration

The mobile app connects to the ChatterFix backend using the following endpoints:

- `/analytics/kpi/summary` - Dashboard KPIs
- `/work-orders` - Work order management
- `/assets` - Asset management  
- `/iot/sensors/` - IoT sensor data
- `/ai/chat` - AI assistant

## Offline Support

The app uses:
- AsyncStorage for local data persistence
- SQLite for offline work order queue
- Background sync when connectivity restored

## Push Notifications

Configure push notifications with:
- Firebase Cloud Messaging (Android)
- Apple Push Notification Service (iOS)

See `src/services/pushNotifications.ts` for implementation details.
