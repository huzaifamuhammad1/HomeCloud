HOMECLOUD — STAGE 4: DEVICE PAIRING

What Stage 4 adds:
- One-time QR pairing from the Mac
- Pairing secret expires after 5 minutes
- Pairing secret can be used only once
- Random long-term device token for the iPhone
- Only the SHA-256 hash of the device token is stored in SQLite
- Token is kept in an HttpOnly browser cookie
- Protected file routes reject unpaired network devices
- Localhost access on the Mac remains available for administration
- Mac-only paired-device list
- Revoke button to immediately disable a paired phone

HOW TO PAIR:
1. Run HomeCloud normally.
2. On the Mac browser, click "Pair a phone".
3. Open the iPhone Camera app.
4. Scan the QR.
5. Tap the QR banner.
6. Tap "Pair this iPhone".
7. HomeCloud opens and the file library becomes available.

IMPORTANT:
This is ACCESS CONTROL, not internet encryption.
HomeCloud is still intended only for your trusted local Wi-Fi at Stage 4.
Do not expose port 5050 to the public internet.

Stage 5: install-like PWA experience.
Stage 6: safe remote access.
