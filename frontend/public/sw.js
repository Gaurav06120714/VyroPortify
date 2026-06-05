// VyroPortify service worker (v2.2.1).
//
// Strategy
// --------
// - Cache the offline shell at install time so an offline visitor sees
//   a branded "you're offline" page instead of Chrome's dinosaur.
// - Network-first for HTML navigations (so logged-in dashboard pages
//   stay fresh) with offline-shell fallback.
// - Stale-while-revalidate for /_next/static (immutable, hashed) so
//   repeat visits are instant.
// - Skip everything else (API, third-party). API responses contain
//   auth-stamped data and must not be cached.
//
// Versioning: bump CACHE_VERSION on any change. The activate handler
// purges anything that doesn't match.

const CACHE_VERSION = "vyro-v1";
const SHELL_CACHE = `${CACHE_VERSION}-shell`;
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const SHELL_URL = "/offline.html";

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE).then((cache) => cache.add(SHELL_URL)),
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => !k.startsWith(CACHE_VERSION))
          .map((k) => caches.delete(k)),
      ),
    ),
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  const url = new URL(request.url);

  // Skip cross-origin entirely.
  if (url.origin !== self.location.origin) return;

  // Skip API routes — auth-bound data must always be fresh.
  if (url.pathname.startsWith("/api/")) return;

  // HTML navigations: network-first, offline-shell on failure.
  //
  // B17 fix: if the precache somehow missed /offline.html (first
  // install dropped mid-fetch, storage quota hit, etc.) caches.match
  // resolves to `undefined` and respondWith(undefined) turns into a
  // hard network error on the page. The fallback chain now ends in a
  // hardcoded inline Response so the user always sees *something*
  // instead of a broken page.
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(async () => {
        const cached = await caches.match(SHELL_URL, { ignoreSearch: true });
        if (cached) return cached;
        return new Response(
          "<!doctype html><meta charset=utf-8><title>Offline</title>" +
            "<style>body{font-family:system-ui;display:flex;align-items:center;" +
            "justify-content:center;height:100dvh;margin:0;background:#fff;" +
            "color:#0b1220;text-align:center;padding:1rem}</style>" +
            "<div><h1>You're offline</h1><p>Reconnect and refresh.</p></div>",
          { status: 503, headers: { "Content-Type": "text/html; charset=utf-8" } },
        );
      }),
    );
    return;
  }

  // /_next/static assets: stale-while-revalidate.
  if (url.pathname.startsWith("/_next/static/")) {
    event.respondWith(
      caches.open(STATIC_CACHE).then(async (cache) => {
        const cached = await cache.match(request);
        const fetcher = fetch(request)
          .then((resp) => {
            if (resp.ok) cache.put(request, resp.clone());
            return resp;
          })
          .catch(() => cached);
        return cached || fetcher;
      }),
    );
  }
});
