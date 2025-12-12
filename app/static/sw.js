// ChatterFix CMMS - Ultimate Multi-Device Service Worker
// Version 3.0 - Enhanced for Jake, Anna, Sam, Maria personas with adaptive caching

const CACHE_VERSION = 'v3-ultimate';
const CACHE_NAME = `chatterfix-${CACHE_VERSION}`;
const DATA_CACHE_NAME = `chatterfix-data-${CACHE_VERSION}`;
const DB_NAME = 'ChatterFixMultiDeviceDB';
const DB_VERSION = 2;

// Static assets to cache on install
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/static/css/style.css',
    '/static/js/main.js',
    '/static/js/demo-system.js',
    '/static/manifest.json',
    '/demo',
    '/demo/work-orders',
    '/demo/assets',
    '/demo/planner',
    '/analytics/dashboard',
    '/fix-it-fred/interface',
    '/demo/team',
    '/inventory',
    '/demo/purchasing',
    // User personas routes
    '/?persona=jake',
    '/?persona=anna',
    '/?persona=sam',
    '/?persona=maria'
];

// API endpoints to cache for offline use
const API_CACHE_ROUTES = [
    '/quick-stats',
    '/analytics/kpi/summary',
    '/analytics/charts/'
];

// ========== IndexedDB Helper Functions ==========

function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
        
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            
            // Work Orders store for offline creation/updates
            if (!db.objectStoreNames.contains('workOrders')) {
                const woStore = db.createObjectStore('workOrders', { keyPath: 'id', autoIncrement: true });
                woStore.createIndex('status', 'status', { unique: false });
                woStore.createIndex('synced', 'synced', { unique: false });
            }
            
            // Offline actions queue
            if (!db.objectStoreNames.contains('offlineQueue')) {
                const queueStore = db.createObjectStore('offlineQueue', { keyPath: 'id', autoIncrement: true });
                queueStore.createIndex('timestamp', 'timestamp', { unique: false });
                queueStore.createIndex('type', 'type', { unique: false });
            }
            
            // Cached data store
            if (!db.objectStoreNames.contains('cachedData')) {
                db.createObjectStore('cachedData', { keyPath: 'key' });
            }
            
            // Sensor readings for offline IoT data
            if (!db.objectStoreNames.contains('sensorReadings')) {
                const sensorStore = db.createObjectStore('sensorReadings', { keyPath: 'id', autoIncrement: true });
                sensorStore.createIndex('synced', 'synced', { unique: false });
                sensorStore.createIndex('timestamp', 'timestamp', { unique: false });
            }
        };
    });
}

async function saveToStore(storeName, data) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);
        const request = store.put(data);
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
    });
}

async function getFromStore(storeName, key) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction([storeName], 'readonly');
        const store = transaction.objectStore(storeName);
        const request = store.get(key);
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
    });
}

async function getAllFromStore(storeName, indexName = null, indexValue = null) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction([storeName], 'readonly');
        const store = transaction.objectStore(storeName);
        let request;
        
        if (indexName && indexValue !== null) {
            const index = store.index(indexName);
            request = index.getAll(indexValue);
        } else {
            request = store.getAll();
        }
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
    });
}

async function deleteFromStore(storeName, key) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);
        const request = store.delete(key);
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve();
    });
}

// ========== Install Event ==========

self.addEventListener('install', event => {
    console.log('[SW] Installing ChatterFix Service Worker v2...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[SW] Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                console.log('[SW] Installation complete');
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('[SW] Installation failed:', error);
            })
    );
});

// ========== Activate Event ==========

