# ChatterFix Mobile App Setup

## Firebase Configuration

1. Create a Firebase project at https://console.firebase.google.com/
2. Enable Authentication with Email/Password provider
3. Enable Firestore Database
4. Get your Firebase config from Project Settings

## Environment Setup

Create a `.env` file in the mobile directory or update the firebase.ts file with your Firebase config:

```typescript
const firebaseConfig = {
  apiKey: "your-api-key",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "123456789",
  appId: "your-app-id",
};
```

## API Configuration

Update the API base URL in `src/services/api.ts` to point to your deployed ChatterFix backend.

## Installation

```bash
npm install
npm start
```

## Features

- Firebase Authentication (Login/Signup)
- Firestore integration for data
- Offline-capable with local SQLite storage
- Real-time KPI dashboard
- Work order management
- Asset tracking
- Push notifications (configured but not implemented)
