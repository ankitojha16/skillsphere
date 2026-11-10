// SkillSphere Progressive Web App (PWA) Service Worker
const CACHE_NAME = 'skillsphere-pwa-v1';
const OFFLINE_URL = '/offline/';

const PRECACHE_ASSETS = [
    '/',
    OFFLINE_URL,
    '/static/css/style.css',
    '/static/js/main.js',
    '/static/js/pwa-install.js',
    '/static/images/pwa/icon-192.png',
    '/static/images/pwa/icon-512.png',
    '/static/images/pwa/icon-180.png',
    '/static/images/pwa/icon-32.png'
];

// Install Event: Pre-cache core shell
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(PRECACHE_ASSETS).catch((err) => {
                console.warn('[SW] Pre-caching partial failure, continuing:', err);
            });
        }).then(() => self.skipWaiting())
    );
});

// Activate Event: Clean old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cache) => {
                    if (cache !== CACHE_NAME) {
                        console.log('[SW] Clearing old cache:', cache);
                        return caches.delete(cache);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch Event: Network-First for Navigation, Cache-First for Static Assets
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Bypass non-GET requests (e.g. POST form submits, chat requests, login)
    if (request.method !== 'GET') {
        return;
    }

    // Bypass admin, API writes, and internal URLs
    if (url.pathname.startsWith('/admin/')) {
        return;
    }

    // Strategy 1: HTML Navigation (Pages) -> Network-first with offline fallback
    if (request.mode === 'navigate' || (request.headers.get('accept') && request.headers.get('accept').includes('text/html'))) {
        event.respondWith(
            fetch(request)
                .then((networkResponse) => {
                    if (networkResponse && networkResponse.status === 200) {
                        const copy = networkResponse.clone();
                        caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
                    }
                    return networkResponse;
                })
                .catch(async () => {
                    const cachedResponse = await caches.match(request);
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    const offlineShell = await caches.match(OFFLINE_URL);
                    return offlineShell || new Response('Offline - SkillSphere', {
                        headers: { 'Content-Type': 'text/html' }
                    });
                })
        );
        return;
    }

    // Strategy 2: Static assets (CSS, JS, Fonts, Images) -> Cache-first
    if (
        url.pathname.startsWith('/static/') ||
        url.hostname.includes('fonts.googleapis.com') ||
        url.hostname.includes('fonts.gstatic.com') ||
        url.hostname.includes('cdn.jsdelivr.net') ||
        url.hostname.includes('cdnjs.cloudflare.com')
    ) {
        event.respondWith(
            caches.match(request).then((cachedResponse) => {
                if (cachedResponse) {
                    return cachedResponse;
                }
                return fetch(request).then((networkResponse) => {
                    if (networkResponse && networkResponse.status === 200) {
                        const copy = networkResponse.clone();
                        caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
                    }
                    return networkResponse;
                }).catch(() => cachedResponse);
            })
        );
        return;
    }

    // Default: Network with cache fallback
    event.respondWith(
        fetch(request).catch(() => caches.match(request))
    );
});

// Listen for messages from frontend
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});