self.addEventListener('activate', event => {
    console.log('[SW] Activating ChatterFix Service Worker v2...');
    
    event.waitUntil(
        Promise.all([
            // Clean up old caches
            caches.keys().then(cacheNames => {
                return Promise.all(
                    cacheNames
                        .filter(name => name.startsWith('chatterfix-') && name !== CACHE_NAME && name !== DATA_CACHE_NAME)
                        .map(name => {
                            console.log('[SW] Deleting old cache:', name);
                            return caches.delete(name);
                        })
                );
            }),
            // Take control of all clients
            self.clients.claim()
        ]).then(() => {
            console.log('[SW] Activation complete');
        })
    );
});

// ========== Fetch Event - Network First with Cache Fallback ==========

self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);
    
    // Skip non-GET requests for caching
    if (event.request.method !== 'GET') {
        // Handle offline POST requests
        if (!navigator.onLine) {
            event.respondWith(handleOfflinePost(event.request));
        }
        return;
    }
    
    // API requests - Network first, cache fallback
    if (isApiRequest(url)) {
        event.respondWith(handleApiRequest(event.request));
        return;
    }
    
    // Static assets - Cache first, network fallback
    event.respondWith(handleStaticRequest(event.request));
});

function isApiRequest(url) {
    return API_CACHE_ROUTES.some(route => url.pathname.includes(route)) ||
           url.pathname.startsWith('/api/') ||
           url.pathname.startsWith('/analytics/') ||
           url.pathname.startsWith('/iot/');
}

async function handleApiRequest(request) {
    const url = new URL(request.url);
    const cacheKey = url.pathname + url.search;
    
    try {
        // Try network first
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            // Cache the response
            const cache = await caches.open(DATA_CACHE_NAME);
            cache.put(request, networkResponse.clone());
            
            // Also save to IndexedDB for structured access
            try {
                const data = await networkResponse.clone().json();
                await saveToStore('cachedData', { key: cacheKey, data, timestamp: Date.now() });
            } catch (e) {
                // Not JSON, skip IndexedDB storage
            }
        }
        
        return networkResponse;
    } catch (error) {
        console.log('[SW] Network failed, trying cache:', cacheKey);
        
        // Try cache
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Try IndexedDB
        try {
            const cachedData = await getFromStore('cachedData', cacheKey);
            if (cachedData) {
                return new Response(JSON.stringify(cachedData.data), {
                    headers: { 'Content-Type': 'application/json' }
                });
            }
        } catch (e) {
            console.log('[SW] IndexedDB lookup failed:', e);
        }
        
        // Return offline response
        return new Response(JSON.stringify({
            error: 'offline',
            message: 'You are offline. Data will sync when connection is restored.'
        }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

async function handleStaticRequest(request) {
    // Try cache first
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
        // Fetch fresh version in background
        fetchAndCache(request);
        return cachedResponse;
    }
    
    // Try network
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        // Return offline page if available
        const offlinePage = await caches.match('/');
        if (offlinePage) {
            return offlinePage;
        }
        
        return new Response('Offline - Please check your connection', {
            status: 503,
            headers: { 'Content-Type': 'text/plain' }
        });
    }
}

async function fetchAndCache(request) {
    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response);
        }
    } catch (e) {
        // Silently fail background fetch
    }
}

