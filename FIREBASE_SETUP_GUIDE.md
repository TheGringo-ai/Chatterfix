# 🔥 Firebase Setup Guide for ChatterFix CMMS

## Quick Setup (5 minutes)

### Step 1: Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project"
3. Project name: `chatterfix-cmms` (or keep `fredfix` if you prefer)
4. Enable Google Analytics (optional)
5. Click "Create project"

### Step 2: Enable Authentication
1. In Firebase console, go to **Authentication** → **Get started**
2. Go to **Sign-in method** tab
3. Enable **Email/Password** authentication
4. Click **Save**

### Step 3: Enable Firestore Database
1. Go to **Firestore Database** → **Create database**
2. Choose **Start in test mode** (we'll secure it later)
3. Choose your preferred location (e.g., `us-central1`)
4. Click **Done**

### Step 4: Get Service Account Key
1. Go to **Project Settings** (gear icon) → **Service accounts**
2. Click **Generate new private key**
3. Download the JSON file
4. Rename it to `firebase-credentials.json`
5. Place it in your ChatterFix project root directory

### Step 5: Get Project Configuration
1. In Project Settings → **General** tab
2. Scroll down to "Your apps"
3. Click "Add app" → Web app (</>) 
4. App nickname: "ChatterFix Web"
5. Copy the config object (we'll use this)

### Step 6: Update Environment Variables
See the `.env` configuration below ⬇️

---

## Automated Setup Script

Run this script to quickly configure Firebase: