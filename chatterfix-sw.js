/**
 * ChatterFix CMMS PWA Service Worker
 * Enables offline functionality and app-like experience
 */

const CACHE_NAME = 'chatterfix-v6b-1';
const STATIC_CACHE = 'chatterfix-static-v6b-1';
const DYNAMIC_CACHE = 'chatterfix-dynamic-v6b-1';

// Static resources to cache
const STATIC_RESOURCES = [
  '/',
  '/manifest.json',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
  'https://cdn.jsdelivr.net/npm/chart.js',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js'
];

// API endpoints to cache
const CACHE_API_PATTERNS = [
  /\/api\/health/,
  /\/api\/system\/performance/,
  /\/api\/dashboard/,
  /\/api\/work-orders/,
  /\/api\/assets/,
  /\/api\/parts/,
  /\/api\/diy/
];

// Install event - cache static resources
self.addEventListener('install', (event) => {
  console.log('ChatterFix SW: Installing service worker...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('ChatterFix SW: Caching static resources');
        return cache.addAll(STATIC_RESOURCES);
      })
      .then(() => {
        console.log('ChatterFix SW: Static resources cached');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('ChatterFix SW: Failed to cache static resources:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('ChatterFix SW: Activating service worker...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
              console.log('ChatterFix SW: Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('ChatterFix SW: Service worker activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - serve from cache with network fallback
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip cross-origin requests
  if (url.origin !== location.origin) {
    return;
  }
  
  // Handle different request types
  if (request.method === 'GET') {
    event.respondWith(handleGetRequest(request));
  } else {
    // For POST/PUT/DELETE, always go to network
    event.respondWith(
      fetch(request)
        .catch(() => {
          return new Response(
            JSON.stringify({ 
              error: 'Offline mode', 
              message: 'This action requires internet connection' 
            }),
            { 
              status: 503,
              headers: { 'Content-Type': 'application/json' }
            }
          );
        })
    );
  }
});

async function handleGetRequest(request) {
  const url = new URL(request.url);
  
  try {
    // API requests - cache with network first strategy
    if (url.pathname.startsWith('/api/')) {
      return await handleApiRequest(request);
    }
    
    // Static resources - cache first strategy
    if (isStaticResource(url)) {
      return await handleStaticRequest(request);
    }
    
    // HTML pages - network first with cache fallback
    if (request.headers.get('Accept')?.includes('text/html')) {
      return await handlePageRequest(request);
    }
    
    // Default: network first
    return await fetch(request);
    
  } catch (error) {
    console.error('ChatterFix SW: Fetch error:', error);
    return await handleOfflineResponse(request);
  }
}

async function handleApiRequest(request) {
  const url = new URL(request.url);
  
  // Check if this API should be cached
  const shouldCache = CACHE_API_PATTERNS.some(pattern => pattern.test(url.pathname));
  
  if (!shouldCache) {
    return fetch(request);
  }
  
  try {
    // Try network first
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // Cache successful responses
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    // Network failed, try cache
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
      console.log('ChatterFix SW: Serving API from cache:', request.url);
      return cachedResponse;
    }
    
    // No cache available, return offline response
    return new Response(
      JSON.stringify({
        error: 'Offline mode',
        message: 'This data is not available offline',
        cached: false
      }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

async function handleStaticRequest(request) {
  // Cache first for static resources
  const cachedResponse = await caches.match(request);
  
  if (cachedResponse) {
    return cachedResponse;
  }
  
  // Not in cache, fetch from network
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.error('ChatterFix SW: Failed to fetch static resource:', request.url);
    throw error;
  }
}

async function handlePageRequest(request) {
  try {
    // Try network first for pages
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    // Network failed, try cache
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
      console.log('ChatterFix SW: Serving page from cache:', request.url);
      return cachedResponse;
    }
    
    // No cache available, return offline page
    return new Response(
      generateOfflinePage(),
      {
        status: 200,
        headers: { 'Content-Type': 'text/html' }
      }
    );
  }
}

async function handleOfflineResponse(request) {
  const url = new URL(request.url);
  
  // Try to serve from cache
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }
  
  // Return appropriate offline response
  if (url.pathname.startsWith('/api/')) {
    return new Response(
      JSON.stringify({
        error: 'Offline mode',
        message: 'No cached data available',
        offline: true
      }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
  
  if (request.headers.get('Accept')?.includes('text/html')) {
    return new Response(
      generateOfflinePage(),
      {
        status: 200,
        headers: { 'Content-Type': 'text/html' }
      }
    );
  }
  
  return new Response('Offline', { status: 503 });
}

function isStaticResource(url) {
  const staticExtensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2'];
  return staticExtensions.some(ext => url.pathname.endsWith(ext)) ||
         url.hostname.includes('cdn.jsdelivr.net') ||
         url.hostname.includes('cdnjs.cloudflare.com');
}

function generateOfflinePage() {
  return `
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>ChatterFix CMMS - Offline</title>
      <style>
        body {
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          margin: 0;
          padding: 0;
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          text-align: center;
        }
        .offline-container {
          background: rgba(255,255,255,0.1);
          padding: 2rem;
          border-radius: 15px;
          backdrop-filter: blur(10px);
          max-width: 400px;
          margin: 0 1rem;
        }
        .offline-icon {
          font-size: 4rem;
          margin-bottom: 1rem;
        }
        .offline-title {
          font-size: 1.8rem;
          font-weight: bold;
          margin-bottom: 1rem;
        }
        .offline-message {
          font-size: 1rem;
          margin-bottom: 2rem;
          opacity: 0.9;
        }
        .retry-button {
          background: white;
          color: #667eea;
          border: none;
          padding: 0.75rem 1.5rem;
          border-radius: 8px;
          font-weight: bold;
          cursor: pointer;
          transition: transform 0.2s ease;
        }
        .retry-button:hover {
          transform: translateY(-2px);
        }
      </style>
    </head>
    <body>
      <div class="offline-container">
        <div class="offline-icon">📱</div>
        <div class="offline-title">ChatterFix CMMS</div>
        <div class="offline-message">
          You're currently offline. Some features may not be available until you reconnect to the internet.
        </div>
        <button class="retry-button" onclick="window.location.reload()">
          Try Again
        </button>
      </div>
    </body>
    </html>
  `;
}

// Background sync for form submissions
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync-forms') {
    event.waitUntil(doBackgroundSync());
  }
});

async function doBackgroundSync() {
  console.log('ChatterFix SW: Performing background sync');
  // Handle any queued form submissions or data updates
}

// Push notification handling
self.addEventListener('push', (event) => {
  if (!event.data) return;
  
  const data = event.data.json();
  const options = {
    body: data.body || 'New notification from ChatterFix CMMS',
    icon: '/manifest.json',
    badge: '/manifest.json',
    tag: data.tag || 'chatterfix-notification',
    data: data.data || {},
    actions: [
      {
        action: 'view',
        title: 'View'
      },
      {
        action: 'dismiss',
        title: 'Dismiss'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title || 'ChatterFix CMMS', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

console.log('ChatterFix SW: Service worker loaded successfully');