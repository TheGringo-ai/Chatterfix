// Service Worker for ChatterFix CMMS PWA
// Provides offline functionality, caching, and background sync

const CACHE_NAME = 'chatterfix-cmms-v1.0.0';
const OFFLINE_URL = '/offline.html';

// Resources to cache for offline functionality
const CACHE_URLS = [
  '/',
  '/login',
  '/work-orders',
  '/assets', 
  '/parts',
  '/static/manifest.json',
  '/static/css/app.css',
  '/static/js/app.js',
  '/ai-inject.js',
  OFFLINE_URL
];

// Critical API endpoints to cache
const API_CACHE_URLS = [
  '/api/work-orders',
  '/api/assets',
  '/api/parts',
  '/health'
];

// Install event - cache essential resources
self.addEventListener('install', event => {
  console.log('🔧 ChatterFix CMMS Service Worker installing...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('📦 Caching core application resources');
        return cache.addAll(CACHE_URLS);
      })
      .then(() => {
        console.log('✅ Service Worker installation complete');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('❌ Service Worker installation failed:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('🚀 ChatterFix CMMS Service Worker activating...');
  
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames
            .filter(cacheName => cacheName !== CACHE_NAME)
            .map(cacheName => {
              console.log('🗑️ Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            })
        );
      })
      .then(() => {
        console.log('✅ Service Worker activation complete');
        return self.clients.claim();
      })
  );
});

// Fetch event - implement cache-first strategy with network fallback
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests and chrome-extension URLs
  if (request.method !== 'GET' || url.protocol === 'chrome-extension:') {
    return;
  }
  
  // Handle API requests with network-first strategy
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/global-ai/')) {
    event.respondWith(handleApiRequest(request));
    return;
  }
  
  // Handle navigation requests
  if (request.mode === 'navigate') {
    event.respondWith(handleNavigationRequest(request));
    return;
  }
  
  // Handle static resources with cache-first strategy
  event.respondWith(handleStaticRequest(request));
});

