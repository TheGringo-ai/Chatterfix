# ChatterFix Relay

Offline-first voice command relay for ChatterFix CMMS.

## Stack

| Technology | Purpose |
|------------|---------|
| **Expo SDK 52** | React Native framework (Managed + Prebuild) |
| **Expo Router** | File-based navigation |
| **WatermelonDB** | High-performance offline database |
| **NativeWind** | Tailwind CSS for React Native |
| **Zustand** | Fast, lightweight state management |

## Getting Started

### Prerequisites

- Node.js 18+
- Expo CLI (`npm install -g expo-cli`)
- iOS Simulator or Android Emulator

### Installation

```bash
# Install dependencies
npm install

# Generate native projects (required for WatermelonDB)
npm run prebuild

# Start development
npm start
```

### Running on Device

```bash
# iOS
npm run ios

# Android
npm run android
```

## Project Structure

```
chatterfix-relay/
├── app/                    # Expo Router pages
│   ├── _layout.tsx         # Root layout with navigation
│   ├── index.tsx           # Home/Dashboard
│   ├── settings.tsx        # Settings modal
│   ├── assets/
│   │   ├── index.tsx       # Assets list
│   │   └── [id].tsx        # Asset detail
│   └── logs/
│       └── index.tsx       # Voice logs list
├── src/
│   ├── db/                 # WatermelonDB
│   │   ├── schema.ts       # Database schema
│   │   ├── index.ts        # Database initialization
│   │   └── models/         # Model classes
│   │       ├── Asset.ts
│   │       └── Log.ts
│   ├── stores/             # Zustand stores
│   │   └── appStore.ts
│   ├── components/         # Shared components
│   ├── hooks/              # Custom hooks
│   └── types/              # TypeScript types
├── assets/                 # Images, fonts
├── global.css              # Tailwind global styles
└── tailwind.config.js      # Tailwind configuration
```

## WatermelonDB Schema

### Assets Table
| Column | Type | Description |
|--------|------|-------------|
| id | string | Auto-generated primary key |
| name | string | Asset name |
| status | string | operational / warning / critical / offline |
| asset_tag | string? | Asset identifier |
| location | string? | Physical location |
| last_synced_at | number? | Timestamp of last sync |
| created_at | number | Creation timestamp |
| updated_at | number | Last update timestamp |

### Logs Table
| Column | Type | Description |
|--------|------|-------------|
| id | string | Auto-generated primary key |
| asset_id | string | Foreign key to assets |
| audio_file | string? | Local file path/URI |
| transcript | string? | Voice command text |
| command_type | string? | work_order / checkout / inspection |
| synced_at | number? | Null if not synced |
| created_at | number | Creation timestamp |

## Offline-First Design

- All data stored locally in WatermelonDB (SQLite)
- Ghost Mode: Actions queued when offline
- Automatic sync when connectivity returns
- Conflict resolution handled server-side

## Scripts

```bash
npm start          # Start Expo dev server
npm run ios        # Run on iOS simulator
npm run android    # Run on Android emulator
npm run prebuild   # Generate native projects
npm run lint       # Run ESLint
```

## Environment Variables

Create `.env` file:

```env
EXPO_PUBLIC_API_URL=https://api.chatterfix.com
```

---

Built for ChatterFix - Technician-First CMMS
