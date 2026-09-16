const SHELL_CACHE = "homecloud-shell-v5";

const SHELL_ASSETS = [
  "/manifest.webmanifest",
  "/static/css/style.css",
  "/static/js/app.js",
  "/static/js/pwa.js",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
  "/static/icons/apple-touch-icon.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE).then((cache) => cache.addAll(SHELL_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key.startsWith("homecloud-shell-") && key !== SHELL_CACHE)
          .map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);

  if (request.method !== "GET" || url.origin !== self.location.origin) {
    return;
  }

  const isStaticShell =
    url.pathname.startsWith("/static/") ||
    url.pathname === "/manifest.webmanifest";

  if (isStaticShell) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;

        return fetch(request).then((response) => {
          const copy = response.clone();
          caches.open(SHELL_CACHE).then((cache) => cache.put(request, copy));
          return response;
        });
      })
    );
    return;
  }

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(
        () =>
          new Response(
            `<!doctype html>
            <meta name="viewport" content="width=device-width,initial-scale=1">
            <title>HomeCloud offline</title>
            <style>
              body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f4f6fb;color:#11182b;margin:0;min-height:100vh;display:grid;place-items:center;padding:24px}
              main{max-width:440px;background:white;border:1px solid #e3e7f0;border-radius:28px;padding:32px;text-align:center;box-shadow:0 24px 70px rgba(21,31,61,.09)}
              h1{letter-spacing:-.05em;margin:8px 0 12px}
              p{color:#697188;line-height:1.6}
            </style>
            <main>
              <div>☁️</div>
              <h1>Your Mac is unreachable.</h1>
              <p>HomeCloud needs your Mac to be online. Reconnect, then open the app again.</p>
            </main>`,
            {
              headers: {
                "Content-Type": "text/html; charset=utf-8",
                "Cache-Control": "no-store",
              },
            }
          )
      )
    );
  }
});