async function handleOfflinePost(request) {
    const url = new URL(request.url);
    
    // Queue the request for later sync
    try {
        const body = await request.clone().json();
        await saveToStore('offlineQueue', {
            url: url.pathname,
            method: request.method,
            body: body,
            timestamp: Date.now(),
            synced: false
        });
        
        // Register for background sync
        if ('sync' in self.registration) {
            await self.registration.sync.register('sync-offline-data');
        }
        
        return new Response(JSON.stringify({
            success: true,
            offline: true,
            message: 'Request queued for sync when online'
        }), {
            headers: { 'Content-Type': 'application/json' }
        });
    } catch (e) {
        return new Response(JSON.stringify({
            error: 'offline',
            message: 'Unable to process request offline'
        }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// ========== Background Sync ==========

self.addEventListener('sync', event => {
    console.log('[SW] Background sync triggered:', event.tag);
    
    if (event.tag === 'sync-offline-data' || event.tag === 'sync-data') {
        event.waitUntil(syncOfflineData());
    }
    
    if (event.tag === 'sync-work-orders') {
        event.waitUntil(syncWorkOrders());
    }
    
    if (event.tag === 'sync-sensor-data') {
        event.waitUntil(syncSensorData());
    }
});

async function syncOfflineData() {
    console.log('[SW] Syncing offline data...');
    
    try {
        const queuedItems = await getAllFromStore('offlineQueue', 'synced', false);
        console.log(`[SW] Found ${queuedItems.length} items to sync`);
        
        for (const item of queuedItems) {
            try {
                const response = await fetch(item.url, {
                    method: item.method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(item.body)
                });
                
                if (response.ok) {
                    await deleteFromStore('offlineQueue', item.id);
                    console.log('[SW] Synced item:', item.id);
                }
            } catch (e) {
                console.log('[SW] Failed to sync item:', item.id, e);
            }
        }
        
        // Notify clients of sync completion
        const clients = await self.clients.matchAll();
        clients.forEach(client => {
            client.postMessage({
                type: 'SYNC_COMPLETE',
                count: queuedItems.length
            });
        });
        
    } catch (e) {
        console.error('[SW] Sync failed:', e);
    }
}

async function syncWorkOrders() {
    console.log('[SW] Syncing work orders...');
    
    try {
        const unsyncedWOs = await getAllFromStore('workOrders', 'synced', false);
        
        for (const wo of unsyncedWOs) {
            try {
                const response = await fetch('/work-orders', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(wo)
                });
                
                if (response.ok) {
                    wo.synced = true;
                    await saveToStore('workOrders', wo);
                }
            } catch (e) {
                console.log('[SW] Failed to sync work order:', wo.id);
            }
        }
    } catch (e) {
        console.error('[SW] Work order sync failed:', e);
    }
}

async function syncSensorData() {
    console.log('[SW] Syncing sensor data...');
    
    const results = {
        total: 0,
        synced: 0,
        failed: 0,
        errors: []
    };
    
    try {
        const unsyncedReadings = await getAllFromStore('sensorReadings', 'synced', false);
        results.total = unsyncedReadings.length;
        
        if (unsyncedReadings.length > 0) {
            try {
                const response = await fetch('/iot/sensors/data/batch', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ readings: unsyncedReadings })
                });
                
                if (response.ok) {
                    const responseData = await response.json();
                    
                    // Mark successfully synced readings
                    for (const reading of unsyncedReadings) {
                        try {
                            reading.synced = true;
                            await saveToStore('sensorReadings', reading);
                            results.synced++;
                        } catch (e) {
                            results.failed++;
                            results.errors.push(`Failed to update reading ${reading.id}: ${e.message}`);
                        }
                    }
                    
                    console.log(`[SW] Sensor sync complete: ${results.synced}/${results.total} synced`);
                } else {
                    // Server error - try individual syncs
                    console.log('[SW] Batch sync failed, trying individual readings...');
                    
                    for (const reading of unsyncedReadings) {
                        try {
                            const individualResponse = await fetch('/iot/sensors/data', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify(reading)
                            });
                            
                            if (individualResponse.ok) {
                                reading.synced = true;
                                await saveToStore('sensorReadings', reading);
                                results.synced++;
                            } else {
                                results.failed++;
                                results.errors.push(`Reading ${reading.id}: HTTP ${individualResponse.status}`);
                            }
                        } catch (e) {
                            results.failed++;
                            results.errors.push(`Reading ${reading.id}: ${e.message}`);
                        }
                    }
                }
            } catch (networkError) {
                results.failed = results.total;
                results.errors.push(`Network error: ${networkError.message}`);
                console.error('[SW] Network error during sensor sync:', networkError);
            }
        }
        
        // Notify clients of sync results
        const clients = await self.clients.matchAll();
        clients.forEach(client => {
            client.postMessage({
                type: 'SENSOR_SYNC_COMPLETE',
                results: results
            });
        });
        
    } catch (e) {
        console.error('[SW] Sensor data sync failed:', e);
        results.errors.push(`Sync error: ${e.message}`);
    }
    
    return results;
}