// Network-first strategy for API requests
async function handleApiRequest(request) {
  try {
    // Try network first
    const networkResponse = await fetch(request);
    
    // Cache successful responses
    if (networkResponse.status === 200) {
      const cache = await caches.open(CACHE_NAME);
      await cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    // Network failed, try cache
    console.log('📱 Network unavailable, serving from cache:', request.url);
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline response for API calls
    return new Response(
      JSON.stringify({
        error: 'Network unavailable',
        message: 'This request requires an internet connection',
        offline: true
      }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

// Handle navigation requests with cache-first fallback
async function handleNavigationRequest(request) {
  try {
    // Try network first for navigation
    const networkResponse = await fetch(request);
    
    // Cache the response
    const cache = await caches.open(CACHE_NAME);
    await cache.put(request, networkResponse.clone());
    
    return networkResponse;
  } catch (error) {
    // Network failed, try cache
    console.log('📱 Serving cached page:', request.url);
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline page
    return caches.match(OFFLINE_URL);
  }
}

// Cache-first strategy for static resources
async function handleStaticRequest(request) {
  // Check cache first
  const cachedResponse = await caches.match(request);
  
  if (cachedResponse) {
    // Return cached version and update in background
    updateCacheInBackground(request);
    return cachedResponse;
  }
  
  // Not in cache, fetch from network
  try {
    const networkResponse = await fetch(request);
    
    // Cache the response
    const cache = await caches.open(CACHE_NAME);
    await cache.put(request, networkResponse.clone());
    
    return networkResponse;
  } catch (error) {
    console.log('❌ Failed to fetch resource:', request.url);
    
    // For images, return a placeholder
    if (request.destination === 'image') {
      return generatePlaceholderImage();
    }
    
    throw error;
  }
}

// Update cache in background
async function updateCacheInBackground(request) {
  try {
    const networkResponse = await fetch(request);
    const cache = await caches.open(CACHE_NAME);
    await cache.put(request, networkResponse);
  } catch (error) {
    // Silent failure for background updates
    console.log('Background cache update failed:', request.url);
  }
}

// Generate placeholder image for offline mode
function generatePlaceholderImage() {
  const svg = `
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
      <rect width="200" height="200" fill="#667eea"/>
      <text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="white" font-family="Arial, sans-serif" font-size="14">
        ChatterFix
      </text>
      <text x="50%" y="65%" text-anchor="middle" dy=".3em" fill="white" font-family="Arial, sans-serif" font-size="12">
        Offline
      </text>
    </svg>
  `;
  
  return new Response(svg, {
    headers: { 'Content-Type': 'image/svg+xml' }
  });
}

// Background sync for offline actions
self.addEventListener('sync', event => {
  console.log('🔄 Background sync triggered:', event.tag);
  
  if (event.tag === 'background-sync') {
    event.waitUntil(syncOfflineActions());
  }
});

// Sync offline actions when connection is restored
async function syncOfflineActions() {
  try {
    // Retrieve offline actions from IndexedDB
    const offlineActions = await getOfflineActions();
    
    for (const action of offlineActions) {
      try {
        await fetch(action.url, action.options);
        await removeOfflineAction(action.id);
        console.log('✅ Synced offline action:', action.type);
      } catch (error) {
        console.log('❌ Failed to sync action:', action.type, error);
      }
    }
  } catch (error) {
    console.error('Background sync failed:', error);
  }
}

// Push notification handler
self.addEventListener('push', event => {
  if (!event.data) return;
  
  const data = event.data.json();
  const options = {
    body: data.body || 'New update from ChatterFix CMMS',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/badge-72x72.png',
    vibrate: [200, 100, 200],
    data: data.data || {},
    actions: [
      {
        action: 'view',
        title: 'View',
        icon: '/static/icons/action-view.png'
      },
      {
        action: 'dismiss',
        title: 'Dismiss',
        icon: '/static/icons/action-dismiss.png'
      }
    ],
    requireInteraction: data.priority === 'high',
    silent: data.priority === 'low'
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title || 'ChatterFix CMMS', options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  const action = event.action;
  const data = event.notification.data;
  
  if (action === 'view' || !action) {
    // Open the app or navigate to specific page
    const urlToOpen = data.url || '/';
    
    event.waitUntil(
      clients.matchAll({ type: 'window' })
        .then(clientList => {
          // Check if app is already open
          for (const client of clientList) {
            if (client.url.includes(self.location.origin)) {
              return client.focus();
            }
          }
          
          // Open new window
          return clients.openWindow(urlToOpen);
        })
    );
  }
});

// Message handler for communication with main app
self.addEventListener('message', event => {
  const { data } = event;
  
  switch (data.type) {
    case 'SKIP_WAITING':
      self.skipWaiting();
      break;
      
    case 'GET_VERSION':
      event.ports[0].postMessage({ version: CACHE_NAME });
      break;
      
    case 'CACHE_URLS':
      event.waitUntil(
        caches.open(CACHE_NAME)
          .then(cache => cache.addAll(data.urls))
          .then(() => event.ports[0].postMessage({ success: true }))
          .catch(error => event.ports[0].postMessage({ error: error.message }))
      );
      break;
  }
});

// IndexedDB helpers for offline functionality
function openOfflineDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('ChatterFixOffline', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      
      // Create object store for offline actions
      if (!db.objectStoreNames.contains('offlineActions')) {
        const store = db.createObjectStore('offlineActions', { keyPath: 'id', autoIncrement: true });
        store.createIndex('timestamp', 'timestamp');
        store.createIndex('type', 'type');
      }
    };
  });
}

async function storeOfflineAction(action) {
  const db = await openOfflineDB();
  const tx = db.transaction(['offlineActions'], 'readwrite');
  const store = tx.objectStore('offlineActions');
  
  await store.add({
    ...action,
    timestamp: Date.now(),
    id: Date.now() + Math.random()
  });
}

async function getOfflineActions() {
  const db = await openOfflineDB();
  const tx = db.transaction(['offlineActions'], 'readonly');
  const store = tx.objectStore('offlineActions');
  
  return new Promise((resolve, reject) => {
    const request = store.getAll();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function removeOfflineAction(id) {
  const db = await openOfflineDB();
  const tx = db.transaction(['offlineActions'], 'readwrite');
  const store = tx.objectStore('offlineActions');
  
  await store.delete(id);
}

console.log('🔧 ChatterFix CMMS Service Worker loaded successfully');