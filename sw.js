// Service Worker — stale-while-revalidate for API, cache-first for static assets

const CACHE_NAME = 'tempest-dashboard-v1';
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/css/style.css',
    '/js/config.js',
    '/js/state.js',
    '/js/api.js',
    '/js/current.js',
    '/js/controls.js',
    '/js/charts.js',
    '/js/plugins.js',
    '/js/app.js',
    '/manifest.json',
    '/plugins.json',
    '/icons/favicon.svg',
    '/icons/icon-192.png',
    '/icons/icon-512.png',
];

const CDN_ASSETS = [
    'https://cdn.jsdelivr.net/npm/chart.js@4.5.1/dist/chart.umd.min.js',
    'https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js',
    'https://cdn.jsdelivr.net/npm/hammerjs@2.0.8/hammer.min.js',
    'https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.2.0/dist/chartjs-plugin-zoom.min.js',
];

// Install: cache static assets and CDN libraries
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll([...STATIC_ASSETS, ...CDN_ASSETS]);
        })
    );
    self.skipWaiting();
});

// Activate: clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((names) => {
            return Promise.all(
                names
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => caches.delete(name))
            );
        })
    );
    self.clients.claim();
});

// Fetch: different strategies for static vs API
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // API requests: stale-while-revalidate
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(staleWhileRevalidate(event.request));
        return;
    }

    // Static assets (same origin or CDN): cache-first
    event.respondWith(cacheFirst(event.request));
});

async function cacheFirst(request) {
    const cached = await caches.match(request);
    if (cached) return cached;

    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response.clone());
        }
        return response;
    } catch {
        return new Response('Offline', { status: 503, statusText: 'Service Unavailable' });
    }
}

async function staleWhileRevalidate(request) {
    const cache = await caches.open(CACHE_NAME);
    const cached = await cache.match(request);

    // Fetch fresh data in the background
    const fetchPromise = fetch(request)
        .then((response) => {
            if (response.ok) {
                cache.put(request, response.clone());
            }
            return response;
        })
        .catch(() => null);

    // Return cached immediately if available, otherwise wait for network
    if (cached) {
        fetchPromise; // fire and forget
        return cached;
    }

    const response = await fetchPromise;
    if (response) return response;

    return new Response(JSON.stringify({ error: 'Offline' }), {
        status: 503,
        headers: { 'Content-Type': 'application/json' },
    });
}