// ========== Push Notifications ==========

self.addEventListener('push', event => {
    console.log('[SW] Push notification received');
    
    let data = {
        title: 'ChatterFix',
        body: 'New notification',
        icon: '/static/images/icon-192.png',
        badge: '/static/images/icon-192.png',
        tag: 'chatterfix-notification',
        data: {}
    };
    
    if (event.data) {
        try {
            data = { ...data, ...event.data.json() };
        } catch (e) {
            data.body = event.data.text();
        }
    }
    
    const options = {
        body: data.body,
        icon: data.icon || '/static/images/icon-192.png',
        badge: data.badge || '/static/images/icon-192.png',
        vibrate: [200, 100, 200],
        tag: data.tag,
        data: data.data,
        requireInteraction: data.priority === 'high' || data.priority === 'urgent',
        actions: [
            { action: 'view', title: 'View' },
            { action: 'dismiss', title: 'Dismiss' }
        ]
    };
    
    // Add urgency-specific styling
    if (data.priority === 'urgent') {
        options.vibrate = [300, 100, 300, 100, 300];
        options.requireInteraction = true;
    }
    
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

self.addEventListener('notificationclick', event => {
    console.log('[SW] Notification clicked:', event.action);
    
    event.notification.close();
    
    if (event.action === 'dismiss') {
        return;
    }
    
    const urlToOpen = event.notification.data?.url || '/';
    
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then(windowClients => {
                // Check if there's already a window open
                for (const client of windowClients) {
                    if (client.url === urlToOpen && 'focus' in client) {
                        return client.focus();
                    }
                }
                // Open a new window
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
    );
});

// ========== Message Handler ==========

self.addEventListener('message', event => {
    console.log('[SW] Message received:', event.data);
    
    if (event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data.type === 'CACHE_URLS') {
        event.waitUntil(
            caches.open(CACHE_NAME).then(cache => {
                return cache.addAll(event.data.urls);
            })
        );
    }
    
    if (event.data.type === 'CLEAR_CACHE') {
        event.waitUntil(
            caches.delete(CACHE_NAME).then(() => {
                return caches.delete(DATA_CACHE_NAME);
            })
        );
    }
    
    if (event.data.type === 'SAVE_WORK_ORDER') {
        event.waitUntil(
            saveToStore('workOrders', {
                ...event.data.workOrder,
                synced: false,
                createdOffline: true,
                timestamp: Date.now()
            })
        );
    }
    
    if (event.data.type === 'SAVE_SENSOR_READING') {
        event.waitUntil(
            saveToStore('sensorReadings', {
                ...event.data.reading,
                synced: false,
                timestamp: Date.now()
            })
        );
    }
});

// ========== Periodic Background Sync (if supported) ==========

self.addEventListener('periodicsync', event => {
    console.log('[SW] Periodic sync:', event.tag);
    
    if (event.tag === 'sync-dashboard-data') {
        event.waitUntil(refreshDashboardCache());
    }
});

async function refreshDashboardCache() {
    console.log('[SW] Refreshing dashboard cache...');
    
    const apiEndpoints = [
        '/quick-stats',
        '/analytics/kpi/summary?days=30',
        '/analytics/charts/work-order-status?days=30'
    ];
    
    for (const endpoint of apiEndpoints) {
        try {
            const response = await fetch(endpoint);
            if (response.ok) {
                const cache = await caches.open(DATA_CACHE_NAME);
                cache.put(endpoint, response);
            }
        } catch (e) {
            console.log('[SW] Failed to refresh:', endpoint);
        }
    }
}

console.log('[SW] ChatterFix Service Worker v2 loaded');
