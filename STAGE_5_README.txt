HOMECLOUD — STAGE 5: HOME SCREEN / PWA SHELL

What this update adds:
- Web app manifest
- HomeCloud app icon
- iPhone Home Screen / standalone metadata
- Install instructions inside HomeCloud
- Bottom mobile navigation
- Settings panel
- Multi-file upload queue
- Service worker shell prepared for HTTPS
- Offline "Mac unreachable" screen once service workers are active
- Sensitive file/API responses explicitly marked no-store

IMPORTANT IPHONE / HTTPS REALITY

Your current iPhone reaches HomeCloud using:
http://YOUR-MAC-IP:5050

iPhone can add this page to the Home Screen and launch it like an app.
However, browser service workers require a secure context. A raw local IP over
plain HTTP is not a secure context.

So at Stage 5:
- Home Screen icon: YES
- Standalone app-like launch: YES
- Manual upload/gallery/download: YES
- Multi-file selection: YES
- Protected paired-device access: YES
- Full service-worker offline behavior on the local-IP URL: NOT YET

The service-worker code is already included. It will become usable once HomeCloud
is served through HTTPS in the secure remote-access stage.

Also: a PWA cannot be trusted to continuously back up the entire iPhone photo
library in the background. That belongs to the later native-app stage.
